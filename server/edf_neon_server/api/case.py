"""/api/case* routes implementation"""

from collections.abc import Iterator
from io import BufferedIOBase
from pathlib import Path
from uuid import uuid4

from aiohttp.web import Request, StreamResponse
from edf_fusion.helper.aiohttp import (
    get_guid,
    get_json_body,
    json_response,
    stream_multipart_part_content,
    stream_multipart_parts,
    stream_response,
)
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.streaming import stream_from_file, stream_to_file
from edf_fusion.server.case import (
    AttachContext,
    CreateContext,
    DeleteContext,
    EnumerateContext,
    RetrieveContext,
    UpdateContext,
)
from edf_fusion.server.download import get_fusion_dl_api
from edf_fusion.server.event import get_fusion_evt_api
from edf_fusion.server.storage import get_fusion_storage
from edf_neon_core.concept import Case
from pyzipper import AESZipFile, BadZipFile

from ..helper.aiohttp import prologue

_LOGGER = get_logger('server.api.case', root='neon')


async def attach_case_impl(ctx: AttachContext) -> Case | None:
    """Attach case"""
    storage = get_fusion_storage(ctx.request)
    success = await storage.attach_case(ctx.case_guid, ctx.next_case_guid)
    if not success:
        return None
    case = await storage.retrieve_case(ctx.next_case_guid)
    return case


async def create_case_impl(ctx: CreateContext) -> Case | None:
    """Create case"""
    storage = get_fusion_storage(ctx.request)
    fusion_evt_api = get_fusion_evt_api(ctx.request)
    case = await storage.create_case(ctx.managed, ctx.body)
    if not case:
        return None
    await fusion_evt_api.notify(category='create_case', case=case)
    return case


async def update_case_impl(ctx: UpdateContext) -> Case | None:
    """Update case"""
    storage = get_fusion_storage(ctx.request)
    fusion_evt_api = get_fusion_evt_api(ctx.request)
    case = await storage.update_case(ctx.case_guid, ctx.body)
    await fusion_evt_api.notify(category='update_case', case=case)
    return case


async def delete_case_impl(ctx: DeleteContext) -> bool:
    """Delete case"""
    storage = get_fusion_storage(ctx.request)
    fusion_evt_api = get_fusion_evt_api(ctx.request)
    case = await storage.retrieve_case(ctx.case_guid)
    deleted = await storage.delete_case(ctx.case_guid)
    if deleted:
        await fusion_evt_api.notify(category='delete_case', case=case)
    return deleted


async def retrieve_case_impl(ctx: RetrieveContext) -> Case | None:
    """Retrieve case"""
    storage = get_fusion_storage(ctx.request)
    case = await storage.retrieve_case(ctx.case_guid)
    return case


async def enumerate_cases_impl(ctx: EnumerateContext) -> list[Case]:
    """Enumerate cases"""
    storage = get_fusion_storage(ctx.request)
    return [case async for case in storage.enumerate_cases()]


async def api_samples_get(request: Request):
    """Retrieve case samples"""
    case_guid = get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid GUID")
    _, storage = await prologue(
        request, 'enumerate_samples', {'case_guid': case_guid}
    )
    samples = [sample async for sample in storage.enumerate_samples(case_guid)]
    return json_response(data=[sample.to_dict() for sample in samples])


async def api_sample_get(request: Request):
    """Retrieve case sample"""
    case_guid = get_guid(request, 'case_guid')
    sample_guid = get_guid(request, 'sample_guid')
    if not case_guid or not sample_guid:
        return json_response(status=400, message="Invalid GUID")
    _, storage = await prologue(
        request,
        'retrieve_sample',
        {'case_guid': case_guid, 'sample_guid': sample_guid},
    )
    sample = await storage.retrieve_sample(case_guid, sample_guid)
    if not sample:
        return json_response(status=404, message="Sample not found")
    return json_response(data=sample.to_dict())


