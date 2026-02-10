import telebot
from threading import Lock
import json, os, random
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

# ------------------ تنظیمات اولیه ------------------
bot = telebot.TeleBot('7998730211:AAFIyWka_cwKfVW_w0xtqrZmrKk3NicxQCk', parse_mode='html')

# نام فایل‌های ذخیره‌سازی
DATA_FILE = "players_data.json"
ADMINS_FILE = "bot_admins.json" 

# متغیرهای سراسری اصلی و ساختارهای داده جدید
players_dict = {}
main_message_dict = {}
nazor_dict = {}

# ساختارهای داده پیشرفته (ذخیره‌سازی می‌شود)
LIST_LOCKED_DICT = {}       # {chat_id: True/False}
BANNED_NAMES = []           # [name1, name2] (Global)
WARNINGS_DICT = {}          # {user_id: count} (Global)
GROUP_TAG_LISTS = {}        # {chat_id: [username1, username2]}
LIST_STYLE_IDS = {}         # {chat_id: 0, 1, or 2}

# متغیرهای سراسری تنظیمات
START_TIME = "23:00"
LIST_CAPACITY = 16
CURRENT_ROLES = [] 
SCHEDULER = None 
SCHEDULER_ENABLED = True
TAGGING_ENABLED = True
REMINDER_TIME = "20:30" 
BOT_ADMINS = [] 
lock = Lock()

# نقش‌ها و نام‌های ممنوعه پیش‌فرض
DEFAULT_ROLES = ["شهروندساده", "شهروند ساده", "رییس مافیا", "شیاد", "ناتو", "رویین تن", "کاراگاه", "دکتر", "محقق", "بازپرس"]
HARDCODED_BANNED_NAMES = ["مستانه", "مثتانه", "مصتانه"] 

# لیست استایل‌های لیست (برای انتخاب توسط ادمین)
LIST_STYLES_OPTIONS = [
    {"icon": "🎭", "separator": "═" * 16, "bullet": "🔸", "name": "کلاسیک"},
    {"icon": "🌙", "separator": "•" * 20, "bullet": "✨", "name": "مهتاب"},
    {"icon": "♟️", "separator": "⎽" * 25, "bullet": "🔲", "name": "شطرنجی"},
]

# ... (funny_add_messages, funny_remove_messages و animal_emojis بدون تغییر)
funny_add_messages = [
    "😂 هیجان‌انگیز شد! یک بازیکن شجاع یا یک قربانی جدید؟", "😎 اومد بالاخره! فکر کردیم ترسیدی و نیای.", 
    "🤣 بفرما، اینم امضای تو زیر حکم مافیا! دیگه نمیشه حذف کرد.", "📝 ثبت نامت اوکی شد. امیدوارم این بار آبرومونو نبری!", 
    "💪 شجاعت به خرج دادی اومدی. آفرین بر این حماقت!", "🤦‍♂️ ببین کی اینجاست! حالا بازی یه کمکی مزخرف‌تر میشه.", 
    "🛡️ اضافه شدی! دیگه حق نداری بگی کسی تگت نکرده.", "🔫 به سلامتی! حالا بگو کی مافیاست، وقت نداریم.", 
    "🚪 حیف جا نبود، وگرنه نمی‌ذاشتیم بیای! ولی بفرمایید.", "💡 فکر نکن خیلی مهمی، فقط چون جا بود اسمتو نوشتیم.", 
    "🔥 تو هم اومدی؟ چقدر فاز بازی سنگین شد یهو!", "💯 هشتاد و نهمین شانس برای تو! خوش اومدی.", 
    "🧐 بیا ببینم این بار چه گندی می‌زنی؟", "🏃 بدو بیا تو که دیر اومدن عادتت نشه!", 
    "🗝️ بفرمایید، دیگه جای برگشت نیست! باید بازی کنی.", "🎉 لیست داره پر میشه. خوشحالیم که نفرات اضافی هم هستن!", 
    "🚫 دیگه بهونه نیار، اسمتو نوشتم.", "👑 آره، تو هم شدی بازیکن! مبارکه.", 
    "🐺 فکر کردی با نیومدنت مافیا می‌ترسه؟ برو ثبت نام کن!", "🐑 یه شهروند ساده‌ی دیگه به لیست اضافه شد. حیف!", 
    "📝 اسمت رو با اکراه ثبت کردیم. برو بازی کن.", "📣 اوه! نفر بعدی که قراره سوتی بده اومد.", 
    "🕵️‍♂️ خودتو معرفی کن، مافیا شناسایی کنه!", "⏱️ چه عجب! فکر کردم رفتی تو کار تماشاچی بودن.", 
    "🚧 بیا تو لیست، تا بریم مرحله بعدی سوتی دادن.", "🗳️ اسم تو، مساوی با یک رای اشتباه. ثبت شد!", 
    "🎯 تو رو برای شلیک اشتباه می‌خوایم! خوش اومدی.", "🔢 باشه، تو هم بیا. حداقل می‌تونیم رولات رو بشماریم.", 
    "🥵 اسم تو = بازی سخت‌تر برای همه. مرسی!", "❌ این همون نفره که همیشه اشتباه می‌کشه؟ آره؟", 
    "💤 لیست بدون تو یه جورایی بی‌مزه‌تر بود. کاش دیرتر میومدی.", "🔑 فقط اگر قول بدی این بار حرف گوش کنی، ثبت نامت می‌کنم!", 
    "🎁 از طرف مافیا، بهت خوش‌آمد میگم شهروند ساده!", "⚰️ یه قربانی جدید به لیست اضافه شد. قربونش برم.", 
    "⛔ تو هم میای؟ اوکی. فقط زیاد شلوغش نکن!", "🎭 دکتر یا کارآگاه، فقط زیاد خرابکاری نکن!", 
    "💡 بفرما، اینجا همونجاست که همیشه می‌سوزی!", "✍️ اسمت رو نوشتم، ولی مسئولیت بازی‌ات با خودته!", 
    "❓ چرا انقدر اصرار داشتی بیای تو لیست؟ باشه بیا.", "🦢 بیا تو که بازی امشب خیلی به تو نیاز داره! (دروغ گفتم)."
]
funny_remove_messages = [
    "😂 خداحافظ! ظرفیت اشغال کن کمتر!", "😅 آسون‌ترین حذف تاریخ! کاش اسمتو نمی‌نوشتی.", 
    "🤣 رفتی که چی؟ یه ترسو کمتر! لیست تمیز شد.", "🚪 در رو ببند! مافیا بدون تو هم بازی می‌کنه.", 
    "📉 کیفیت بازی با رفتنت افت نکرد. برو راحت باش.", "🤦‍♂️ ای بابا! کم آوردی؟ برو دنبال سرنوشتت.", 
    "👻 برو به سلامت. اصلا انگار نه انگار که بودی!", "🗑️ حیف اون اسم که اینجا نوشته شد! حذف شد.", 
    "⚠️ خودت خواستی. ما به زور کسی رو نگه نمی‌داریم.", "😴 فکر کنم خوابت اومد. برو استراحت کن قهرمان!", 
    "❌ حذف شد! لیست جای آدمای قویه.", "🪓 ما خودمون حذف کردیم، منتظر نموندیم!", 
    "🚶 تو که بازی بلد نبودی، چرا اصلاً اومدی؟", "🤮 زود انصراف دادی که! شل و ول!", 
    "🤬 به درک که رفتی! جدی نمی‌شی.", "💡 بالاخره یه حرکت درست زدی و انصراف دادی.", 
    "🚷 فضای لیست رو برای حرفه‌ای‌ها باز کردی. مرسی.", "👀 تا چشم کار می‌کنه یه ترسو دیگه رفت!", 
    "⏳ بازی با آدمای سست، حیف وقته!", "😤 حالا راحت‌تر میشه نفس کشید. برو خونه!", 
    "💥 اسمت رو شوت کردیم بیرون! دفعه بعد برگرد.", "🤡 تو رو برای شات شب هم نگه نداشتن، برو!", 
    "💀 بای بای. امیدوارم تو بازی بعدی باز خراب نکنی.", "🧐 فکر کردی خیلی مهمی؟ حذف شدی! برو پی کارت.", 
    "🦢 لنگه جوراب نداشتی تو خونه؟ برو بپوش!", "🐒 از همون اول هم نباید ثبت‌نام می‌کردی.", 
    "🐍 یه بازیکن دیگه در رفت! فرار مغزها...", "✂️ اسم رو با قیچی زدیم. دیگه برنگردی!", 
    "🦠 لیست داره ضدعفونی میشه. تو هم یکی از اونایی!", "⛔ این لیست جای آدمای بی‌برنامه نیست. بفرمایید بیرون.", 
    "👋 فعلاً خوش باشی. شاید یه قرن دیگه اومدی."
]
members_ids_list = [
    "Tbsom_s8119", "Motanashi", "Nazi_Tala_80", "SajjadR2025", "navidhmi", "Matador7i", "MR_Rrahimi", "P_arsq", 
    "davoodsaberii", "arka12105", "Elinaz78", "Tthe_void", "HosseinM_O", "Ffaaaatteeeemmeeee_h", 
    "tanhavash_007", "Flower_505", "Zaki99841", "Zahra75a", "tf56vrji", "Moonlight_M8", 
    "Miracle_1_1", "amirhtpr", "Ninish8888", "am_nazm", "Shayad_az_aval_eshtebah_bod", 
    "Ravashzahra", "Alirezaghanaiy", "shuhrukh_ind", "arashaaz", "Constantine_911", 
    "Feri00800", "Mammaddasht", "Farjadparsa222", "Frzam1234", "iDalef", 
    "Xm_sadegh_hp77X", "mohammadkhz1380", "Azad_0017", "AMIRABBAS6857"
]

