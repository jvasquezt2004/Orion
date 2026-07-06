from fastapi import APIRouter, UploadFile, File, HTTPException
from app.workers.process_file import process_file_task
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
        task = await process_file_task.kiq(
            temp_path=temp_path,
            original_name=file.filename,
            content_type=file.content_type,
        )
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=503, detail="Failed to queue file for processing"
        )

    return {
        "task_id": task.task_id,
        "filename": file.filename,
        "status": "processing"
    }