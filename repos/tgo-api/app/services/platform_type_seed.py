"""Seed default platform types into ai_platform_types table (idempotent).

This runs on service startup and performs an upsert by unique key `type` to
avoid duplicate rows while keeping names/icons up to date.
"""
from __future__ import annotations

from typing import List, Dict

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import startup_log
from app.models.platform import PlatformTypeDefinition


SEED_PLATFORM_TYPES: List[Dict[str, str]] = [
    {
        "type": "wechat",
        "name": "WeChat",
        "icon": """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\"><circle cx=\"26\" cy=\"26\" r=\"18\" fill=\"#07C160\"/><circle cx=\"42\" cy=\"42\" r=\"14\" fill=\"#07C160\"/><circle cx=\"20\" cy=\"24\" r=\"3\" fill=\"#ffffff\"/><circle cx=\"32\" cy=\"24\" r=\"3\" fill=\"#ffffff\"/><circle cx=\"36\" cy=\"40\" r=\"3\" fill=\"#ffffff\"/><circle cx=\"46\" cy=\"40\" r=\"3\" fill=\"#ffffff\"/></svg>""",
    },
    {
        "type": "website",
        "name": "Website",
        "icon": """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\"><rect x=\"8\" y=\"12\" width=\"48\" height=\"32\" rx=\"4\" fill=\"#2563eb\"/><rect x=\"12\" y=\"16\" width=\"40\" height=\"24\" rx=\"2\" fill=\"#ffffff\"/><rect x=\"20\" y=\"46\" width=\"24\" height=\"4\" rx=\"2\" fill=\"#1e3a8a\"/><rect x=\"24\" y=\"52\" width=\"16\" height=\"4\" rx=\"2\" fill=\"#1e40af\"/></svg>""",
    },
    {
        "type": "tiktok",
        "name": "TikTok",
        "icon": """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\"><path fill=\"#010101\" d=\"M36 8h8.2C44.6 15 49.2 19 56 19v8.4c-4.9 0-8.8-1.5-12-4v18c0 8.6-7 15.6-15.6 15.6S12.8 49 12.8 40.4s7-15.6 15.6-15.6c1.2 0 2.3.1 3.4.4V34c-.9-.3-1.9-.4-2.9-.4-3.6 0-6.6 3-6.6 6.6s3 6.6 6.6 6.6S35 43.8 35 40.2V8z\"/><path fill=\"#69C9D0\" d=\"M52 19.5c-3.9-.6-7.1-2.7-9.8-5.5v5.6c2.3 1.8 5.4 3.5 9.8 3.7V19.5z\"/><path fill=\"#EE1D52\" d=\"M28.4 24.8c-8.6 0-15.6 7-15.6 15.6 0 6.6 4.2 12.2 10.1 14.4-3.4-2.7-5.6-6.9-5.6-11.5 0-8.6 7-15.6 15.6-15.6 1.2 0 2.3.1 3.4.4v-6.2c-1.2-.2-2.5-.3-3.9-.3z\"/></svg>""",
    },
    {
        "type": "douyin",
        "name": "Douyin",
        "icon": """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\"><path fill=\"#121212\" d=\"M37 8h8c.4 6.3 5.1 10.6 12 11.1v8c-4.6-.3-8.5-1.9-12-4.3V42c0 8.8-7.2 16-16 16S13 50.8 13 42s7.2-16 16-16c1.3 0 2.6.2 3.8.5v7.6c-1.1-.6-2.4-.9-3.8-.9-4.2 0-7.6 3.4-7.6 7.6s3.4 7.6 7.6 7.6S40 47.2 40 43V8z\"/><path fill=\"#20D5C3\" d=\"M52 19.2c-3.9-.9-7-3-9.5-6v5.6c2.3 1.9 5.3 3.6 9.5 4V19.2z\"/><path fill=\"#FF0050\" d=\"M29 25.5c-8.8 0-16 7.2-16 16 0 6.9 4.4 12.8 10.6 15-3.6-2.8-5.9-7.1-5.9-12 0-8.8 7.2-16 16-16 1.3 0 2.6.1 3.8.4v-6.7c-1.4-.4-2.8-.7-4.5-.7z\"/></svg>""",
    },
    {
        "type": "email",
        "name": "Email",
        "icon": """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\"><rect x=\"8\" y=\"16\" width=\"48\" height=\"32\" rx=\"4\" fill=\"#0ea5e9\"/><path fill=\"#ffffff\" d=\"M12 20h40v24H12z\"/><path fill=\"#0ea5e9\" d=\"M12 20l20 16L52 20v4L32 40 12 24z\"/></svg>""",
    },
    {
        "type": "custom",
        "name": "Custom",
        "icon": """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\"><path fill=\"#9333ea\" d=\"M26 12a10 10 0 0 1 9.7 7.4l4.5 12.6H34l-2.9-8.4a4 4 0 0 0-3.1-2.6 8 8 0 1 0-1.6 15.8h5.1l4.7 13.1a10 10 0 1 1-9.2 3.9l5.5-.1 1.6 4.3a4 4 0 1 0 7.4-2.8L31.5 34H40a8 8 0 1 0 7.8-10.2H39.7l-1.9-5.3A10 10 0 0 1 46 16a10 10 0 0 1 0 20h-.3a12 12 0 1 1-11.4 16.2A12 12 0 1 1 16 32h.3A10 10 0 0 1 26 12z\"/></svg>""",
    },
]


def ensure_platform_types_seed() -> None:
    """Ensure default platform types exist; upsert by unique `type`."""
    db: Session = SessionLocal()
    try:
        for row in SEED_PLATFORM_TYPES:
            stmt = insert(PlatformTypeDefinition).values(
                type=row["type"], name=row["name"], icon=row["icon"],
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[PlatformTypeDefinition.type],
                set_={
                    "name": stmt.excluded.name,
                    "icon": stmt.excluded.icon,
                },
            )
            db.execute(stmt)
        db.commit()
        startup_log("✅ Platform types seeded (idempotent)")
    except Exception as e:  # pragma: no cover
        db.rollback()
        startup_log(f"⚠️  Failed to seed platform types: {e}")
    finally:
        db.close()

