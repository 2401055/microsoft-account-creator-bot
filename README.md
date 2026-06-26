# Microsoft Account Creator Telegram Bot

هذا البوت يساعدك على إنشاء حسابات Microsoft (Outlook/Hotmail) من خلال واجهة تليجرام بسيطة.

## المميزات
- واجهة سهلة الاستخدام.
- جمع البيانات المطلوبة (البريد، كلمة المرور، الاسم).
- جاهز للاستضافة على **Railway**.

## متطلبات التشغيل
- Python 3.10+
- `python-telegram-bot`
- `playwright`

## الاستضافة على Railway
1. قم بربط حسابك في GitHub بموقع [Railway.app](https://railway.app/).
2. اختر "New Project" ثم "Deploy from GitHub repo".
3. اختر هذا المستودع.
4. أضف المتغيرات البيئية (Variables):
   - `TELEGRAM_TOKEN`: التوكن الخاص بك.
5. سيقوم Railway بتثبيت المتطلبات وتشغيل البوت تلقائياً.

## ملاحظة هامة
إنشاء حسابات مايكروسوفت يتطلب تجاوز نظام **Funcaptcha**. هذا الكود يوفر الهيكل الأساسي، ولتجاوز الكابتشا برمجياً ستحتاج لاستخدام خدمات مثل `2captcha` أو `Anti-Captcha`.
