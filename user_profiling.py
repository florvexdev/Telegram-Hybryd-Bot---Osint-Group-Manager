import logging
from sqlalchemy import select, func
from datetime import datetime, timedelta
from database import (
    get_session, 
    UserProfile, 
    MessageLog, 
    UserActivity, 
    MessageMetadata,
    UserInteraction
)

logger = logging.getLogger(__name__)


async def get_user_profile_report(chat_id: int, user_id: int) -> dict:
    """
    Generates a complete report on a user in a specific group.
    
    Return:
        dict with profile, statistics, recent messages and interactions
    """
    async with get_session() as session:
        # 1. Get user profile
        result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        # 2. Get activity in the group
        result = await session.execute(
            select(UserActivity).where(
                UserActivity.user_id == user_id,
                UserActivity.chat_id == chat_id,
            )
        )
        activity = result.scalar_one_or_none()
        
        if not activity:
            return None
        
        # 3. Statistics on messages
        result = await session.execute(
            select(func.count(MessageMetadata.id)).where(
                MessageMetadata.user_id == user_id,
                MessageMetadata.chat_id == chat_id,
                MessageMetadata.media_type != None,
            )
        )
        with_media = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(MessageMetadata.id)).where(
                MessageMetadata.user_id == user_id,
                MessageMetadata.chat_id == chat_id,
                MessageMetadata.media_type == None,
            )
        )
        text_only = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(MessageMetadata.id)).where(
                MessageMetadata.user_id == user_id,
                MessageMetadata.chat_id == chat_id,
                MessageMetadata.has_mention == True,
            )
        )
        with_mention = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(MessageMetadata.id)).where(
                MessageMetadata.user_id == user_id,
                MessageMetadata.chat_id == chat_id,
                MessageMetadata.has_hashtag == True,
            )
        )
        with_hashtag = result.scalar() or 0
        
        result = await session.execute(
            select(func.avg(MessageMetadata.text_length)).where(
                MessageMetadata.user_id == user_id,
                MessageMetadata.chat_id == chat_id,
            )
        )
        avg_length = result.scalar() or 0
        
        # 4. Get replies to user
        result = await session.execute(
            select(func.count(MessageMetadata.id)).where(
                MessageMetadata.user_id == user_id,
                MessageMetadata.chat_id == chat_id,
                MessageMetadata.reply_to_message_id != None,
            )
        )
        replies_sent = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(MessageMetadata.id)).where(
                MessageMetadata.reply_to_user_id == user_id,
                MessageMetadata.chat_id == chat_id,
                MessageMetadata.reply_to_message_id != None,
            )
        )
        replies_received = result.scalar() or 0
        
        # 5. Users they reply to most
        result = await session.execute(
            select(
                MessageMetadata.reply_to_user_id,
                func.count(MessageMetadata.id).label("cnt")
            ).where(
                MessageMetadata.user_id == user_id,
                MessageMetadata.chat_id == chat_id,
                MessageMetadata.reply_to_user_id != None,
            )
            .group_by(MessageMetadata.reply_to_user_id)
            .order_by(func.count(MessageMetadata.id).desc())
            .limit(5)
        )
        most_replied_to_rows = result.all()
        most_replied_to = []
        for replied_user_id, count in most_replied_to_rows:
            user_prof_result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == replied_user_id)
            )
            user_prof = user_prof_result.scalar_one_or_none()
            username = user_prof.username if user_prof else "Unknown"
            most_replied_to.append((replied_user_id, username, count))
        
        # 6. Who replies to them most
        result = await session.execute(
            select(
                MessageMetadata.user_id,
                func.count(MessageMetadata.id).label("cnt")
            ).where(
                MessageMetadata.reply_to_user_id == user_id,
                MessageMetadata.chat_id == chat_id,
                MessageMetadata.reply_to_message_id != None,
            )
            .group_by(MessageMetadata.user_id)
            .order_by(func.count(MessageMetadata.id).desc())
            .limit(5)
        )
        most_replies_from_rows = result.all()
        most_replies_from = []
        for replying_user_id, count in most_replies_from_rows:
            user_prof_result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == replying_user_id)
            )
            user_prof = user_prof_result.scalar_one_or_none()
            username = user_prof.username if user_prof else "Unknown"
            most_replies_from.append((replying_user_id, username, count))
        
        # 7. Activity by hour
        result = await session.execute(
            select(MessageMetadata.message_date).where(
                MessageMetadata.user_id == user_id,
                MessageMetadata.chat_id == chat_id,
            )
        )
        dates = result.scalars().all()
        activity_by_hour = {}
        for msg_date in dates:
            if msg_date:
                hour = msg_date.hour
                activity_by_hour[hour] = activity_by_hour.get(hour, 0) + 1
        
        top_hours = sorted(activity_by_hour.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 8. Last 5 messages with details
        result = await session.execute(
            select(MessageMetadata).where(
                MessageMetadata.user_id == user_id,
                MessageMetadata.chat_id == chat_id,
            )
            .order_by(MessageMetadata.message_date.desc())
            .limit(5)
        )
        recent_messages = result.scalars().all()
        
        messages_detail = []
        for msg in recent_messages:
            # Get message text from MessageLog
            text_result = await session.execute(
                select(MessageLog.text).where(
                    MessageLog.message_id == msg.message_id,
                    MessageLog.user_id == user_id,
                    MessageLog.chat_id == chat_id,
                )
            )
            text = text_result.scalar_one_or_none() or "[Media/Sticker]"
            
            # If it's a reply, get info about the user being replied to
            reply_to_username = None
            if msg.reply_to_user_id:
                reply_user_result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == msg.reply_to_user_id)
                )
                reply_user_profile = reply_user_result.scalar_one_or_none()
                reply_to_username = reply_user_profile.username if reply_user_profile else "Unknown"
            
            messages_detail.append({
                'date': msg.message_date,
                'text': text[:100] if text else "",  # Primi 100 caratteri
                'reply_to_user_id': msg.reply_to_user_id,
                'reply_to_username': reply_to_username,
                'media_type': msg.media_type,
            })
        
        return {
            'profile': profile,
            'total_messages': activity.total_messages,
            'first_seen': activity.first_seen,
            'last_seen': activity.last_seen,
            'message_stats': {
                'text_only': text_only,
                'with_media': with_media,
                'with_mention': with_mention,
                'with_hashtag': with_hashtag,
                'avg_length': round(avg_length, 1),
            },
            'replies_sent': replies_sent,
            'replies_received': replies_received,
            'most_replied_to': most_replied_to,
            'most_replies_from': most_replies_from,
            'activity_by_hour': activity_by_hour,
            'top_hours': top_hours,
            'messages_detail': messages_detail,
        }


