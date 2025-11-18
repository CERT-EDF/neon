"""Neon API module"""

from aiohttp.web import Application, delete, get, post, put
from edf_fusion.helper.logging import get_logger

from .case import (
    api_sample_analyses_get,
    api_sample_analysis_download_get,
    api_sample_analysis_log_get,
    api_sample_delete,
    api_sample_download_get,
    api_sample_get,
    api_sample_post,
    api_sample_put,
    api_samples_get,
    attach_case_impl,
    create_case_impl,
    delete_case_impl,
    enumerate_cases_impl,
    retrieve_case_impl,
    update_case_impl,
)
from .config import api_analyzers_get

_LOGGER = get_logger('server.api', root='neon')


def setup_api(webapp: Application):
    """Setup webapp routes"""
    _LOGGER.info("install neon api...")
    webapp.add_routes(
        [
            get('/api/case/{case_guid}/samples', api_samples_get),
            post('/api/case/{case_guid}/sample', api_sample_post),
            put(
                '/api/case/{case_guid}/sample/{sample_guid}',
                api_sample_put,
            ),
            delete(
                '/api/case/{case_guid}/sample/{sample_guid}',
                api_sample_delete,
            ),
            get(
                '/api/case/{case_guid}/sample/{sample_guid}',
                api_sample_get,
            ),
            get(
                '/api/case/{case_guid}/sample/{sample_guid}/download',
                api_sample_download_get,
            ),
            get(
                '/api/case/{case_guid}/sample/{sample_guid}/analyses',
                api_sample_analyses_get,
            ),
            get(
                '/api/case/{case_guid}/sample/{sample_guid}/analysis/{analyzer}/log',
                api_sample_analysis_log_get,
            ),
            get(
                '/api/case/{case_guid}/sample/{sample_guid}/analysis/{analyzer}/download',
                api_sample_analysis_download_get,
            ),
            get('/api/config/analyzers', api_analyzers_get),
        ]
    )
    _LOGGER.info("neon api installed.")