animal_emojis = ["🐒","🐶","🐺","🦊","🐱","🦁","🐯","🐴","🦄","🐮","🐷","🐗","🐭","🐹","🐰","🐻","🐼","🐨","🐔","🐧","🐦","🦉","🐸","🐊","🐢","🐍","🐳","🐬","🐠","🦈","🦋","🐛"]


# ------------------ توابع مدیریت داده‌ها و تنظیمات ------------------
def load_data():
    global players_dict, nazor_dict, START_TIME, LIST_CAPACITY, CURRENT_ROLES, SCHEDULER_ENABLED, TAGGING_ENABLED
    global LIST_LOCKED_DICT, BANNED_NAMES, WARNINGS_DICT, GROUP_TAG_LISTS, LIST_STYLE_IDS

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                players_dict = data.get("players", {})
                nazor_dict = data.get("nazor", {})
                
                # بارگذاری تنظیمات اصلی
                settings = data.get("settings", {})
                START_TIME = settings.get("start_time", "23:00")
                LIST_CAPACITY = settings.get("list_capacity", 16)
                CURRENT_ROLES = settings.get("roles", DEFAULT_ROLES)
                SCHEDULER_ENABLED = settings.get("scheduler_enabled", True)
                TAGGING_ENABLED = settings.get("tagging_enabled", True)

                # بارگذاری تنظیمات پیشرفته
                LIST_LOCKED_DICT = data.get("list_locked", {})
                BANNED_NAMES = data.get("banned_names", [])
                WARNINGS_DICT = data.get("warnings", {})
                GROUP_TAG_LISTS = data.get("group_tag_lists", {})
                LIST_STYLE_IDS = data.get("list_style_ids", {})

            except json.JSONDecodeError:
                print("Error loading data. Using default settings.")
                CURRENT_ROLES = DEFAULT_ROLES
    else:
        CURRENT_ROLES = DEFAULT_ROLES
        BANNED_NAMES = HARDCODED_BANNED_NAMES.copy() # برای اولین اجرا

def save_data():
    settings = {
        "start_time": START_TIME,
        "list_capacity": LIST_CAPACITY,
        "roles": CURRENT_ROLES,
        "scheduler_enabled": SCHEDULER_ENABLED,
        "tagging_enabled": TAGGING_ENABLED,
    }
    data_to_save = {
        "players": players_dict,
        "nazor": nazor_dict,
        "settings": settings,
        "list_locked": LIST_LOCKED_DICT,
        "banned_names": BANNED_NAMES,
        "warnings": WARNINGS_DICT,
        "group_tag_lists": GROUP_TAG_LISTS,
        "list_style_ids": LIST_STYLE_IDS
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)

# <اضافه شده برای قابلیت ریست>
def reset_list(chat_id):
    chat_id_str = str(chat_id)
    with lock:
        # ریست لیست بازیکنان
        if chat_id_str in players_dict:
            players_dict[chat_id_str].clear()
        # ریست ناظرین
        if chat_id_str in nazor_dict:
            nazor_dict[chat_id_str] = ["___", "___"]
        save_data()
# </اضافه شده برای قابلیت ریست>
        
def load_admins():
    global BOT_ADMINS
    # ... (تابع load_admins بدون تغییر)
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r") as f:
            try:
                BOT_ADMINS = json.load(f)
                if not isinstance(BOT_ADMINS, list): BOT_ADMINS = []
            except json.JSONDecodeError: BOT_ADMINS = []
    
def save_admins():
    # ... (تابع save_admins بدون تغییر)
    with open(ADMINS_FILE, "w") as f:
        json.dump(BOT_ADMINS, f)

def is_bot_admin(user_id):
    # ... (تابع is_bot_admin بدون تغییر)
    return user_id in BOT_ADMINS

def is_group_admin(chat_id, user_id):
    # ... (تابع is_group_admin بدون تغییر)
    try:
        admins = bot.get_chat_administrators(chat_id)
        return user_id in [admin.user.id for admin in admins]
    except Exception as e:
        print(f"Error checking group admin: {e}")
        return False

