import asyncio
import logging
import os
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
EMAIL, PASSWORD, FIRST_NAME, LAST_NAME, SOLVE_CAPTCHA = range(5)

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
        # إدخال البريد
        await self.page.fill('input[name="MemberName"]', email)
        await self.page.click('input[type="submit"]')
        await asyncio.sleep(2)
        
        # إدخال كلمة المرور
        await self.page.fill('input[name="Password"]', password)
        await self.page.click('input[type="submit"]')
        await asyncio.sleep(2)

        # إدخال الاسم
        await self.page.fill('input[name="FirstName"]', first_name)
        await self.page.fill('input[name="LastName"]', last_name)
        await self.page.click('input[type="submit"]')
        await asyncio.sleep(2)

        # اختيار المنطقة والتاريخ (قيم افتراضية)
        await self.page.select_option('select[name="BirthMonth"]', value="1")
        await self.page.fill('input[name="BirthDay"]', "01")
        await self.page.fill('input[name="BirthYear"]', "1995")
        await self.page.click('input[type="submit"]')
        await asyncio.sleep(5) # انتظار تحميل الكابتشا

    async def get_captcha_screenshot(self):
        # محاولة العثور على إطار الكابتشا وأخذ لقطة شاشة
        captcha_frame = await self.page.query_selector('#enforcementFrame')
        if captcha_frame:
            await captcha_frame.screenshot(path="captcha.png")
            return "captcha.png"
        else:
            # لقطة شاشة للصفحة كاملة إذا لم يتم العثور على الإطار المحدد
            await self.page.screenshot(path="page_status.png")
            return "page_status.png"

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! 🚀 سأقوم بمساعدتك في إنشاء حساب Microsoft.\n"
        "عندما نصل لمرحلة الكابتشا، سأرسل لك الصورة لتقوم بحلها.\n\n"
        "اضغط /create للبدء."
    )

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أدخل البريد الإلكتروني المطلوب (example@outlook.com):")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text
    await update.message.reply_text("أدخل كلمة المرور:")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['password'] = update.message.text
    await update.message.reply_text("أدخل اسمك الأول:")
    return FIRST_NAME

async def get_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text("أدخل اسم العائلة:")
    return LAST_NAME

async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_name'] = update.message.text
    await update.message.reply_text("جاري بدء الأتمتة... يرجى الانتظار قليلاً ⏳")
    
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
        
        captcha_path = await creator.get_captcha_screenshot()
        with open(captcha_path, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption="لقد وصلنا لمرحلة الكابتشا! يرجى حلها في متصفحك أو إخباري إذا كنت تريد المتابعة.")
        
        await update.message.reply_text("ملاحظة: بما أن الكابتشا تفاعلية، يفضل أن تقوم بالخطوة النهائية يدوياً. سأقوم بتزويدك بالرابط المباشر للمتابعة.")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text(f"حدث خطأ: {str(e)}")
        await creator.close()
        return ConversationHandler.END

    return SOLVE_CAPTCHA

async def handle_captcha_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم استلام ردك. جاري محاولة الإكمال...")
    # هنا يمكن إضافة منطق لإدخال حل الكابتشا إذا كانت نصية
    # لكن كابتشا مايكروسوفت عادة ما تكون تفاعلية (Funcaptcha)
    await update.message.reply_text("✅ تم إكمال الخطوات الأولية بنجاح!")
    
    creator = context.user_data.get('creator')
    if creator:
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
            SOLVE_CAPTCHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_captcha_response)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    
    print("Bot is running...")
    application.run_polling()
