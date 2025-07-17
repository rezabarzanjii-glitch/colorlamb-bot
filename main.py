import telebot
import re
import os
import time

# --- تنظیمات اصلی ربات ---
BOT_TOKEN = os.environ.get("BOT_TOKEN") # توکن از متغیرهای محیطی خوانده می‌شود
ALLOWED_USERNAMES = ['maeisoleimani', 'miladbarzanji', 'colorlamb'] 
REZA_ID = 1160573576
COUNTER_FILE = "/var/data/order_counter.txt" # مسیر مناسب برای ذخیره‌سازی در Render

# اطمینان از وجود پوشه داده
os.makedirs(os.path.dirname(COUNTER_FILE), exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN)

def get_next_order_number():
    last_num = 1000
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    last_num = int(content)
        except (IOError, ValueError):
            last_num = 1000
    next_num = last_num + 1
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(next_num))
    return f'#CLR-{next_num}'

def parse_order_details(text):
    data = {"customer_name": "ثبت نشده", "mobile": "ثبت نشده", "product": "ثبت نشده", "color": "ثبت نشده", "address": "ثبت نشده", "method": "ثبت نشده"}
    lines = text.strip().split('\n')
    unmatched_lines = []
    for line in lines:
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key == 'نام' or 'نام مشتری' in key: data['customer_name'] = value
            elif 'موبایل' in key or 'مبایل' in key: data['mobile'] = value
            elif 'محصول' in key: data['product'] = value
            elif key == 'رنگ' or 'رنگ انتخابی' in key: data['color'] = value
            elif 'آدرس' in key or 'ادرس' in key: data['address'] = value
            elif 'روش' in key: data['method'] = value
            else: unmatched_lines.append(line)
            continue
        mobile_match = re.search(r'((0|۰)9\d{9})', line.replace(" ", ""))
        if mobile_match:
            data['mobile'] = mobile_match.group(1)
            continue
        if any(keyword in line for keyword in ['واتساپ', 'تلگرام', 'اینستا', 'سایت']):
            data['method'] = line
            continue
        unmatched_lines.append(line)
    if unmatched_lines:
        if data['customer_name'] == 'ثبت نشده':
            data['customer_name'] = unmatched_lines.pop(0)
        if unmatched_lines and data['address'] == 'ثبت نشده':
            data['address'] = "، ".join(unmatched_lines)
    if data['customer_name'] == 'ثبت نشده' and data['mobile'] == 'ثبت نشده':
        return None
    return data

@bot.message_handler(func=lambda message: message.from_user.username in ALLOWED_USERNAMES and message.chat.type in ['group', 'supergroup'])
def handle_order(message):
    order_data = parse_order_details(message.text)
    if not order_data: return
    order_number = get_next_order_number()
    final_message = f"""
✅ سفارش جدید ثبت شد

🔢 شماره سفارش: {order_number}
👤 نام مشتری: {order_data['customer_name']}
📱 موبایل: {order_data['mobile']}
📦 محصول: {order_data['product']}
🎨 رنگ انتخابی: {order_data['color']}
📍 آدرس: {order_data['address']}
📡 روش ثبت سفارش: {order_data['method']}
🛒 ثبت‌شده توسط: @{message.from_user.username}
"""
    try:
        bot.reply_to(message, final_message)
        bot.send_message(REZA_ID, final_message)
    except Exception as e:
        print(f"An error occurred: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! ربات ثبت سفارش فعال است.")

while True:
    try:
        print("Bot is running...")
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Bot crashed with error: {e}. Restarting in 5 seconds...")
        time.sleep(5)
