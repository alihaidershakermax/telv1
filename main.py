import telebot
from telebot.types import Message
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, InputMediaPhoto, InputMediaVideo
import os
import time
from functools import wraps
import logging
import traceback  # إضافة استيراد traceback
import sys
from config import Config  # استيراد فئة Config

# التحقق من تحميل المتغيرات
if not Config.TOKEN or not Config.ADMIN_ID:
    print("❌ تأكد من ضبط جميع المتغيرات في Secrets!")
    print(f"TOKEN is set: {Config.TOKEN is not None}")  # إضافة فحوصات للتحقق
    print(f"ADMIN_ID is set: {Config.ADMIN_ID is not None}")  # إضافة فحوصات للتحقق
    logging.error("❌ تأكد من ضبط جميع المتغيرات في Secrets!") # Log the error
    sys.exit(1)  # Exit with a non-zero exit code

# تحويل ADMIN_ID إلى عدد صحيح هنا، بعد التأكد من وجوده
try:
    ADMIN_ID = int(Config.ADMIN_ID)
except ValueError:
    print("❌ ADMIN_ID ليس رقمًا صحيحًا!")
    logging.error("❌ ADMIN_ID ليس رقمًا صحيحًا!")
    sys.exit(1)
except TypeError:  # في حالة كان ADMIN_ID لا يزال None
    print("❌ ADMIN_ID غير معرّف!")
    logging.error("❌ ADMIN_ID غير معرّف!")
    sys.exit(1)

user_message_ids = {}
user_states = {}  # لتتبع حالة المستخدم (مثل إرسال رسالة جماعية)
bot_stats = {"total_users": 0, "start_command_usage": 0}

# إعدادات تسجيل الأخطاء (Logging)
LOG_FILE = "bot.log"  # اسم ملف السجل (يمكنك تغييره)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"  # "a" للإضافة إلى الملف الحالي، "w" للكتابة فوقه في كل مرة
)
logging.info("البوت بدأ التشغيل...")

