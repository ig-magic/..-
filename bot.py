import asyncio
import os
import random
from pyrogram import Client, filters

# ===== ENV =====
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session = os.environ.get("SESSION")

MAIN_ID = int(os.environ.get("MAIN_ID"))
TARGET_USERS = list(map(int, os.environ.get("TARGET_USERS").split(",")))

# ===== CLIENT =====
app = Client("userbot", api_id=api_id, api_hash=api_hash, session_string=session)

msg_map = {}
forwarding = True


# ===== SAFE SEND =====
async def safe_send(chat_id, text):
    await asyncio.sleep(random.randint(1, 3))
    return await app.send_message(chat_id, text)


# ===== UNREAD MESSAGES =====
async def forward_unread():
    for user in TARGET_USERS:
        async for msg in app.get_chat_history(user, limit=20):
            if msg.unread:

                name = msg.from_user.first_name if msg.from_user else "User"
                text = msg.text or "📎 Media"

                sent = await safe_send(
                    MAIN_ID,
                    f"📩 Unread {name}:\n{text}"
                )

                msg_map[sent.id] = user


# ===== NEW MESSAGES =====
@app.on_message(filters.private & filters.incoming)
async def new_messages(client, message):
    global forwarding

    if not forwarding:
        return

    if not message.from_user:
        return

    user_id = message.from_user.id

    if user_id in TARGET_USERS:

        name = message.from_user.first_name

        if message.text:
            sent = await safe_send(
                MAIN_ID,
                f"👤 {name}:\n{message.text}"
            )
        else:
            sent = await message.forward(MAIN_ID)

        msg_map[sent.id] = user_id


# ===== REPLY HANDLER =====
@app.on_message(filters.private & filters.user(MAIN_ID))
async def reply_handler(client, message):

    if message.reply_to_message:

        reply_id = message.reply_to_message.id

        if reply_id in msg_map:
            user = msg_map[reply_id]

            if message.text:
                await safe_send(user, message.text)


# ===== COMMANDS =====

@app.on_message(filters.user(MAIN_ID) & filters.command("help"))
async def help_cmd(client, message):
    await message.reply_text(
"""📌 Commands:
/users
/history
/history <id>
/send <id> message
/forwardon
/forwardoff
"""
    )


@app.on_message(filters.user(MAIN_ID) & filters.command("users"))
async def users_cmd(client, message):
    text = "👥 Users:\n"
    for u in TARGET_USERS:
        text += f"{u}\n"
    await message.reply_text(text)


@app.on_message(filters.user(MAIN_ID) & filters.command("history"))
async def history_cmd(client, message):

    parts = message.text.split()

    if len(parts) == 1:
        for user in TARGET_USERS:
            async for msg in app.get_chat_history(user, limit=5):

                name = msg.from_user.first_name if msg.from_user else "User"
                text = msg.text or "📎 Media"

                await safe_send(MAIN_ID, f"📜 {name}:\n{text}")

    else:
        try:
            user = int(parts[1])
        except:
            return await message.reply_text("Invalid user id")

        async for msg in app.get_chat_history(user, limit=5):

            name = msg.from_user.first_name if msg.from_user else "User"
            text = msg.text or "📎 Media"

            await safe_send(MAIN_ID, f"📜 {name}:\n{text}")


@app.on_message(filters.user(MAIN_ID) & filters.command("send"))
async def send_cmd(client, message):

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        return await message.reply_text("Usage: /send id message")

    try:
        user = int(parts[1])
    except:
        return await message.reply_text("Invalid user id")

    text = parts[2]

    await safe_send(user, text)
    await message.reply_text("✅ Sent")


@app.on_message(filters.user(MAIN_ID) & filters.command("forwardoff"))
async def off_cmd(client, message):
    global forwarding
    forwarding = False
    await message.reply_text("⛔ Forward OFF")


@app.on_message(filters.user(MAIN_ID) & filters.command("forwardon"))
async def on_cmd(client, message):
    global forwarding
    forwarding = True
    await message.reply_text("✅ Forward ON")


# ===== MAIN =====
async def main():
    await app.start()
    print("Userbot running...")

    await forward_unread()

    # keep alive forever
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
