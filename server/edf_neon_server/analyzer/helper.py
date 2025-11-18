"""Analyzer Helper"""

from collections.abc import AsyncIterator
from pathlib import Path
from re import compile as regexp
from shutil import copyfileobj

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.redis import create_redis_lock
from edf_neon_core.concept import Analysis, Status
from pyzipper import AESZipFile

from ..storage import Storage
from .task import AnalyzerTask, Samples

_LOGGER = get_logger('server.analyzer.helper', root='neon')
_NAME_PATTERN = regexp(r'([a-z]+_)*[a-z]+')
_VERSION_PATTERN = regexp(r'\d+(\.\d+){2}')


def check_analyzer_info(info: AnalyzerInfo) -> bool:
    """Determine if name and version are valid"""
    if not _NAME_PATTERN.fullmatch(info.name):
        _LOGGER.critical("invalid analyzer name: '%s'", info.name)
        return False
    if not _VERSION_PATTERN.fullmatch(info.version):
        _LOGGER.critical("invalid analyzer version: '%s'", info.version)
        return False
    return True


async def set_analysis_status(
    storage: Storage, analyzer_task: AnalyzerTask, status: Status
):
    """Set analysis status"""
    await storage.update_analysis(
        analyzer_task.primary_digest,
        analyzer_task.analysis.analyzer,
        {'status': status.value},
    )


async def find_analyses(
    storage: Storage, analyzer: str
) -> AsyncIterator[str, Analysis]:
    """Find all analyzer analyses in storage"""
    async for primary_digest in storage.enumerate_primary_digests():
        analysis = await storage.retrieve_analysis(primary_digest, analyzer)
        yield primary_digest, analysis


async def find_pending_analyses(
    storage: Storage, analyzer: str
) -> AsyncIterator[str, Analysis]:
    """Find pending analyzer analyses in storage"""
    async for primary_digest, analysis in find_analyses(storage, analyzer):
        if analysis.status != Status.PENDING:
            continue
        yield primary_digest, analysis


async def perform_analyses_recovery(storage: Storage, analyzer: str) -> int:
    """Perform analysis recovery when service was stopped while ananyzing"""
    recovered = 0
    async for primary_digest, analysis in find_analyses(storage, analyzer):
        if analysis.completed:
            continue
        if analysis.status == Status.PENDING:
            continue
        await storage.update_analysis(
            primary_digest,
            analyzer,
            {'status': Status.PENDING.value},
        )
        recovered += 1
    return recovered


def _extract_sample(storage: Storage, a_task: AnalyzerTask) -> Path:
    success = False
    sample_zip = storage.sample_zip(a_task.primary_digest)
    sample_raw = storage.sample_raw(a_task.primary_digest)
    if sample_raw.is_file():
        _LOGGER.info("extraction skipped for sample %s", a_task.primary_digest)
        return True
    _LOGGER.info("extrating sample %s", a_task.primary_digest)
    try:
        with AESZipFile(str(sample_zip), 'r') as zipf:
            zipf.setpassword(a_task.primary_digest.encode('utf-8'))
            info = zipf.getinfo(a_task.primary_digest)
            with sample_raw.open('wb') as fdst:
                with zipf.open(info, 'r') as fsrc:
                    copyfileobj(fsrc, fdst)
        success = True
    except:
        _LOGGER.exception(
            "extraction failed for sample %s", a_task.primary_digest
        )
    return success


async def extract_sample(storage: Storage, a_task: AnalyzerTask) -> bool:
    """Extract sample data"""
    success = False
    lock_name = f'sample-data-lock-{a_task.primary_digest}'
    lock = create_redis_lock(storage.redis, lock_name)
    _LOGGER.info("waiting for %s", lock_name)
    async with lock:
        sample_raw = storage.sample_raw(a_task.primary_digest)
        if sample_raw.is_file():
            _LOGGER.info(
                "extraction skipped for sample %s", a_task.primary_digest
            )
            return True
        success = _extract_sample(storage, a_task)
    return success
