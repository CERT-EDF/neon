"""Neon Content Type Analyzer"""

from dataclasses import dataclass
from json import loads
from pathlib import Path

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.subprocess import create_subprocess_and_wait
from edf_fusion.server.config import FusionAnalyzerConfig
from edf_neon_core.concept import OperatingSystem
from edf_neon_server.analyzer import Analyzer, AnalyzerTask
from edf_neon_server.storage import Storage

_LOGGER = get_logger('analyzer.ct', root='neon')
_MAGIKA_LABEL_OS_MAPPING = (
    (OperatingSystem.IOS, {}),
    (OperatingSystem.LINUX, {'deb', 'elf', 'coff', 'rpm', 'squashfs', 'snap'}),
    (OperatingSystem.DARWIN, {'applebplist', 'appleplist', 'dmg', 'dsstore'}),
    (OperatingSystem.ANDROID, {'apk', 'dex'}),
    (
        OperatingSystem.WINDOWS,
        {
            'outlook',
            'mscompress',
            'asp',
            'autohotkey',
            'autoit',
            'pdb',
            'thumbsdb',
            'pebin',
            'one',
            'msi',
            'lnk',
            'doc',
            'docx',
            'powershell',
            'ppt',
            'pptx',
            'cat',
            'chm',
            'cab',
            'vba',
            'winregistry',
            'xar',
            'xls',
            'xlsb',
            'xlsx',
        },
    ),
)


def _parse_magika_output(magika_output: Path):
    ct_label = None
    with magika_output.open('r', encoding='utf-8') as fobj:
        for line in fobj:
            line = line.strip()
            if not line.startswith('{'):
                continue
            dct = loads(line)
            result = dct.get('result', {})
            value = result.get('value', {})
            output = value.get('output', {})
            ct_label = output.get('label')
    return ct_label


@dataclass(kw_only=True)
class ContentTypeAnalyzerConfig(FusionAnalyzerConfig):
    """Content Type Analyzer Config"""

    program_ent: Path | None = None
    program_file: Path | None = None
    program_magika: Path | None = None

    @classmethod
    def from_dict(cls, dct):
        config = super().from_dict(dct)
        config.program_ent = Path(dct['program_ent'])
        config.program_file = Path(dct['program_file'])
        config.program_magika = Path(dct['program_magika'])
        return config


async def _ct_process_impl(
    info: AnalyzerInfo,
    config: ContentTypeAnalyzerConfig,
    storage: Storage,
    a_task: AnalyzerTask,
) -> bool:
    sample_raw = storage.sample_raw(a_task.primary_digest)
    analysis_storage = storage.analysis_storage(
        a_task.primary_digest, info.name
    )
    analysis_storage.data_dir.mkdir(parents=True, exist_ok=True)
    magika_output = analysis_storage.data_dir / 'magika.jsonl'
    specs = (
        (
            [
                str(config.program_magika),
                '--no-colors',
                '--jsonl',
                str(sample_raw),
            ],
            magika_output.name,
        ),
        (
            [str(config.program_file), '--mime-type', str(sample_raw)],
            'file_mime_type.txt',
        ),
        ([str(config.program_file), str(sample_raw)], 'file.txt'),
        ([str(config.program_ent), str(sample_raw)], 'ent.txt'),
    )
    with analysis_storage.log.open('wb') as logf:
        for argv, filename in specs:
            logf.write(b'========================================\n')
            logf.write(str(argv).encode('utf-8'))
            logf.write(b'\n')
            logf.write(b'----------------------------------------\n')
            logf.flush()
            output = analysis_storage.data_dir / filename
            with output.open('wb') as datf:
                success = await create_subprocess_and_wait(
                    argv, stdout=datf, stderr=logf
                )
                if not success:
                    return False
    # parse output and enrich sample
    ct_label = _parse_magika_output(magika_output)
    if not ct_label:
        return False
    opsystem = OperatingSystem.ANY
    for candidate, ct_labels in _MAGIKA_LABEL_OS_MAPPING:
        if ct_label in ct_labels:
            opsystem = candidate
            break
    for case, sample in a_task.samples:
        sample.opsystem = opsystem
        sample.tags.update({ct_label, sample.opsystem.value})
        await storage.update_sample(case.guid, sample.guid, sample.to_dict())
    if success:
        analysis_storage.create_archive()
    analysis_storage.remove_data_dir()
    return True


def main():
    """Analyzer entrypoint"""
    analyzer = Analyzer(
        info=AnalyzerInfo(
            name='content_type',
            tags={},
            version='0.1.0',
        ),
        config_cls=ContentTypeAnalyzerConfig,
        process_impl=_ct_process_impl,
    )
    analyzer.run()


if __name__ == '__main__':
    main()
