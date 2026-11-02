"""Synthetic Channel3 product candidate catalog for demo testing and offline operation."""

from typing import Any, List

RAW_DEMO_PRODUCTS: List[dict[str, Any]] = [
    {
        "product_id": "PROD-SONY-WH1000XM5",
        "title": "Sony WH-1000XM5 Wireless Noise Canceling Headphones",
        "brand": "Sony",
        "category": "over-ear headphones",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80",
        "description": "Industry Leading Noise Canceling with Auto NC Optimizer, 30-hour battery life, ultra-comfortable lightweight design.",
        "offers": [
            {
                "id": "OFFER-APEX-NEW-BLK",
                "merchant_name": "Apex Electronics",
                "merchant_domain": "apextech.com",
                "title": "Sony WH-1000XM5 - Brand New (Black)",
                "price": 89.99,
                "currency": "USD",
                "condition": "new",  # Explicit new
                "color": "black",
                "rating": 4.9,
                "in_stock": True,
                "shipping_fee": 0.00,
                "estimated_delivery_days": 3,
                "sku": "WH1000XM5-BLK-NEW",
            },
            {
                "id": "OFFER-SOUNDWAVE-NEW-SLV",
                "merchant_name": "SoundWave Hub",
                "merchant_domain": "soundwave.io",
                "title": "Sony WH-1000XM5 - Brand New (Silver)",
                "price": 94.99,
                "currency": "USD",
                "condition": "new",
                "color": "silver",
                "rating": 4.7,
                "in_stock": True,
                "shipping_fee": 5.00,
                "estimated_delivery_days": 4,
                "sku": "WH1000XM5-SLV-NEW",
            },
            {
                "id": "OFFER-RENEWED-REFURB-BLK",
                "merchant_name": "TechRenew Direct",
                "merchant_domain": "techrenew.com",
                "title": "Sony WH-1000XM5 - Certified Refurbished (Black)",
                "price": 69.99,
                "currency": "USD",
                "condition": "refurbished",
                "color": "black",
                "rating": 4.5,
                "in_stock": True,
                "shipping_fee": 0.00,
                "estimated_delivery_days": 3,
                "sku": "WH1000XM5-BLK-REFURB",
            },
            {
                "id": "OFFER-BARGAIN-NULL-COND",
                "merchant_name": "Market Bargains",
                "merchant_domain": "bargainmarket.net",
                "title": "Sony WH-1000XM5 Headphones (Open Box Deal)",
                "price": 79.99,
                "currency": "USD",
                "condition": None,  # DISC-02: condition: null must be treated as UNVERIFIED, never NEW
                "color": "black",
                "rating": 4.1,
                "in_stock": True,
                "shipping_fee": 0.00,
                "estimated_delivery_days": 5,
                "sku": "WH1000XM5-BLK-UNVERIFIED",
            },
            {
                "id": "OFFER-EURO-EUR-NONUSD",
                "merchant_name": "EuroSound Paris",
                "merchant_domain": "eurosound.fr",
                "title": "Sony WH-1000XM5 - Import Edition",
                "price": 85.00,
                "currency": "EUR",  # Non-USD currency for testing DISC-02 rejection
                "condition": "new",
                "color": "black",
                "rating": 4.6,
                "in_stock": True,
                "shipping_fee": 10.00,
                "estimated_delivery_days": 7,
                "sku": "WH1000XM5-BLK-EUR",
            },
        ],
    }
]

