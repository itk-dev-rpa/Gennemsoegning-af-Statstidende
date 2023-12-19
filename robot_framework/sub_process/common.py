"""This module contains common logic shared between KMD Boliglån and Opus."""

from email.message import EmailMessage
import smtplib
import os

from robot_framework import config


def compare_addresses(address_a, street_b, zipcode_b) -> bool:
    """Check if the given street and zipcode matches the address."""
    return zipcode_b in address_a and street_b in address_a


def get_birthdate(debitor_id: str) -> str:
    """Extract the birthdate from an id if it's a cpr number.

    Args:
        debitor_id: The id of the debitor.

    Returns:
        The birthdate in the format 'yyyy-mm-dd'.
    """
    if len(debitor_id) != 10:
        return None

    year = debitor_id[4:6]
    month = debitor_id[2:4]
    day = debitor_id[0:2]

    # Guess the birth decade.
    # Assuming year is between 1920 and 2019.
    if int(year) < 20:
        year = '20'+year
    else:
        year = '19'+year

    return f"{year}-{month}-{day}"


def send_email(to_address: str | list[str], subject: str, body: str, attachment_path: str) -> None:
    """Send an email with an attachment using SMTP.

    Args:
        to_address: Address or list of addresses to send the email to.
        subject: The subject of the email.
        body: The text body of the email.
        attachment_path: The path to the file to attach to the email.
    """
    # Create message
    msg = EmailMessage()
    msg['to'] = to_address
    msg['from'] = config.EMAIL_SENDER
    msg['subject'] = subject
    msg.set_content(body)

    # Attach file
    file_name = os.path.basename(attachment_path)
    with open(attachment_path, 'rb') as file:
        msg.add_attachment(file.read(), maintype='application', subtype='octet-stream', filename=file_name)

    # Send message
    with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.send_message(msg)
