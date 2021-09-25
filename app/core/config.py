import logging
import os
import uuid
from typing import List

from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings

config = Config(".env")

# General Config
DEBUG: bool = config("DEBUG", cast=bool, default=False)
VERSION: str = config("VERSION", cast=str, default="1.0.0")

SERVICE_IDENTIFIER: str = config("SERVICE_IDENTIFIER", cast=str, default="SCR")

APPLICATION_NAME: str = config("APPLICATION_NAME", cast=str, default="scalable-capital-reporting-service")
API_CONTEXT_PATH: str = "/" + APPLICATION_NAME

HOST: str = config("HOST", cast=str, default="0.0.0.0")
PORT: str = config("PORT", cast=str, default="8000")

# Logging Config
LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO

# DB Config
DB_USER: str = config("DB_USER", cast=str, default="scalable")
DB_PWD: str = config("DB_PWD", cast=str, default="capital")
DB_NAME: str = config("DB_NAME", cast=str, default="reporting")
DB_PORT: int = config("DB_PORT", cast=int, default=5432)
DB_HOST: str = config("DB_HOST", cast=str, default="127.0.0.1")

# File Locations
BASE_DIR: str = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),'..'))
DATASET_DIR: str = os.path.realpath(os.path.join(BASE_DIR,'static/data'))
TEMPLATE_DIR: str = os.path.realpath(os.path.join(BASE_DIR,'static/templates'))