import logging
import os
import sys

if getattr(sys, 'Frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(__file__)

APP_NAME = 'KHOV Asana'
LOG_FILE = fr"{application_path}\{APP_NAME}.log"

logger = logging

logger.basicConfig(
    filename=LOG_FILE,
    format="%(asctime)s - " + APP_NAME + " - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger.getLogger().addHandler(logging.StreamHandler(sys.stdout))
