"""Neon Client"""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aiohttp import FormData
from edf_fusion.client import FusionClient
from edf_fusion.concept import AnalyzerInfo, PendingDownloadKey
from edf_fusion.helper.logging import get_logger
from edf_neon_core.concept import Analysis, Sample

_LOGGER = get_logger('client', root='neon')


@dataclass(kw_only=True)
class NeonClient:
    """Neon Client"""

    fusion_client: FusionClient

    async def retrieve_samples(self, case_guid: UUID) -> list[Sample] | None:
        """Retrieve samples"""
        endpoint = f'/api/case/{case_guid}/samples'
        return await self.fusion_client.get(endpoint, concept_cls=Sample)

    async def create_samples(
        self, case_guid: UUID, secret: bytes, filepath: Path
    ) -> list[Sample] | None:
        """Create sample"""
        _LOGGER.info("uploading archive %s in case %s", filepath, case_guid)
        endpoint = f'/api/case/{case_guid}/sample'
        data = FormData()
        data.add_field('secret', secret)
        data.add_field('file', filepath.open('rb'), filename=filepath.name)
        return await self.fusion_client.post(
            endpoint, concept_cls=Sample, data=data
        )

    async def update_sample(
        self, case_guid: UUID, sample: Sample
    ) -> Sample | None:
        """Update sample"""
        _LOGGER.info("updating sample %s in case %s", sample.guid, case_guid)
        endpoint = f'/api/case/{case_guid}/sample/{sample.guid}'
        return await self.fusion_client.put(
            endpoint, sample, concept_cls=Sample
        )

    async def delete_sample(self, case_guid: UUID, sample_guid: UUID) -> bool:
        """Delete sample"""
        _LOGGER.info("deleting sample %s in case %s", sample_guid, case_guid)
        endpoint = f'/api/case/{case_guid}/sample/{sample_guid}'
        return await self.fusion_client.delete(endpoint)

    async def retrieve_sample(
        self, case_guid: UUID, sample_guid: UUID
    ) -> Sample | None:
        """Retrieve sample"""
        endpoint = f'/api/case/{case_guid}/sample/{sample_guid}'
        return await self.fusion_client.get(endpoint, concept_cls=Sample)

    async def download_sample(
        self, case_guid: UUID, sample_guid: UUID
    ) -> PendingDownloadKey | None:
        """Download sample"""
        _LOGGER.info(
            "downloading sample %s in case %s", sample_guid, case_guid
        )
        endpoint = f'/api/case/{case_guid}/sample/{sample_guid}/download'
        return await self.fusion_client.get(
            endpoint, concept_cls=PendingDownloadKey
        )

    async def retrieve_analyses(
        self, case_guid: UUID, sample_guid: UUID
    ) -> list[Analysis] | None:
        """Retrieve sample analyses"""
        endpoint = f'/api/case/{case_guid}/sample/{sample_guid}/analyses'
        return await self.fusion_client.get(endpoint, concept_cls=Analysis)

    async def download_analysis(
        self, case_guid: UUID, sample_guid: UUID, analyzer: str
    ) -> PendingDownloadKey | None:
        """Download analysis"""
        _LOGGER.info(
            "downloading analysis %s for sample %s in case %s",
            analyzer,
            sample_guid,
            case_guid,
        )
        endpoint = f'/api/case/{case_guid}/sample/{sample_guid}/analysis/{analyzer}/download'
        return await self.fusion_client.get(
            endpoint, concept_cls=PendingDownloadKey
        )

    async def retrieve_analysis_log(
        self, case_guid: UUID, sample_guid: UUID, analyzer: str, output: Path
    ) -> Path | None:
        """Retrieve sample analysis"""
        endpoint = f'/api/case/{case_guid}/sample/{sample_guid}/analysis/{analyzer}/log'
        return await self.fusion_client.download(endpoint, output)

    async def retrieve_analyzers(self) -> list[AnalyzerInfo]:
        """Retrieve analyzers"""
        endpoint = '/api/config/analyzers'
        return await self.fusion_client.get(endpoint, concept_cls=AnalyzerInfo)