# ------------------ زمان‌بندی (Scheduler) ------------------
# ... (توابع setup_scheduler و send_reminder بدون تغییر)
def setup_scheduler():
    global SCHEDULER
    if SCHEDULER is not None:
        try: SCHEDULER.shutdown(wait=False)
        except: pass
            
    if not SCHEDULER_ENABLED:
        print("Scheduler is disabled by admin setting.")
        return

    try:
        tz = pytz.timezone("Asia/Tehran")
        SCHEDULER = BackgroundScheduler(timezone=tz)
        
        start_hour, start_minute = map(int, START_TIME.split(':'))
        reminder_hour, reminder_minute = map(int, REMINDER_TIME.split(':'))
        
        SCHEDULER.add_job(lambda: [reset_list(cid) for cid in players_dict.keys()], 
                         'cron', hour=start_hour, minute=start_minute, id='daily_reset')
        
        SCHEDULER.add_job(send_reminder, 
                         'cron', hour=reminder_hour, minute=reminder_minute, id='daily_reminder')
        
        SCHEDULER.start()
        print(f"Scheduler started. Reset time: {START_TIME}, Reminder time: {REMINDER_TIME}")
    except Exception as e:
        print(f"Error setting up scheduler: {e}")

def send_reminder():
    for cid in players_dict.keys():
        try: 
            bot.send_message(cid, f"⏰ بازی امشب ساعت {START_TIME} شروع می‌شود!")
        except Exception as e: 
            print(f"Error sending reminder to chat {cid}: {e}")
            pass

# ------------------ تولید لیست و نقش‌ها (با استایل پویا) ------------------
# ... (توابع generate_list و generate_role_prediction و add_names و remove_name بدون تغییر)
def get_style(chat_id):
    style_id = LIST_STYLE_IDS.get(str(chat_id))
    if style_id is not None and 0 <= style_id < len(LIST_STYLES_OPTIONS):
        return LIST_STYLES_OPTIONS[style_id]
    else:
        return random.choice(LIST_STYLES_OPTIONS)

def generate_list(chat_id):
    players = players_dict.get(str(chat_id), [])
    nazor = nazor_dict.get(str(chat_id), ["___", "___"])
    
    style = get_style(chat_id) # استفاده از استایل ذخیره‌شده یا تصادفی
    is_locked = LIST_LOCKED_DICT.get(str(chat_id), False)
    
    header = f"{style['icon']} <b><i>THE MAFIA NIGHT LIST</i></b> {style['icon']}\n"
    header += f"🗓️ شروع بازی: <b>امشب ساعت {START_TIME}</b>\n" 
    header += f"{style['separator']}\n"
    
    nazor_section = "👥 <b>نــاظــریــن:</b>\n"
    nazor_section += f"👁‍🗨 ناظر ۱: <i>{nazor[0]}</i>\n"
    nazor_section += f"👁‍🗨 ناظر ۲: <i>{nazor[1]}</i>\n"
    nazor_section += f"{style['separator']}\n"
    
    players_header = f"📜 <b>لیست فعال (ظرفیت: {len(players)}/{LIST_CAPACITY})</b>\n"
    body = ""
    
    number_emojis = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩", "⑪", "⑫", "⑬", "⑭", "⑮", "⑯", "⑰", "⑱", "⑲", "⑳"]
    
    for i in range(1, LIST_CAPACITY + 1):
        name_placeholder = "<i>[خالی]</i>" 
        name = players[i-1] if i-1 < len(players) else name_placeholder
        
        if name != name_placeholder:
            name = f"<b>{name}</b>"
            
        emoji_index = (i - 1) % len(number_emojis) 
        body += f"{number_emojis[emoji_index]} {name}\n"
        
    footer = f"{style['separator']}\n"
    if is_locked:
        footer += "❌ <b>لیست بسته است. ثبت‌نام یا حذف امکان‌پذیر نیست.</b> 🔒"
    elif len(players) < LIST_CAPACITY:
         footer += "⏳ <b>آماده‌ای؟</b> اسمتو با ریپلای روی همین پیام اضافه کن! 📝"
    else:
         footer += "🎉 <b>ظرفیت تکمیل شد!</b> بازی آماده‌ی آغاز است. 💣"

    return header + nazor_section + players_header + body + footer

def generate_role_prediction(chat_id):
    # ... (تابع generate_role_prediction بدون تغییر)
    players = players_dict.get(str(chat_id), [])
    if not players:
        return "⚠️ لیست خالی است، پیش‌بینی ممکن نیست."
    
    role_list = CURRENT_ROLES.copy() 
    roles_available = role_list.copy()
    random.shuffle(roles_available)
    prediction = ""
    for idx, player_with_emoji in enumerate(players):
        player = player_with_emoji
        for emoji in animal_emojis:
            player = player.replace(f" {emoji}", "")
            
        if not roles_available:
            roles_available = role_list.copy()
            random.shuffle(roles_available)
        
        role = roles_available.pop(0) if roles_available else "نقش نامشخص"
        
        prefix = "▪️" if idx%2==0 else "▫️"
        prediction += f"{prefix} {idx+1}- {player} - نقش: {role}\n"
    return "<b>پیش‌بینی نقش‌ها:</b>\n" + prediction

# ------------------ توابع اصلی لیست (با قفل و ممنوعیت) ------------------
def add_names(text, chat_id):
    chat_id_str = str(chat_id)
    if LIST_LOCKED_DICT.get(chat_id_str, False): return [] # لیست قفل است

    name = text.strip() 
    added = []
    
    if not name: return added 

    # بررسی لیست سیاه (شامل اسامی هاردکد شده)
    banned_list = [n.lower() for n in BANNED_NAMES + HARDCODED_BANNED_NAMES]
    if name.lower() in banned_list:
        return []

    with lock:
        is_present = any(name in p for p in players_dict.get(chat_id_str, []))
        
        if not is_present and len(players_dict.get(chat_id_str,[])) < LIST_CAPACITY: 
            emoji = random.choice(animal_emojis)
            name_with_emoji = f"{name} {emoji}" 
            players_dict[chat_id_str].append(name_with_emoji)
            added.append(name) 
        save_data()
    return added

def remove_name(name, chat_id):
    chat_id_str = str(chat_id)
    if LIST_LOCKED_DICT.get(chat_id_str, False): return False # لیست قفل است

    with lock:
        current_players = players_dict.get(chat_id_str, [])
        for player_with_emoji in current_players:
            original_name = player_with_emoji
            for emoji in animal_emojis:
                if original_name.endswith(f" {emoji}"):
                    original_name = original_name.replace(f" {emoji}", "")
                    break
            
            if original_name == name:
                players_dict[chat_id_str].remove(player_with_emoji)
                save_data()
                return True
    return False

