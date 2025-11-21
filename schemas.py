"""
Database Schemas for Affiliate iGaming app

Each Pydantic model below maps to a MongoDB collection with the lowercase
class name. For example: BonusOffer -> "bonusoffer" collection.

Use these models with the helper functions from database.py
(create_document, get_documents) in your API routes.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AffiliatePartner(BaseModel):
    name: str = Field(..., description="Partner/platform name, e.g., Clash.gg")
    slug: str = Field(..., description="URL-safe identifier")
    logo_url: Optional[str] = Field(None, description="Public logo URL")
    website_url: Optional[str] = Field(None, description="Destination website homepage")
    rating: Optional[float] = Field(4.5, ge=0, le=5, description="Average rating out of 5")
    categories: List[str] = Field(default_factory=list, description="Supported categories: casino, esports, sports, slots, etc.")
    is_featured: bool = Field(False, description="Show on homepage as featured")


class BonusOffer(BaseModel):
    partner_slug: str = Field(..., description="Slug of the partner this offer belongs to")
    title: str = Field(..., description="Short headline for the bonus")
    code: Optional[str] = Field(None, description="Affiliate/bonus code for easy copy")
    bonus_type: str = Field(..., description="e.g., deposit match, free credits, cash back, free spins")
    amount: Optional[float] = Field(None, ge=0, description="Numeric amount (if applicable)")
    currency: Optional[str] = Field("USD", description="Currency code if amount is monetary")
    terms: Optional[str] = Field(None, description="Short summary of terms")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration datetime")
    url: str = Field(..., description="Tracking URL to claim the bonus")
    min_deposit: Optional[float] = Field(None, ge=0, description="Minimum deposit if applicable")
    categories: List[str] = Field(default_factory=list, description="Tags/categories for filtering")
    clicks: int = Field(0, ge=0, description="Click-through count for leaderboard/conversion stats")
    is_featured: bool = Field(False, description="Promote on homepage")


class LeaderboardEntry(BaseModel):
    username: str = Field(..., description="Display name or anonymized user tag")
    period: str = Field(..., description="daily | weekly | monthly | all-time")
    winnings: float = Field(..., ge=0, description="Total winnings or points")
    bonuses_claimed: int = Field(0, ge=0, description="Count of bonuses claimed")


class Article(BaseModel):
    title: str = Field(...)
    slug: str = Field(...)
    cover_image: Optional[str] = Field(None)
    excerpt: Optional[str] = Field(None)
    content: str = Field(..., description="Markdown or HTML content")
    tags: List[str] = Field(default_factory=list)
    published_at: datetime = Field(default_factory=datetime.utcnow)
    author: Optional[str] = Field("Editorial Team")


class Testimonial(BaseModel):
    name: str
    quote: str
    avatar_url: Optional[str] = None


class SiteStat(BaseModel):
    total_users: int = 0
    total_bonuses_claimed: int = 0
    partners_count: int = 0

# Existing example schemas kept for reference
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True


class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
