from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import generic_exception_handler
from app.core.logging import setup_logging

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


def create_app() -> FastAPI:
    setup_logging()

    application = FastAPI(
        title="EightySix",
        description="EightySix — Restaurant Operations Backend",
        version=settings.APP_VERSION,
    )

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_exception_handler(Exception, generic_exception_handler)
    application.include_router(api_router)

    return application


app = create_app()


@app.on_event("startup")
async def _seed_demo():
    """Ensure demo user has a real password hash and a populated location."""
    import logging
    logger = logging.getLogger(__name__)

    if not settings.DEMO_MODE:
        return

    from app.db.session import async_session_factory
    from app.services.auth_service import hash_password, get_user_by_email

    async with async_session_factory() as db:
        try:
            # Advisory lock to prevent race between uvicorn workers
            from sqlalchemy import text
            lock_result = await db.execute(text("SELECT pg_try_advisory_lock(86860001)"))
            got_lock = lock_result.scalar()
            if not got_lock:
                logger.info("Another worker is seeding demo data, skipping")
                return

            user = await get_user_by_email(db, settings.DEMO_USER_EMAIL)
            if user and user.hashed_password == "$PLACEHOLDER$":
                user.hashed_password = hash_password(settings.DEMO_USER_PASSWORD)
                await db.flush()
                logger.info("Demo user password hash set")

            # Bootstrap demo location if no locations exist
            from sqlalchemy import select, func
            from app.db.models.location import Location
            count = (await db.execute(select(func.count()).select_from(Location))).scalar()
            if count == 0:
                from app.services.demo_bootstrap import bootstrap_demo_location
                await bootstrap_demo_location(db)
                logger.info("Demo location bootstrapped with 8 weeks of history")

            # Seed holidays for current and next year if none exist
            from app.db.models.external_event import ExternalEvent
            from datetime import date
            holiday_count = (await db.execute(
                select(func.count()).select_from(ExternalEvent).where(ExternalEvent.event_type == "holiday")
            )).scalar()
            if holiday_count == 0:
                from app.external.holidays import generate_holiday_events
                year = date.today().year
                for evt in generate_holiday_events(year) + generate_holiday_events(year + 1):
                    db.add(evt)
                await db.flush()
                logger.info("Seeded holiday calendar for %d and %d", year, year + 1)

            await db.commit()
            await db.execute(text("SELECT pg_advisory_unlock(86860001)"))
        except Exception:
            logger.exception("Demo seed failed — non-fatal, continuing startup")
            await db.rollback()
            await db.execute(text("SELECT pg_advisory_unlock(86860001)"))
