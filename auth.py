"""
Run this script ONCE on your local machine to generate a session string.
Copy the printed session string into your .env file as TG_SESSION.
After that, Railway can run main.py without interactive login.
"""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

async def main():
    api_id = int(input("API ID: ").strip())
    api_hash = input("API Hash: ").strip()

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start()

    session_string = client.session.save()
    print("\n" + "=" * 60)
    print("SESSION STRING (save this as TG_SESSION in your .env):")
    print("=" * 60)
    print(session_string)
    print("=" * 60 + "\n")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
