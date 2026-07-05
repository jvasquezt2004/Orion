"""Tests for the Beanie Reference Document (reference-storage spec).

Coverage split note (design review warning #5):
- MinIO is mocked here (fput_object) — we test the worker-only insert path.
- process_file_task.kiq is mocked in test_upload.py — we test the upload path.
- No single unmocked E2E test covers both. A real-container smoke test is a
  documented follow-up (open item).
"""

from unittest.mock import patch
from uuid import uuid4

from app.db.reference import Reference, ReferenceType, MediaKind
from app.workers.process_file import process_file_task


async def test_insert_and_retrieve_all_fields(mongo):
    """Insert a Reference, retrieve by id — all fields unchanged, enums persist as strings."""
    ref = Reference(
        type=ReferenceType.COMPOSITION,
        media=MediaKind.IMAGE,
        original_name="photo.jpg",
        stored_name="abc123_photo.jpg",
        bucket="app-bucket",
        object_path="uploads/abc123_photo.jpg",
        is_processed=True,
        description="A test composition",
        thumbnail_url="http://example.com/thumb.jpg",
    )
    await ref.insert()

    retrieved = await Reference.get(ref.id)
    assert retrieved is not None
    assert retrieved.id == ref.id
    assert retrieved.type == ReferenceType.COMPOSITION
    assert retrieved.type.value == "composition"
    assert retrieved.media == MediaKind.IMAGE
    assert retrieved.media.value == "image"
    assert retrieved.original_name == "photo.jpg"
    assert retrieved.stored_name == "abc123_photo.jpg"
    assert retrieved.bucket == "app-bucket"
    assert retrieved.object_path == "uploads/abc123_photo.jpg"
    assert retrieved.is_processed is True
    assert retrieved.description == "A test composition"
    assert retrieved.thumbnail_url == "http://example.com/thumb.jpg"
    assert retrieved.created_at is not None


async def test_unknown_id_returns_none(mongo):
    """Looking up a non-existent id returns None (not raise)."""
    result = await Reference.get(uuid4())
    assert result is None


async def test_process_file_task_inserts_reference(mongo, tmp_path):
    """Direct process_file_task invocation with mocked MinIO inserts a Reference.

    Mocks minio_client.fput_object to avoid real object storage.
    """
    # Create a dummy file for cv2.imread to attempt reading
    dummy_file = tmp_path / "test_image.png"
    dummy_file.write_bytes(b"not a real image")

    with patch("app.workers.process_file.minio_client") as mock_minio:
        mock_minio.fput_object.return_value = None
        mock_minio.bucket_exists.return_value = True

        await process_file_task(
            temp_path=str(dummy_file),
            original_name="test_image.png",
        )

    # Verify a Reference was inserted
    refs = await Reference.find_all().to_list()
    assert len(refs) == 1
    ref = refs[0]
    assert ref.original_name == "test_image.png"
    assert ref.bucket == "app-bucket"
    assert ref.type == ReferenceType.REFERENCE
    # cv2.imread will fail on our dummy file, so media should be UNKNOWN
    assert ref.media == MediaKind.UNKNOWN
    assert ref.is_processed is False


async def test_uuid_pk_round_trips_through_bson(mongo):
    """UUID primary key survives a full BSON encode/decode round-trip.

    This was an open question (design OQ-3): pymongo's native UUID encoding
    vs manual bson_encoders. Confirmed: no bson_encoders needed — the UUID
    pk round-trips cleanly.
    """
    ref = Reference(
        type=ReferenceType.REFERENCE,
        media=MediaKind.IMAGE,
        original_name="uuid_test.jpg",
        stored_name="uuid_test.jpg",
        bucket="app-bucket",
        object_path="uploads/uuid_test.jpg",
    )
    original_id = ref.id
    await ref.insert()

    retrieved = await Reference.get(original_id)
    assert retrieved is not None
    assert retrieved.id == original_id
    assert isinstance(retrieved.id, type(original_id))
