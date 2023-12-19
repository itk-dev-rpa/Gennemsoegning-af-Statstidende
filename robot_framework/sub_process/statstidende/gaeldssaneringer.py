"""This module is responsible for the logic regarding Statstidende gældssaneringer."""

from typing import Any


GAELDSSANERINGER_KEYS = {
    "96d0fb63-1a78-5e5c-ac54-6fb04f9cca41": "Indledning - præklusivt proklama",
    "c52f38d1-27d8-5905-b391-ed1879aeeb93": "Præklusivt proklama (gældssanering i konkurs)",
    "eb534b4d-4aaf-585b-ad64-788ca8fc1389": "Kreditormøde",
    "5241697a-3f84-535c-8d66-847b16014c17": "Kendelse",
    "addc8185-5bc7-52b6-a7c4-fd12654e8351": "Andre meddelelser"
}


def get_gaeldssaneringer(data: dict[str, Any]) -> dict[str, list[tuple[str]]]:
    """Get all gældssaneringer from the given data.

    Returns:
        A dict in the format: birthdate -> list[ (Name, Type, Case number, Case date) ]
    """
    gaeldssaneringer = {}

    for message in data:
        if message["messageTypePublicKey"] in GAELDSSANERINGER_KEYS:
            birthdate = get_birthdate(message)
            name = get_name(message)
            case_type = "Gældssaneringer - " + get_case_type(message)
            case_number = get_case_number(message)
            case_date = get_case_date(message)

            if birthdate not in gaeldssaneringer:
                gaeldssaneringer[birthdate] = []

            gaeldssaneringer[birthdate].append((name, case_type, case_number, case_date))

    return gaeldssaneringer


def get_birthdate(message: dict[str, Any]) -> str:
    """Extract the birthdate from a Statstidende message."""
    for field_group in message['fieldGroups']:
        if field_group['name'] == 'Skyldner(e)':
            for field in field_group['fields']:
                if field['name'] == 'Fødselsdato':
                    return field['value']

    return None


def get_name(message: dict[str, Any]) -> str:
    """Extract the name from a Statstidende message."""
    for field_group in message['fieldGroups']:
        if field_group['name'] == 'Skyldner(e)':
            for field in field_group['fields']:
                if field['name'] == 'Navn':
                    return field['value']

    return None


def get_case_type(message: dict[str, Any]) -> str:
    """Extract the case type from a Statstidende message."""
    return GAELDSSANERINGER_KEYS[message['messageTypePublicKey']]


def get_case_number(message: dict[str, Any]) -> str:
    """Extract the case number from a Statstidende message."""
    return message['messageNumber']


def get_case_date(message: dict[str, Any]) -> str:
    """Extract the case date from a Statstidende message."""
    sag = get_case_number(message)
    return f"{sag[1:3]}-{sag[3:5]}-{sag[5:9]}"
