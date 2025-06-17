import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.helpers import escape_markdown 

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Отримання токена бота з змінної оточення
TOKEN = os.getenv("BOT_TOKEN")

user_selections = {}

TARGET_USER_ID = os.getenv("TARGET_USER_ID")
TARGET_USER_ID_2 = os.getenv("TARGET_USER_ID_2") 

# --- Функції для відображення меню ---

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Відправляє головне меню вибору кольору."""
    keyboard = [
        [InlineKeyboardButton("1) Кольорові", callback_data="select_color_Кольорові")],
        [InlineKeyboardButton("2) Натуральні", callback_data="select_color_Натуральні")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Оновлений список кроків
    initial_message = (
        "Щоб Замовити Устілки потрібно виконати наступні кроки:\n"
        "1\\. Вибрати колір\n"
        "2\\. Вибрати розмір\n"
        "3\\. Вказати кількість\n\n" # Прибрано кроки 4 і 5
        "Починаємо замовлення\\!"
    )

    if update.callback_query: 
        await update.callback_query.edit_message_text(
            initial_message, reply_markup=reply_markup, parse_mode='MarkdownV2'
        )
        await update.callback_query.answer()
    else: 
        await update.message.reply_text(initial_message, reply_markup=reply_markup, parse_mode='MarkdownV2')
    logger.info(f"Головне меню відправлено користувачу {update.effective_user.id}")


async def send_size_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Відправляє меню вибору розміру."""
    query = update.callback_query
    await query.answer()

    color = query.data.replace("select_color_", "")
    user_selections.setdefault(query.from_user.id, {})['color'] = color
    logger.info(f"Користувач {query.from_user.id} вибрав колір: {color}")


    keyboard = [
        [InlineKeyboardButton("1) 29-33", callback_data="select_size_29-33")],
        [InlineKeyboardButton("2) 34-36", callback_data="select_size_34-36")],
        [InlineKeyboardButton("3) 37-41", callback_data="select_size_37-41")],
        [InlineKeyboardButton("4) Тільки для вас 47 розмір !", callback_data="select_size_47")],
        [InlineKeyboardButton("5) 42-46", callback_data="select_size_42-46")],
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
    user_selections.setdefault(query.from_user.id, {})['size'] = size
    logger.info(f"Користувач {query.from_user.id} вибрав розмір: {size}")

    keyboard = [[InlineKeyboardButton("⬅️ Назад до розміру", callback_data="back_to_size_selection")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "Вкажіть кількість пар (введіть число):",
        reply_markup=reply_markup
    )
    context.user_data['awaiting_quantity'] = True
    # Ці прапори тепер не потрібні, але можна залишити для очищення
    context.user_data['awaiting_contact_method'] = False 
    context.user_data['awaiting_phone_number'] = False 
    logger.info(f"Запит кількості відправлено користувачу {query.from_user.id}")

async def handle_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє введену користувачем кількість та завершує замовлення."""
    logger.info(f"handle_quantity_input викликано для {update.effective_user.id}. awaiting_quantity: {context.user_data.get('awaiting_quantity')}")

    if 'awaiting_quantity' not in context.user_data or not context.user_data['awaiting_quantity']:
        logger.warning(f"handle_quantity_input спрацював, але прапор awaiting_quantity не встановлений для {update.effective_user.id}. Ігноруємо повідомлення.")
        return 

    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            raise ValueError
        
        user_id = update.effective_user.id
        user_selections[user_id]['quantity'] = quantity
        
        context.user_data['awaiting_quantity'] = False
        logger.info(f"Кількість '{quantity}' збережено. Прапор awaiting_quantity вимкнено.")

        # --- Логіка завершення замовлення, перенесена з handle_phone_number_input ---
        final_color = user_selections[user_id].get('color', 'не вибрано')
        final_size = user_selections[user_id].get('size', 'не вибрано')
        final_quantity = user_selections[user_id].get('quantity', 'не вказано')
        # Спосіб зв'язку та номер телефону більше не запитуються, тому не включаємо їх у підсумок
        
        summary_text = (
            f"**Ви купуєте:**\n"
            f"Колір: **{final_color}**\n"
            f"Розмір: **{final_size}**\n"
            f"Кількість пар: **{final_quantity}**\n"
        )
        await update.message.reply_text(summary_text, parse_mode='Markdown')
        logger.info(f"Підсумок покупки для {user_id}: Колір={final_color}, Розмір={final_size}, Кількість={final_quantity}")

        user_info = f"ID: {user_id}"
        if update.effective_user.username:
            user_info += f", Логін: @{escape_markdown(update.effective_user.username, version=2)}"
        if update.effective_user.first_name:
            user_info += f", Ім'я: {escape_markdown(update.effective_user.first_name, version=2)}"
        if update.effective_user.last_name:
            user_info += f", Прізвище: {escape_markdown(update.effective_user.last_name, version=2)}"

        admin_summary_text = (
            f"**Нове замовлення від користувача \\({user_info}\\):**\n"
            f"Колір: **{escape_markdown(final_color, version=2)}**\n"
            f"Розмір: **{escape_markdown(final_size, version=2)}**\n"
            f"Кількість пар: **{escape_markdown(str(final_quantity), version=2)}**\n"
        )

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
        logger.info(f"Вибір користувача {user_id} очищено.")
        
        keyboard = [[InlineKeyboardButton("Почати спочатку", callback_data="start_over")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Дякуємо за покупку!", reply_markup=reply_markup)
        logger.info(f"Заключне повідомлення відправлено користувачу {user_id}.")

    except ValueError:
        await update.message.reply_text("Будь ласка, введіть дійсне число для кількості пар.")
        logger.warning(f"Невірний ввід кількості від {update.effective_user.id}: {update.message.text}")
    except Exception as e:
        logger.error(f"Невідома помилка під час обробки кількості або завершення замовлення для {user_id}: {e}", exc_info=True)
        await update.message.reply_text("Виникла помилка при обробці вашого замовлення. Спробуйте почати спочатку.")


# --- Обробники кнопок "Назад" ---
# Усі прапори awaiting_* в context.user_data мають бути скинуті при переході назад або на /start
async def back_to_color_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in user_selections:
        del user_selections[user_id]
    context.user_data['awaiting_quantity'] = False
    context.user_data['awaiting_contact_method'] = False # Очищуємо прапори
    context.user_data['awaiting_phone_number'] = False
    await send_main_menu(update, context)
    logger.info(f"Користувач {update.effective_user.id} повернувся до вибору кольору.")

async def back_to_size_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_color = user_selections[user_id]['color'] if user_id in user_selections and 'color' in user_selections[user_id] else None

    if current_color:
        keyboard = [
            [InlineKeyboardButton("1) 29-33", callback_data="select_size_29-33")],
            [InlineKeyboardButton("2) 34-36", callback_data="select_size_34-36")],
            [InlineKeyboardButton("3) 37-41", callback_data="select_size_37-41")],
            [InlineKeyboardButton("4) Тільки для вас 47 розмір !", callback_data="select_size_47")],
            [InlineKeyboardButton("5) 42-46", callback_data="select_size_42-46")],
            [InlineKeyboardButton("⬅️ Назад до кольору", callback_data="back_to_color_selection")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Виберіть розмір:", reply_markup=reply_markup)
        context.user_data['awaiting_quantity'] = False
        context.user_data['awaiting_contact_method'] = False # Очищуємо прапори
        context.user_data['awaiting_phone_number'] = False

        logger.info(f"Користувач {user_id} повернувся до вибору розміру.")
    else:
        await send_main_menu(update, context)

# Кнопка "Назад до кількості" залишається, але тепер це останній крок перед завершенням
async def back_to_quantity_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_color = user_selections[user_id].get('color')
    current_size = user_selections[user_id].get('size')

    if current_color and current_size:
        keyboard = [[InlineKeyboardButton("⬅️ Назад до розміру", callback_data="back_to_size_selection")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "Вкажіть кількість пар (введіть число):",
            reply_markup=reply_markup
        )
        context.user_data['awaiting_quantity'] = True
        context.user_data['awaiting_contact_method'] = False 
        context.user_data['awaiting_phone_number'] = False

        logger.info(f"Користувач {user_id} повернувся до запиту кількості.")
    else:
        await send_main_menu(update, context)

# --- Функція запуску бота ---
def main() -> None:
    """Запускає бота."""
    if not TOKEN:
        logger.error("BOT_TOKEN environment variable not set. Please set it in Render dashboard.")
        print("Помилка: Токен бота не встановлено. Будь ласка, встановіть BOT_TOKEN у змінних середовища Render.")
        exit(1)

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", send_main_menu))
    application.add_handler(CallbackQueryHandler(send_main_menu, pattern="^start_over$"))

    application.add_handler(CallbackQueryHandler(send_size_menu, pattern="^select_color_"))
    application.add_handler(CallbackQueryHandler(ask_for_quantity, pattern="^select_size_"))

    # ВИДАЛЕНО: Обробники для способу зв'язку та номера телефону (як окремі кроки)
    # application.add_handler(CallbackQueryHandler(handle_contact_method_selection, pattern="^contact_method_"))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_phone_number_input))
    
    # Обробник текстових повідомлень для введення кількості - тепер він також завершує замовлення
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_quantity_input
    ))


    application.add_handler(CallbackQueryHandler(back_to_color_selection, pattern="^back_to_color_selection$"))
    application.add_handler(CallbackQueryHandler(back_to_size_selection, pattern="^back_to_size_selection$"))
    application.add_handler(CallbackQueryHandler(back_to_quantity_selection, pattern="^back_to_quantity_selection$"))
    # ВИДАЛЕНО: Обробник кнопки "Назад" для способу зв'язку
    # application.add_handler(CallbackQueryHandler(back_to_contact_method_selection, pattern="^back_to_contact_method_selection$"))


    print("Бот запущено в режимі Polling...")
    logger.info("Бот запущено в режимі Polling. Очікування оновлень...")
    application.run_polling()

if __name__ == "__main__":
    main()
