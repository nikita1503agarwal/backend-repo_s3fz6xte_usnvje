import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents

app = FastAPI(title="Affiliate iGaming API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Affiliate iGaming API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:100]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:100]}"

    return response


# ===== Models for requests =====
class BonusClick(BaseModel):
    offer_id: str


# ===== Helper =====

def _to_safe(doc):
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


# ===== Endpoints =====
# Partners
@app.get("/api/partners")
def list_partners(featured: Optional[bool] = None):
    query = {}
    if featured is True:
        query["is_featured"] = True
    items = get_documents("affiliatepartner", query)
    return [_to_safe(i) for i in items]


# Bonus Offers
@app.get("/api/offers")
def list_offers(
    q: Optional[str] = None,
    category: Optional[str] = None,
    partner: Optional[str] = None,
    sort: Optional[str] = Query("featured", description="featured|amount_desc|amount_asc|latest"),
):
    query = {}
    if q:
        # Simple case-insensitive regex search on title and terms
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"terms": {"$regex": q, "$options": "i"}},
        ]
    if category:
        query["categories"] = {"$regex": f"^.*{category}.*$", "$options": "i"}
    if partner:
        query["partner_slug"] = partner

    items = get_documents("bonusoffer", query)

    def sort_key(it):
        if sort == "amount_desc":
            return -(it.get("amount") or 0)
        if sort == "amount_asc":
            return (it.get("amount") or 0)
        if sort == "latest":
            dt = it.get("created_at") or datetime.min
            try:
                return -dt.timestamp()
            except Exception:
                return 0
        # featured default: featured first, then clicks desc
        return (0 if it.get("is_featured") else 1, -(it.get("clicks") or 0))

    items = sorted(items, key=sort_key)
    return [_to_safe(i) for i in items]


@app.post("/api/offers/{offer_id}/click")
def track_click(offer_id: str):
    # lightweight increment using MongoDB update
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    res = db["bonusoffer"].update_one({"_id": {"$eq": __import__("bson").ObjectId(offer_id)}}, {"$inc": {"clicks": 1}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Offer not found")
    return {"ok": True}


# Leaderboard
@app.get("/api/leaderboard")
def get_leaderboard(period: str = Query("weekly", pattern="^(daily|weekly|monthly|all-time)$")):
    items = get_documents("leaderboardentry", {"period": period})
    items = sorted(items, key=lambda x: -(x.get("winnings") or 0))
    return [_to_safe(i) for i in items]


# Articles
@app.get("/api/articles")
def list_articles(tag: Optional[str] = None, q: Optional[str] = None):
    query = {}
    if tag:
        query["tags"] = tag
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"excerpt": {"$regex": q, "$options": "i"}},
        ]
    items = get_documents("article", query)
    items = sorted(items, key=lambda x: x.get("published_at") or datetime.min, reverse=True)
    return [_to_safe(i) for i in items]


@app.get("/api/articles/{slug}")
def get_article(slug: str):
    items = get_documents("article", {"slug": slug}, limit=1)
    if not items:
        raise HTTPException(status_code=404, detail="Article not found")
    return _to_safe(items[0])


# Site stats
@app.get("/api/stats")
def get_stats():
    docs = get_documents("sitestat", {}, limit=1)
    base = {"total_users": 0, "total_bonuses_claimed": 0, "partners_count": 0}
    if docs:
        base.update({k: docs[0].get(k, v) for k, v in base.items()})
    return base
