"""This module contains the main process of the robot."""

from datetime import datetime
import os
import json

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework import config
from robot_framework.sub_process import common, opus, kmd_boliglaan
from robot_framework.sub_process.statstidende import statstidende


def process(orchestrator_connection: OrchestratorConnection) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")
    arguments = json.loads(orchestrator_connection.process_arguments)

    date = datetime.now().strftime('%d-%m-%Y')

    statstidende_path = f'cases {date}.json'

    if not os.path.isfile(statstidende_path):
        statstidende.create_cases_file(statstidende_path, orchestrator_connection)

    with open(statstidende_path, 'r', encoding='utf-8') as file:
        cases = json.load(file)

    opus_name = f"Opus Statstidende {date}"
    opus_path = opus_name + ".xlsx"
    opus_text = arguments[config.EMAIL_TEXT].replace("%SYSTEM%", "OPUS")
    opus_receivers = arguments[config.OPUS_RECEIVERS]

    if not os.path.isfile(opus_path):
        opus_cases = opus.find_relevant_cases(cases, orchestrator_connection)
        opus.write_excel(opus_path, opus_cases)
        opus.delete_emails()

    boliglaan_name = f"Boliglån Statstidende {date}"
    boliglaan_path = boliglaan_name + ".xlsx"
    boliglaan_text = arguments[config.EMAIL_TEXT].replace("%SYSTEM%", "KMD Boliglån")
    boliglaan_receivers = arguments[config.BOLIGLAAN_RECEIVERS]

    if not os.path.isfile(boliglaan_path):
        boliglaan_cases = kmd_boliglaan.find_relevant_cases(cases, orchestrator_connection)
        kmd_boliglaan.write_excel(boliglaan_path, boliglaan_cases)

    # Send results
    common.send_email(opus_receivers, opus_name, opus_text, opus_path)
    common.send_email(boliglaan_receivers, boliglaan_name, boliglaan_text, boliglaan_path)
