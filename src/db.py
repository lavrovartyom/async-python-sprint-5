from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import SETTINGS
from models import Base

DATABASE_URL = (
    f"postgresql+asyncpg:/"
    f"/{SETTINGS.DB_USER}:{SETTINGS.DB_PASSWORD}@"
    f"{SETTINGS.DB_HOST}:{SETTINGS.DB_PORT}/{SETTINGS.DB_NAME}"
)

engine = create_async_engine(DATABASE_URL, echo=SETTINGS.ECHO_DB)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_db():
    await engine.dispose()
