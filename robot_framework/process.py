"""This module contains the main process of the robot."""

from datetime import datetime
import os
import json

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
import itk_dev_event_log

from robot_framework import config
from robot_framework.sub_process import common, opus, kmd_boliglaan
from robot_framework.sub_process.statstidende import statstidende


def process(orchestrator_connection: OrchestratorConnection) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")
    arguments = json.loads(orchestrator_connection.process_arguments)
    opus_receivers = arguments[config.OPUS_RECEIVERS]
    boliglaan_receivers = arguments[config.BOLIGLAAN_RECEIVERS]

    event_log = orchestrator_connection.get_constant("Event Log")
    itk_dev_event_log.setup_logging(event_log.value)

    # Load cases from Statstidende
    date = datetime.now().strftime('%d-%m-%Y')

    statstidende_path = f'cases {date}.json'

    if not os.path.isfile(statstidende_path):
        statstidende.create_cases_file(statstidende_path, orchestrator_connection)

    with open(statstidende_path, 'r', encoding='utf-8') as file:
        cases = json.load(file)
    itk_dev_event_log.emit(orchestrator_connection.process_name, "Cases created", len(cases))

    # Load data from OPUS emails and find relevant cases
    opus_name = f"Opus Statstidende {date}"
    opus_path = opus_name + ".xlsx"

    if not os.path.isfile(opus_path):
        opus_cases = opus.find_relevant_cases(cases, orchestrator_connection)
        itk_dev_event_log.emit(orchestrator_connection.process_name, "Opus cases found", len(opus_cases))
        opus.write_excel(opus_path, opus_cases)

    # Load data from Boliglån and find relevant cases
    boliglaan_name = f"Boliglån Statstidende {date}"
    boliglaan_path = boliglaan_name + ".xlsx"

    if not os.path.isfile(boliglaan_path):
        boliglaan_cases = kmd_boliglaan.find_relevant_cases(cases, orchestrator_connection)
        itk_dev_event_log.emit(orchestrator_connection.process_name, "Boliglån cases found", len(boliglaan_cases))
        kmd_boliglaan.write_excel(boliglaan_path, boliglaan_cases)

    # Send results
    opus_text = config.EMAIL_TEXT.replace("%SYSTEM%", "OPUS")
    orchestrator_connection.log_info(f"Sending OPUS email to: {opus_receivers}")
    common.send_email(opus_receivers, opus_name, opus_text, opus_path)

    boliglaan_text = config.EMAIL_TEXT.replace("%SYSTEM%", "KMD Boliglån")
    orchestrator_connection.log_info(f"Sending Boliglån email to: {boliglaan_receivers}")
    common.send_email(boliglaan_receivers, boliglaan_name, boliglaan_text, boliglaan_path)

    # Delete OPUS emails
    opus.delete_emails(orchestrator_connection)