# ------------------ پنل مدیریتی: UI و توابع CallBack ------------------
# ... (تمام توابع مربوط به پنل مدیریتی بدون تغییر)
def get_admin_panel_markup(chat_id):
    chat_id_str = str(chat_id)
    current_time = START_TIME
    current_capacity = LIST_CAPACITY
    scheduler_status = "✅ فعال" if SCHEDULER_ENABLED else "❌ غیرفعال"
    tagging_status = "✅ فعال" if TAGGING_ENABLED else "❌ غیرفعال"
    list_locked_status = "🔒 قفل" if LIST_LOCKED_DICT.get(chat_id_str, False) else "🔓 باز"
    
    style_id = LIST_STYLE_IDS.get(chat_id_str)
    current_style = LIST_STYLES_OPTIONS[style_id]['name'] if style_id is not None else "تصادفی"
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    # --- تنظیمات عمومی ---
    markup.add(
        telebot.types.InlineKeyboardButton(f"⏰ ساعت شروع: {current_time}", callback_data="admin_set_time"),
        telebot.types.InlineKeyboardButton(f"🔢 ظرفیت: {current_capacity}", callback_data="admin_set_capacity")
    )
    markup.add(
        telebot.types.InlineKeyboardButton(f"🖼️ استایل: {current_style}", callback_data="admin_set_style"),
        telebot.types.InlineKeyboardButton("🔠 مدیریت نقش‌ها", callback_data="admin_set_roles")
    )
    
    # --- ابزارهای گروه ---
    markup.add(
        telebot.types.InlineKeyboardButton(f"🔒 لیست: {list_locked_status}", callback_data="admin_toggle_lock"),
        telebot.types.InlineKeyboardButton("✏️ ویرایش نام بازیکن", callback_data="admin_edit_player_name")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("❌ حذف با شماره ردیف", callback_data="admin_remove_by_row"),
        telebot.types.InlineKeyboardButton("🔀 جابجایی بازیکنان", callback_data="admin_swap_players")
    )

    # --- ابزارهای ادمین/نظارتی ---
    markup.add(
        telebot.types.InlineKeyboardButton("🚫 مدیریت لیست سیاه", callback_data="admin_manage_banned"),
        telebot.types.InlineKeyboardButton("⚠️ اخطارات بازیکنان", callback_data="admin_view_warnings")
    )

    # --- ابزارهای سیستمی ---
    markup.add(
        telebot.types.InlineKeyboardButton(f"🔄 زمانبندی: {scheduler_status}", callback_data="admin_toggle_scheduler"),
        telebot.types.InlineKeyboardButton("🔔 ارسال فوری یادآوری", callback_data="admin_send_reminder")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("💾 پشتیبان‌گیری لیست", callback_data="admin_backup_list"),
        telebot.types.InlineKeyboardButton(f"📢 تگ کردن: {tagging_status}", callback_data="admin_toggle_tagging")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("🏷️ مدیریت تگ‌های گروه", callback_data="admin_manage_tags"),
        telebot.types.InlineKeyboardButton("📊 آمار کلی", callback_data="admin_stats")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("⚙️ مدیریت ادمین‌های ربات", callback_data="admin_manage_bot_admins")
    )
    
    return markup

def show_admin_panel(chat_id, message_id=None):
    if message_id:
        try:
            bot.edit_message_text("⚙️ پنل مدیریتی ربات مافیا:", chat_id, message_id, reply_markup=get_admin_panel_markup(chat_id))
        except:
             bot.send_message(chat_id, "⚙️ پنل مدیریتی ربات مافیا:", reply_markup=get_admin_panel_markup(chat_id))
    else:
        bot.send_message(chat_id, "⚙️ پنل مدیریتی ربات مافیا:", reply_markup=get_admin_panel_markup(chat_id))

# ------------------ توابع ثبت ورودی پنل (Next Step Handlers) ------------------

# --- Set Time (بدون تغییر) ---
def prompt_set_time(chat_id):
    msg = bot.send_message(chat_id, "لطفا ساعت شروع جدید را با فرمت <b>HH:MM</b> (مثلا 23:00) ارسال کنید:", parse_mode='html')
    bot.register_next_step_handler(msg, process_set_time)

def process_set_time(message):
    global START_TIME
    chat_id = message.chat.id
    new_time = message.text.strip()
    try:
        datetime.strptime(new_time, '%H:%M')
        START_TIME = new_time
        save_data()
        setup_scheduler()
        bot.send_message(chat_id, f"✅ ساعت شروع بازی با موفقیت به <b>{START_TIME}</b> تغییر یافت و زمانبندی به‌روز شد.", parse_mode='html')
    except ValueError:
        bot.send_message(chat_id, "⚠️ فرمت ساعت اشتباه است. باید به صورت HH:MM باشد.")
    show_admin_panel(chat_id)

# --- Set Capacity (بدون تغییر) ---
def prompt_set_capacity(chat_id):
    msg = bot.send_message(chat_id, "لطفا ظرفیت جدید لیست را (یک عدد بین 1 تا 20) ارسال کنید:")
    bot.register_next_step_handler(msg, process_set_capacity)

def process_set_capacity(message):
    global LIST_CAPACITY
    chat_id = message.chat.id
    try:
        new_capacity = int(message.text.strip())
        if 1 <= new_capacity <= 20:
            LIST_CAPACITY = new_capacity
            save_data()
            bot.send_message(chat_id, f"✅ ظرفیت لیست با موفقیت به <b>{LIST_CAPACITY}</b> تغییر یافت.", parse_mode='html')
            if str(chat_id) in main_message_dict:
                bot.edit_message_text(generate_list(chat_id), chat_id, main_message_dict[str(chat_id)])
        else:
            bot.send_message(chat_id, "⚠️ ظرفیت باید یک عدد بین 1 تا 20 باشد.")
    except ValueError:
        bot.send_message(chat_id, "⚠️ ورودی نامعتبر است. لطفا فقط عدد ارسال کنید.")
    show_admin_panel(chat_id)

# --- Set Roles (بدون تغییر) ---
def prompt_set_roles(chat_id):
    current_roles_text = "، ".join(CURRENT_ROLES)
    msg = bot.send_message(chat_id, 
                           f"<b>🔠 مدیریت نقش‌ها:</b>\nنقش‌های فعلی: {current_roles_text}\n\n"
                           "لطفا لیست جدید نقش‌ها را با کاما جدا کنید و ارسال نمایید (مثلاً: مافیا, دکتر, شهروند, کارآگاه):", 
                           parse_mode='html')
    bot.register_next_step_handler(msg, process_set_roles)

def process_set_roles(message):
    global CURRENT_ROLES
    chat_id = message.chat.id
    new_roles_str = message.text.strip()
    if new_roles_str:
        new_roles = [r.strip() for r in new_roles_str.split(',') if r.strip()]
        if new_roles:
            CURRENT_ROLES = new_roles
            save_data()
            bot.send_message(chat_id, f"✅ لیست نقش‌ها با موفقیت به‌روز شد. تعداد نقش‌ها: {len(CURRENT_ROLES)}", parse_mode='html')
        else:
             bot.send_message(chat_id, "⚠️ لیست نقش‌ها نباید خالی باشد.")
    else:
        bot.send_message(chat_id, "⚠️ ورودی نامعتبر است.")
    show_admin_panel(chat_id)

# --- Remove by Row (بدون تغییر) ---
def prompt_remove_by_row(chat_id):
    list_len = len(players_dict.get(str(chat_id), []))
    if list_len == 0:
        bot.send_message(chat_id, "⚠️ لیست خالی است. عملیات حذف امکان‌پذیر نیست.")
        show_admin_panel(chat_id)
        return
    msg = bot.send_message(chat_id, f"لطفا شماره ردیف بازیکن مورد نظر برای حذف (بین 1 تا {list_len}) را ارسال کنید:")
    bot.register_next_step_handler(msg, process_remove_by_row)

