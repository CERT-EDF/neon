"""/api/config* routes implementation"""

from aiohttp.web import Request
from edf_fusion.helper.aiohttp import json_response
from edf_fusion.server.config import FusionAnalyzerConfig

from ..config import get_neon_config
from ..helper.aiohttp import prologue


async def api_analyzers_get(request: Request):
    """Retrieve analyzers config"""
    _, storage = await prologue(request, 'enumerate_analyzers')
    config = get_neon_config(request)
    analyzers = []
    async for analyzer in storage.enumerate_analyzers():
        analyzer_config = config.analyzer.get(
            analyzer.name, FusionAnalyzerConfig
        )
        if not analyzer_config.enabled:
            continue
        analyzers.append(analyzer.to_dict())
    return json_response(data=analyzers)
