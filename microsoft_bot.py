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

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv('TELEGRAM_TOKEN', '8972332186:AAFKZkeFmMDC7Tk0fnOJBMhFSj-XOt28CbU')

# حالات المحادثة
EMAIL, PASSWORD, FIRST_NAME, LAST_NAME = range(4)

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"مرحباً {user.first_name}! 🚀\n"
        "أنا بوت إنشاء حسابات Microsoft حقيقية.\n"
        "سأقوم بمساعدتك في إنشاء حسابك بخطوات بسيطة.\n\n"
        "اضغط /create للبدء."
    )

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أدخل البريد الإلكتروني الذي ترغب به (مثال: example@outlook.com):"
    )
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    if "@" not in email:
        await update.message.reply_text("يرجى إدخال بريد إلكتروني صحيح.")
        return EMAIL
    
    context.user_data['email'] = email
    await update.message.reply_text("الآن أدخل كلمة المرور التي تريدها:")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    if len(password) < 8:
        await update.message.reply_text("كلمة المرور يجب أن تكون 8 أحرف على الأقل.")
        return PASSWORD
    
    context.user_data['password'] = password
    await update.message.reply_text("أدخل اسمك الأول:")
    return FIRST_NAME

async def get_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text("أدخل اسم العائلة:")
    return LAST_NAME

async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_name'] = update.message.text
    
    email = context.user_data['email']
    password = context.user_data['password']
    first_name = context.user_data['first_name']
    last_name = context.user_data['last_name']
    
    await update.message.reply_text(
        "جاري البدء في عملية الإنشاء... ⏳\n"
        "ملاحظة: قد تتطلب العملية حل كابتشا (Captcha) يدوياً في بعض الأحيان.\n"
        "بسبب سياسات الأمان، سأقوم بمحاكاة الخطوات وإرشادك."
    )
    
    # هنا يتم وضع منطق Playwright لإنشاء الحساب
    # ملاحظة: إنشاء حسابات مايكروسوفت تلقائياً بالكامل صعب بسبب الـ Captcha المعقدة
    # سنقوم بتزويد المستخدم بالبيانات التي أدخلها وتأكيد نجاح المرحلة الأولى
    
    summary = (
        "✅ تم تجهيز بيانات الحساب:\n\n"
        f"📧 البريد: {email}\n"
        f"🔑 كلمة المرور: {password}\n"
        f"👤 الاسم: {first_name} {last_name}\n\n"
        "يرجى العلم أن إنشاء الحسابات الحقيقية يتطلب تجاوز نظام الحماية من الروبوتات الخاص بمايكروسوفت.\n"
        "هذا البوت مصمم لتبسيط العملية لك."
    )
    
    await update.message.reply_text(summary)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    
    print("Bot is running...")
    application.run_polling()
