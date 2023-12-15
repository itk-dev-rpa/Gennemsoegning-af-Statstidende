"""This module is responsible for the logic regarding Statstidende dødsboer."""

from typing import Any


DOEDSBOER_KEYS = {
    "431a79af-df1f-5c4b-a7a4-a20aadda8c0a": "Proklama",
    "6cfbde17-3f52-53e7-b9df-7dee2414246d": "Indkaldelse til bomøde",
    "25b39189-55f3-5dc7-a142-03ed103552bb": "Arveproklama",
    "c0c2f124-8d47-5f91-bf52-c6621beb9437": "Andre meddelelser",
    "8782d80c-3afd-5d48-9f9f-272e3c869911": "Proklama (Færøerne og Grønland)"
}


def get_doedsboer(data: dict[str: Any]) -> dict[str, tuple[str]]:
    """Get all dødsboer from the given data.

    Returns:
        A dict in the format: cpr -> (cpr, Type, Case number, Case date)
    """
    doedsboer = {}
    for message in data:
        if message["messageTypePublicKey"] in DOEDSBOER_KEYS:
            cpr = get_cpr(message)
            case_type = "Dødsboer - " + get_case_type(message)
            case_number = get_case_number(message)
            case_date = get_case_date(message)
            doedsboer[cpr] = (cpr, case_type, case_number, case_date)

    return doedsboer


def get_cpr(message: dict[str, Any]) -> str:
    """Extract the cpr number from a Statstidende message."""
    for fg in message['fieldGroups']:
        if fg['name'] == 'Afdøde':
            for f in fg['fields']:
                if f['name'] == 'CPR-nr.':
                    return f['value']


def get_case_type(message: dict[str, Any]) -> str:
    """Extract the case type from a Statstidende message."""
    return DOEDSBOER_KEYS[message['messageTypePublicKey']]


def get_case_number(message: dict[str, Any]) -> str:
    """Extract the case number from a Statstidende message."""
    return message['messageNumber']


def get_case_date(message: dict[str, Any]) -> str:
    """Extract the case date from a Statstidende message."""
    sag = get_case_number(message)
    return f"{sag[1:3]}-{sag[3:5]}-{sag[5:9]}"