def retry_on_rate_limit(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except telebot.apihelper.ApiTelegramException as e:
                    if e.error_code == 429:
                        retry_after = int(str(e).split('retry after ')[1])
                        logging.warning(f"تم تجاوز الحد الأقصى للطلبات. الانتظار لمدة {retry_after} ثانية.")
                        time.sleep(retry_after)
                        retries += 1
                        continue
                    raise
            raise Exception("❌ فشلت العملية بعد عدة محاولات.")
        return wrapper
    return decorator

class Bot:
    def __init__(self):
        self.bot = telebot.TeleBot(None)  # لا تقم بتهيئة البوت هنا
        self.user_list = self.load_user_list() # تحميل قائمة المستخدمين عند بدء التشغيل

    def setup_commands(self):
        commands = [
            BotCommand("start", "يا هلا بيك"),
            BotCommand("help", "شتحتاجين؟"),  # تعديل: صيغة المؤنث
            BotCommand("info", "معلومات عني"),  # تعديل: صيغة المؤنث
        ]
        self.bot.set_my_commands(commands)

    def create_admin_keyboard(self): #تم ازالتها
       pass

    def create_welcome_inline_buttons(self):
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("📢 قناتي", url="https://t.me/zaa_azd"),
            InlineKeyboardButton("✉️ راسليني", callback_data="contact_me"),
        )
        return keyboard

    def format_welcome_message(self, user):
        name = user.first_name
        welcome_text = f"هلو، اني زهرة 🌸. شلون اكدر اساعدج، {name}؟\nاتركيلي رسالة و اراسلج بأقرب فرصة 😉."  # تعديل: صيغة المؤنث + رموز تعبيرية
        return welcome_text

    def load_user_list(self):
        """تحميل قائمة المستخدمين من ملف (إذا كان موجودًا)"""
        try:
            with open("user_list.txt", "r") as f:
                user_ids = [int(line.strip()) for line in f]
            return set(user_ids)
        except FileNotFoundError:
            return set()

    def save_user_list(self):
        """حفظ قائمة المستخدمين في ملف"""
        with open("user_list.txt", "w") as f:
            for user_id in self.user_list:
                f.write(str(user_id) + "\n")

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        @retry_on_rate_limit()
        def start(message):
            try:
                user_id = message.from_user.id
                if user_id not in self.user_list:
                    self.user_list.add(user_id)
                    self.save_user_list()
                    bot_stats["total_users"] += 1
                bot_stats["start_command_usage"] += 1

                welcome_text = self.format_welcome_message(message.from_user)
                if WELCOME_IMAGE:
                    self.bot.send_photo(
                        message.chat.id,
                        photo=WELCOME_IMAGE,
                        caption=welcome_text,
                        reply_markup=self.create_welcome_inline_buttons(),
                        parse_mode='HTML'
                    )
                else:
                    self.bot.send_message(
                        message.chat.id,
                        welcome_text,
                        reply_markup=self.create_welcome_inline_buttons(),
                        parse_mode='HTML'
                    )

                if message.from_user.id != ADMIN_ID:
                    new_user_info = f"""
👤 مستخدم جديد طب للبوت:
• الاسم: {message.from_user.first_name} {message.from_user.last_name or ''}
• المعرف: @{message.from_user.username or 'ماكو'}
• الآيدي: {message.from_user.id}
                    """
                    self.bot.send_message(ADMIN_ID, new_user_info)
                    logging.info(f"New user: {message.from_user.id}")

            except Exception as e:
                logging.exception(f"Error in start handler: {traceback.format_exc()}")
                self.bot.reply_to(message, "عذرًا، صار خلل. حاول مرة لخ.")

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            if call.data == "contact_me":
                contact_text = "دز رسالتك و ارد عليج بأقرب وقت." # تعديل: صيغة المؤنث
                self.bot.answer_callback_query(call.id)
                self.bot.send_message(call.message.chat.id, contact_text)

        @self.bot.message_handler(commands=['info'])
        def info(message):
            info_text = f"""
🤖 معلومات عني:  # تعديل: صيغة المؤنث
- آني بوت  اني بوت زهور انخلقت لتسهيل تواصل مع زهرة
- صممتني: @zaa_azd  # تعديل: صيغة المؤنث  !!تم تعديل اسم المتغير بشكل مباشر!!
- قناتي: [https://t.me/your_channel](https://t.me/zaa_azd)
            """
            self.bot.reply_to(message, info_text, parse_mode='Markdown')

        @self.bot.message_handler(commands=['help'])
        def help(message):
            help_text = """
🆘 المساعدة:
- /start: بدء استخدامي. # تعديل: صيغة المؤنث
- /help: عرض رسالة المساعدة.
- /info: معلومات عني. # تعديل: صيغة المؤنث
            """
            self.bot.reply_to(message, help_text)

        @self.bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.text == "📢 إرسال رسالة للكل")
        def admin_broadcast_message_start(message):
            self.bot.reply_to(message, "دز الرسالة اللي تريد أرسلها للكل.")
            user_states[message.from_user.id] = "waiting_for_broadcast_message"

        @self.bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_for_broadcast_message", content_types=['text', 'photo', 'video', 'sticker', 'document'])
        def admin_broadcast_message_content(message):
            try:
                count = 0
                for user_id in self.user_list:
                    try:
                        if message.content_type == 'text':
                            self.bot.send_message(user_id, message.text)
                        elif message.content_type == 'photo':
                            self.bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
                        elif message.content_type == 'video':
                            self.bot.send_video(user_id, message.video.file_id, caption=message.caption)
                        elif message.content_type == 'sticker':
                            self.bot.send_sticker(user_id, message.sticker.file_id)
                        elif message.content_type == 'document':
                            self.bot.send_document(user_id, message.document.file_id, caption=message.caption)
                        count += 1
                        time.sleep(0.05)  # تجنب تجاوز الحد الأقصى للطلبات
                    except Exception as e:
                        logging.warning(f"Failed to send message to {user_id}: {e}")
                self.bot.reply_to(message, f"تم إرسال الرسالة إلى {count} مستخدم.")
            except Exception as e:
                logging.exception(f"Error during broadcast: {traceback.format_exc()}")
                self.bot.reply_to(message, "صار خلل أثناء إرسال الرسالة.")
            finally:
                user_states[message.from_user.id] = None  # reset state

        @self.bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'sticker', 'document'])
        def handle_messages(message):
            try:
                self.bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
                self.bot.reply_to(message, "وصلت رسالتك للمسؤول. شكراً لتواصلج 😉 .") # تعديل: صيغة المؤنث ورمز تعبيري

                user_id = message.from_user.id
                if user_id not in self.user_list:
                    self.user_list.add(user_id)
                    self.save_user_list()
                    bot_stats["total_users"] += 1
                    logging.info(f"New user: {message.from_user.id}")

            except Exception as e:
                logging.exception(f"Error handling message: {traceback.format_exc()}")
                self.bot.reply_to(message, "صار خلل. حاول مرة لخ.")

    @retry_on_rate_limit()
    def send_heartbeat(self):
        """إرسال رسالة 'نبض قلب' للمحافظة على البوت قيد التشغيل."""
        try:
            self.bot.send_message(ADMIN_ID, "البوت بعده شغال 💖") # تعديل: رمز تعبيري
            logging.info("تم إرسال رسالة نبض القلب.")
            return True  # للإشارة إلى النجاح
        except telebot.apihelper.ApiTelegramException as e:
            logging.warning(f"فشل إرسال رسالة نبض القلب: {e}")
            return False # للإشارة إلى الفشل
        except Exception as e:
            logging.exception(f"خطأ غير متوقع أثناء إرسال نبض القلب: {traceback.format_exc()}")
            return False

    def run(self):
        print("✅ البوت يشتغل...")

        TOKEN = Config.TOKEN
        ADMIN_ID = Config.ADMIN_ID
        WEBHOOK_URL = Config.WEBHOOK_URL
        PORT = Config.PORT

        print("Checking environment variables during startup...") # إضافة فحص للمتغيرات

        print(f"TOKEN: {TOKEN}")  # عرض قيم المتغيرات
        print(f"ADMIN_ID: {ADMIN_ID}")
        print(f"WEBHOOK_URL: {WEBHOOK_URL}")
        print(f"PORT: {PORT}")

        print("Environment variables check complete.")

        if not TOKEN or not ADMIN_ID:  # التحقق مرة أخرى هنا
            print("❌ المتغيرات TOKEN أو ADMIN_ID غير معرّفة حتى داخل run()!")
            logging.error("❌ المتغيرات TOKEN أو ADMIN_ID غير معرّفة حتى داخل run()!")
            sys.exit(1)

        try:
            ADMIN_ID = int(ADMIN_ID)  # التحويل إلى عدد صحيح هنا
        except ValueError:
            print("❌ ADMIN_ID ليس رقمًا صحيحًا!")
            logging.error("❌ ADMIN_ID ليس رقمًا صحيحًا!")
            sys.exit(1)
        except TypeError:
            print("❌ ADMIN_ID غير معرّف!")
            logging.error("❌ ADMIN_ID غير معرّف!")
            sys.exit(1)

        try:
            self.bot = telebot.TeleBot(TOKEN)  # تهيئة البوت هنا
            self.setup_commands() # إعداد الأوامر هنا
            self.setup_handlers() # إعداد المعالجات هنا
        except Exception as e:
            logging.exception(f"Failed to initialize bot: {traceback.format_exc()}")
            logging.error(f"Failed to initialize bot: {traceback.format_exc()}")
            sys.exit(1)

        if WEBHOOK_URL:
            # إعداد الويب هوك
            self.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
            print(f"✅ تم إعداد الويب هوك على: {WEBHOOK_URL}/{TOKEN}")
        else:
            print("⚠️ لم يتم العثور على رابط الويب هوك.  التشغيل في وضع الاستطلاع الطويل.")
            self.bot.remove_webhook()  # إزالة أي ويب هوك موجود
            self.bot.infinity_polling() #  التشغيل في وضع الاستطلاع الطويل

        start_time = time.time()  # تسجيل وقت بدء التشغيل

        while True:
            try:
                # فحص كل فترة (HEARTBEAT_INTERVAL)
                time.sleep(HEARTBEAT_INTERVAL)

                # حساب وقت التشغيل
                uptime = time.time() - start_time
                print(f"البوت شغال لمدة: {uptime:.2f} ثانية")
                logging.info(f"Uptime: {uptime:.2f} seconds")

                # ارسال رسالة "نبض قلب" للمحافظة على البوت قيد التشغيل.  (مهم!)
                if not self.send_heartbeat():
                    logging.warning("فشل إرسال نبض القلب. سيتم إعادة المحاولة لاحقًا.")

                # تشغيل البوت باستمرار
                try:
                    self.bot.infinity_polling(timeout=20, long_polling_timeout=5)
                except Exception as e:
                    logging.exception(f"خطأ أثناء infinity_polling: {e}")

            except Exception as e:
                logging.exception("خطأ في الحلقة الرئيسية:")
                time.sleep(10)  # الانتظار قبل إعادة المحاولة

if __name__ == "__main__":
    bot = Bot()
    bot.run()
