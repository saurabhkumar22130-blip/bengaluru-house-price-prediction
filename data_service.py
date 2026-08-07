"""Real estate data layer — listings, luxury picks, deals, and brokers."""

from __future__ import annotations

import random
from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd

PROPERTY_IMAGES = [
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&q=80",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&q=80",
    "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800&q=80",
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&q=80",
    "https://images.unsplash.com/photo-1605276374101-dee0d0c3a0c0?w=800&q=80",
    "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=800&q=80",
    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&q=80",
    "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800&q=80",
]

LUXURY_IMAGES = [
    "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=800&q=80",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&q=80",
    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800&q=80",
    "https://images.unsplash.com/photo-1600210492486-724fe4c6d6a0?w=800&q=80",
]

LISTING_TYPES = ("sale", "rent", "invest")
AMENITIES_POOL = [
    "Swimming Pool", "Gym", "Clubhouse", "24/7 Security",
    "Power Backup", "Parking", "Garden", "Smart Home",
]


@dataclass
class Broker:
    id: int
    name: str
    title: str
    phone: str
    email: str
    areas: str
    rating: float
    deals_closed: int
    photo: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


BROKERS = [
    Broker(1, "Priya Sharma", "Senior Luxury Advisor", "+91 98765 43210",
           "priya.sharma@estatehub.in", "Indira Nagar, Whitefield", 4.9, 142,
           "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=200&q=80"),
    Broker(2, "Rahul Mehta", "Investment Specialist", "+91 98765 43211",
           "rahul.mehta@estatehub.in", "Electronic City, Sarjapur", 4.8, 98,
           "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&q=80"),
    Broker(3, "Ananya Reddy", "Commercial & Residential", "+91 98765 43212",
           "ananya.reddy@estatehub.in", "Koramangala, HSR Layout", 4.7, 115,
           "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=200&q=80"),
    Broker(4, "Vikram Singh", "Luxury Portfolio Manager", "+91 98765 43213",
           "vikram.singh@estatehub.in", "Cunningham Road, Malleshwaram", 4.9, 167,
           "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&q=80"),
]


class PropertyCatalog:
    """Builds enriched property listings from the training CSV."""

    def __init__(self, csv_path: str) -> None:
        self._df = pd.read_csv(csv_path)
        self._df = self._df.dropna(subset=["location", "price", "total_sqft", "bhk"])
        random.seed(42)
        self._listings = self._build_listings()

    def _build_listings(self) -> list[dict[str, Any]]:
        listings: list[dict[str, Any]] = []
        sample = self._df.sample(n=min(400, len(self._df)), random_state=42)

        for idx, row in sample.iterrows():
            price = float(row["price"])
            sqft = float(row["total_sqft"])
            bhk = int(row["bhk"])
            location = str(row["location"])
            listing_type = random.choice(LISTING_TYPES)
            is_luxury = price >= 150
            discount = random.choice([0, 0, 0, 5, 8, 10, 12, 15]) if price > 60 else random.choice([0, 0, 5])
            original = round(price * (1 + discount / 100), 2) if discount else price
            amenities = random.sample(AMENITIES_POOL, k=random.randint(2, 5))
            trending_score = round(min(99, 50 + price / 20 + random.uniform(0, 15)), 1)

            listings.append({
                "id": int(idx),
                "title": f"{bhk} BHK {'Villa' if sqft > 2000 else 'Apartment'} in {location}",
                "location": location,
                "price": round(price, 2),
                "original_price": round(original, 2),
                "discount_pct": discount,
                "sqft": int(sqft),
                "bath": int(row["bath"]) if pd.notna(row.get("bath")) else bhk,
                "bhk": bhk,
                "listing_type": listing_type,
                "is_luxury": is_luxury,
                "image": LUXURY_IMAGES[len(listings) % len(LUXURY_IMAGES)]
                if is_luxury else PROPERTY_IMAGES[len(listings) % len(PROPERTY_IMAGES)],
                "amenities": amenities,
                "trending_score": trending_score,
                "price_per_sqft": round(price * 100000 / sqft) if sqft else 0,
                "verified": random.random() > 0.15,
            })

        return sorted(listings, key=lambda x: x["price"], reverse=True)

    @property
    def locations(self) -> list[str]:
        return sorted(self._df["location"].unique())

    def all_listings(self) -> list[dict[str, Any]]:
        return self._listings

    def filter_listings(
        self,
        location: str | None = None,
        listing_type: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        bhk: int | None = None,
        luxury_only: bool = False,
        deals_only: bool = False,
    ) -> list[dict[str, Any]]:
        results = self._listings
        if location:
            results = [p for p in results if location.lower() in p["location"].lower()]
        if listing_type:
            results = [p for p in results if p["listing_type"] == listing_type]
        if min_price is not None:
            results = [p for p in results if p["price"] >= min_price]
        if max_price is not None:
            results = [p for p in results if p["price"] <= max_price]
        if bhk is not None:
            results = [p for p in results if p["bhk"] == bhk]
        if luxury_only:
            results = [p for p in results if p["is_luxury"]]
        if deals_only:
            results = [p for p in results if p["discount_pct"] > 0]
        return results

    def trending_luxury(self, area: str | None = None, limit: int = 8) -> list[dict[str, Any]]:
        luxury = [p for p in self._listings if p["is_luxury"]]
        if area:
            luxury = [p for p in luxury if area.lower() in p["location"].lower()]
        luxury.sort(key=lambda x: (x["trending_score"], x["price"]), reverse=True)
        return luxury[:limit]

    def hot_deals(self, limit: int = 8) -> list[dict[str, Any]]:
        deals = [p for p in self._listings if p["discount_pct"] >= 5]
        deals.sort(key=lambda x: x["discount_pct"], reverse=True)
        return deals[:limit]

    def featured(self, limit: int = 6) -> list[dict[str, Any]]:
        featured = sorted(self._listings, key=lambda x: x["trending_score"], reverse=True)
        return featured[:limit]

    def get_by_id(self, property_id: int) -> dict[str, Any] | None:
        for p in self._listings:
            if p["id"] == property_id:
                return p
        return None

    def market_stats(self) -> dict[str, Any]:
        df = self._df
        return {
            "total_listings": len(self._listings),
            "avg_price": round(df["price"].mean(), 1),
            "median_price": round(df["price"].median(), 1),
            "locations_count": df["location"].nunique(),
            "luxury_count": sum(1 for p in self._listings if p["is_luxury"]),
            "active_deals": sum(1 for p in self._listings if p["discount_pct"] > 0),
            "avg_price_per_sqft": round((df["price"] * 100000 / df["total_sqft"]).mean()),
        }

    def location_trends(self, limit: int = 6) -> list[dict[str, Any]]:
        trends = (
            self._df.groupby("location")["price"]
            .agg(["mean", "count"])
            .reset_index()
        )
        trends.columns = ["location", "avg_price", "count"]
        trends = trends[trends["count"] >= 20].sort_values("avg_price", ascending=False)
        results = []
        for _, row in trends.head(limit).iterrows():
            results.append({
                "location": row["location"],
                "avg_price": round(row["avg_price"], 1),
                "growth_pct": round(random.uniform(4, 18), 1),
                "demand": random.choice(["High", "Very High", "Moderate"]),
            })
        return results


def format_price_lakh(price: float) -> str:
    if price >= 100:
        return f"₹{price / 100:.2f} Cr"
    return f"₹{price:.0f} L"
