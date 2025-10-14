"""Neon FLOSS Analyzer"""

from dataclasses import dataclass
from pathlib import Path

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.subprocess import create_subprocess_and_wait
from edf_fusion.server.config import FusionAnalyzerConfig
from edf_neon_server.analyzer import Analyzer, AnalyzerTask
from edf_neon_server.storage import Storage

_LOGGER = get_logger('analyzer.floss', root='neon')


@dataclass(kw_only=True)
class FLOSSAnalyzerConfig(FusionAnalyzerConfig):
    """FLOSS Analyzer Config"""

    program: Path | None = None

    @classmethod
    def from_dict(cls, dct):
        config = super().from_dict(dct)
        config.program = Path(dct['program'])
        return config


async def _floss_process_impl(
    info: AnalyzerInfo,
    config: FLOSSAnalyzerConfig,
    storage: Storage,
    a_task: AnalyzerTask,
) -> bool:
    sample_raw = storage.sample_raw(a_task.primary_digest)
    argv = [
        str(config.program),
        '--color',
        'never',
        str(sample_raw),
    ]
    analysis_storage = storage.analysis_storage(
        a_task.primary_digest, info.name
    )
    analysis_storage.data_dir.mkdir(parents=True, exist_ok=True)
    output = analysis_storage.data_dir / 'output.txt'
    with analysis_storage.log.open('wb') as logf:
        with output.open('wb') as datf:
            success = await create_subprocess_and_wait(
                argv, stdout=datf, stderr=logf
            )
    if success:
        analysis_storage.create_archive()
    analysis_storage.remove_data_dir()
    return success


def main():
    """Analyzer entrypoint"""
    analyzer = Analyzer(
        info=AnalyzerInfo(
            name='floss',
            tags={},
            version='0.1.0',
        ),
        config_cls=FLOSSAnalyzerConfig,
        process_impl=_floss_process_impl,
    )
    analyzer.run()


if __name__ == '__main__':
    main()
