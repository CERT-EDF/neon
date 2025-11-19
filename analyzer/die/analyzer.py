"""Neon Detect It Easy Analyzer"""

from dataclasses import dataclass
from pathlib import Path

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.subprocess import create_subprocess_and_wait
from edf_fusion.server.config import FusionAnalyzerConfig
from edf_neon_server.analyzer import Analyzer, AnalyzerTask
from edf_neon_server.storage import Storage

_LOGGER = get_logger('analyzer.die', root='neon')


@dataclass(kw_only=True)
class DIEAnalyzerConfig(FusionAnalyzerConfig):
    """Detect It Easy Analyzer Config"""

    program: Path | None = None

    @classmethod
    def from_dict(cls, dct):
        config = super().from_dict(dct)
        config.program = Path(dct['program'])
        return config


async def _die_process_impl(
    info: AnalyzerInfo,
    config: DIEAnalyzerConfig,
    storage: Storage,
    a_task: AnalyzerTask,
) -> bool:
    sample_raw = storage.sample_raw(a_task.primary_digest)
    analysis_storage = storage.analysis_storage(
        a_task.primary_digest, info.name
    )
    analysis_storage.data_dir.mkdir(parents=True, exist_ok=True)
    argv = [str(config.program), '-u', '--verbose', str(sample_raw)]
    with analysis_storage.log.open('wb') as logf:
        logf.write(f'{argv}\n'.encode('utf-8'))
        logf.flush()
        output = analysis_storage.data_dir / 'diec.txt'
        with output.open('wb') as datf:
            success = await create_subprocess_and_wait(
                argv, stdout=datf, stderr=logf
            )
    if success:
        analysis_storage.create_archive()
    analysis_storage.remove_data_dir()
    return True


def main():
    """Analyzer entrypoint"""
    analyzer = Analyzer(
        info=AnalyzerInfo(
            name='die',
            tags={},
            version='0.1.0',
        ),
        config_cls=DIEAnalyzerConfig,
        process_impl=_die_process_impl,
    )
    analyzer.run()


if __name__ == '__main__':
    main()
