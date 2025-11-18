"""
Database Schemas for Toshi Home

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercase name of the class. Example: Homestay -> "homestay" collection

These schemas are used for validation when creating documents.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class Homestay(BaseModel):
    """Homestay listings users can book"""
    title: str = Field(..., description="Listing title")
    description: Optional[str] = Field(None, description="Short description")
    location: str = Field(..., description="City/Area")
    country: str = Field(..., description="Country")
    price_per_night: float = Field(..., ge=0, description="Price per night in USD")
    max_guests: int = Field(..., ge=1, le=20, description="Maximum guests allowed")
    amenities: List[str] = Field(default_factory=list, description="List of amenities")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")


class Booking(BaseModel):
    """Bookings made by guests for a homestay"""
    homestay_id: str = Field(..., description="Target homestay _id as string")
    guest_name: str = Field(..., description="Name of guest")
    guest_email: EmailStr = Field(..., description="Contact email")
    guests: int = Field(..., ge=1, le=20, description="Number of guests")
    check_in: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    check_out: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    notes: Optional[str] = Field(None, description="Optional notes from guest")
