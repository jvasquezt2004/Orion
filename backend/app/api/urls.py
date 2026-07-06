from pydantic import BaseModel, HttpUrl
from fastapi import APIRouter
from app.db.reference import MediaKind, Reference, ReferenceType
from app.services.enrich_url import enrich_url

router = APIRouter()


class CreateUrlRequest(BaseModel):
    originalUrl: HttpUrl


@router.post("/urls")
async def create_url(data: CreateUrlRequest):
    original_url = str(data.originalUrl)

    ref = await Reference(
        type=ReferenceType.REFERENCE,
        media=MediaKind.UNKNOWN,
        original_name=original_url,
        stored_name="",
        bucket="",
        object_path="",
        original_url=original_url,
        is_processed=False,
    ).insert()

    await enrich_url(
        reference_id=str(ref.id),
        original_url=original_url,
    )

    return {"id": str(ref.id), "status": "done"}
