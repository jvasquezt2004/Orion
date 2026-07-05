"""Upload endpoint tests — unauthenticated (local-only mode)."""

from unittest.mock import patch, AsyncMock


async def test_upload_returns_200(client):
    """Upload without auth → 200 with task_id."""
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
