import asyncio
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from evaluator import evaluate_post
from config import Config

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


def format_notification(score: int, summary: str, reason: str, channel_title: str) -> str:
    bar = "🟩" * score + "⬜" * (10 - score)
    return (
        f"📊 **투자 인사이트 알림** [{score}/10]\n"
        f"{bar}\n\n"
        f"**요약**\n{summary}\n\n"
        f"**평가 이유** {reason}\n\n"
        f"📢 출처: {channel_title}"
    )


async def main():
    client = TelegramClient(
        StringSession(Config.SESSION),
        Config.API_ID,
        Config.API_HASH,
    )

    @client.on(events.NewMessage(chats=Config.CHANNELS))
    async def handler(event):
        msg = event.message
        text = msg.text or msg.caption or ""

        if len(text) < Config.MIN_TEXT_LENGTH:
            return

        channel_title = getattr(await event.get_chat(), "title", "알 수 없는 채널")
        log.info(f"New post from {channel_title} ({len(text)} chars) — evaluating...")

        score, summary, reason = await evaluate_post(text)
        log.info(f"Score: {score}/10")

        if score >= Config.MIN_SCORE:
            notification = format_notification(score, summary, reason, channel_title)
            await client.send_message(Config.NOTIFY_TARGET, notification)
            await client.forward_messages(Config.NOTIFY_TARGET, msg)
            log.info(f"Notification sent (score={score})")

    await client.start()
    log.info(f"Monitoring {len(Config.CHANNELS)} channels: {Config.CHANNELS}")
    log.info(f"Min score to notify: {Config.MIN_SCORE}/10")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
