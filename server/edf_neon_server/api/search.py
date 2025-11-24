"""/api/search* routes implementation"""

from re import compile as regexp

from aiohttp.web import Request
from edf_fusion.helper.aiohttp import json_response
from edf_fusion.server.auth import get_fusion_auth_api
from edf_neon_core.concept import CaseHit, DigestHits

from ..helper.aiohttp import prologue

_PRIMARY_DIGEST_PATTERN = regexp(r'[a-f\d]{64}')


def _get_primary_digest(request: Request) -> str | None:
    """Get primary digest from request match info"""
    try:
        primary_digest = request.match_info['primary_digest'].lower()
    except ValueError:
        return None
    if not _PRIMARY_DIGEST_PATTERN.fullmatch(primary_digest):
        return None
    return primary_digest


async def api_search_digest_get(request: Request):
    """Search samples for given digest"""
    primary_digest = _get_primary_digest(request)
    if not primary_digest:
        return json_response(status=400, message="Bad primary digest")
    identity, storage = await prologue(request, 'search_digest')
    fusion_auth_api = get_fusion_auth_api(request)
    sample_zip = storage.sample_zip(primary_digest)
    if not sample_zip.is_file():
        return json_response(status=404, message="Digest not found")
    digest_hits = DigestHits()
    async for case, sample in storage.enumerate_related_samples(
        primary_digest
    ):
        digest_hits.total += 1
        if fusion_auth_api.can_access_case(case, identity):
            digest_hits.hits.append(CaseHit(case=case, sample=sample))
    return json_response(data=digest_hits)
