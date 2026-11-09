import asyncio
import re
from fast_rub import Client, filters
from fast_rub.types import Update

# ==========================================
# ⚙️ تنظیمات
# ==========================================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
# آیدی عددی خودتان (مالک ربات) — برای دسترسی به همه دستورات
OWNER_ID = "YOUR_RUBIKA_USER_ID"

bot = Client("group_manager_session", token=BOT_TOKEN)

# ==========================================
# 🧠 حافظه موقت تنظیمات هر گروه (در حافظه)
# در نسخه پیشرفته‌تر می‌توانید به SQLite منتقل کنید
# ==========================================
group_settings = {}
# ساختار: { chat_id: {"lock_link": False, "lock_forward": False} }

def get_settings(chat_id: str) -> dict:
    if chat_id not in group_settings:
        group_settings[chat_id] = {"lock_link": False, "lock_forward": False}
    return group_settings[chat_id]

# ==========================================
# 🔐 بررسی ادمین بودن
# ==========================================
async def is_admin(msg: Update) -> bool:
    """بررسی اینکه فرستنده در گروه ادمین است یا خیر."""
    # مالک ربات همیشه دسترسی دارد
    if str(msg.sender_id) == OWNER_ID:
        return True

    try:
        # دریافت لیست ادمین‌های گروه از طریق API روبیکا
        admins = await bot.get_chat_administrators(msg.chat_id)
        admin_ids = [str(a.get("user_id", "")) for a in admins]
        return str(msg.sender_id) in admin_ids
    except Exception:
        return False

# ==========================================
# 🛠️ دستورات مدیریتی
# ==========================================

# -------- /help --------
@bot.on_message(filters.text("/help") & filters.group)
async def cmd_help(msg: Update):
    text = (
        "🛠️ **دستورات مدیریت گروه**\n\n"
        "**مدیریت کاربران:**\n"
        "`/kick` (ریپلای) — اخراج کاربر از گروه\n"
        "`/ban` (ریپلای) — مسدود کردن کاربر\n"
        "`/mute` (ریپلای) — سکوت کاربر (بدون زمان = ۱ ساعت)\n"
        "`/unmute` (ریپلای) — رفع سکوت کاربر\n\n"
        "**قفل‌ها:**\n"
        "`/lock link` — قفل کردن ارسال لینک\n"
        "`/unlock link` — باز کردن قفل لینک\n"
        "`/lock forward` — قفل کردن فوروارد\n"
        "`/unlock forward` — باز کردن قفل فوروارد\n"
        "`/locks` — مشاهده وضعیت قفل‌ها"
    )
    await msg.reply(text)

# -------- /kick --------
@bot.on_message(filters.text.startswith("/kick") & filters.group)
async def cmd_kick(msg: Update):
    if not await is_admin(msg):
        await msg.reply("⛔ فقط ادمین‌های گروه می‌توانند از این دستور استفاده کنند.")
        return

    # پیدا کردن کاربر هدف از طریق ریپلای
    reply_to = getattr(msg, "reply_to_message_id", None)
    target_id = None
    if reply_to:
        try:
            replied_msg = await bot.get_message(msg.chat_id, reply_to)
            target_id = str(replied_msg.sender_id)
        except Exception:
            pass

    if not target_id:
        await msg.reply("⚠️ لطفاً روی پیام کاربر مورد نظر **ریپلای** کنید و سپس `/kick` بفرستید.")
        return

    try:
        await bot.ban_chat_member(msg.chat_id, target_id)
        await msg.reply(f"👢 کاربر `{target_id}` از گروه اخراج شد.")
    except Exception as e:
        await msg.reply(f"❌ خطا در اخراج: `{e}`")

# -------- /ban --------
@bot.on_message(filters.text.startswith("/ban") & filters.group)
async def cmd_ban(msg: Update):
    if not await is_admin(msg):
        await msg.reply("⛔ فقط ادمین‌های گروه می‌توانند از این دستور استفاده کنند.")
        return

    reply_to = getattr(msg, "reply_to_message_id", None)
    target_id = None
    if reply_to:
        try:
            replied_msg = await bot.get_message(msg.chat_id, reply_to)
            target_id = str(replied_msg.sender_id)
        except Exception:
            pass

    if not target_id:
        await msg.reply("⚠️ لطفاً روی پیام کاربر مورد نظر **ریپلای** کنید و سپس `/ban` بفرستید.")
        return

    try:
        await bot.ban_chat_member(msg.chat_id, target_id)
        await msg.reply(f"🚫 کاربر `{target_id}` مسدود شد.")
    except Exception as e:
        await msg.reply(f"❌ خطا در مسدودسازی: `{e}`")

# -------- /mute --------
@bot.on_message(filters.text.startswith("/mute") & filters.group)
async def cmd_mute(msg: Update):
    if not await is_admin(msg):
        await msg.reply("⛔ فقط ادمین‌های گروه می‌توانند از این دستور استفاده کنند.")
        return

    reply_to = getattr(msg, "reply_to_message_id", None)
    target_id = None
    if reply_to:
        try:
            replied_msg = await bot.get_message(msg.chat_id, reply_to)
            target_id = str(replied_msg.sender_id)
        except Exception:
            pass

    if not target_id:
        await msg.reply("⚠️ لطفاً روی پیام کاربر مورد نظر **ریپلای** کنید و سپس `/mute` بفرستید.")
        return

    try:
        # در FastRub متد mute_chat برای سکوت چت وجود دارد
        await bot.mute_chat(msg.chat_id, target_id)
        await msg.reply(f"🔇 کاربر `{target_id}` سکوت شد.")
    except Exception as e:
        await msg.reply(f"❌ خطا در سکوت: `{e}`")

