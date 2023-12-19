"""This module is responsible for all logic concerning KMD Boliglån"""

import csv
import os
import time
import re
import uuid
from _ctypes import COMError

from pywinauto.application import Application
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo
from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework.sub_process import common


def login(username: str, password: str):
    """Launch and login to KMD Boliglån."""
    Application(backend="uia").start(r'"C:\Program Files (x86)\KMD\KMD.LW.Boliglaan\KMD.LW.KMDBoliglaan.Client.exe"')

    app = Application(backend='uia').connect(title="KMD Logon - Brugernavn og kodeord", timeout=30)
    dlg = app.top_window()

    user_field = dlg.child_window(auto_id="UserPwTextBoxUserName")
    user_field.set_edit_text(username)

    pass_field = dlg.child_window(auto_id="UserPwPasswordBoxPassword")
    pass_field.set_edit_text(password)

    # Retry pressing the login button until it works
    for _ in range(5):
        try:
            logon = dlg.child_window(auto_id="UserPwLogonButton")
            logon.click()
            break
        except COMError:
            time.sleep(1)
    else:
        raise RuntimeError("KMD login button didn't work after 5 tries.")


def load_lenders() -> list[tuple[str]]:
    """Go through KMD Boliglån and save a list of lenders based on filter
    criteria. Read the list and return the data.
    """
    laanestatus = [
        "Bevilget",
        "Udbetalt",
        "Afvikling - frivillig",
        "Afvikling - 5 års løbetid"
    ]

    laanetype = [
        "Pligtlån 5 års løbetid §56, §57",
        "Pligtlån sanering §54",
        "Pligtlån pensionister §54",
        "Pligtlån enkeltværelse §54",
        "Pligtlån genhusning §54",
        "Pligtlån ældrebolig §54",
        "Flygtningelån 100% 5 års løbetid §66, §67",
        "Flygtningelån 100% sanering §66, §67",
        "Flygtningelån 100% pensionister §66, §67",
        "Flygtninglån 50% 5 års løbetid §68",
        "Kommune lån §59"
    ]

    app = Application(backend="uia").connect(title="KMD Boliglån", timeout=30)
    boliglaan = app.top_window()
    boliglaan.click_input()
    boliglaan.set_focus()
    boliglaan.type_keys("^b")

    laanesager_window = boliglaan.child_window(title="Udsøg lånesager")
    checkboxes = laanesager_window.descendants(class_name="CheckEdit")

    for checkbox in checkboxes:
        if checkbox.window_text() in laanestatus+laanetype:
            if checkbox.get_toggle_state() == 0:
                checkbox.toggle()

    laanesager_window.child_window(title="Søg").click()

    boliglaan.child_window(auto_id="DockLayoutManager")\
        .child_window(auto_id="SagerLayoutPanel", found_index=0)\
        .child_window(title="Save", control_type="Button").click()

    # Create a unique filename in the current working dir
    file_name = os.path.join(os.getcwd(), f'Lånesager {uuid.uuid4()}.csv')

    boliglaan.child_window(title="Gem som")\
        .child_window(auto_id="FileNameControlHost")\
        .child_window(auto_id="1001")\
        .set_edit_text(file_name)

    boliglaan.child_window(title="Gem som")\
        .child_window(title="Gem")\
        .click()

    # Wait for boliglån to write file
    time.sleep(2)
    data = read_csv(file_name)

    return data


def read_csv(file_name: str) -> list[tuple[str]]:
    """Read a csv file from KMD Boliglån and extract
    cpr, name and address for each lender.
    """
    lenders = []
    with open(file_name, encoding='ansi') as file:
        # Skip first 12 rows (Meta date)
        for _ in range(12):
            next(file)

        # Read data
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            lender = (
                row[1],  # cpr
                row[2],  # Name
                row[5]   # Address
            )
            lenders.append(lender)

    return lenders


