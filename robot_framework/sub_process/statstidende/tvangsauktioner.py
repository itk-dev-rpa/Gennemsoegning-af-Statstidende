"""This module is responsible for the logic regarding Statstidende tvangsauktioner."""

from typing import Any


TVANGSAUKTIONER_KEYS = {
    "2aa7d6a1-b250-51a8-88a6-3f6c18574526": "Fast ejendom",
    # "08a6eaef-98cf-50d8-a870-a16c5184c99b": "Skibe, luftfartøjer og løsøre",
    # "2fb3c7d1-2198-5b88-b4ca-f27d4b95fc06": "Aflysninger, udsættelser og berigtigelser"
}


def get_tvangsauktioner(data: dict[str: Any]) -> dict[str, tuple[str]]:
    """Get all tvangsauktioner from the given data.

    Returns:
        A dict in the format: address -> (address, Type, Case number, Case date)
    """
    tvangsauktioner = {}
    for message in data:
        if message["messageTypePublicKey"] in TVANGSAUKTIONER_KEYS:
            address = get_address(message)
            case_type = "Tvangsauktioner - " + get_case_type(message)
            case_number = get_case_number(message)
            case_date = get_case_date(message)
            tvangsauktioner[address] = (address, case_type, case_number, case_date)

    return tvangsauktioner


def get_address(message: dict[str, Any]) -> str:
    """Extract the address number from a Statstidende message."""
    street = ""
    number = ""
    zipcode = ""
    city = ""

    for field_group in message['fieldGroups']:
        if field_group['name'] == 'Ejendom':
            for field in field_group['fields']:
                if field['name'] == 'Vejnavn':
                    street = field['value']
                elif field['name'] == 'Husnr.':
                    number = field['value']
                elif field['name'] == 'Postnr':
                    zipcode = field['value']
                elif field['name'] == 'By':
                    city = field['value']

    return " ".join((street, number, zipcode, city))


def get_case_type(message: dict[str, Any]) -> str:
    """Extract the case type from a Statstidende message."""
    return TVANGSAUKTIONER_KEYS[message['messageTypePublicKey']]


def get_case_number(message: dict[str, Any]) -> str:
    """Extract the case number from a Statstidende message."""
    return message['messageNumber']


def get_case_date(message: dict[str, Any]) -> str:
    """Extract the case date from a Statstidende message."""
    sag = get_case_number(message)
    return f"{sag[1:3]}-{sag[3:5]}-{sag[5:9]}"
