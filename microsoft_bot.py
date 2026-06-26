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
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start_session(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True, args=['--no-sandbox'])
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def fill_initial_info(self, email, password, first_name, last_name):
        await self.page.goto("https://signup.live.com/signup")
        await self.page.fill('input[name="MemberName"]', email)
        await self.page.click('input[type="submit"]')
        await asyncio.sleep(2)
        
        await self.page.fill('input[name="Password"]', password)
        await self.page.click('input[type="submit"]')
        await asyncio.sleep(2)

        await self.page.fill('input[name="FirstName"]', first_name)
        await self.page.fill('input[name="LastName"]', last_name)
        await self.page.click('input[type="submit"]')
        await asyncio.sleep(2)

        await self.page.select_option('select[name="BirthMonth"]', value="1")
        await self.page.fill('input[name="BirthDay"]', "01")
        await self.page.fill('input[name="BirthYear"]', "1995")
        await self.page.click('input[type="submit"]')
        await asyncio.sleep(5)

    async def get_audio_captcha(self):
        # محاولة التبديل للكابتشا الصوتية
        try:
            # البحث عن زر الكابتشا الصوتية (غالباً ما يكون أيقونة سماعة)
            audio_btn = await self.page.query_selector('button[aria-label="Get an audio challenge"]')
            if audio_btn:
                await audio_btn.click()
                await asyncio.sleep(3)
                
                # البحث عن رابط تحميل الملف الصوتي
                download_link = await self.page.query_selector('a[href*="audio"]')
                if download_link:
                    url = await download_link.get_attribute('href')
                    response = requests.get(url)
                    with open("captcha_audio.wav", "wb") as f:
                        f.write(response.content)
                    return "captcha_audio.wav"
        except Exception as e:
            logging.error(f"Audio Captcha Error: {e}")
        return None

    async def submit_audio_solution(self, solution):
        try:
            input_field = await self.page.query_selector('input[aria-label="Type the numbers you hear"]')
            if input_field:
                await input_field.fill(solution)
                await self.page.click('button:has-text("Verify")')
                await asyncio.sleep(3)
                return True
        except Exception as e:
            logging.error(f"Submit Error: {e}")
        return False

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! سأرسل لك الكابتشا كـ Record لتسمعها وترسل لي الأرقام.")

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
    await update.message.reply_text("جاري تجهيز الكابتشا الصوتية... ⏳")
    
    creator = MicrosoftCreator()
    context.user_data['creator'] = creator
    
    try:
        await creator.start_session()
        await creator.fill_initial_info(
            context.user_data['email'],
            context.user_data['password'],
            context.user_data['first_name'],
            context.user_data['last_name']
        )
        
        audio_path = await creator.get_audio_captcha()
        if audio_path:
            with open(audio_path, 'rb') as audio:
                await update.message.reply_audio(audio=audio, caption="اسمع التسجيل وأرسل لي الأرقام التي سمعتها.")
            return SOLVE_AUDIO_CAPTCHA
        else:
            await update.message.reply_text("لم أتمكن من العثور على كابتشا صوتية، قد تكون الصفحة تطلب كابتشا مرئية فقط حالياً.")
            await creator.close()
            return ConversationHandler.END
            
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")
        await creator.close()
        return ConversationHandler.END

async def handle_audio_solution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    solution = update.message.text
    creator = context.user_data.get('creator')
    
    await update.message.reply_text("جاري التحقق من الحل... ⏳")
    success = await creator.submit_audio_solution(solution)
    
    if success:
        await update.message.reply_text("✅ تم التحقق بنجاح! جاري إكمال إنشاء الحساب.")
    else:
        await update.message.reply_text("❌ فشل التحقق، يرجى المحاولة مرة أخرى.")
    
    await creator.close()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    creator = context.user_data.get('creator')
    if creator:
        await creator.close()
    await update.message.reply_text("تم إلغاء العملية.")
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
    
    print("Bot is running...")
    application.run_polling()
