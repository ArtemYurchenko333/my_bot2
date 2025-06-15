# ... (весь ваш попередній код) ...

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

    application.add_handler(CallbackQueryHandler(handle_contact_method_selection, pattern="^contact_method_"))
    
    # *** ЗМІНЕНИЙ ПОРЯДОК ОБРОБНИКІВ ТЕКСТУ ***
    # Обробник для номера телефону повинен бути ПЕРШИМ, оскільки це останній текстовий ввід у послідовності.
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_phone_number_input
    ))
    
    # Обробник для кількості - ДРУГИЙ.
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_quantity_input
    ))
    # *****************************************


    application.add_handler(CallbackQueryHandler(back_to_color_selection, pattern="^back_to_color_selection$"))
    application.add_handler(CallbackQueryHandler(back_to_size_selection, pattern="^back_to_size_selection$"))
    application.add_handler(CallbackQueryHandler(back_to_quantity_selection, pattern="^back_to_quantity_selection$"))
    application.add_handler(CallbackQueryHandler(back_to_contact_method_selection, pattern="^back_to_contact_method_selection$"))


    print("Бот запущено в режимі Polling...")
    logger.info("Бот запущено в режимі Polling. Очікування оновлень...")
    application.run_polling()

if __name__ == "__main__":
    main()
