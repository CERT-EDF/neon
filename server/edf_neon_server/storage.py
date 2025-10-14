"""Neon Storage"""

from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from functools import cached_property
from hashlib import new
from pathlib import Path
from typing import Type
from uuid import UUID

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.filesystem import GUID_GLOB, iter_guid_items
from edf_fusion.helper.flock import Flock
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.zip import create_zip
from edf_fusion.server.storage import ConceptStorage, FusionStorage
from edf_neon_core.concept import (
    Analysis,
    Case,
    Digests,
    Indicator,
    IndicatorNature,
    Sample,
)
from pyzipper import WZ_AES, AESZipFile

from .config import NeonStorageConfig

_LOGGER = get_logger('server.storage', root='neon')


async def _autopsy(name: str, content: bytes) -> Sample:
    size = len(content)
    digests = {alg: new(alg) for alg in Digests.algorithms()}
    for digest in digests.values():
        digest.update(content)
    digests = {alg: digest.hexdigest() for alg, digest in digests.items()}
    digests = Digests.from_dict(digests)
    return Sample(
        name=name,
        size=size,
        digests=digests,
        indicators=[
            Indicator(value=digests.md5, nature=IndicatorNature.MD5),
            Indicator(value=digests.sha1, nature=IndicatorNature.SHA1),
            Indicator(value=digests.sha256, nature=IndicatorNature.SHA256),
            Indicator(value=digests.sha512, nature=IndicatorNature.SHA512),
        ],
    )


def _storage_instances(
    directory: Path,
    storage_cls: Type[ConceptStorage],
    pattern: str,
) -> Iterator[ConceptStorage]:
    if not directory:
        return
    for item in directory.glob(pattern):
        if not item.is_dir():
            continue
        yield storage_cls(directory=item)


@dataclass(kw_only=True)
class AnalysisStorage(ConceptStorage):
    """Analysis Storage"""

    @cached_property
    def log(self) -> Path:
        """Engine log file"""
        return self.directory / 'analysis.log'

    def create_archive(self):
        """Create analyzer output archive"""
        create_zip(
            self.data,
            self.directory,
            files=[self.log],
            directories=[self.data_dir],
        )


@dataclass(kw_only=True)
class SampleStorage(ConceptStorage):
    """Sample storage"""


@dataclass(kw_only=True)
class CaseStorage(ConceptStorage):
    """Case storage"""

    @cached_property
    def tmp_dir(self) -> Path:
        """Temporary directory"""
        return self.directory / 'tmp'

    @cached_property
    def sample_dir(self) -> Path:
        """Sample directory"""
        return self.directory / 'sample'

    def samples(self) -> Iterator[SampleStorage]:
        """Case samples"""
        yield from _storage_instances(
            self.sample_dir, SampleStorage, GUID_GLOB
        )


