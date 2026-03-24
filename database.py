from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, Boolean, Float
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    title = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, index=True, nullable=False)
    user_id = Column(BigInteger, index=True, nullable=False)
    date = Column(DateTime, nullable=True)
    message_id = Column(Integer, nullable=True)
    text = Column(Text, nullable=True)


class UserActivity(Base):
    __tablename__ = "user_activity"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True, nullable=False)
    chat_id = Column(BigInteger, index=True, nullable=False)
    total_messages = Column(Integer, default=0)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    profile_photo_url = Column(String, nullable=True)
    is_bot = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    phone = Column(String, nullable=True)
    dc_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MessageMetadata(Base):
    __tablename__ = "message_metadata"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, index=True, nullable=False)
    message_id = Column(Integer, nullable=False)
    user_id = Column(BigInteger, index=True, nullable=False)
    reply_to_message_id = Column(Integer, nullable=True)
    reply_to_user_id = Column(BigInteger, nullable=True)
    media_type = Column(String, nullable=True)  # photo, video, document, etc.
    text_length = Column(Integer, default=0)
    has_mention = Column(Boolean, default=False)
    has_hashtag = Column(Boolean, default=False)
    message_date = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, index=True, nullable=False)
    from_user_id = Column(BigInteger, index=True, nullable=False)
    to_user_id = Column(BigInteger, index=True, nullable=False)
    interaction_type = Column(String, nullable=False)  # reply, mention, quote
    count = Column(Integer, default=1)
    last_interaction = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


async def init_db() -> None:
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager to get a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