async def api_sample_delete(request: Request):
    """Delete case sample"""
    case_guid = get_guid(request, 'case_guid')
    sample_guid = get_guid(request, 'sample_guid')
    fusion_evt_api = get_fusion_evt_api(request)
    if not case_guid or not sample_guid:
        return json_response(status=400, message="Invalid GUID")
    _, storage = await prologue(
        request,
        'delete_sample',
        {
            'case_guid': case_guid,
            'sample_guid': sample_guid,
            'is_delete_op': True,
        },
    )
    case = await storage.retrieve_case(case_guid)
    sample = await storage.retrieve_sample(case_guid, sample_guid)
    deleted = await storage.delete_sample(case_guid, sample_guid)
    if not deleted:
        return json_response(status=400, message="Not deleted")
    await fusion_evt_api.notify(
        category='delete_sample', case=case, ext={'sample': sample.to_dict()}
    )
    return json_response()


async def api_sample_analyses_get(request: Request):
    """Enumerate case sample analyses"""
    case_guid = get_guid(request, 'case_guid')
    sample_guid = get_guid(request, 'sample_guid')
    if not case_guid or not sample_guid:
        return json_response(status=400, message="Invalid GUID")
    _, storage = await prologue(
        request,
        'enumerate_analyses',
        context={
            'case_guid': case_guid,
            'sample_guid': sample_guid,
        },
    )
    sample = await storage.retrieve_sample(case_guid, sample_guid)
    if not sample:
        return json_response(status=404, message="Sample not found")
    return json_response(
        data=[
            analysis.to_dict()
            async for analysis in storage.enumerate_analyses(
                sample.primary_digest
            )
        ]
    )


async def api_sample_analysis_log_get(request: Request) -> StreamResponse:
    """Retrieve analysis log"""
    case_guid = get_guid(request, 'case_guid')
    sample_guid = get_guid(request, 'sample_guid')
    analyzer = request.match_info['analyzer']
    if not case_guid or not sample_guid or not analyzer:
        return json_response(status=400, message="Bad request")
    _, storage = await prologue(
        request,
        'analysis_log',
        context={
            'case_guid': case_guid,
            'sample_guid': sample_guid,
            'analyzer': analyzer,
        },
    )
    sample = await storage.retrieve_sample(case_guid, sample_guid)
    if not sample:
        return json_response(status=404, message="Sample not found")
    analysis_storage = storage.analysis_storage(
        sample.primary_digest, analyzer
    )
    if not analysis_storage.log.is_file():
        return json_response(status=404, message="Analysis log not found")
    response = await stream_response(
        request,
        f'{sample_guid}_{analyzer}.log',
        stream_from_file(analysis_storage.log),
    )
    return response


async def api_sample_analysis_download_get(request: Request):
    """Retrieve analysis pending download key"""
    case_guid = get_guid(request, 'case_guid')
    sample_guid = get_guid(request, 'sample_guid')
    fusion_dl_api = get_fusion_dl_api(request)
    analyzer = request.match_info['analyzer']
    if not case_guid or not sample_guid or not analyzer:
        return json_response(status=400, message="Bad request")
    _, storage = await prologue(
        request,
        'analysis_download',
        context={
            'case_guid': case_guid,
            'sample_guid': sample_guid,
            'analyzer': analyzer,
        },
    )
    sample = await storage.retrieve_sample(case_guid, sample_guid)
    if not sample:
        return json_response(status=404, message="Sample not found")
    filepath = await storage.retrieve_analysis_data(
        sample.primary_digest, analyzer
    )
    if not filepath:
        return json_response(status=404, message="Analysis data not found")
    filename = f'{sample_guid}_{analyzer}.zip'
    pdk = await fusion_dl_api.prepare(filepath, filename)
    if not pdk:
        return json_response(
            status=503, message="Cannot process more download requests for now"
        )
    return json_response(data=pdk.to_dict())


