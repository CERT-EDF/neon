"""Neon Case Synchronizer"""

from argparse import ArgumentParser
from pathlib import Path
from shutil import copy

from edf_fusion.concept import Case
from edf_fusion.helper.logging import get_logger
from edf_fusion.server.storage import SyncStorage
from edf_fusion.server.synchronizer import FusionSynchronizer

from .__version__ import version
from .config import NeonServerConfig
from .storage import Storage

_LOGGER = get_logger('synchronizer', root='neon')


async def _sync_case_impl(storage: Storage, case: Case, directory: Path):
    sync_storage = SyncStorage(case=case, directory=directory)
    # sync case report
    report = sync_storage.reports / 'neon_case.md'
    report.write_text(case.report, encoding='utf-8')
    async for sample in storage.enumerate_samples(case.guid):
        # sync sample report
        name = f'neon_sample_{sample.primary_digest}.md'
        report = sync_storage.reports / name
        report.write_text(sample.report, encoding='utf-8')
        # sync sample metadata
        metadata = sync_storage.samples / f'{sample.primary_digest}.json'
        sample.to_filepath(metadata)
        # sync sample data
        stored = storage.sample_zip(sample.primary_digest)
        synced = sync_storage.samples / stored.name
        copy(stored, synced)


def _parse_args():
    parser = ArgumentParser(description="Neon Synchronizer")
    parser.add_argument(
        '--config',
        '-c',
        type=Path,
        default=Path('neon.yml'),
        help="Configuration file",
    )
    return parser.parse_args()


def app():
    """Application entrypoint"""
    _LOGGER.info("Neon Synchronizer %s", version)
    args = _parse_args()
    config = NeonServerConfig.from_filepath(args.config)
    synchronizer = FusionSynchronizer(
        config=config.synchronizer,
        storage=Storage(config=config.storage),
        sync_case_impl=_sync_case_impl,
    )
    synchronizer.run()


if __name__ == '__main__':
    app()
