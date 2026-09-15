import os
import tempfile

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import RPCError

from nsfw import is_nsfw


API_ID = int(os.getenv("24984010", "0"))
API_HASH = os.getenv("dbcf69134629b947fbbf0544860a6a74", "")
BOT_TOKEN = os.getenv("8855777009:AAF75aXE8yogImBS_4TrEkP6GEjfCqsAHr0", "")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError(
        "Set API_ID, API_HASH and BOT_TOKEN environment variables."
    )


app = Client(
    "nsfw_moderation_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# User ID -> warning count
warnings = {}

MAX_WARNINGS = 3


@app.on_message(filters.sticker & filters.group)
async def sticker_moderation(client: Client, message: Message):

    # Admins ko scan nahi karna
    try:
        member = await client.get_chat_member(
            message.chat.id,
            message.from_user.id
        )

        if member.status in ("administrator", "owner"):
            return

    except Exception:
        pass

    # Static stickers only
    if message.sticker.is_animated or message.sticker.is_video:
        return

    path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".webp",
            delete=False
        ) as temp:
            path = temp.name

        await client.download_media(
            message,
            file_name=path
        )

        # Actual sticker image scan hoti hai.
        # Attached emoji (😂❤️🥵 etc.) ko ignore kiya jata hai.
        detected = is_nsfw(path)

        if not detected:
            return

        user = message.from_user

        # Delete NSFW sticker
        try:
            await message.delete()
        except RPCError as e:
            print("Delete error:", e)

        # Warning
        user_id = user.id
        warnings[user_id] = warnings.get(user_id, 0) + 1

        count = warnings[user_id]

        if count >= MAX_WARNINGS:

            try:
                # 3rd warning → mute for 24 hours
                from datetime import datetime, timedelta, timezone

                until = datetime.now(timezone.utc) + timedelta(hours=24)

                await client.restrict_chat_member(
                    message.chat.id,
                    user_id,
                    permissions=None,
                    until_date=until
                )

                await client.send_message(
                    message.chat.id,
                    f"🔇 {user.mention} muted for 24 hours.\n"
                    f"Reason: 3 NSFW sticker warnings."
                )

            except RPCError as e:
                print("Mute error:", e)

        else:
            await client.send_message(
                message.chat.id,
                f"⚠️ {user.mention}, NSFW sticker is not allowed.\n"
                f"Warning: {count}/{MAX_WARNINGS}"
            )

    except Exception as e:
        print("Moderation error:", e)

    finally:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


print("🤖 NSFW Moderation Bot started...")
app.run()
