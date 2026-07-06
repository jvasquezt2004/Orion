from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.process_file import process_file
import os
import tempfile

router = APIRouter()

CHUNK_SIZE = 1024 * 1024  # 1 MiB

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
):
    suffix = os.path.splitext(file.filename)[1].lower() or ".bin"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        temp_path = tmp.name
        while chunk := await file.read(CHUNK_SIZE):
            tmp.write(chunk)

    try:
        await process_file(
            temp_path=temp_path,
            original_name=file.filename,
            content_type=file.content_type,
        )
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=500, detail="Failed to process file"
        )

    return {
        "filename": file.filename,
        "status": "done",
    }