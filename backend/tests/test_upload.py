"""Upload endpoint tests — authenticated (Slice 2)."""

from unittest.mock import patch, AsyncMock


async def test_unauthenticated_upload_returns_401(client):
    """Upload without auth token → 401."""
    response = await client.post(
        "/api/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 401


async def test_authenticated_upload_returns_200(client, auth_token):
    """Upload with valid Bearer token → 200."""
    access_token, _ = auth_token
    mock_task_result = type("TaskResult", (), {"task_id": "test-task-123"})()

    with patch("app.api.upload.process_file_task") as mock_task:
        mock_task.kiq = AsyncMock(return_value=mock_task_result)

        response = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "test-task-123"
    assert data["filename"] == "test.txt"
    assert data["status"] == "processing"
