#!/usr/bin/env python3
"""Neon Client Test"""

from argparse import ArgumentParser
from asyncio import run, sleep
from pathlib import Path

from edf_fusion.client import (
    FusionAuthAPIClient,
    FusionCaseAPIClient,
    FusionClient,
    FusionClientConfig,
    FusionConstantAPIClient,
    FusionDownloadAPIClient,
    FusionInfoAPIClient,
    create_session,
)
from edf_fusion.helper.logging import get_logger
from edf_neon_core.concept import Case, Constant, Sample
from yarl import URL

from edf_neon_client import NeonClient

_LOGGER = get_logger('client', root='test')
_TEST_FILE = Path(__file__).parent / 'test.zip'
_TEST_SECRET = b'test'
_TEST_OUTPUT_DIR = Path('/tmp')


async def _test_retrieve_info(fusion_client: FusionClient):
    fusion_info_api_client = FusionInfoAPIClient(fusion_client=fusion_client)
    info = await fusion_info_api_client.info()
    _LOGGER.info("retrieved info: %s", info)


async def _test_retrieve_constant(fusion_client: FusionClient):
    fusion_constant_api_client = FusionConstantAPIClient(
        constant_cls=Constant, fusion_client=fusion_client
    )
    constant = await fusion_constant_api_client.constant()
    _LOGGER.info("retrieved constant: %s", constant)


async def _test_case_lifecycle(fusion_case_api_client: FusionCaseAPIClient):
    # create case
    case = await fusion_case_api_client.create_case(
        Case(tsid=None, name='T', description='D', acs={'test'})
    )
    _LOGGER.info("created case: %s", case)
    # update case
    case.report = 'test case report'
    case = await fusion_case_api_client.update_case(case)
    _LOGGER.info("updated case: %s", case)
    # retrieve case
    case = await fusion_case_api_client.retrieve_case(case.guid)
    _LOGGER.info("retrieved case: %s", case)
    # enumerate cases
    cases = await fusion_case_api_client.enumerate_cases()
    _LOGGER.info("enumerated cases: %s", cases)
    # delete case
    deleted = await fusion_case_api_client.delete_case(case.guid)
    _LOGGER.info("case deleted: %s", deleted)
    # enumerate cases
    cases = await fusion_case_api_client.enumerate_cases()
    _LOGGER.info("enumerated cases: %s", cases)


async def _test_sample_lifecycle(
    neon_client: NeonClient,
    fusion_download_api_client: FusionDownloadAPIClient,
    case: Case,
):
    # create sample
    samples = await neon_client.create_samples(
        case.guid, _TEST_SECRET, _TEST_FILE
    )
    _LOGGER.info("created samples: %s", samples)
    # update sample
    sample = samples[0]
    sample.report = 'R'
    sample = await neon_client.update_sample(case.guid, sample)
    _LOGGER.info("updated sample: %s", sample)
    # retrieve sample
    sample = await neon_client.retrieve_sample(case.guid, sample.guid)
    _LOGGER.info("retrieved sample: %s", sample)
    # retrieve case samples
    samples = await neon_client.retrieve_samples(case.guid)
    _LOGGER.info("retrieved samples (case): %s", samples)
    # download sample
    pdk = await neon_client.download_sample(case.guid, sample.guid)
    output = await fusion_download_api_client.download(pdk, _TEST_OUTPUT_DIR)
    _LOGGER.info("output: %s", output)
    # delete sample
    deleted = await neon_client.delete_sample(case.guid, sample.guid)
    _LOGGER.info("sample deleted: %s", deleted)


async def _wait_for_analyses(
    neon_client: NeonClient,
    case: Case,
    sample: Sample,
):
    while True:
        analyses = await neon_client.retrieve_analyses(case.guid, sample.guid)
        _LOGGER.info("retrieved analyses: %s", analyses)
        ready = True
        for analysis in analyses:
            ready = ready and analysis.completed
        if ready:
            break
        _LOGGER.info("waiting for analysis result to complete")
        await sleep(5)


async def _test_search(neon_client: NeonClient, sample: Sample):
    digest_hits = await neon_client.search_digest(sample.primary_digest)
    _LOGGER.info("digest hits: %s", digest_hits)


async def _test_analyzers(
    neon_client: NeonClient,
    fusion_download_api_client: FusionDownloadAPIClient,
    case: Case,
    sample: Sample,
):
    # wait for analysis to be ready
    await _wait_for_analyses(neon_client, case, sample)
    # retrieve analyzers
    analyzers = await neon_client.retrieve_analyzers()
    _LOGGER.info("retrieved analyzers: %s", analyzers)
    for analyzer in analyzers:
        # retrieve analysis log
        output = await neon_client.retrieve_analysis_log(
            case.guid, sample.guid, analyzer.name, _TEST_OUTPUT_DIR
        )
        _LOGGER.info("retrieved analysis log: %s", output)
        # download analysis data
        pdk = await neon_client.download_analysis(
            case.guid, sample.guid, analyzer.name
        )
        if not pdk:
            continue
        output = await fusion_download_api_client.download(
            pdk, _TEST_OUTPUT_DIR
        )
        _LOGGER.info("downloaded analysis data: %s", output)


async def _playbook(fusion_client: FusionClient):
    fusion_case_api_client = FusionCaseAPIClient(
        case_cls=Case, fusion_client=fusion_client
    )
    fusion_download_api_client = FusionDownloadAPIClient(
        fusion_client=fusion_client
    )
    neon_client = NeonClient(fusion_client=fusion_client)
    await _test_retrieve_info(fusion_client)
    await _test_retrieve_constant(fusion_client)
    await _test_case_lifecycle(fusion_case_api_client)
    case = await fusion_case_api_client.create_case(
        Case(tsid=None, name='T', description='D', acs={'test'})
    )
    _LOGGER.info("created case: %s", case)
    input("execution paused, press enter to continue!")
    await _test_sample_lifecycle(neon_client, fusion_download_api_client, case)
    samples = await neon_client.create_samples(
        case.guid, _TEST_SECRET, _TEST_FILE
    )
    sample = samples[0]
    await _test_search(neon_client, sample)
    await _test_analyzers(
        neon_client, fusion_download_api_client, case, sample
    )
    await neon_client.delete_sample(case.guid, sample.guid)
    await fusion_case_api_client.delete_case(case.guid)


def _parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '--api-url',
        type=URL,
        default=URL('http://neon.domain.lan/'),
        help="API URL",
    )
    return parser.parse_args()


async def app():
    """Application entrypoint"""
    args = _parse_args()
    config = FusionClientConfig(api_url=args.api_url)
    session = create_session(config, unsafe=True)
    async with session:
        fusion_client = FusionClient(config=config, session=session)
        fusion_auth_api_client = FusionAuthAPIClient(
            fusion_client=fusion_client
        )
        identity = await fusion_auth_api_client.login('test', 'test')
        if not identity:
            return
        _LOGGER.info("logged as: %s", identity)
        try:
            await _playbook(fusion_client)
        finally:
            await fusion_auth_api_client.logout()


if __name__ == '__main__':
    run(app())