@dataclass(kw_only=True)
class Storage(FusionStorage):
    """Neon Storage"""

    config: NeonStorageConfig

    @cached_property
    def data_dir(self) -> Path:
        """Sample data storage"""
        directory = self.config.directory / 'data'
        directory.mkdir(parents=False, exist_ok=True)
        return directory

    @cached_property
    def analysis_dir(self) -> Path:
        """Sample analysis storage"""
        directory = self.config.directory / 'analysis'
        directory.mkdir(parents=False, exist_ok=True)
        return directory

    @cached_property
    def temporary_dir(self) -> Path:
        """Sample temporary storage"""
        self.config.temporary.mkdir(parents=False, exist_ok=True)
        return self.config.temporary

    def sample_zip(self, primary_digest: str) -> Path:
        """Sample data file"""
        return self.data_dir / f'{primary_digest}.zip'

    def sample_raw(self, primary_digest: str) -> Path:
        """Sample data file"""
        return self.temporary_dir / f'{primary_digest}'

    def case_storage(self, case_guid: UUID) -> CaseStorage:
        """Retrieve case storage"""
        directory = self.config.directory / str(case_guid)
        return CaseStorage(directory=directory)

    def sample_storage(
        self, case_guid: UUID, sample_guid: UUID
    ) -> SampleStorage:
        """Retrieve collector storage"""
        case_storage = self.case_storage(case_guid)
        directory = case_storage.sample_dir / str(sample_guid)
        return SampleStorage(directory=directory)

    def analysis_storage(
        self, primary_digest: str, analyzer: str
    ) -> AnalysisStorage:
        """Retrieve analysis storage"""
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        directory = self.analysis_dir / primary_digest / analyzer
        return AnalysisStorage(directory=directory)

    async def attach_case(self, case_guid: UUID, next_case_guid: UUID) -> bool:
        case = await self.retrieve_case(case_guid)
        if case.managed:
            _LOGGER.warning(
                "prevented an attempt to attach a managed case: %s => %s",
                case_guid,
                next_case_guid,
            )
            return False
        case_storage = self.case_storage(case_guid)
        # update case metadata
        case.guid = next_case_guid
        case.to_filepath(case_storage.metadata)
        # rename case directory
        next_directory = case_storage.directory.parent / str(next_case_guid)
        try:
            case_storage.directory.rename(next_directory)
        except FileExistsError:
            _LOGGER.warning(
                "prevented attach logic to replace an existing case: %s => %s",
                case_guid,
                next_case_guid,
            )
            return False
        return True

    async def create_case(self, managed: bool, dct) -> Case | None:
        if managed:
            dct['managed'] = True
            case = Case.from_dict(dct)
        else:
            case = Case(
                tsid=dct.get('tsid'),
                name=dct['name'],
                description=dct['description'],
                acs=set(dct.get('acs', [])),
                report=dct.get('report'),
            )
        case_storage = self.case_storage(case.guid)
        case_storage.create()
        case.to_filepath(case_storage.metadata)
        return case

    async def update_case(self, case_guid: UUID, dct) -> Case | None:
        case_storage = self.case_storage(case_guid)
        metadata = case_storage.metadata
        if not metadata.is_file():
            _LOGGER.error("case metadata not found: %s", metadata)
            return None
        case = Case.from_filepath(metadata)
        case.update(dct)
        case.to_filepath(metadata)
        return case

    async def retrieve_case(self, case_guid: UUID) -> Case | None:
        case_storage = self.case_storage(case_guid)
        metadata = case_storage.metadata
        if not metadata.is_file():
            _LOGGER.error("case metadata not found: %s", metadata)
            return None
        return Case.from_filepath(metadata)

    async def enumerate_cases(self) -> AsyncIterator[Case]:
        for directory in iter_guid_items(self.config.directory):
            if not directory.is_dir():
                continue
            metadata = CaseStorage(directory=directory).metadata
            if not metadata.is_file():
                continue
            yield Case.from_filepath(metadata)

    async def create_sample(
        self, case_guid: UUID, name: str, content: bytes
    ) -> Sample | None:
        """Create case sample"""
        sample = await _autopsy(name, content)
        sample_zip = self.sample_zip(sample.primary_digest)
        filename = sample.digests.primary_digest
        with AESZipFile(sample_zip, 'w', encryption=WZ_AES) as zipf:
            zipf.setpassword(filename.encode('utf-8'))
            zipf.writestr(filename, content)
        sample_storage = self.sample_storage(case_guid, sample.guid)
        sample_storage.create()
        sample.to_filepath(sample_storage.metadata)
        return sample

    async def update_sample(
        self, case_guid: UUID, sample_guid: UUID, dct
    ) -> Sample | None:
        """Update case sample (MUTEX)"""
        sample_storage = self.sample_storage(case_guid, sample_guid)
        metadata = sample_storage.metadata
        async with Flock(filepath=metadata):
            if not metadata.is_file():
                _LOGGER.error("sample metadata not found: %s", metadata)
                return None
            sample = Sample.from_filepath(metadata)
            sample.update(dct)
            sample.to_filepath(metadata)
            return sample

    async def retrieve_sample(
        self, case_guid: UUID, sample_guid: UUID
    ) -> Sample | None:
        """Retrieve case sample"""
        sample_storage = self.sample_storage(case_guid, sample_guid)
        metadata = sample_storage.metadata
        if not metadata.is_file():
            _LOGGER.error("sample metadata not found: %s", metadata)
            return None
        return Sample.from_filepath(metadata)

    async def enumerate_samples(
        self, case_guid: UUID
    ) -> AsyncIterator[Sample]:
        """Enumerate case samples"""
        case_storage = self.case_storage(case_guid)
        for sample_storage in case_storage.samples():
            metadata = sample_storage.metadata
            if not metadata.is_file():
                continue
            yield Sample.from_filepath(metadata)

    async def enumerate_primary_digests(self) -> AsyncIterator[str]:
        """Enumerate samples primary digests"""
        if not self.data_dir.is_dir():
            return
        for sample_zip in self.data_dir.iterdir():
            yield sample_zip.stem

    async def retrieve_analysis(
        self, primary_digest: str, analyzer: str
    ) -> Analysis:
        """Retrieve analysis (create if needed)"""
        analysis_storage = self.analysis_storage(primary_digest, analyzer)
        metadata = analysis_storage.metadata
        if metadata.is_file():
            return Analysis.from_filepath(metadata)
        analysis_storage.create()
        analysis = Analysis(analyzer=analyzer)
        analysis.to_filepath(metadata)
        return analysis

    async def update_analysis(
        self,
        primary_digest: str,
        analyzer: str,
        dct,
    ) -> Analysis | None:
        """Restart case sample analysis"""
        analysis_storage = self.analysis_storage(primary_digest, analyzer)
        metadata = analysis_storage.metadata
        if not metadata.is_file():
            _LOGGER.error("analysis metadata not found: %s", metadata)
            return None
        analysis = Analysis.from_filepath(metadata)
        analysis.update(dct)
        analysis.to_filepath(metadata)
        return analysis

    async def retrieve_analysis_log(
        self, primary_digest: str, analyzer: str
    ) -> Path | None:
        """Retrieve case sample analysis data"""
        analysis_storage = self.analysis_storage(primary_digest, analyzer)
        log = analysis_storage.log
        if not log.is_file():
            _LOGGER.error("analysis log not found: %s", log)
            return None
        return log

    async def retrieve_analysis_data(
        self, primary_digest: str, analyzer: str
    ) -> Path | None:
        """Retrieve case sample analysis data"""
        analysis_storage = self.analysis_storage(primary_digest, analyzer)
        data = analysis_storage.data
        if not data.is_file():
            _LOGGER.error("analysis data not found: %s", data)
            return None
        return data

    async def enumerate_analyses(
        self, primary_digest: str
    ) -> AsyncIterator[Analysis]:
        """Retrieve case sample analysis"""
        directory = self.analysis_dir / primary_digest
        for item in directory.glob('*'):
            analysis_storage = self.analysis_storage(primary_digest, item.name)
            metadata = analysis_storage.metadata
            if not metadata.is_file():
                _LOGGER.warning("analysis metadata not found: %s", metadata)
                continue
            yield Analysis.from_filepath(metadata)

    async def register_analyzer(self, info: AnalyzerInfo):
        """Register an analyzer"""
        self.cache_dir.mkdir(exist_ok=True)
        metadata = self.cache_dir / f'analyzer_{info.name}.json'
        info.to_filepath(metadata)

    async def enumerate_analyzers(self) -> AsyncIterator[AnalyzerInfo]:
        """Enumerate registered analyzers"""
        for metadata in self.cache_dir.glob('analyzer_*.json'):
            yield AnalyzerInfo.from_filepath(metadata)
