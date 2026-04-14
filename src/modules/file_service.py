"""File upload and normalization service."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from src import config
from src.data.repository import BackendRepository
from src.extraction.text_extractor import extract_text_from_uploaded_file
from src.utils.file_io import NamedBytesIO


class FileService:
    def __init__(self, repository: BackendRepository) -> None:
        self._repository = repository

    def save_and_normalize(
        self,
        user_id: str,
        filename: str,
        content_type: str,
        raw_content: bytes,
    ) -> dict:
        ext = Path(filename).suffix.lower()
        storage_name = f"{uuid.uuid4()}{ext}"
        storage_path = config.FILES_DATA_DIR / storage_name
        storage_path.write_bytes(raw_content)

        upload_like = NamedBytesIO(raw_content, filename)
        extraction_result = extract_text_from_uploaded_file(upload_like)
        record = self._repository.save_file(
            user_id=user_id,
            filename=filename,
            content_type=content_type or "application/octet-stream",
            stored_path=os.fspath(storage_path),
            normalized_text=extraction_result.text,
            warning=extraction_result.warning,
        )
        return {
            "file_id": record["id"],
            "filename": filename,
            "uploaded_at": record["uploaded_at"],
            "warning": extraction_result.warning,
            "text_length": len(extraction_result.text),
        }
