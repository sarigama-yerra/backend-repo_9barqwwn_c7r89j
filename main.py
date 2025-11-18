import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Homestay, Booking

app = FastAPI(title="Toshi Home API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(doc)
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    # Convert datetimes to isoformat strings
    for k, v in list(out.items()):
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
    return out


@app.get("/")
def read_root():
    return {"message": "Toshi Home backend is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from Toshi Home API"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# ------- Schema discovery (optional helper) -------
class SchemaInfo(BaseModel):
    name: str
    fields: List[str]


@app.get("/schema", response_model=List[SchemaInfo])
def get_schema_info():
    homestay_fields = list(Homestay.model_fields.keys())
    booking_fields = list(Booking.model_fields.keys())
    return [
        {"name": "homestay", "fields": homestay_fields},
        {"name": "booking", "fields": booking_fields},
    ]


# ------- Homestays -------
@app.get("/api/homestays")
def list_homestays(
    q: Optional[str] = None,
    country: Optional[str] = None,
    minPrice: Optional[float] = None,
    maxPrice: Optional[float] = None,
    guests: Optional[int] = None,
    limit: int = 24,
):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_query: Dict[str, Any] = {}

    if q:
        # Simple text search across title/description/location
        filter_query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"location": {"$regex": q, "$options": "i"}},
            {"country": {"$regex": q, "$options": "i"}},
        ]

    if country:
        filter_query["country"] = {"$regex": f"^{country}$", "$options": "i"}

    price_clause: Dict[str, Any] = {}
    if minPrice is not None:
        price_clause["$gte"] = float(minPrice)
    if maxPrice is not None:
        price_clause["$lte"] = float(maxPrice)
    if price_clause:
        filter_query["price_per_night"] = price_clause

    if guests is not None:
        filter_query["max_guests"] = {"$gte": int(guests)}

    items = db["homestay"].find(filter_query).limit(int(limit))
    return [serialize_doc(x) for x in items]


@app.get("/api/homestays/featured")
def featured_homestays(limit: int = 8):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    cursor = db["homestay"].find({}).limit(int(limit))
    return [serialize_doc(x) for x in cursor]


@app.post("/api/homestays", status_code=201)
def create_homestay(payload: Homestay):
    collection = "homestay"
    _id = create_document(collection, payload)
    doc = db[collection].find_one({"_id": db[collection].ObjectId(_id)}) if hasattr(db[collection], 'ObjectId') else db[collection].find_one({"_id": db[collection].find_one({"_id": {"$exists": True}})["_id"]})
    # Fallback: just return id when not easily re-finding
    return {"id": _id}


# ------- Bookings -------
@app.post("/api/bookings", status_code=201)
def create_booking(payload: Booking):
    # Basic date sanity
    try:
        ci = datetime.fromisoformat(payload.check_in)
        co = datetime.fromisoformat(payload.check_out)
        if co <= ci:
            raise HTTPException(status_code=400, detail="check_out must be after check_in")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    _id = create_document("booking", payload)
    return {"id": _id, "status": "created"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
