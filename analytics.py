import logging
from sqlalchemy import select, func
from datetime import datetime, timedelta
from database import get_session, MessageLog, UserActivity

logger = logging.getLogger(__name__)


async def generate_group_report(chat_id: int, days: int = 30) -> str:
    """Generates a text report with group statistics."""
    since = datetime.utcnow() - timedelta(days=days)

    async with get_session() as session:
        # Total messages in the period
        total_msgs = await session.scalar(
            select(func.count(MessageLog.id)).where(
                MessageLog.chat_id == chat_id,
                MessageLog.date >= since,
            )
        )

        # Active unique users
        active_users = await session.scalar(
            select(func.count(func.distinct(MessageLog.user_id))).where(
                MessageLog.chat_id == chat_id,
                MessageLog.date >= since,
            )
        )

        # Top 5 users by number of messages
        result = await session.execute(
            select(MessageLog.user_id, func.count(MessageLog.id).label("cnt"))
            .where(
                MessageLog.chat_id == chat_id,
                MessageLog.date >= since,
            )
            .group_by(MessageLog.user_id)
            .order_by(func.count(MessageLog.id).desc())
            .limit(5)
        )
        top_rows = result.all()

    top_list = [f"• User `{uid}`: {cnt} messages" for uid, cnt in top_rows]
    top_text = "\n".join(top_list) if top_list else "No data available"

    report = (
        f"📊 *Group report (last {days} days)*\n\n"
        f"📨 Total messages: *{total_msgs or 0}*\n"
        f"👥 Active users: *{active_users or 0}*\n\n"
        f"🏆 *Top users by messages:*\n{top_text}"
    )
    return report


async def process_message(message_data: dict) -> None:
    """
    Optional processing of a message in real-time
    (e.g., sentiment analysis, keyword detection, etc.).
    """
    pass
