"""This module is responsible for collecting data from the Statstidende API."""

from datetime import datetime, timedelta
import json
import time
import os

import requests
from cryptography.fernet import Fernet
from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

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
    """Finds the encrypted certificate and decrypts it to the working dir.

    Args:
        orchestrator_connection: The connection to OpenOrchestrator.

    Returns:
        The path to the decrypted file.
    """
    locked_cert_path = json.loads(orchestrator_connection.process_arguments)[config.CERT_PATH]
    locked_cert_path = os.path.expanduser(locked_cert_path)

    crypto_key = orchestrator_connection.get_credential(config.STATSTIDENDE_KEY).password
    cipher = Fernet(crypto_key)

    unlocked_cert_path = "Certifikat.pem"

    with open(locked_cert_path, 'rb') as locked_file, open(unlocked_cert_path, 'wb') as unlocked_file:
        data = locked_file.read()
        data = cipher.decrypt(data)
        unlocked_file.write(data)

    return unlocked_cert_path
