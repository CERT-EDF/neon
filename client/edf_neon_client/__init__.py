"""Neon Client"""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aiohttp import FormData
from edf_fusion.client import FusionClient
from edf_fusion.concept import AnalyzerInfo, PendingDownloadKey
from edf_neon_core.concept import Analysis, Sample


@dataclass(kw_only=True)
class NeonClient:
    """Neon Client"""

    fusion_client: FusionClient

    async def retrieve_samples(self, case_guid: UUID) -> list[Sample] | None:
        """Retrieve samples"""
        endpoint = f'/api/case/{case_guid}/samples'
        return await self.fusion_client.get(endpoint, concept_cls=Sample)

    async def create_sample(
        self, case_guid: UUID, secret: bytes, filepath: Path
    ) -> list[Sample] | None:
        """Create sample"""
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
        endpoint = f'/api/case/{case_guid}/sample/{sample.guid}'
        return await self.fusion_client.put(
            endpoint, sample, concept_cls=Sample
        )

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

    async def retrieve_analysis_data(
        self,
        case_guid: UUID,
        sample_guid: UUID,
        analyzer: str,
        output: Path,
    ) -> Path | None:
        """Retrieve sample analysis"""
        endpoint = f'/api/case/{case_guid}/sample/{sample_guid}/analysis/{analyzer}/data'
        return await self.fusion_client.download(endpoint, output)

    async def retrieve_analyzers(self) -> list[AnalyzerInfo]:
        """Retrieve analyzers"""
        endpoint = '/api/config/analyzers'
        return await self.fusion_client.get(endpoint, concept_cls=AnalyzerInfo)
