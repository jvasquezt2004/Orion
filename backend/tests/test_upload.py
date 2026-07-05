"""Upload endpoint tests for Slice 1 state (unauthenticated).

Slice 2 will update this: unauthenticated → 401, authenticated → 200.
"""

import asyncio
from unittest.mock import patch, AsyncMock

import httpx


async def test_unauthenticated_upload_returns_200(client):
    """In Slice 1, the upload endpoint has no auth — unauthenticated upload → 200."""
    # Slice 2 will update this: unauthenticated → 401, authenticated → 200
    mock_task_result = type("TaskResult", (), {"task_id": "test-task-123"})()

    with patch("app.api.upload.process_file_task") as mock_task:
        mock_task.kiq = AsyncMock(return_value=mock_task_result)

        response = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "test-task-123"
    assert data["filename"] == "test.txt"
    assert data["status"] == "processing"