async def api_sample_download_get(request: Request):
    """Retrieve pending download key for sample data"""
    case_guid = get_guid(request, 'case_guid')
    sample_guid = get_guid(request, 'sample_guid')
    fusion_dl_api = get_fusion_dl_api(request)
    if not case_guid or not sample_guid:
        return json_response(status=400, message="Invalid GUID")
    _, storage = await prologue(
        request,
        'sample_download',
        {'case_guid': case_guid, 'sample_guid': sample_guid},
    )
    sample = await storage.retrieve_sample(case_guid, sample_guid)
    if not sample:
        return json_response(status=400, message="Sample not found")
    sample_zip = storage.sample_zip(sample.primary_digest)
    if not sample_zip.is_file():
        return json_response(status=400, message="Sample data not available")
    pdk = await fusion_dl_api.prepare(sample_zip, sample_zip.name)
    if not pdk:
        return json_response(
            status=503, message="Cannot process more download requests for now"
        )
    return json_response(data=pdk.to_dict())


async def _receive_multipart_data(
    request: Request, archive: Path
) -> bytes | None:
    secret = None
    async for part in stream_multipart_parts(request, {'file', 'secret'}):
        if part.name == 'file' and not archive.is_file():
            await stream_to_file(archive, stream_multipart_part_content(part))
            continue
        if part.name == 'secret' and not secret:
            secret = await part.read(decode=True)
            secret = bytes(secret)
            continue
        await part.release()
    return secret


def _items_from_archive(
    archive: Path, secret: bytes
) -> Iterator[tuple[str, BufferedIOBase]]:
    with AESZipFile(str(archive), 'r') as zipf:
        zipf.setpassword(secret)
        for info in zipf.infolist():
            if info.is_dir():
                continue
            with zipf.open(info, 'r') as fobj:
                yield info.filename, fobj


async def api_sample_post(request: Request):
    """Add sample to case"""
    case_guid = get_guid(request, 'case_guid')
    fusion_evt_api = get_fusion_evt_api(request)
    if not case_guid:
        return json_response(status=400, message="Invalid GUID")
    _, storage = await prologue(
        request,
        'create_sample',
        context={'case_guid': case_guid, 'case_open_check': True},
    )
    case_storage = storage.case_storage(case_guid)
    case_storage.tmp_dir.mkdir(parents=True, exist_ok=True)
    archive = case_storage.tmp_dir / str(uuid4())
    secret = None
    # receive multipart data
    try:
        secret = await _receive_multipart_data(request, archive)
    except:
        _LOGGER.exception("failed to receive client multipart data")
        archive.unlink(missing_ok=True)
        return json_response(status=400, message="Multipart upload failed")
    # determine if archive is present
    if not archive.is_file():
        return json_response(status=400, message="Missing file in multipart")
    # determine if secret is present
    if not secret:
        archive.unlink()
        return json_response(status=400, message="Missing secret in multipart")
    # extract samples from archive
    samples = []
    try:
        for filename, fobj in _items_from_archive(archive, secret):
            sample = await storage.create_sample(case_guid, filename, fobj)
            samples.append(sample)
    except RuntimeError:
        _LOGGER.warning("invalid password")
        return json_response(status=400, message="Invalid password")
    except BadZipFile:
        _LOGGER.warning("invalid zip file")
        return json_response(status=400, message="Invalid zip file")
    finally:
        archive.unlink()
    samples = [sample.to_dict() for sample in samples]
    case = await storage.retrieve_case(case_guid)
    await fusion_evt_api.notify(
        category='create_sample', case=case, ext={'samples': samples}
    )
    return json_response(data=samples)


async def api_sample_put(request: Request):
    """Update case sample"""
    case_guid = get_guid(request, 'case_guid')
    sample_guid = get_guid(request, 'sample_guid')
    fusion_evt_api = get_fusion_evt_api(request)
    if not case_guid or not sample_guid:
        return json_response(status=400, message="Invalid GUID")
    _, storage = await prologue(
        request,
        'update_sample',
        context={
            'case_guid': case_guid,
            'sample_guid': sample_guid,
            'case_open_check': True,
        },
    )
    body = await get_json_body(request)
    sample = await storage.update_sample(case_guid, sample_guid, body)
    if not sample:
        return json_response(status=400, message="Invalid sample")
    sample = sample.to_dict()
    case = await storage.retrieve_case(case_guid)
    await fusion_evt_api.notify(
        category='update_sample', case=case, ext={'sample': sample}
    )
    return json_response(data=sample)
