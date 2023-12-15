"""This module is responsible for the logic regarding Statstidende konkursboer."""

from typing import Any


KONKURSBOER_KEYS = {
    "383f1800-1b39-5f39-8250-61a5c0798fad": "Ophævelse af dekret",
    "941c2e75-9f32-5408-a946-031217b6d669": "Skiftesamling",
    "24295ca1-259a-5876-ba7b-f8ef496feed6": "Indkaldelse til fordringsprøvelse",
    "018d0141-0efb-5472-a698-9328817df00a": "Regnskab og boafslutning",
    "603102f0-9e3f-5ad9-9538-175719970bde": "Andre meddelelser",
    "14a1d71d-f215-58e5-ade0-214f90482cdc": "Dekret"
}


def get_konkursboer(data: dict[str: Any]) -> dict[str, tuple[str]]:
    """Get all konkursboer from the given data.

    Returns:
        A dict in the format: cvr -> (cvr, Type, Case number, Case date)
    """
    konkursboer = {}
    for message in data:
        if message["messageTypePublicKey"] in KONKURSBOER_KEYS:
            cvr = get_cvr(message)
            case_type = "Konkursboer - " + get_case_type(message)
            case_number = get_case_number(message)
            case_date = get_case_date(message)
            if cvr:
                konkursboer[cvr] = (cvr, case_type, case_number, case_date)

    return konkursboer


def get_cvr(message: dict[str, Any]) -> str:
    """Extract the cvr number from a Statstidende message."""
    for field_group in message['fieldGroups']:
        if field_group['name'] == 'Skyldner(e)':
            for field in field_group['fields']:
                if field['name'] == 'CVR-nr.':
                    return field['value']


def get_case_type(message: dict[str, Any]) -> str:
    """Extract the case type from a Statstidende message."""
    return KONKURSBOER_KEYS[message['messageTypePublicKey']]


def get_case_number(message: dict[str, Any]) -> str:
    """Extract the case number from a Statstidende message."""
    return message['messageNumber']


def get_case_date(message: dict[str, Any]) -> str:
    """Extract the case date from a Statstidende message."""
    sag = get_case_number(message)
    return f"{sag[1:3]}-{sag[3:5]}-{sag[5:9]}"