def find_relevant_cases(in_cases: list[dict], orchestrator_connection: OrchestratorConnection) -> list[tuple[str]]:
    """Find all Statstidende cases that could have relevance for lenders in KMD Boliglån.

    Args:
        in_cases: A list of Statstidende cases.

    Returns:
        A list of relevant cases.
    """
    doedsboer, gaeldssaneringer, _, tvangsauktioner = in_cases

    orchestrator_connection.log_info("Finder lånere i Boliglån.")
    lenders = load_lenders()
    orchestrator_connection.log_info(f"Lånere i boliglån: {len(lenders)}")

    out_cases = []

    for lender in lenders:
        cpr = lender[0]
        name = lender[1]
        first_name = name.split()[0]
        address = lender[2]
        street = address.split()[0]
        zipcode = get_zipcode(address)
        birthdate = common.get_birthdate(cpr)

        # Search dødsboer on cpr
        if cpr in doedsboer:
            out_cases.append((lender, doedsboer[cpr]))

        # Search gældssaneringer on birthdate and first name
        if birthdate in gaeldssaneringer:
            for case in gaeldssaneringer[birthdate]:
                if first_name in case[0]:
                    out_cases.append((lender, case))

        # Search tvangsauktioner on street and zipcode
        if street and zipcode:
            for address in tvangsauktioner:
                if common.compare_addresses(address, street, zipcode):
                    out_cases.append((lender, tvangsauktioner[address]))

    return out_cases


def get_zipcode(address: str) -> str:
    """Extract the zipcode from an address string.

    Args:
        address: The full address.

    Returns:
        The zipcode from the address. If none is found '9999' is returned.
    """
    # Use regular expressions to find all four-digit numbers
    pattern = r"\b\d{4}\b"
    matches = re.findall(pattern, address)

    if matches:
        postal_code = matches[-1]  # Get the last occurrence
        return postal_code

    return '9999'

# pylint: disable=R0801
def write_excel(path: str, cases: tuple[tuple[str]]) -> None:
    """Write the given cases to an excel file on the given path.

    Args:
        path: Where to save the excel file.
        cases: A tuple of cases in the format:
            ((Debitor), (Case)) = ((fp, id, fornavn, efternavn, gade, husnr, postnummer, by), (X, Type, Sagsnummer, dato))
    """
    # Cases = ((Debitor),(Case)) = ((cpr, navn, adresse),(X, Type, Sagsnummer, dato))
    wb = openpyxl.Workbook()
    doedsboer_sheet = wb.active
    doedsboer_sheet.title = "Dødsboer"
    gaeldssaneringer_sheet = wb.create_sheet("Gældssaneringer")
    tvangsauktioner_sheet = wb.create_sheet("Tvangsauktioner")

    doedsboer_sheet.append(("CPR", "Navn", "Adresse", "CPR på Sag", "Type", "Sagsnummer", "Sagsdato"))
    gaeldssaneringer_sheet.append(("CPR", "Navn", "Adresse", "Navn på sag", "Type", "Sagsnummer", "Sagsdato"))
    tvangsauktioner_sheet.append(("CPR", "Navn", "Adresse", "Adresse på sag", "Type", "Sagsnummer", "Sagsdato"))

    for case in cases:
        case_type = case[1][1]
        data = list(case[0]) + list(case[1])

        if case_type.startswith("Dødsboer"):
            doedsboer_sheet.append(data)
        elif case_type.startswith("Gældssanering"):
            gaeldssaneringer_sheet.append(data)
        elif case_type.startswith("Tvangsauktioner"):
            tvangsauktioner_sheet.append(data)

    for ws in wb:
        dim = ws.dimensions
        if dim == 'A1:G1':
            continue
        table = Table(displayName=ws.title, ref=dim)
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9", showFirstColumn=False, showLastColumn=False, showRowStripes=True, showColumnStripes=True)
        ws.add_table(table)

    wb.save(path)
    wb.close()


def kill_boliglaan():
    """Kill KMD Logon, KMD Boliglån and Notepad."""
    os.system("taskkill /f /im KMD.LW.KMDBoliglaan.Client.exe")
    os.system("taskkill /f /im KMD.YH.Security.Logon.Desktop.exe")
    os.system("taskkill /f /im notepad*")