# -------- /unmute --------
@bot.on_message(filters.text.startswith("/unmute") & filters.group)
async def cmd_unmute(msg: Update):
    if not await is_admin(msg):
        await msg.reply("⛔ فقط ادمین‌های گروه می‌توانند از این دستور استفاده کنند.")
        return

    reply_to = getattr(msg, "reply_to_message_id", None)
    target_id = None
    if reply_to:
        try:
            replied_msg = await bot.get_message(msg.chat_id, reply_to)
            target_id = str(replied_msg.sender_id)
        except Exception:
            pass

    if not target_id:
        await msg.reply("⚠️ لطفاً روی پیام کاربر مورد نظر **ریپلای** کنید و سپس `/unmute` بفرستید.")
        return

    try:
        await bot.unmute_chat(msg.chat_id, target_id)
        await msg.reply(f"🔊 کاربر `{target_id}` از سکوت خارج شد.")
    except Exception as e:
        await msg.reply(f"❌ خطا در رفع سکوت: `{e}`")

# ==========================================
# 🔒 قفل لینک و فوروارد
# ==========================================
URL_REGEX = re.compile(
    r'^(https?://)?'
    r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'
    r'(:\d+)?(/[^\s]*)?$'
)

@bot.on_message(filters.text & filters.group)
async def enforce_locks(msg: Update):
    """هر پیام متنی گروه را بررسی می‌کند و در صورت فعال بودن قفل، پیام را حذف می‌کند."""
    # ادمین‌ها از قفل‌ها معاف هستند
    if await is_admin(msg):
        return

    settings = get_settings(msg.chat_id)
    text = msg.text.strip()

    # --- قفل لینک ---
    if settings["lock_link"]:
        if URL_REGEX.match(text):
            try:
                await bot.delete_message(msg.chat_id, msg.message_id)
                await msg.reply("🔗 ارسال لینک در این گروه ممنوع است.")
            except Exception:
                pass
            return

    # --- قفل فوروارد ---
    if settings["lock_forward"]:
        # تشخیص فوروارد: وجود فیلد forward از مبدا
        is_forward = getattr(msg, "forwarded_from", None) or getattr(msg, "forward_from", None)
        if is_forward:
            try:
                await bot.delete_message(msg.chat_id, msg.message_id)
                await msg.reply("🔁 ارسال فوروارد در این گروه ممنوع است.")
            except Exception:
                pass
            return

# -------- دستورات مدیریت قفل‌ها --------
@bot.on_message(filters.text.startswith("/lock") & filters.group)
async def cmd_lock(msg: Update):
    if not await is_admin(msg):
        await msg.reply("⛔ فقط ادمین‌ها می‌توانند قفل‌ها را تغییر دهند.")
        return

    parts = msg.text.split()
    if len(parts) < 2:
        await msg.reply("⚠️ استفاده: `/lock link` یا `/lock forward`")
        return

    target = parts[1].lower()
    settings = get_settings(msg.chat_id)

    if target == "link":
        settings["lock_link"] = True
        await msg.reply("🔒 قفل لینک فعال شد.")
    elif target == "forward":
        settings["lock_forward"] = True
        await msg.reply("🔒 قفل فوروارد فعال شد.")
    else:
        await msg.reply("⚠️ گزینه نامعتبر. فقط `link` یا `forward`.")

@bot.on_message(filters.text.startswith("/unlock") & filters.group)
async def cmd_unlock(msg: Update):
    if not await is_admin(msg):
        await msg.reply("⛔ فقط ادمین‌ها می‌توانند قفل‌ها را تغییر دهند.")
        return

    parts = msg.text.split()
    if len(parts) < 2:
        await msg.reply("⚠️ استفاده: `/unlock link` یا `/unlock forward`")
        return

    target = parts[1].lower()
    settings = get_settings(msg.chat_id)

    if target == "link":
        settings["lock_link"] = False
        await msg.reply("🔓 قفل لینک غیرفعال شد.")
    elif target == "forward":
        settings["lock_forward"] = False
        await msg.reply("🔓 قفل فوروارد غیرفعال شد.")
    else:
        await msg.reply("⚠️ گزینه نامعتبر. فقط `link` یا `forward`.")

@bot.on_message(filters.text("/locks") & filters.group)
async def cmd_locks_status(msg: Update):
    if not await is_admin(msg):
        await msg.reply("⛔ فقط ادمین‌ها می‌توانند وضعیت قفل‌ها را ببینند.")
        return

    s = get_settings(msg.chat_id)
    link_status = "🔒 فعال" if s["lock_link"] else "🔓 غیرفعال"
    fwd_status = "🔒 فعال" if s["lock_forward"] else "🔓 غیرفعال"
    await msg.reply(
        f"📋 **وضعیت قفل‌های گروه**\n"
        f"🔗 قفل لینک: {link_status}\n"
        f"🔁 قفل فوروارد: {fwd_status}"
    )

# ==========================================
# 🚀 اجرا
# ==========================================
async def main():
    print("✅ ربات مدیریت گروه آماده است...")
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
