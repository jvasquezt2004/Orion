from fastapi import APIRouter, UploadFile, HTTPException, File
import shutil
from app.workers.process_file import process_file_task
import os
import tempfile

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1].lower() or ".bin"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    task = await process_file_task.kiq(
        temp_path=temp_path,
        original_name=file.filename
    )

    return {
        "task_id": task.task_id,
        "filename": file.filename,
        "status": "processing"
    }