def process_remove_by_row(message):
    chat_id = str(message.chat.id)
    try:
        row_num = int(message.text.strip())
        players = players_dict.get(chat_id, [])
        if 1 <= row_num <= len(players):
            removed_player_with_emoji = players.pop(row_num - 1)
            save_data()
            bot.send_message(message.chat.id, f"✅ بازیکن در ردیف <b>{row_num}</b> ({removed_player_with_emoji}) با موفقیت حذف شد.")
            if chat_id in main_message_dict:
                bot.edit_message_text(generate_list(chat_id), chat_id, main_message_dict[chat_id])
        else:
            bot.send_message(message.chat.id, "⚠️ شماره ردیف خارج از محدوده است.")
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ ورودی نامعتبر است. لطفا فقط شماره ردیف را ارسال کنید.")
    show_admin_panel(int(chat_id))

# --- Swap Players (بدون تغییر) ---
def prompt_swap_players(chat_id):
    list_len = len(players_dict.get(str(chat_id), []))
    if list_len < 2:
        bot.send_message(chat_id, "⚠️ برای جابجایی حداقل دو بازیکن لازم است.")
        show_admin_panel(chat_id)
        return
    msg = bot.send_message(chat_id, f"لطفا شماره ردیف دو بازیکن را با کاما جدا کنید (مثلا: 3, 8):")
    bot.register_next_step_handler(msg, process_swap_players)

def process_swap_players(message):
    chat_id = str(message.chat.id)
    try:
        rows = list(map(int, [r.strip() for r in message.text.split(',')]))
        if len(rows) != 2: raise ValueError
        r1, r2 = rows[0], rows[1]
        
        players = players_dict.get(chat_id, [])
        list_len = len(players)
        
        if 1 <= r1 <= list_len and 1 <= r2 <= list_len and r1 != r2:
            idx1, idx2 = r1 - 1, r2 - 1
            players[idx1], players[idx2] = players[idx2], players[idx1] # Swap
            save_data()
            bot.send_message(message.chat.id, f"✅ بازیکنان ردیف <b>{r1}</b> و <b>{r2}</b> با موفقیت جابجا شدند.", parse_mode='html')
            if chat_id in main_message_dict:
                bot.edit_message_text(generate_list(chat_id), chat_id, main_message_dict[chat_id])
        else:
            bot.send_message(message.chat.id, "⚠️ شماره ردیف‌ها نامعتبر یا تکراری هستند.")
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ ورودی نامعتبر است. لطفا دو عدد را با کاما جدا کنید (مثلاً: 3, 8).")
    show_admin_panel(int(chat_id))

# --- Edit Player Name (جدید) ---
def prompt_edit_player_name(chat_id):
    list_len = len(players_dict.get(str(chat_id), []))
    if list_len == 0:
        bot.send_message(chat_id, "⚠️ لیست خالی است. عملیات ویرایش امکان‌پذیر نیست.")
        show_admin_panel(chat_id)
        return
    msg = bot.send_message(chat_id, f"لطفا شماره ردیف و نام جدید را با کاما جدا کنید (مثلاً: 5, علی رضا):")
    bot.register_next_step_handler(msg, process_edit_player_name)

def process_edit_player_name(message):
    chat_id = str(message.chat.id)
    try:
        parts = [p.strip() for p in message.text.split(',', 1)]
        if len(parts) != 2: raise ValueError
        
        row_num = int(parts[0])
        new_name = parts[1]
        
        players = players_dict.get(chat_id, [])
        list_len = len(players)
        
        if 1 <= row_num <= list_len and new_name:
            # استخراج ایموجی قبلی
            old_entry = players[row_num - 1]
            emoji = next((e for e in animal_emojis if old_entry.endswith(f" {e}")), random.choice(animal_emojis))
            
            # ثبت نام جدید
            players[row_num - 1] = f"{new_name} {emoji}"
            save_data()
            bot.send_message(message.chat.id, f"✅ نام بازیکن در ردیف <b>{row_num}</b> با موفقیت به <b>{new_name}</b> ویرایش شد.", parse_mode='html')
            if chat_id in main_message_dict:
                bot.edit_message_text(generate_list(chat_id), chat_id, main_message_dict[chat_id])
        else:
            bot.send_message(message.chat.id, "⚠️ ورودی نامعتبر: شماره ردیف خارج از محدوده است یا نام جدید خالی است.")
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ ورودی نامعتبر است. لطفا شماره ردیف و نام جدید را با کاما جدا کنید (مثلاً: 5, علی رضا).")
    show_admin_panel(int(chat_id))

# --- Manage Banned Names (جدید) ---
def prompt_manage_banned_names(chat_id):
    banned_text = "، ".join(BANNED_NAMES) if BANNED_NAMES else "خالی"
    msg = bot.send_message(chat_id, 
                           f"<b>🚫 لیست سیاه نام‌ها:</b>\nاسامی ممنوعه: {banned_text}\n\n"
                           "برای افزودن: <code>+ نام</code>\nبرای حذف: <code>- نام</code>\nبرای نمایش دوباره: <code>نمایش</code>\n\n"
                           "لطفا دستور خود را ارسال کنید (مثلاً: + اسپم):", 
                           parse_mode='html')
    bot.register_next_step_handler(msg, process_manage_banned_names)

def process_manage_banned_names(message):
    chat_id = message.chat.id
    text = message.text.strip().lower()
    
    if text == "نمایش":
        prompt_manage_banned_names(chat_id)
        return
        
    if text.startswith('+ '):
        name = text[2:].strip()
        if name and name not in BANNED_NAMES:
            BANNED_NAMES.append(name)
            save_data()
            bot.send_message(chat_id, f"✅ نام <b>{name}</b> به لیست سیاه اضافه شد.")
        else:
            bot.send_message(chat_id, "⚠️ نام وارد شده نامعتبر است یا از قبل وجود دارد.")
    elif text.startswith('- '):
        name = text[2:].strip()
        if name and name in BANNED_NAMES:
            BANNED_NAMES.remove(name)
            save_data()
            bot.send_message(chat_id, f"✅ نام <b>{name}</b> از لیست سیاه حذف شد.")
        else:
            bot.send_message(chat_id, "⚠️ نام وارد شده در لیست سیاه یافت نشد.")
    else:
        bot.send_message(chat_id, "⚠️ دستور نامعتبر است. لطفا از فرمت <code>+ نام</code> یا <code>- نام</code> استفاده کنید.")
    
    show_admin_panel(chat_id)

# --- Manage Group Tags (جدید) ---
def prompt_manage_tags(chat_id):
    chat_id_str = str(chat_id)
    current_tags = GROUP_TAG_LISTS.get(chat_id_str, members_ids_list) # نمایش لیست گروه یا لیست پیش‌فرض
    tags_text = "، ".join(current_tags)
    
    msg = bot.send_message(chat_id, 
                           f"<b>🏷️ مدیریت لیست تگ‌های گروه:</b>\nتگ‌های فعلی این گروه: {tags_text}\n\n"
                           "برای افزودن: <code>+ username</code>\nبرای حذف: <code>- username</code>\nبرای بازگشت به لیست عمومی: <code>ریست</code>\n\n"
                           "لطفا دستور خود را ارسال کنید:", 
                           parse_mode='html')
    bot.register_next_step_handler(msg, process_manage_tags)

