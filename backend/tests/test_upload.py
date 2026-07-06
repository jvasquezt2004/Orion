"""Upload endpoint tests — unauthenticated (local-only mode)."""

from unittest.mock import patch, AsyncMock


async def test_upload_returns_200(client):
    """Upload without auth → 200 with status done."""
    with patch("app.api.upload.process_file", new_callable=AsyncMock) as mock_process:
        response = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["status"] == "done"
    mock_process.assert_awaited_once()
