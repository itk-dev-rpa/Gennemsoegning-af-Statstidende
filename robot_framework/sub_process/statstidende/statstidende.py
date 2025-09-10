"""This module is responsible for collecting data from the Statstidende API."""

from datetime import datetime, timedelta
import json
import time

import requests
from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from hvac import Client

from robot_framework import config
from robot_framework.sub_process.statstidende import doedsboer, gaeldssaneringer, konkursboer, tvangsauktioner


def load_statstidende_cases(days: int, orchestrator_connection: OrchestratorConnection) -> tuple[dict]:
    """Load the data from Statstidende from today and the given number
    of days back in time. The data is returned as four dicts for each category of cases.

    Args:
        days: The number of days to go back and retrieve data from including today.
        orchestrator_connection: The connection to OpenOrchestrator.

    Returns:
        Four dictionaries with (dødsboer, gældssaneringer, konkursboer, tvangsauktioner)
    """
    doedsboer_cases = {}
    tvangsauktioner_cases = {}
    gaeldssaneringer_cases = {}
    konkursboer_cases = {}

    today = datetime.now().date()

    for i in range(days):
        date = today + timedelta(days=-i)
        data = get_api_data(date.strftime("%Y-%m-%d"), orchestrator_connection)

        if data:
            # Combine case data with data from other days
            doedsboer_cases |= doedsboer.get_doedsboer(data)
            tvangsauktioner_cases |= tvangsauktioner.get_tvangsauktioner(data)
            konkursboer_cases |= konkursboer.get_konkursboer(data)

            # There might be multiple gældssaneringer per debitor_id.
            # Combine the results as lists
            temp_gaeldssaneringer = gaeldssaneringer.get_gaeldssaneringer(data)
            for foedselsdato, case_list in temp_gaeldssaneringer.items():
                if foedselsdato in gaeldssaneringer_cases:
                    gaeldssaneringer_cases[foedselsdato] += case_list
                else:
                    gaeldssaneringer_cases[foedselsdato] = case_list

    if len(doedsboer_cases) == 0 or len(doedsboer_cases) == 0 or len(gaeldssaneringer_cases) == 0 or len(konkursboer_cases) == 0 or len(tvangsauktioner_cases) == 0:
        raise RuntimeError(f"Got an unexpected number of cases from Statstidende: Dødsboer: {len(doedsboer_cases)}. Gældssaneringer: {len(gaeldssaneringer_cases)}. Konkursboer: {len(konkursboer_cases)}. Tvangsauktioner: {len(tvangsauktioner_cases)}.")

    orchestrator_connection.log_info(f'Fra statstidende: Dødsboer: {len(doedsboer_cases)}. Gældssaneringer: {len(gaeldssaneringer_cases)}. Konkursboer: {len(konkursboer_cases)}. Tvangsauktioner: {len(tvangsauktioner_cases)}.')

    return (doedsboer_cases, gaeldssaneringer_cases, konkursboer_cases, tvangsauktioner_cases)


def get_api_data(date: str, orchestrator_connection: OrchestratorConnection) -> dict | None:
    """Get the data from Statstidende on the given date.

    Args:
        date: The date to retrieve data from in yyyy-mm-dd format.
        orchestrator_connection: The connection to OpenOrchestrator.

    Returns:
        The response json if any.
    """
    # Join all the relevant message types
    message_types = [f"&messagetypes={t}" for t in doedsboer.DOEDSBOER_KEYS]
    message_types += [f"&messagetypes={t}" for t in gaeldssaneringer.GAELDSSANERINGER_KEYS]
    message_types += [f"&messagetypes={t}" for t in konkursboer.KONKURSBOER_KEYS]
    message_types += [f"&messagetypes={t}" for t in tvangsauktioner.TVANGSAUKTIONER_KEYS]
    message_types = "".join(message_types)

    url = f"https://api.statstidende.dk/v1/messages?publicationdate={date}{message_types}"
    orchestrator_connection.log_info(f"Fetching Statstidende data from: {date}")

    session = requests.Session()
    session.cert = get_certification_file(orchestrator_connection)

    for _ in range(10):
        response = session.get(url)
        status = response.status_code

        if status == 200:
            return response.json()

        if status == 429:
            time.sleep(2)
        else:
            return None

    return None


def create_cases_file(path: str, orchestrator_connection: OrchestratorConnection):
    """Get data from Statstidende for the last 7 days and dump it in a text file.

    Args:
        path: The path to save the file on.
    """
    cases = load_statstidende_cases(days=7, orchestrator_connection=orchestrator_connection)

    with open(path, 'w', encoding='utf-8') as file:
        json.dump(cases, file, indent=4, ensure_ascii=False)


def get_certification_file(orchestrator_connection: OrchestratorConnection) -> str:
    """Get the certificate from the key vault and write it to a file.

    Args:
        orchestrator_connection: The connection to Orchestrator.

    Returns:
        The path to the certificate file.
    """
    # Access Key vault
    vault_auth = orchestrator_connection.get_credential(config.KEYVAULT_CREDENTIALS)
    vault_uri = orchestrator_connection.get_constant(config.KEYVAULT_URI).value
    vault_client = Client(vault_uri)
    token = vault_client.auth.approle.login(role_id=vault_auth.username, secret_id=vault_auth.password)
    vault_client.token = token['auth']['client_token']

    # Get certificate
    read_response = vault_client.secrets.kv.v2.read_secret_version(mount_point='rpa', path=config.KEYVAULT_PATH, raise_on_deleted_version=True)
    certificate = read_response['data']['data']['cert']

    # Write to file
    certificate_path = "certificate.pem"
    with open(certificate_path, 'w', encoding='utf-8') as cert_file:
        cert_file.write(certificate)

    return certificate_path