import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import AffiliatePartner, BonusOffer, LeaderboardEntry, Article, SiteStat

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


# ===== Admin/Seed =====
@app.post("/admin/seed-demo")
def seed_demo():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    now = datetime.now(timezone.utc)

    partners = [
        AffiliatePartner(
            name="Clash.gg",
            slug="clash-gg",
            logo_url="https://logos-world.net/wp-content/uploads/2020/11/CSGO-Emblem.png",
            website_url="https://clash.gg",
            rating=4.6,
            categories=["esports", "cases", "casino"],
            is_featured=True,
        ),
        AffiliatePartner(
            name="Stake",
            slug="stake",
            logo_url="https://seeklogo.com/images/S/stake-logo-63B55D46E5-seeklogo.com.png",
            website_url="https://stake.com",
            rating=4.8,
            categories=["sports", "casino", "slots"],
            is_featured=True,
        ),
        AffiliatePartner(
            name="Rollbit",
            slug="rollbit",
            logo_url="https://cryptologos.cc/logos/bitcoin-btc-logo.png",
            website_url="https://rollbit.com",
            rating=4.4,
            categories=["casino", "trading"],
            is_featured=False,
        ),
    ]

    offers = [
        BonusOffer(
            partner_slug="clash-gg",
            title="100% Deposit Match up to $200",
            code="CLASH200",
            bonus_type="deposit match",
            amount=200,
            currency="USD",
            terms="New users only. 18+ T&C apply.",
            url="https://clash.gg/aff/claim?code=CLASH200",
            min_deposit=20,
            categories=["esports", "casino"],
            is_featured=True,
        ),
        BonusOffer(
            partner_slug="stake",
            title="10% Rakeback for 7 Days",
            code="RAKE10",
            bonus_type="cash back",
            terms="Available after first deposit.",
            url="https://stake.com/aff/RAKE10",
            categories=["sports", "casino"],
            is_featured=True,
        ),
        BonusOffer(
            partner_slug="rollbit",
            title="50 Free Spins on Sign Up",
            code=None,
            bonus_type="free spins",
            amount=50,
            terms="No deposit required. Selected slots only.",
            url="https://rollbit.com/bonus/free-spins",
            categories=["slots"],
            is_featured=False,
        ),
    ]

    leaderboard = [
        LeaderboardEntry(username="AceHunter", period="weekly", winnings=1520.75, bonuses_claimed=3),
        LeaderboardEntry(username="LuckyLuke", period="weekly", winnings=985.2, bonuses_claimed=5),
        LeaderboardEntry(username="Shadow", period="weekly", winnings=2100.0, bonuses_claimed=1),
        LeaderboardEntry(username="SpinQueen", period="weekly", winnings=1337.0, bonuses_claimed=4),
    ]

    articles = [
        Article(
            title="Top Esports Betting Bonuses This Week",
            slug="top-esports-bonuses-week",
            cover_image="https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=1600&auto=format&fit=crop",
            excerpt="We roundup the best esports betting bonuses and how to maximize them.",
            content="""
            <h2>Best picks</h2>
            <p>Here are the standout offers across our partners this week, covering match bets, risk-free slips, and deposit matches.</p>
            <ul>
              <li>Clash.gg – 100% up to $200 with code CLASH200</li>
              <li>Stake – 10% Rakeback for 7 Days</li>
              <li>Rollbit – 50 Free Spins on Sign Up</li>
            </ul>
            """,
            tags=["esports", "bonuses"],
            author="Editorial Team",
        ),
        Article(
            title="Beginner's Guide to Casino Rakeback",
            slug="beginners-guide-rakeback",
            cover_image="https://images.unsplash.com/photo-1504274066651-8d31a536b11a?q=80&w=1600&auto=format&fit=crop",
            excerpt="Understand how rakeback works and how to take advantage without overspending.",
            content="""
            <p>Rakeback returns a percentage of house edge to the player. We'll cover the basics and pitfalls.</p>
            """,
            tags=["casino", "guides"],
            author="Editorial Team",
        ),
    ]

    stats = SiteStat(total_users=12450, total_bonuses_claimed=3287, partners_count=3)

    # Upsert helpers
    def upsert_partner(p: AffiliatePartner):
        db["affiliatepartner"].update_one(
            {"slug": p.slug},
            {"$set": {**p.model_dump(), "updated_at": now}, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

    def upsert_offer(o: BonusOffer):
        db["bonusoffer"].update_one(
            {"partner_slug": o.partner_slug, "title": o.title},
            {"$set": {**o.model_dump(), "updated_at": now}, "$setOnInsert": {"created_at": now, "clicks": 0}},
            upsert=True,
        )

    def upsert_leaderboard(e: LeaderboardEntry):
        db["leaderboardentry"].update_one(
            {"period": e.period, "username": e.username},
            {"$set": {**e.model_dump(), "updated_at": now}, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

    def upsert_article(a: Article):
        db["article"].update_one(
            {"slug": a.slug},
            {"$set": {**a.model_dump(), "updated_at": now}, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

    # Execute upserts
    for p in partners:
        upsert_partner(p)
    for o in offers:
        upsert_offer(o)
    for e in leaderboard:
        upsert_leaderboard(e)
    for a in articles:
        upsert_article(a)

    # Stats (single doc)
    db["sitestat"].update_one(
        {}, {"$set": {**stats.model_dump(), "updated_at": now}, "$setOnInsert": {"created_at": now}}, upsert=True
    )

    # Return counts
    counts = {
        "partners": db["affiliatepartner"].count_documents({}),
        "offers": db["bonusoffer"].count_documents({}),
        "leaderboard": db["leaderboardentry"].count_documents({}),
        "articles": db["article"].count_documents({}),
        "stats_docs": db["sitestat"].count_documents({}),
    }

    return {"ok": True, "seeded": counts}


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
