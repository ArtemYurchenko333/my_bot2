import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.helpers import escape_markdown

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Отримання токена бота з змінної оточення
TOKEN = os.getenv("BOT_TOKEN") 

# Словник для зберігання стану вибору користувача
# Наприклад: user_data[user_id] = {'color': 'Кольорові', 'size': '37-41', 'quantity': 5, 'phone_number': '+380...'}
user_selections = {}

# Цільові ID користувачів для відправки додаткового повідомлення
TARGET_USER_ID = os.getenv("TARGET_USER_ID")
TARGET_USER_ID_2 = os.getenv("TARGET_USER_ID_2") # Нова глобальна змінна для другого адміна

# --- Функції для відображення меню та обробки кроків ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Відправляє початкове повідомлення з кроками замовлення."""
    intro_message = (
        "Щоб Замовити Устілки потрібно виконати наступні кроки:\n\n"
        "1. Вибрати колір\n"
        "2. Вибрати розмір\n"
        "3. Вказати кількість\n"
        "4. Вказати номер телефону.\n\n"
        "Починаємо замовлення."
    )
    keyboard = [[InlineKeyboardButton("Почати замовлення", callback_data="start_order")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(intro_message, reply_markup=reply_markup)
    logger.info(f"Початкове повідомлення відправлено користувачу {update.effective_user.id}")

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Відправляє головне меню вибору кольору."""
    keyboard = [
        [InlineKeyboardButton("1) Кольорові", callback_data="select_color_Кольорові")],
        [InlineKeyboardButton("2) Натуральні", callback_data="select_color_Натуральні")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "Виберіть колір:", reply_markup=reply_markup
        )
        await update.callback_query.answer()
    else:
        if update.message:
            await update.message.reply_text("Виберіть колір:", reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text("Виберіть колір:", reply_markup=reply_markup)
            await update.callback_query.answer()
    
    logger.info(f"Головне меню відправлено користувачу {update.effective_user.id}")


async def send_size_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Відправляє меню вибору розміру."""
    query = update.callback_query
    await query.answer()

    color = query.data.replace("select_color_", "")
    user_selections[query.from_user.id] = {'color': color}
    logger.info(f"Користувач {query.from_user.id} вибрав колір: {color}")

    keyboard = [
        [InlineKeyboardButton("1) 29-33", callback_data="select_size_29-33")],
        [InlineKeyboardButton("2) 34-36", callback_data="select_size_34-36")],
        [InlineKeyboardButton("3) 37-41", callback_data="select_size_37-41")],
        [InlineKeyboardButton("4) 42-46", callback_data="select_size_42-46")],
        [InlineKeyboardButton("⬅️ Назад до кольору", callback_data="back_to_color_selection")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Виберіть розмір:", reply_markup=reply_markup)
    logger.info(f"Меню розмірів відправлено користувачу {query.from_user.id}")

async def ask_for_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Просить користувача ввести кількість пар."""
    query = update.callback_query
    await query.answer()

    size = query.data.replace("select_size_", "")
    user_selections[query.from_user.id]['size'] = size
    logger.info(f"Користувач {query.from_user.id} вибрав розмір: {size}")

    keyboard = [[InlineKeyboardButton("⬅️ Назад до розміру", callback_data="back_to_size_selection")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "Вкажіть кількість пар (введіть число):",
        reply_markup=reply_markup
    )
    context.user_data['awaiting_quantity'] = True
    logger.info(f"Запит кількості відправлено користувачу {update.effective_user.id}")


async def handle_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє введену користувачем кількість та запитує номер телефону."""
    user_id = update.effective_user.id

    if 'awaiting_quantity' not in context.user_data or not context.user_data['awaiting_quantity']:
        return

    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            raise ValueError
        
        user_selections[user_id]['quantity'] = quantity
        
        context.user_data['awaiting_quantity'] = False
        
        await ask_for_phone_number(update, context)

    except ValueError:
        await update.message.reply_text("Будь ласка, введіть дійсне число для кількості пар.")
        logger.warning(f"Невірний ввід кількості від {user_id}: {update.message.text}")


async def ask_for_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Просить користувача надати номер телефону."""
    keyboard = [[KeyboardButton("Надіслати мій номер телефону", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Тепер, будь ласка, надайте свій номер телефону.\n"
        "Ви можете використати кнопку нижче, щоб поділитися номером з профілю Telegram, або ввести його вручну.",
        reply_markup=reply_markup
    )
    context.user_data['awaiting_phone_number'] = True
    logger.info(f"Запит номера телефону відправлено користувачу {update.effective_user.id}")


async def handle_phone_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє отриманий номер телефону (від кнопки або вручну)."""
    user_id = update.effective_user.id

    if 'awaiting_phone_number' not in context.user_data or not context.user_data['awaiting_phone_number']:
        return

    phone_number = None
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        logger.info(f"Отримано номер телефону через кнопку від {user_id}: {phone_number}")
    elif update.message.text:
        phone_number = update.message.text
        logger.info(f"Отримано номер телефону вручну від {user_id}: {phone_number}")
    
    if phone_number:
        user_selections[user_id]['phone_number'] = phone_number
        context.user_data['awaiting_phone_number'] = False

        await update.message.reply_text(
            "Дякуємо! Ваше замовлення майже готове.",
            reply_markup=ReplyKeyboardRemove()
        )

        final_color = user_selections[user_id].get('color', 'не вибрано')
        final_size = user_selections[user_id].get('size', 'не вибрано')
        final_quantity = user_selections[user_id].get('quantity', 'не вказано')
        final_phone_number = user_selections[user_id].get('phone_number', 'не вказано')

        summary_text = (
            f"**Ви купуєте:**\n"
            f"Колір: **{final_color}**\n"
            f"Розмір: **{final_size}**\n"
            f"Кількість пар: **{final_quantity}**\n"
            f"Номер телефону: **{final_phone_number}**"
        )
        await update.message.reply_text(summary_text, parse_mode='Markdown')
        logger.info(f"Підсумок покупки для {user_id}: Колір={final_color}, Розмір={final_size}, Кількість={final_quantity}, Телефон={final_phone_number}")

        user_info = f"ID: {user_id}"
        if update.effective_user.username:
            user_info += f", Логін: @{escape_markdown(update.effective_user.username, version=2)}"
        if update.effective_user.first_name:
            user_info += f", Ім'я: {escape_markdown(update.effective_user.first_name, version=2)}"
        if update.effective_user.last_name:
            user_info += f", Прізвище: {escape_markdown(update.effective_user.last_name, version=2)}"
        
        telegram_contact_phone = None
        if update.message.contact and update.message.contact.phone_number:
            telegram_contact_phone = update.message.contact.phone_number

        admin_summary_text = (
            f"**Нове замовлення від користувача \\({user_info}\\):**\n"
            f"Колір: **{escape_markdown(final_color, version=2)}**\n"
            f"Розмір: **{escape_markdown(final_size, version=2)}**\n"
            f"Кількість пар: **{escape_markdown(str(final_quantity), version=2)}**\n"
            f"Наданий номер телефону: **{escape_markdown(final_phone_number, version=2)}**\n"
        )
        if telegram_contact_phone and telegram_contact_phone != final_phone_number:
            admin_summary_text += f"Номер телефону з профілю Telegram: **{escape_markdown(telegram_contact_phone, version=2)}**"
        elif telegram_contact_phone:
             admin_summary_text += f"Номер телефону (з профілю Telegram): **{escape_markdown(telegram_contact_phone, version=2)}**"

        if TARGET_USER_ID:
            try:
                await context.bot.send_message(chat_id=TARGET_USER_ID, text=admin_summary_text, parse_mode='MarkdownV2')
                logger.info(f"Повідомлення про замовлення відправлено користувачу {TARGET_USER_ID}")
            except Exception as e:
                logger.error(f"Не вдалося відправити повідомлення користувачу {TARGET_USER_ID}: {e}")
        else:
            logger.warning("TARGET_USER_ID не встановлено. Повідомлення першому адміну не відправлено.")

        if TARGET_USER_ID_2:
            try:
                await context.bot.send_message(chat_id=TARGET_USER_ID_2, text=admin_summary_text, parse_mode='MarkdownV2')
                logger.info(f"Повідомлення про замовлення відправлено користувачу {TARGET_USER_ID_2}")
            except Exception as e:
                logger.error(f"Не вдалося відправити повідомлення користувачу {TARGET_USER_ID_2}: {e}")
        else:
            logger.warning("TARGET_USER_ID_2 не встановлено. Повідомлення другому адміну не відправлено.")

        if user_id in user_selections:
            del user_selections[user_id]
        
        keyboard = [[InlineKeyboardButton("Почати спочатку", callback_data="start_over")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Дякуємо за покупку!", reply_markup=reply_markup)

    else:
        await update.message.reply_text("Будь ласка, надайте дійсний номер телефону, використовуючи кнопку або ввівши його вручну.")
        logger.warning(f"Невірний ввід номера телефону від {user_id}")


async def back_to_color_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Повертає до вибору кольору."""
    await send_main_menu(update, context)
    logger.info(f"Користувач {update.effective_user.id} повернувся до вибору кольору.")

async def back_to_size_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Повертає до вибору розміру."""
    user_id = update.effective_user.id
    current_color = user_selections.get(user_id, {}).get('color')

    if current_color:
        keyboard = [
            [InlineKeyboardButton("1) 29-33", callback_data="select_size_29-33")],
            [InlineKeyboardButton("2) 34-36", callback_data="select_size_34-36")],
            [InlineKeyboardButton("3) 37-41", callback_data="select_size_37-41")],
            [InlineKeyboardButton("4) 42-46", callback_data="select_size_42-46")],
            [InlineKeyboardButton("⬅️ Назад до кольору", callback_data="back_to_color_selection")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Виберіть розмір:", reply_markup=reply_markup)
        logger.info(f"Користувач {user_id} повернувся до вибору розміру.")
    else:
        await send_main_menu(update, context)


# --- Функція запуску бота ---
def main() -> None:
    """Запускає бота."""
    if not TOKEN:
        logger.error("BOT_TOKEN environment variable not set. Please set it.")
        print("Помилка: Токен бота не встановлено. Будь ласка, встановіть BOT_TOKEN у змінних середовища.")
        exit(1)

    application = ApplicationBuilder().token(TOKEN).build()

    # Обробник команди /start - тепер він показує інтро
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(send_main_menu, pattern="^start_order$"))
    application.add_handler(CallbackQueryHandler(start_command, pattern="^start_over$"))

    # Обробники вибору кольору
    application.add_handler(CallbackQueryHandler(send_size_menu, pattern="^select_color_"))

    # Обробники вибору розміру
    application.add_handler(CallbackQueryHandler(ask_for_quantity, pattern="^select_size_"))

    # Обробник текстових повідомлень для введення кількості
    # ВИПРАВЛЕННЯ: filters.PRIVATE_CHAT на filters.private
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.private & filters.User(lambda user: user.id in user_selections and context.user_data.get('awaiting_quantity')),
        handle_quantity_input)
    )
    
    # Обробник для отримання номера телефону (кнопка або ручне введення)
    # ВИПРАВЛЕННЯ: filters.PRIVATE_CHAT на filters.private
    application.add_handler(MessageHandler(
        (filters.CONTACT | filters.TEXT) & filters.private & filters.User(lambda user: user.id in user_selections and context.user_data.get('awaiting_phone_number')),
        handle_phone_number_input)
    )

    # Обробники кнопок "Назад"
    application.add_handler(CallbackQueryHandler(back_to_color_selection, pattern="^back_to_color_selection$"))
    application.add_handler(CallbackQueryHandler(back_to_size_selection, pattern="^back_to_size_selection$"))

    print("Бот запущено в режимі Polling...")
    logger.info("Бот запущено в режимі Polling. Очікування оновлень...")
    application.run_polling()

if __name__ == "__main__":
    main()
