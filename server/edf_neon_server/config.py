"""Configuration"""

from dataclasses import dataclass
from pathlib import Path

from aiohttp.web import Application, Request
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.serializing import Loadable
from edf_fusion.server.auth import FusionAuthAPIConfig
from edf_fusion.server.case import FusionCaseAPIConfig
from edf_fusion.server.config import (
    FusionAnalyzerMapping,
    FusionServerConfig,
    FusionStorageConfig,
    FusionSynchronizerConfig,
)
from edf_fusion.server.constant import FusionConstantAPIConfig
from edf_fusion.server.download import FusionDownloadAPIConfig
from edf_fusion.server.event import FusionEventAPIConfig
from edf_fusion.server.info import FusionInfoAPIConfig

_LOGGER = get_logger('server.config', root='neon')
_NEON_CONFIG = '__neon_config'


@dataclass(kw_only=True)
class NeonStorageConfig(FusionStorageConfig):
    """Neon Storage Config"""

    temporary: Path | None = None

    @classmethod
    def from_dict(cls, dct: dict):
        config = super().from_dict(dct)
        config.temporary = Path(dct['temporary'])
        return config


@dataclass(kw_only=True)
class NeonServerConfig(Loadable):
    """Neon configuration"""

    server: FusionServerConfig
    storage: NeonStorageConfig
    auth_api: FusionAuthAPIConfig
    case_api: FusionCaseAPIConfig
    info_api: FusionInfoAPIConfig
    event_api: FusionEventAPIConfig
    constant_api: FusionConstantAPIConfig
    download_api: FusionDownloadAPIConfig
    synchronizer: FusionSynchronizerConfig
    analyzer: FusionAnalyzerMapping

    @classmethod
    def from_dict(cls, dct):
        return cls(
            server=FusionServerConfig.from_dict(dct['server']),
            storage=NeonStorageConfig.from_dict(dct['storage']),
            auth_api=FusionAuthAPIConfig.from_dict(dct['auth_api']),
            case_api=FusionCaseAPIConfig.from_dict(dct['case_api']),
            info_api=FusionInfoAPIConfig.from_dict(dct['info_api']),
            event_api=FusionEventAPIConfig.from_dict(dct['event_api']),
            constant_api=FusionConstantAPIConfig.from_dict(
                dct['constant_api']
            ),
            download_api=FusionDownloadAPIConfig.from_dict(
                dct['download_api']
            ),
            synchronizer=FusionSynchronizerConfig.from_dict(
                dct['synchronizer']
            ),
            analyzer=FusionAnalyzerMapping.from_dict(dct['analyzer']),
        )

    def setup(self, webapp: Application):
        """Register config in webapp context"""
        webapp[_NEON_CONFIG] = self


def get_neon_config(app_or_req: Application | Request) -> NeonServerConfig:
    """Retrieve config from webapp context"""
    if isinstance(app_or_req, Request):
        app_or_req = app_or_req.app
    return app_or_req[_NEON_CONFIG]