def format_profile_report(report: dict, user_id: int) -> str:
    """Format the profile report into a readable message."""
    if not report:
        return f"❌ No data available for user {user_id}"
    
    profile = report['profile']
    stats = report['message_stats']
    
    name = f"{profile.first_name or ''} {profile.last_name or ''}".strip() or "Unknown"
    username = f"@{profile.username}" if profile.username else "N/A"
    
    first_seen = report['first_seen'].strftime("%d/%m/%Y %H:%M") if report['first_seen'] else "—"
    last_seen = report['last_seen'].strftime("%d/%m/%Y %H:%M") if report['last_seen'] else "—"
    
    # Giorni di attività
    if report['first_seen'] and report['last_seen']:
        days_active = (report['last_seen'] - report['first_seen']).days + 1
    else:
        days_active = 0
    
    # Top hours
    top_hours_text = ""
    if report['top_hours']:
        top_hours_text = "\n".join(
            f"    {h:02d}:00 — {count} msg" for h, count in report['top_hours']
        )
    else:
        top_hours_text = "    —"
    
    # Most replied to
    most_replied_text = ""
    if report['most_replied_to']:
        most_replied_text = "\n".join(
            f"    • {username or f'User {uid}'}: {count} replies"
            for uid, username, count in report['most_replied_to']
        )
    else:
        most_replied_text = "    —"
    
    # Most replies from
    most_replies_from_text = ""
    if report['most_replies_from']:
        most_replies_from_text = "\n".join(
            f"    • {username or f'User {uid}'}: {count} replies"
            for uid, username, count in report['most_replies_from']
        )
    else:
        most_replies_from_text = "    —"
    
    # Recent messages
    messages_text = ""
    if report.get('messages_detail'):
        messages_lines = []
        for i, msg in enumerate(report['messages_detail'], 1):
            time_str = msg['date'].strftime("%H:%M") if msg['date'] else "—"
            text_preview = msg['text'][:80] if msg['text'] else "[No text]"
            
            reply_info = ""
            if msg['reply_to_username']:
                reply_info = f"\n       └ Reply to: @{msg['reply_to_username']}"
            
            media_info = ""
            if msg['media_type']:
                media_info = f" [{msg['media_type'].upper()}]"
            
            messages_lines.append(f"    {i}. {time_str} — {text_preview}{media_info}{reply_info}")
        
        messages_text = "\n".join(messages_lines)
    else:
        messages_text = "    —"
    
    message = (
        f"👤  <b>COMPLETE PROFILE</b>\n"
        f"{'┄' * 35}\n\n"
        f"<b>Identity</b>\n"
        f"  ID: <code>{profile.user_id}</code>\n"
        f"  Name: {name}\n"
        f"  Username: {username}\n"
        f"  Bot: {'✅' if profile.is_bot else '❌'}\n"
        f"  Premium: {'✅' if profile.is_premium else '❌'}\n\n"
        f"<b>Group activity</b>\n"
        f"  Total messages: <b>{report['total_messages']}</b>\n"
        f"  First message: {first_seen}\n"
        f"  Last message: {last_seen}\n"
        f"  Days active: {days_active}\n\n"
        f"<b>Message types</b>\n"
        f"  Text only: {stats['text_only']}\n"
        f"  With media: {stats['with_media']}\n"
        f"  With mentions: {stats['with_mention']}\n"
        f"  With hashtags: {stats['with_hashtag']}\n"
        f"  Average length: {stats['avg_length']} characters\n\n"
        f"<b>Interactions</b>\n"
        f"  Replies sent: {report['replies_sent']}\n"
        f"  Replies received: {report['replies_received']}\n\n"
        f"<b>Top activity hours</b>\n"
        f"{top_hours_text}\n\n"
        f"<b>Users they reply to most</b>\n"
        f"{most_replied_text}\n\n"
        f"<b>Users who reply to them most</b>\n"
        f"{most_replies_from_text}\n\n"
        f"<b>Last 5 messages</b>\n"
        f"{messages_text}"
    )
    
    return message
