import json
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import os
import logging

API_TOKEN = '7618437919:AAEWHTwTGJeInyM8IrhuWImDajVJc4VfQG0'
ALLOWED_CHAT_ID = -1002417581154
ADMIN_IDS = [7094215368, 87654321]

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_members():
    if os.path.exists("members.json"):
        with open("members.json", "r") as f:
            return json.load(f)
    return {}

def save_members(members):
    with open("members.json", "w") as f:
        json.dump(members, f)

async def is_admin(update: Update):
    user_id = update.message.from_user.id
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ยินดีต้อนรับสู่เกมเป่ายิ้งฉุบ! พิมพ์ /register เพื่อสมัครสมาชิก")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    members = load_members()

    if user_id in members:
        await update.message.reply_text("คุณได้ลงทะเบียนเป็นสมาชิกแล้ว! /help เพื่อดูคำสั่ง")
    else:
        members[user_id] = {"name": update.message.from_user.username, "credit": 10, "last_checkin": 0}
        save_members(members)
        await update.message.reply_text("สมัครสมาชิกสำเร็จ! คุณได้รับเครดิตเริ่มต้น 10 เครดิต\nพิมพ์ /help เพื่อดูคำสั่งทั้งหมด")

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    members = load_members()

    if user_id not in members:
        await update.message.reply_text("คุณยังไม่ได้สมัครสมาชิก พิมพ์ /register เพื่อสมัครก่อน")
        return

    current_time = time.time()
    last_checkin = members[user_id]["last_checkin"]

    if current_time - last_checkin < 86400:
        await update.message.reply_text("คุณสามารถเช็คอินได้อีกครั้งใน 24 ชั่วโมง")
        return

    members[user_id]["credit"] += 10
    members[user_id]["last_checkin"] = current_time
    save_members(members)

    await update.message.reply_text("เช็คอินสำเร็จ! คุณได้รับเครดิต 10 เครดิต")

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id != ALLOWED_CHAT_ID:
        await update.message.reply_text("คำสั่งนี้ใช้ได้ในกลุ่มที่กำหนดเท่านั้น")
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("โปรดระบุจำนวนเครดิตที่ต้องการเดิมพัน เช่น /play 10")
        return

    user_id = str(update.message.from_user.id)
    members = load_members()

    if user_id not in members:
        await update.message.reply_text("คุณยังไม่ได้สมัครสมาชิก พิมพ์ /register เพื่อสมัครก่อน")
        return

    bet_amount = int(context.args[0])

    if bet_amount <= 0:
        await update.message.reply_text("จำนวนเครดิตที่เดิมพันต้องมากกว่า 0")
        return

    if bet_amount > members[user_id]["credit"]:
        await update.message.reply_text("คุณมีเครดิตไม่เพียงพอ กรุณาตรวจสอบเครดิตของคุณ")
        return

    # สร้าง inline keyboard สำหรับเลือก
    keyboard = [
        [InlineKeyboardButton("หิน", callback_data='หิน')],
        [InlineKeyboardButton("กระดาษ", callback_data='กระดาษ')],
        [InlineKeyboardButton("กรรไกร", callback_data='กรรไกร')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("กรุณาเลือก: หิน, กระดาษ, หรือ กรรไกร", reply_markup=reply_markup)
    context.user_data['bet_amount'] = bet_amount

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    members = load_members()
    bet_amount = context.user_data.get('bet_amount', 0)

    user_choice = query.data
    choices = ['หิน', 'กระดาษ', 'กรรไกร']
    bot_choice = random.choice(choices)

    # หักเครดิตจากผู้เล่นทันที
    members[user_id]["credit"] -= bet_amount  
    save_members(members)

    # กำหนดเงื่อนไขผลลัพธ์ของเกม
    if user_choice == bot_choice:
        result = "เสมอ! เครดิตของคุณถูกคืนให้"
        # คืนเครดิตให้ผู้เล่น
        members[user_id]["credit"] += bet_amount  # คืนเครดิต
    elif (user_choice == "หิน" and bot_choice == "กรรไกร") or \
         (user_choice == "กรรไกร" and bot_choice == "กระดาษ") or \
         (user_choice == "กระดาษ" and bot_choice == "หิน"):
        result = "คุณชนะ!"
        members[user_id]["credit"] += bet_amount * 2  # เพิ่มเครดิตเป็นสองเท่า
    else:
        result = "บอทชนะ!"

    save_members(members)

    await query.answer()  # ยืนยันการเลือก
    await query.edit_message_text(
        text=f"คุณเลือก: {user_choice}\nบอทเลือก: {bot_choice}\nผลลัพธ์: {result}\nเครดิตของคุณตอนนี้: {members[user_id]['credit']} เครดิต"
    )

async def create_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    members = load_members()

    if user_id not in members:
        await update.message.reply_text("คุณยังไม่ได้สมัครสมาชิก พิมพ์ /register เพื่อสมัครก่อน")
        return

    if members[user_id]["credit"] < 50:
        await update.message.reply_text("คุณมีเครดิตไม่เพียงพอในการสร้างโค้ด กรุณาเช็คเครดิตของคุณ")
        return

    if len(context.args) != 1:
        await update.message.reply_text("โปรดระบุชื่อโค้ดที่คุณต้องการสร้าง เช่น /create_code ชื่อโค้ด (คำเตือน⚠️⚠️ ให้ทักแชทหาบอทก่อนถ้าไม่ทักแล้วสร้างจะเสียเครดิตฟรี)")
        return

    members[user_id]["credit"] -= 50
    save_members(members)

    code_name = context.args[0]
    code = f"vless://986f749e-f54d-42ae-90e0-2aea328b8c81@true-sv7.oceaninternet.online:8880?type=ws&path=%2F%E0%B8%AB%E0%B9%89%E0%B8%B2%E0%B8%A1%E0%B8%88%E0%B8%B3%E0%B8%AB%E0%B8%99%E0%B9%88%E0%B8%B2%E0%B8%A2&host=www.opensignal.com.oceaninternet.online&security=none#{code_name}"

    await context.bot.send_message(chat_id=user_id, text=f"โค้ดของคุณคือ: {code}\nเครดิตของคุณตอนนี้: {members[user_id]['credit']} เครดิต")
    await update.message.reply_text("โค้ดถูกส่งไปยังข้อความส่วนตัวของคุณแล้ว")

async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("คุณไม่มีสิทธิ์ในการเพิ่มเครดิต")
        return

    if len(context.args) != 2 or not context.args[1].isdigit():
        await update.message.reply_text("โปรดระบุชื่อผู้ใช้และจำนวนเครดิตที่ต้องการเพิ่ม เช่น /add_credit @username 10")
        return

    username = context.args[0].lstrip('@')
    amount = int(context.args[1])
    members = load_members()

    user_id = next((uid for uid, info in members.items() if info['name'] == username), None)

    if user_id is None:
        await update.message.reply_text("ไม่พบผู้ใช้ที่ระบุ")
        return

    members[user_id]["credit"] += amount
    save_members(members)

    await update.message.reply_text(f"เพิ่มเครดิตให้ @{username} จำนวน {amount} เครดิตเรียบร้อยแล้ว")

async def check_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    members = load_members()

    if user_id not in members:
        await update.message.reply_text("คุณยังไม่ได้สมัครสมาชิก พิมพ์ /register เพื่อสมัครก่อน")
        return

    credit = members[user_id]["credit"]
    await update.message.reply_text(f"เครดิตของคุณคือ: {credit} เครดิต")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "คำสั่งที่ใช้ได้:\n"
        "/register - ลงทะเบียนสมาชิก\n"
        "/checkin - เช็คอินเพื่อรับเครดิต\n"
        "/play <จำนวนเครดิต> - เล่นเกมเป่ายิ้งฉุบ\n"
        "/create_code <ชื่อโค้ด> - สร้างโค้ด\n"
        "/add_credit <ชื่อผู้ใช้> <จำนวนเครดิต> - เพิ่มเครดิตให้ผู้ใช้ (สำหรับผู้ดูแล)\n"
        "/check_credit - ตรวจสอบเครดิตของคุณ\n"
        "/help - แสดงคำสั่งที่ใช้ได้"
    )
    await update.message.reply_text(help_text)

def main():
    application = Application.builder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("checkin", checkin))
    application.add_handler(CommandHandler("play", play))
    application.add_handler(CommandHandler("create_code", create_code))
    application.add_handler(CommandHandler("add_credit", add_credit))
    application.add_handler(CommandHandler("check_credit", check_credit))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(choose, pattern='หิน|กระดาษ|กรรไกร'))

    application.run_polling()

if __name__ == '__main__':
    main()
