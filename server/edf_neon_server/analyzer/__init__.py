"""Neon Analyzer ABC"""

from argparse import ArgumentParser
from asyncio import (
    Event,
    Queue,
    create_task,
    gather,
    get_running_loop,
    run,
    sleep,
    wait_for,
)
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from signal import SIGINT, SIGTERM

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.redis import Redis, create_redis, close_redis
from edf_fusion.server.config import (
    FusionAnalyzerConfig,
    FusionAnalyzerConfigType,
)
from edf_neon_core.concept import Status

from ..config import NeonServerConfig
from ..storage import Storage
from .helper import (
    check_analyzer_info,
    extract_sample,
    find_pending_analyses,
    find_related_samples,
    perform_analyses_recovery,
    set_analysis_status,
)
from .task import AnalyzerTask

_LOGGER = get_logger('server.analyzer', root='neon')


class AnalyzerError(Exception):
    """Analyzer error"""


@dataclass(kw_only=True)
class Analyzer:
    """Neon Hayabusa Analyzer"""

    info: AnalyzerInfo
    config_cls: FusionAnalyzerConfigType
    process_impl: Callable[
        [AnalyzerInfo, FusionAnalyzerConfig, Storage, AnalyzerTask],
        Awaitable[bool],
    ]
    _event: Event = field(default_factory=Event)
    _redis: Redis | None = None
    _queue: Queue = field(default_factory=Queue)
    _config: FusionAnalyzerConfig | None = None
    _storage: Storage | None = None

    @property
    def config(self) -> FusionAnalyzerConfig:
        """Analyzer configuration"""
        return self._config

    @property
    def storage(self) -> Storage:
        """Neon server storage"""
        return self._storage

    def _shutdown(self):
        _LOGGER.warning("shutdown requested")
        self._event.set()

    def _parse_args(self):
        parser = ArgumentParser(description="")
        parser.add_argument(
            '--config',
            '-c',
            type=Path,
            default=Path('neon.yml'),
            help="Neon configuration file",
        )
        return parser.parse_args()

    async def _startup(self, a_task: AnalyzerTask) -> bool:
        await set_analysis_status(self.storage, a_task, Status.EXTRACTING)
        extracted = await extract_sample(self.storage, a_task)
        if not extracted:
            raise AnalyzerError("extracted data is not available")

    async def _cleanup(self, a_task: AnalyzerTask, success: bool):
        status = Status.SUCCESS if success else Status.FAILURE
        await set_analysis_status(self.storage, a_task, status)

    async def _consumer(self):
        while not self._event.is_set():
            try:
                a_task = await wait_for(self._queue.get(), 5)
            except TimeoutError:
                continue
            _LOGGER.info(
                "analyzer %s processing sample %s",
                a_task.analysis.analyzer,
                a_task.primary_digest,
            )
            success = False
            try:
                await self._startup(a_task)
                await set_analysis_status(
                    self.storage, a_task, Status.PROCESSING
                )
                success = await self.process_impl(
                    self.info, self._config, self.storage, a_task
                )
            except AnalyzerError as exc:
                _LOGGER.error("analyzer error: %s", exc)
            finally:
                await self._cleanup(a_task, success)

    async def _producer(self):
        _LOGGER.info("producer is starting...")
        while not self._event.is_set():
            _LOGGER.info("producer is looking for pending analyses...")
            async for primary_digest, analysis in find_pending_analyses(
                self.storage, self.info.name
            ):
                samples = await find_related_samples(
                    self.storage, primary_digest
                )
                a_task = AnalyzerTask(
                    primary_digest=primary_digest,
                    analysis=analysis,
                    samples=samples,
                )
                _LOGGER.info("producer queueing analysis %s", analysis.guid)
                await self._queue.put(a_task)
                await set_analysis_status(self.storage, a_task, Status.QUEUED)
            try:
                await wait_for(self._event.wait(), 30)
            except TimeoutError:
                continue
        _LOGGER.info("producer shutdown")

    async def _arun(self):
        loop = get_running_loop()
        for sig in (SIGINT, SIGTERM):
            loop.add_signal_handler(sig, self._shutdown)
        _LOGGER.info("registering analyzer %s", self.info.name)
        if not check_analyzer_info(self.info):
            return
        await self._storage.register_analyzer(self.info)
        _LOGGER.info("registered %s", self.info.name)
        try:
            _LOGGER.info("analyses recovery in progress...")
            recovered = await perform_analyses_recovery(
                self.storage, self.info.name
            )
            _LOGGER.info("recovered %d analyses...", recovered)
            coros = [self._producer()]
            coros.extend([self._consumer() for _ in range(self.config.workers)])
            await gather(*coros)
        finally:
            await close_redis(self._redis)
            self._redis = None

    def run(self):
        """Prepare analyzer and start analysis loop"""
        args = self._parse_args()
        try:
            config = NeonServerConfig.from_filepath(args.config)
            self._redis = create_redis(config.server.redis_url)
            self._config = config.analyzer.get(self.info.name, self.config_cls)
        except:
            _LOGGER.exception("invalid configuration file: %s", args.config)
            return
        if not self.config.enabled:
            _LOGGER.warning("%s analyzer is disabled.", self.info.name)
            return
        self._storage = Storage(redis=self._redis, config=config.storage)
        run(self._arun())