def process_manage_tags(message):
    chat_id = str(message.chat.id)
    text = message.text.strip().lower()
    
    if text == "ریست":
        if chat_id in GROUP_TAG_LISTS:
            del GROUP_TAG_LISTS[chat_id]
            save_data()
            bot.send_message(int(chat_id), "✅ لیست تگ‌های این گروه به لیست عمومی (Global) بازگشت.")
        else:
            bot.send_message(int(chat_id), "⚠️ لیست تگ‌های این گروه از قبل روی حالت عمومی بود.")
    
    elif text.startswith('+ ') or text.startswith('- '):
        op = text[0]
        username = text[2:].strip().replace('@', '')
        
        if chat_id not in GROUP_TAG_LISTS:
            GROUP_TAG_LISTS[chat_id] = members_ids_list.copy() # شروع با کپی لیست عمومی

        current_list = GROUP_TAG_LISTS[chat_id]

        if op == '+':
            if username and username not in current_list:
                current_list.append(username)
                bot.send_message(int(chat_id), f"✅ یوزرنیم <b>@{username}</b> به لیست تگ‌های گروه اضافه شد.")
            else:
                bot.send_message(int(chat_id), f"⚠️ یوزرنیم نامعتبر است یا از قبل وجود دارد.")
        elif op == '-':
            if username and username in current_list:
                current_list.remove(username)
                bot.send_message(int(chat_id), f"✅ یوزرنیم <b>@{username}</b> از لیست تگ‌های گروه حذف شد.")
            else:
                bot.send_message(int(chat_id), f"⚠️ یوزرنیم در لیست یافت نشد.")
        
        save_data()
    else:
        bot.send_message(int(chat_id), "⚠️ دستور نامعتبر است.")

    show_admin_panel(int(chat_id))

# --- Set List Style (جدید) ---
def set_list_style_callback(call):
    chat_id = str(call.message.chat.id)
    try:
        style_id = int(call.data.split("_")[3])
        if 0 <= style_id < len(LIST_STYLES_OPTIONS):
            LIST_STYLE_IDS[chat_id] = style_id
            save_data()
            bot.answer_callback_query(call.id, f"✅ استایل لیست به {LIST_STYLES_OPTIONS[style_id]['name']} تغییر یافت.")
        elif style_id == -1:
            if chat_id in LIST_STYLE_IDS:
                del LIST_STYLE_IDS[chat_id]
                save_data()
                bot.answer_callback_query(call.id, "✅ استایل لیست به حالت تصادفی برگشت.")

        show_admin_panel(int(chat_id), call.message.message_id)
        # آپدیت لیست اصلی
        if chat_id in main_message_dict:
            bot.edit_message_text(generate_list(chat_id), chat_id, main_message_dict[chat_id])

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطا: {e}")
        show_admin_panel(int(chat_id), call.message.message_id)

