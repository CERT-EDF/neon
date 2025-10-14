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
    FusionDownloadAPIClient,
    FusionInfoAPIClient,
    create_session,
)
from edf_fusion.helper.logging import get_logger
from edf_neon_core.concept import Case
from yarl import URL

from edf_neon_client import NeonClient

_LOGGER = get_logger('client', root='test')
_TMP_DIRECTORY = Path('/tmp')


async def _playbook(fusion_client: FusionClient):
    fusion_info_api_client = FusionInfoAPIClient(fusion_client=fusion_client)
    fusion_case_api_client = FusionCaseAPIClient(
        case_cls=Case, fusion_client=fusion_client
    )
    fusion_download_api_client = FusionDownloadAPIClient(
        fusion_client=fusion_client
    )
    neon_client = NeonClient(fusion_client=fusion_client)
    # retrieve server info
    info = await fusion_info_api_client.info()
    _LOGGER.info("%s", info)
    # create case
    case = await fusion_case_api_client.create_case(
        Case(
            tsid=None,
            name='test case',
            description='test description',
        )
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
    # create sample
    samples = await neon_client.create_sample(
        case.guid, b'test', Path('./test/test.zip')
    )
    _LOGGER.info("created samples: %s", samples)
    # update sample
    sample = samples[0]
    sample.report = 'test sample report'
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
    _LOGGER.info("pdk: %s", pdk)
    output = await fusion_download_api_client.download(pdk, _TMP_DIRECTORY)
    _LOGGER.info("output: %s", output)
    # wait for analysis to be ready
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
    # retrieve analyzers
    analyzers = await neon_client.retrieve_analyzers()
    _LOGGER.info("retrieved analyzers: %s", analyzers)
    for analyzer in analyzers:
        # download analysis result
        output = await neon_client.retrieve_analysis_data(
            case.guid, sample.guid, analyzer.name, _TMP_DIRECTORY
        )
        _LOGGER.info("downloaded analysis result: %s", output)


def _parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '--port', '-p', type=int, default=10000, help="Server port"
    )
    return parser.parse_args()


async def app():
    """Application entrypoint"""
    args = _parse_args()
    config = FusionClientConfig(api_url=URL(f'http://127.0.0.1:{args.port}/'))
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
