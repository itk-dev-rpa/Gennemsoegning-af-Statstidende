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
STATSTIDENDE_KEY = "Statstidende Key"
BOLIGLAAN_LOGIN = "Mathias KMD"
GRAPH_API = "Graph API"

# Argument json names
EMAIL_TEXT = "email_text"
OPUS_RECEIVERS = "opus_receivers"
BOLIGLAAN_RECEIVERS = "boliglaan_receivers"
CERT_PATH = "cert_path"

# Where the resulting email comes from
EMAIL_SENDER = "itk-rpa@mkb.aarhus.dk"