# ------------------ هندلر کلی CallBack پنل ------------------
# ... (تابع admin_callback_handler بدون تغییر)
@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callback_handler(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if not is_bot_admin(user_id):
        bot.answer_callback_query(call.id, "❌ شما دسترسی ادمین ربات را ندارید.", show_alert=True)
        return

    action = call.data.split("_")[1]
    
    if action == "main":
        show_admin_panel(chat_id, call.message.message_id)
        bot.answer_callback_query(call.id, "به پنل اصلی بازگشتید.")
    
    elif action == "manage" and call.data.endswith("bot_admins"):
        # ... (نمایش ادمین‌ها بدون تغییر)
        admin_list_text = "\n".join([f"• <code>{a}</code>" for a in BOT_ADMINS])
        if not BOT_ADMINS: admin_list_text = "فعلا ادمینی تعریف نشده است."

        current_admins_msg = (
            "<b>لیست ادمین‌های ربات:</b>\n"
            f"{admin_list_text}\n\n"
            "ℹ️ برای افزودن/حذف ادمین، روی پیام کاربر ریپلای کنید و دستور <code>/addadmin</code> یا <code>/removeadmin</code> را بفرستید."
        )
        markup = telebot.types.InlineKeyboardMarkup().add(telebot.types.InlineKeyboardButton("🔙 بازگشت به پنل اصلی", callback_data="admin_main"))
        bot.edit_message_text(current_admins_msg, chat_id, call.message.message_id, reply_markup=markup, parse_mode='html')
        bot.answer_callback_query(call.id, "بخش مدیریت ادمین‌ها.")
    
    # --- ابزارهای مدیریتی با ورودی متنی ---
    elif action in ["set", "remove", "swap", "edit", "manage"]:
        sub_action = call.data.split("_")[2] if len(call.data.split("_")) > 2 else ""
        
        if sub_action in ["time", "capacity", "roles"]: # تنظیمات عمومی
            bot.delete_message(chat_id, call.message.message_id) 
            bot.answer_callback_query(call.id, "لطفا ورودی را در پیام بعدی ارسال کنید.")
            if sub_action == "time": prompt_set_time(chat_id)
            elif sub_action == "capacity": prompt_set_capacity(chat_id)
            elif sub_action == "roles": prompt_set_roles(chat_id)
        
        elif call.data.endswith("by_row"): # حذف با شماره
            bot.delete_message(chat_id, call.message.message_id) 
            bot.answer_callback_query(call.id, "لطفا ورودی را در پیام بعدی ارسال کنید.")
            prompt_remove_by_row(chat_id)
            
        elif call.data.endswith("players"): # جابجایی
            bot.delete_message(chat_id, call.message.message_id) 
            bot.answer_callback_query(call.id, "لطفا ورودی را در پیام بعدی ارسال کنید.")
            prompt_swap_players(chat_id)
            
        elif call.data.endswith("edit_player_name"): # ویرایش نام
            bot.delete_message(chat_id, call.message.message_id) 
            bot.answer_callback_query(call.id, "لطفا ورودی را در پیام بعدی ارسال کنید.")
            prompt_edit_player_name(chat_id)

        elif call.data.endswith("banned"): # مدیریت لیست سیاه
            bot.delete_message(chat_id, call.message.message_id) 
            bot.answer_callback_query(call.id, "لطفا ورودی را در پیام بعدی ارسال کنید.")
            prompt_manage_banned_names(chat_id)

        elif call.data.endswith("tags"): # مدیریت تگ‌های گروه
            bot.delete_message(chat_id, call.message.message_id) 
            bot.answer_callback_query(call.id, "لطفا ورودی را در پیام بعدی ارسال کنید.")
            prompt_manage_tags(chat_id)

    # --- تنظیم استایل لیست ---
    elif action == "set" and call.data.endswith("style"):
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for idx, style in enumerate(LIST_STYLES_OPTIONS):
            markup.add(telebot.types.InlineKeyboardButton(f"🖼️ {style['name']} ({style['icon']} {style['separator']})", callback_data=f"admin_set_style_{idx}"))
        markup.add(telebot.types.InlineKeyboardButton("❌ حالت تصادفی", callback_data="admin_set_style_-1"))
        markup.add(telebot.types.InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="admin_main"))
        bot.edit_message_text("🎨 **انتخاب استایل لیست برای این گروه:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode='html')
        bot.answer_callback_query(call.id, "انتخاب استایل لیست.")

    elif action == "set" and call.data.startswith("admin_set_style_"):
        set_list_style_callback(call)
    
    # --- ابزارهای جابجایی و گزارش ---
    elif action == "toggle":
        setting = call.data.split("_")[2]
        global SCHEDULER_ENABLED, TAGGING_ENABLED

        if setting == "scheduler":
            SCHEDULER_ENABLED = not SCHEDULER_ENABLED
            setup_scheduler()
            status_text = "فعال" if SCHEDULER_ENABLED else "غیرفعال"
            bot.answer_callback_query(call.id, f"✅ زمانبندی: {status_text}")
        elif setting == "tagging":
            TAGGING_ENABLED = not TAGGING_ENABLED
            status_text = "فعال" if TAGGING_ENABLED else "غیرفعال"
            bot.answer_callback_query(call.id, f"✅ تگ کردن: {status_text}")
        elif setting == "lock":
            chat_id_str = str(chat_id)
            LIST_LOCKED_DICT[chat_id_str] = not LIST_LOCKED_DICT.get(chat_id_str, False)
            save_data()
            status_text = "قفل شد" if LIST_LOCKED_DICT[chat_id_str] else "باز شد"
            bot.answer_callback_query(call.id, f"✅ لیست {status_text}")
            if chat_id_str in main_message_dict:
                bot.edit_message_text(generate_list(chat_id), chat_id, main_message_dict[chat_id_str])
        
        save_data()
        show_admin_panel(chat_id, call.message.message_id) 

    elif action == "send":
        if call.data.endswith("reminder"):
            send_reminder()
            bot.answer_callback_query(call.id, "🔔 پیام یادآوری بازی فوراً ارسال شد.")
        show_admin_panel(chat_id, call.message.message_id) 

    elif action == "backup":
        # ... (بک‌آپ لیست بدون تغییر)
        if call.data.endswith("list"):
            players = players_dict.get(str(chat_id), [])
            if players:
                backup_text = f"پشتیبان‌گیری لیست در تاریخ {datetime.now(pytz.timezone('Asia/Tehran')).strftime('%Y-%m-%d %H:%M')}:\n\n"
                for i, p in enumerate(players):
                    backup_text += f"{i+1}. {p}\n"
                
                bot.send_document(chat_id, 
                                 ('backup.txt', backup_text.encode('utf-8')), 
                                 caption="✅ پشتیبان‌گیری از لیست بازیکنان انجام شد.")
                bot.answer_callback_query(call.id, "فایل پشتیبان ارسال شد.")
            else:
                bot.answer_callback_query(call.id, "⚠️ لیست خالی است. پشتیبان‌گیری انجام نشد.")
        show_admin_panel(chat_id, call.message.message_id) 

    elif action == "view" and call.data.endswith("warnings"):
        # نمایش اخطارات
        warnings_text = "⚠️ **لیست اخطارات بازیکنان (جهانی):**\n"
        has_warnings = False
        sorted_warnings = sorted(WARNINGS_DICT.items(), key=lambda item: item[1], reverse=True)
        
        for user_id_str, count in sorted_warnings:
            if count > 0:
                warnings_text += f"• ID: <code>{user_id_str}</code> | اخطار: {count}\n"
                has_warnings = True
        
        if not has_warnings:
            warnings_text += "لیست اخطارات خالی است."

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(telebot.types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main"))
        bot.edit_message_text(warnings_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode='html')
        bot.answer_callback_query(call.id, "مشاهده اخطارات.")

    elif action == "stats":
        # ... (آمار کلی بدون تغییر)
        total_players = sum(len(p) for p in players_dict.values())
        total_chats = len(players_dict)
        
        stats_text = (
            "📊 <b>آمار کلی ربات:</b>\n"
            f"👥 تعداد کل بازیکنان ثبت نام شده: {total_players}\n"
            f"🏠 تعداد کل گروه‌های فعال: {total_chats}\n"
            f"🚫 تعداد نام‌های ممنوعه: {len(BANNED_NAMES)}\n"
            f"🔄 زمانبندی خودکار: {'فعال' if SCHEDULER_ENABLED else 'غیرفعال'}\n"
            f"📢 تگ کردن: {'فعال' if TAGGING_ENABLED else 'غیرفعال'}\n"
            f"⏰ ساعت ریست/شروع: {START_TIME}\n"
            f"🔢 ظرفیت پیش‌فرض: {LIST_CAPACITY}\n"
            f"🔠 تعداد نقش‌ها: {len(CURRENT_ROLES)}"
        )
        markup = telebot.types.InlineKeyboardMarkup().add(telebot.types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main"))
        
        bot.edit_message_text(stats_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode='html')
        bot.answer_callback_query(call.id, "آمار ربات نمایش داده شد.")


# ------------------ دستورات مدیریت ادمین ربات (بدون تغییر) ------------------
# ... (توابع add_admin_command و remove_admin_command بدون تغییر)
@bot.message_handler(commands=['addadmin'])
def add_admin_command(message):
    # ... (تابع add_admin_command بدون تغییر)
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_bot_admin(user_id):
        if not BOT_ADMINS and is_group_admin(chat_id, user_id):
            pass 
        else:
            bot.reply_to(message, "❌ شما دسترسی لازم برای افزودن ادمین جدید را ندارید.")
            return

    if message.reply_to_message:
        new_admin_id = message.reply_to_message.from_user.id
        new_admin_name = message.reply_to_message.from_user.first_name
        
        if new_admin_id not in BOT_ADMINS:
            BOT_ADMINS.append(new_admin_id)
            save_admins()
            bot.reply_to(message, f"✅ کاربر <b>{new_admin_name}</b> (ID: <code>{new_admin_id}</code>) به عنوان ادمین ربات اضافه شد.")
        else:
            bot.reply_to(message, f"⚠️ کاربر <b>{new_admin_name}</b> از قبل ادمین است.")
    else:
        bot.reply_to(message, "⚠️ برای افزودن ادمین جدید، باید روی پیام کاربر مورد نظر ریپلای کنید و دستور <code>/addadmin</code> را بفرستید.")

@bot.message_handler(commands=['removeadmin'])
def remove_admin_command(message):
    # ... (تابع remove_admin_command بدون تغییر)
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_bot_admin(user_id):
        bot.reply_to(message, "❌ شما دسترسی لازم برای حذف ادمین را ندارید.")
        return

    if message.reply_to_message:
        target_admin_id = message.reply_to_message.from_user.id
        target_admin_name = message.reply_to_message.from_user.first_name

        if target_admin_id == user_id:
             bot.reply_to(message, "⚠️ نمی‌توانید خودتان را حذف کنید.")
             return
        
        if target_admin_id in BOT_ADMINS:
            BOT_ADMINS.remove(target_admin_id)
            save_admins()
            bot.reply_to(message, f"✅ کاربر <b>{target_admin_name}</b> (ID: <code>{target_admin_id}</code>) از لیست ادمین‌ها حذف شد.")
        else:
            bot.reply_to(message, f"⚠️ کاربر <b>{target_admin_name}</b> ادمین ربات نیست.")
    else:
        bot.reply_to(message, "⚠️ برای حذف ادمین، باید روی پیام کاربر مورد نظر ریپلای کنید و دستور <code>/removeadmin</code> را بفرستید.")

# ------------------ هندلر کلی پیام‌ها ------------------
@bot.message_handler(func=lambda m: True)
def reply_handler(message):
    chat_id=str(message.chat.id)
    text=message.text.strip()
    user_id=message.from_user.id
    user_name=message.from_user.username or message.from_user.first_name

    # ---------- تشخیص و ارسال پنل مدیریتی ----------
    if text.lower() == "پنل":
        if is_bot_admin(user_id) or is_group_admin(chat_id, user_id):
            show_admin_panel(int(chat_id), message.message_id)
        else:
            bot.reply_to(message, "❌ شما دسترسی لازم برای باز کردن پنل را ندارید.")
        return 

    # ---------- ارسال خودکار لیست با کلیدواژه ----------
    if "لیست بفرست" in text.lower():
        if chat_id not in players_dict: players_dict[chat_id] = []
        if chat_id not in nazor_dict: nazor_dict[chat_id] = ["___","___"]
        
        sent = bot.send_message(chat_id, generate_list(chat_id))
        main_message_dict[chat_id] = sent.message_id
        
        # استفاده از لیست تگ‌های گروهی یا پیش‌فرض
        tag_list = GROUP_TAG_LISTS.get(chat_id, members_ids_list) 

        if TAGGING_ENABLED and tag_list: 
            mentions_text = " ".join([f"@{username}" for username in tag_list])
            bot.send_message(chat_id, mentions_text, reply_to_message_id=sent.message_id) 
            tag_msg = "و اعضا تگ شدند!"
        else:
            tag_msg = ""

        try:
            if "لیست بفرست" in message.text.lower():
                bot.pin_chat_message(chat_id, sent.message_id, disable_notification=True)
                bot.reply_to(message, f"✅ لیست جدید ارسال و پین شد. ({tag_msg})")
            else:
                bot.reply_to(message, "✅ لیست ارسال شد.")
        except Exception as e:
            print(f"Error pinning message: {e}")
            pass
        return

    # ---------- پیام لابی ساعت ----------
    if "لابی ساعت" in text:
        # ... (ارسال پیام لابی)
        try:
            sent_msg = bot.send_message(chat_id, text)
            bot.pin_chat_message(chat_id, sent_msg.message_id, disable_notification=True)
            tag_list = GROUP_TAG_LISTS.get(chat_id, members_ids_list) 
            mentions_text = " ".join([f"@{username}" for username in tag_list])
            bot.send_message(chat_id, mentions_text, reply_to_message_id=sent_msg.message_id)
            bot.reply_to(message, "📌 پیام لابی کپی شد، پین شد و اعضا تگ شدند!")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")
        return

    # ------------------ پیام ریپلای روی لیست ------------------
    if chat_id not in main_message_dict or not message.reply_to_message: return
    if message.reply_to_message.message_id != main_message_dict[chat_id]: return

    # اخطار
    if text.lower() == "اخطار" and is_bot_admin(user_id):
        if message.reply_to_message:
            target_user_id = str(message.reply_to_message.from_user.id)
            WARNINGS_DICT[target_user_id] = WARNINGS_DICT.get(target_user_id, 0) + 1
            save_data()
            count = WARNINGS_DICT[target_user_id]
            bot.reply_to(message, f"⚠️ اخطار برای کاربر <b>{message.reply_to_message.from_user.first_name}</b> ثبت شد. (تعداد کل: {count})")
        return

    # ... (بررسی نام‌های ممنوعه هاردکد شده)
    if text in HARDCODED_BANNED_NAMES:
        bot.reply_to(message,"🚨 <b>هشدار!</b>\nنام خطرناک!")
        return

    # ناظر
    if text.startswith("ناظر"):
        parts=text.split()
        if len(parts)>=3:
            nazor_type = parts[1]
            nazor_name = " ".join(parts[2:]).strip()
            if nazor_type in ["1","یک","۱"]: nazor_dict[chat_id][0]=nazor_name
            elif nazor_type in ["2","دو","۲"]: nazor_dict[chat_id][1]=nazor_name
            bot.reply_to(message,f"👁‍🗨 ناظر ثبت شد: {nazor_name}")
            save_data()
            bot.edit_message_text(generate_list(chat_id),chat_id,main_message_dict[chat_id])
            return

    # اضافه کردن الی
    if text=="الی":
        added=add_names(text,chat_id)
        if added: bot.reply_to(message,"😂خدای مافیا اومد بالاخره")
        bot.edit_message_text(generate_list(chat_id),chat_id,main_message_dict[chat_id])
        return

    # پیش‌بینی نقش‌ها
    if text.lower() in ["پیشبینی","پیشبینی نقش"]:
        bot.reply_to(message, generate_role_prediction(chat_id))
        return

    # ریست
    if text=="ریست":
        try:
            if is_bot_admin(user_id) or is_group_admin(chat_id, user_id):
                reset_list(chat_id)
                bot.reply_to(message,"♻️ لیست ریست شد.")
                # <اضافه شده برای به‌روزرسانی پیام اصلی لیست پس از ریست>
                bot.edit_message_text(generate_list(chat_id),chat_id,main_message_dict[chat_id]) 
                # </اضافه شده برای به‌روزرسانی پیام اصلی لیست پس از ریست>
            else: bot.reply_to(message,"❌ فقط ادمین")
        except: pass
        return

    # حذف خود و دیگران (با ریپلای فان)
    if text.lower() in ["حذف","delete","remove","حذف نام"] or text.startswith("حذف "):
        target = user_name if text.lower() in ["حذف","delete","remove","حذف نام"] else text.replace("حذف ","").strip()
        removed=remove_name(target,chat_id)
        if removed: 
            bot.reply_to(message, random.choice(funny_remove_messages))
        else: 
            bot.reply_to(message,f"⚠️ {target} داخل لیست نبود یا لیست قفل است.")
        bot.edit_message_text(generate_list(chat_id),chat_id,main_message_dict[chat_id])
        return

    # اضافه کردن اسامی
    added=add_names(text,chat_id)
    if added:
        bot.reply_to(message, random.choice(funny_add_messages)) 
    elif LIST_LOCKED_DICT.get(chat_id, False):
        bot.reply_to(message,"❌ لیست قفل است. ثبت‌نام جدید امکان‌پذیر نیست.")
    elif text.lower() in [n.lower() for n in BANNED_NAMES + HARDCODED_BANNED_NAMES]:
        bot.reply_to(message, "🚫 <b>نام شما در لیست سیاه قرار دارد و امکان ثبت‌نام نیست.</b>")
    else:
        bot.reply_to(message,"⚠️ اسمی اضافه نشد (ظرفیت تکمیل، تکراری بودن نام یا قفل بودن لیست).")
    bot.edit_message_text(generate_list(chat_id),chat_id,main_message_dict[chat_id])

# ------------------ شروع ربات ------------------
load_data()
load_admins() 
setup_scheduler()
print("Bot started...")
bot.polling(none_stop=True)
