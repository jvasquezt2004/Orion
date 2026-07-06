from fastapi import APIRouter
from app.db.reference import Reference

router = APIRouter()


@router.get("/registries")
async def get_registries():
    refs = await Reference.find_all().sort(-Reference.created_at).to_list(100)

    results = []
    for ref in refs:
        image_analysis = (
            ref.image_analysis.model_dump() if ref.image_analysis else None
        )

        results.append({
            "id": str(ref.id),
            "type": ref.type.value,
            "media": ref.media.value,
            "original_name": ref.original_name,
            "stored_name": ref.stored_name,
            "object_path": ref.object_path,
            "bucket": ref.bucket,
            "is_processed": ref.is_processed,
            "created_at": ref.created_at.isoformat(),
            "description": ref.description,
            "title": ref.title,
            "thumbnail_url": ref.thumbnail_url,
            "content_type": ref.content_type,
            "original_url": ref.original_url,
            "final_url": ref.final_url,
            "provider": ref.provider,
            "embed_url": ref.embed_url,
            "image_analysis": image_analysis,
        })

    return results
