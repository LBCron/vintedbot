from fastapi import APIRouter
from fastapi.responses import Response
from backend.models.db import db
from backend.services.export import export_service

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/csv")
async def export_csv():
    items = db.get_all()
    csv_content = export_service.export_csv(items)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory.csv"}
    )


@router.get("/vinted")
async def export_vinted():
    items = db.get_all()
    csv_content = export_service.export_vinted_csv(items)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vinted_export.csv"}
    )


@router.get("/json")
async def export_json():
    items = db.get_all()
    json_content = export_service.export_json(items)
    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=inventory.json"}
    )


@router.get("/pdf")
async def export_pdf():
    items = db.get_all()
    pdf_content = export_service.export_pdf(items)
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=inventory.pdf"}
    )
