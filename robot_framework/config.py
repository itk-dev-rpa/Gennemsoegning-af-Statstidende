"""This module contains configuration constants used across the framework"""

# The number of times the robot retries on an error before terminating.
MAX_RETRY_COUNT = 3

# Whether the robot should be marked as failed if MAX_RETRY_COUNT is reached.
FAIL_ROBOT_ON_TOO_MANY_ERRORS = True

# Error screenshot config
SMTP_SERVER = "smtp.aarhuskommune.local"
SMTP_PORT = 25
SCREENSHOT_SENDER = "robot@friend.dk"

# Constant/Credential names
ERROR_EMAIL = "Error Email"
BOLIGLAAN_LOGIN = "Mathias KMD"
GRAPH_API = "Graph API"

KEYVAULT_CREDENTIALS = "Keyvault"
KEYVAULT_URI = "Keyvault URI"
KEYVAULT_PATH = ""  # TODO

# Argument json names
OPUS_RECEIVERS = "opus_receivers"
BOLIGLAAN_RECEIVERS = "boliglaan_receivers"
CERT_PATH = "cert_path"

# Where the resulting email comes from
EMAIL_SENDER = "itk-rpa@mkb.aarhus.dk"

EMAIL_TEXT = (
"""Hej

Her er listen med udsøgning fra Statstidende på debitorer i %SYSTEM% for de sidste 7 dage.

Bemærk for at undgå fejl i forbindelse med udsøgningen er følgende valg taget:
•\tGældssaneringer er fremsøgt via fødselsdato og fornavn.
•\tTvangsauktioner er fremsøgt via vejnavn og postnummer
I skal derfor selv være opmærksomme på om sagen er relevant. Tjek kolonne D op mod kolonne A-C

Med venlig hilsen
Statstidende-Robotten"""
)