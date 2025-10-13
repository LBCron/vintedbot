from fastapi import APIRouter, UploadFile, File, HTTPException
import csv
from io import StringIO
import uuid
from backend.models.schemas import Item, ItemStatus, Condition, PriceSuggestion
from backend.models.db import db

router = APIRouter(prefix="/import", tags=["Import"])


@router.post("/csv")
async def import_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    csv_content = content.decode('utf-8')
    csv_file = StringIO(csv_content)
    
    reader = csv.DictReader(csv_file)
    imported_items = []
    
    for row in reader:
        try:
            condition = None
            if row.get('condition'):
                try:
                    condition = Condition(row['condition'])
                except ValueError:
                    condition = Condition.GOOD
            
            price = float(row.get('price', 0))
            
            item = Item(
                id=row.get('id', str(uuid.uuid4())),
                title=row['title'],
                description=row.get('description', ''),
                brand=row.get('brand'),
                category=row.get('category'),
                size=row.get('size'),
                condition=condition,
                price=price,
                price_suggestion=PriceSuggestion(
                    min=price * 0.7,
                    max=price * 1.3,
                    target=price,
                    justification="Imported from CSV"
                ),
                status=ItemStatus(row.get('status', 'draft'))
            )
            
            saved_item = db.create(item)
            imported_items.append(saved_item)
        except Exception as e:
            print(f"Error importing row: {e}")
            continue
    
    return {
        "message": f"Successfully imported {len(imported_items)} items",
        "items": imported_items
    }
