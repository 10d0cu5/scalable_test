import asyncio
import concurrent
import json
import os
import threading

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.orm import Session

from app.api.dependencies.db_connection import get_db
from app.core.config import DATASET_DIR
from app.helper.import_helper import json_import, bulk_import_from_file, FileReader
from app.models.crud import bulk_create, get_artist
from app.models.schemas import JSONImportData

router = APIRouter(prefix="/data")


# response_model=schemas.User
@router.post("/import/{source}")
def import_from_source(source: str, db: Session = Depends(get_db), import_data: JSONImportData = []):
    """
    Imports to database from source
    Supported sources:
    txt file in file directory
    json data handed over in post request body
    :return: Status of the import (with duplicates, errors)
    """
    if source == "file":
        # First locate file
        logger.info("import from file!")
        try:
            reader = FileReader(db=db)
            lines = reader.get_no_lines()
            reader.read_file_from_to(0,lines)
            logger.info("start import")
            bulk_create(db=db, users=reader.users, tracks=reader.tracks, artists=reader.artists, playlist_entries=reader.playlist_entries)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error on loading data from data source file {e}")

    elif source == "json":
        logger.info("import from json")
        if import_data:
            for entry in import_data.import_data:
                json_import(db=db, data=entry.json())
        else:
            raise HTTPException(status_code=400,
                                detail=f"no json data in body provided for {source} import {import_data}")
    else:
        raise HTTPException(status_code=400, detail=f"unknown data source {source}")

    return {"status": f"successfully imported from {source}"}
