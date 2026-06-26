import asyncio
import logging
import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from playwright.async_api import async_playwright

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv('TELEGRAM_TOKEN', '8972332186:AAFKZkeFmMDC7Tk0fnOJBMhFSj-XOt28CbU')

# حالات المحادثة
EMAIL, PASSWORD, FIRST_NAME, LAST_NAME, SOLVE_AUDIO_CAPTCHA = range(5)

class MicrosoftCreator:
    def __init__(self, update_msg_func):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.update_status = update_msg_func

    async def start_session(self):
        await self.update_status("🚀 جاري بدء تشغيل المتصفح...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()

    async def fill_initial_info(self, email, password, first_name, last_name):
        try:
            await self.update_status("🌐 جاري الدخول لصفحة التسجيل (قد يستغرق وقتاً)...")
            await self.page.goto("https://signup.live.com/signup", wait_until="networkidle", timeout=90000)
            
            await self.update_status("📧 جاري إدخال البيانات...")
            # البحث عن حقل البريد بمهلة أطول ومحددات مرنة
            email_field = await self.page.wait_for_selector('input[name="MemberName"], input[type="email"]', timeout=40000)
            await email_field.fill(email)
            await self.page.click('input[type="submit"]')
            
            password_field = await self.page.wait_for_selector('input[name="Password"]', timeout=30000)
            await password_field.fill(password)
            await self.page.click('input[type="submit"]')

            await self.page.wait_for_selector('input[name="FirstName"]', timeout=30000)
            await self.page.fill('input[name="FirstName"]', first_name)
            await self.page.fill('input[name="LastName"]', last_name)
            await self.page.click('input[type="submit"]')

            await self.page.wait_for_selector('select[name="BirthMonth"]', timeout=30000)
            await self.page.select_option('select[name="BirthMonth"]', value="1")
            await self.page.fill('input[name="BirthDay"]', "01")
            await self.page.fill('input[name="BirthYear"]', "1995")
            await self.page.click('input[type="submit"]')
            
            await self.update_status("🛡️ جاري انتظار الكابتشا...")
            await asyncio.sleep(15)
        except Exception as e:
            await self.page.screenshot(path="debug_error.png")
            raise e

    async def get_audio_captcha(self):
        try:
            audio_btn = await self.page.wait_for_selector('button[aria-label="Get an audio challenge"]', timeout=40000)
            if audio_btn:
                await self.update_status("🎙️ جاري تحميل الكابتشا الصوتية...")
                await audio_btn.click()
                await asyncio.sleep(5)
                download_link = await self.page.wait_for_selector('a[href*="audio"]', timeout=20000)
                if download_link:
                    url = await download_link.get_attribute('href')
                    response = requests.get(url)
                    path = "captcha_audio.wav"
                    with open(path, "wb") as f: f.write(response.content)
                    return path
        except Exception as e:
            await self.page.screenshot(path="captcha_debug.png")
            logging.error(f"Audio Captcha Error: {e}")
        return None

    async def complete_registration(self, solution):
        try:
            await self.update_status("🔄 جاري إرسال الحل...")
            input_field = await self.page.wait_for_selector('input[aria-label="Type the numbers you hear"]', timeout=20000)
            if input_field:
                await input_field.fill(solution)
                await self.page.click('button:has-text("Verify")')
                await asyncio.sleep(15)
                try:
                    yes_btn = await self.page.wait_for_selector('input[value="Yes"]', timeout=15000)
                    if yes_btn: await yes_btn.click()
                except: pass
                return True
        except Exception as e:
            await self.page.screenshot(path="final_debug.png")
            logging.error(f"Completion Error: {e}")
        return False

    async def close(self):
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! تم تحسين البوت وإضافة أدوات تشخيص. استخدم /create للبدء.")

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أدخل البريد الإلكتروني:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text
    await update.message.reply_text("أدخل كلمة المرور:")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['password'] = update.message.text
    await update.message.reply_text("أدخل الاسم الأول:")
    return FIRST_NAME

async def get_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text("أدخل اسم العائلة:")
    return LAST_NAME

async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_name'] = update.message.text
    status_msg = await update.message.reply_text("⏳ جاري البدء...")
    async def update_status(text):
        try: await status_msg.edit_text(text)
        except: pass
    creator = MicrosoftCreator(update_status)
    context.user_data['creator'] = creator
    try:
        await creator.start_session()
        await creator.fill_initial_info(
            context.user_data['email'], context.user_data['password'],
            context.user_data['first_name'], context.user_data['last_name']
        )
        audio_path = await creator.get_audio_captcha()
        if audio_path:
            with open(audio_path, 'rb') as audio:
                await update.message.reply_audio(audio=audio, caption="اسمع التسجيل وأرسل الأرقام.")
            return SOLVE_AUDIO_CAPTCHA
        else:
            await update_status("❌ لم يتم العثور على كابتشا صوتية.")
            if os.path.exists("captcha_debug.png"):
                with open("captcha_debug.png", "rb") as photo:
                    await update.message.reply_photo(photo=photo, caption="صورة توضح ما يراه البوت عند محاولة جلب الكابتشا.")
            await creator.close()
            return ConversationHandler.END
    except Exception as e:
        await update_status(f"❌ خطأ: {e}")
        if os.path.exists("debug_error.png"):
            with open("debug_error.png", "rb") as photo:
                await update.message.reply_photo(photo=photo, caption="صورة تشخيصية للخطأ.")
        await creator.close()
        return ConversationHandler.END

async def handle_audio_solution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    solution = update.message.text
    creator = context.user_data.get('creator')
    await update.message.reply_text("جاري إكمال الحساب... ⏳")
    success = await creator.complete_registration(solution)
    if success: await update.message.reply_text(f"✅ تم إنشاء الحساب بنجاح!\n{context.user_data['email']}")
    else:
        await update.message.reply_text("❌ فشل إكمال الحساب.")
        if os.path.exists("final_debug.png"):
            with open("final_debug.png", "rb") as photo:
                await update.message.reply_photo(photo=photo, caption="صورة تشخيصية للفشل النهائي.")
    await creator.close()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    creator = context.user_data.get('creator')
    if creator: await creator.close()
    await update.message.reply_text("تم الإلغاء.")
    return ConversationHandler.END

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('create', create_command)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_first_name)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_last_name)],
            SOLVE_AUDIO_CAPTCHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_audio_solution)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.run_polling()
