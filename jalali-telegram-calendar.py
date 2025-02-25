import logging
import jdatetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# تنظیمات لاگ برای دیباگ کردن
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# توکن ربات تلگرام (جایگزین کنید با توکن خودتان)
BOT_TOKEN = "توکن ربات خود را اینجا قرار دهید"


async def start(update: Update, context):
    """نمایش تقویم هنگام شروع ربات"""
    await show_calendar(update, context)


async def show_calendar(update: Update, context):
    """نمایش تقویم"""
    today = jdatetime.date.today()
    calendar_markup = build_jalali_calendar(today.year, today.month)

    if update.message:
        await update.message.reply_text(
            "📅 لطفاً یک تاریخ را انتخاب کنید:", reply_markup=calendar_markup
        )
    else:
        await update.effective_message.reply_text(
            "📅 لطفاً یک تاریخ را انتخاب کنید:", reply_markup=calendar_markup
        )


def is_jalali_leap(jy):
    """بررسی سال کبیسه در تقویم جلالی"""
    epbase = jy - 474 if jy > 0 else jy - 473
    epyear = 474 + (epbase % 2820)
    return ((epyear * 682) % 2816) < 682


def get_jalali_month_days(year, month):
    """تعداد روزهای ماه شمسی"""
    if month <= 6:
        return 31
    elif month <= 11:
        return 30
    else:
        return 30 if is_jalali_leap(year) else 29


def build_jalali_calendar(year, month):
    """ساخت تقویم اینلاین برای انتخاب تاریخ"""
    persian_month_names = [
        "",
        "فروردین",
        "اردیبهشت",
        "خرداد",
        "تیر",
        "مرداد",
        "شهریور",
        "مهر",
        "آبان",
        "آذر",
        "دی",
        "بهمن",
        "اسفند",
    ]
    header = f"{persian_month_names[month]} {year}"

    keyboard = [[InlineKeyboardButton(header, callback_data="IGNORE")]]

    weekdays = ["ش", "ی", "د", "س", "چ", "پ", "ج"]
    keyboard.append(
        [InlineKeyboardButton(day, callback_data="IGNORE") for day in weekdays]
    )

    first_day = jdatetime.date(year, month, 1)
    offset = (first_day.togregorian().weekday() + 2) % 7  # محاسبه جایگاه اولین روز
    days_in_month = get_jalali_month_days(year, month)

    row = []
    for _ in range(offset):
        row.append(InlineKeyboardButton(" ", callback_data="IGNORE"))
    for day in range(1, days_in_month + 1):
        row.append(
            InlineKeyboardButton(
                str(day), callback_data=f"CALENDAR:{year}:{month}:{day}"
            )
        )
        if len(row) == 7:
            keyboard.append(row)
            row = []
    if row:
        while len(row) < 7:
            row.append(InlineKeyboardButton(" ", callback_data="IGNORE"))
        keyboard.append(row)

    prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
    next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)

    navigation_buttons = [
        InlineKeyboardButton(
            "◀️", callback_data=f"CALENDAR_NAV:{next_year}:{next_month}"
        ),
        InlineKeyboardButton("📆 امروز", callback_data="CALENDAR_TODAY"),
        InlineKeyboardButton(
            "▶️", callback_data=f"CALENDAR_NAV:{prev_year}:{prev_month}"
        ),
    ]
    keyboard.append(navigation_buttons)

    return InlineKeyboardMarkup(keyboard)


async def calendar_handler(update: Update, context):
    """مدیریت انتخاب تاریخ و ویرایش پیام تاریخ انتخاب شده"""
    query = update.callback_query
    data = query.data

    if data.startswith("CALENDAR_NAV:"):
        """جابجایی بین ماه‌ها"""
        _, year, month = data.split(":")
        new_calendar = build_jalali_calendar(int(year), int(month))

        # فقط دکمه‌های تقویم را ویرایش کن، بدون تغییر پیام
        await query.edit_message_reply_markup(reply_markup=new_calendar)

    elif data == "CALENDAR_TODAY":
        """انتخاب تاریخ امروز"""
        today = jdatetime.date.today()
        selected_date = f"{today.year}/{today.month:02d}/{today.day:02d}"
        await query.answer(f"📅 شما تاریخ {selected_date} را انتخاب کردید.")

        # بررسی اینکه آیا پیام قبلی ذخیره شده است یا نه
        if "last_selected_message" in context.user_data:
            # اگر پیام قبلی وجود دارد، ویرایش شود
            await context.user_data["last_selected_message"].edit_text(
                f"✅ تاریخ انتخاب شده: {selected_date}"
            )
        else:
            # اگر پیام قبلی وجود ندارد، یک پیام جدید ارسال شده و ذخیره شود
            sent_message = await query.message.reply_text(
                f"✅ تاریخ انتخاب شده: {selected_date}"
            )
            context.user_data["last_selected_message"] = (
                sent_message  # ذخیره پیام برای ویرایش بعدی
            )

    elif data.startswith("CALENDAR:"):
        """انتخاب یک تاریخ مشخص"""
        _, year, month, day = data.split(":")
        selected_date = f"{year}/{int(month):02d}/{int(day):02d}"
        await query.answer(f"📅 شما تاریخ {selected_date} را انتخاب کردید.")

        # بررسی اینکه آیا پیام قبلی ذخیره شده است یا نه
        if "last_selected_message" in context.user_data:
            # اگر پیام قبلی وجود دارد، ویرایش شود
            await context.user_data["last_selected_message"].edit_text(
                f"✅ تاریخ انتخاب شده: {selected_date}"
            )
        else:
            # اگر پیام قبلی وجود ندارد، یک پیام جدید ارسال شده و ذخیره شود
            sent_message = await query.message.reply_text(
                f"✅ تاریخ انتخاب شده: {selected_date}"
            )
            context.user_data["last_selected_message"] = (
                sent_message  # ذخیره پیام برای ویرایش بعدی
            )


def main():
    """راه‌اندازی ربات"""
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        CallbackQueryHandler(
            calendar_handler, pattern="^(CALENDAR|CALENDAR_NAV|CALENDAR_TODAY):?"
        )
    )
    app.run_polling()


if __name__ == "__main__":
    main()
