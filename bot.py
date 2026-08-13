import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Вставьте сюда токен, полученный от @BotFather
BOT_TOKEN = "8972987041:AAHTwVh2FP0Z6L0IAhJbceSODGHXeA1cy-0"
# Ссылка на ваш Frontend (пока можно поставить любую для теста)
WEB_APP_URL = "https://lilpe4enka.github.io/fridge-api/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    
    # 1. Главная кнопка открытия Web App
    builder.button(
        text="Открыть холодильник 🧊",
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    
    # 2. Дополнительные Inline-кнопки
    builder.button(text="❤️ Избранные", callback_data="favorites")
    builder.button(text="🛒 Список покупок", callback_data="shopping_list")
    
    # Настраиваем сетку: 1 кнопка в 1 ряду, 2 кнопки во 2 ряду
    builder.adjust(1, 2)
    
    welcome_text = "Приветствую! Если вы не знаете, что приготовить из продуктов, имеющихся у вас в холодильнике, этот бот создан специально для вас! 🍳🤖"
    
    await message.answer(
        text=welcome_text,
        reply_markup=builder.as_markup()
    )

# Обработчик кнопки "Избранные"
@dp.callback_query(F.data == "favorites")
async def favorites_callback(callback: CallbackQuery):
    text = (
        "Ваши любимые рецепты надежно сохранены! 📱\n\n"
        "Чтобы посмотреть их, нажмите на кнопку «Открыть холодильник» и кликните на **«❤️ Избранное»** в правом верхнем углу экрана."
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# Обработчик кнопки "Список покупок"
@dp.callback_query(F.data == "shopping_list")
async def shopping_list_callback(callback: CallbackQuery):
    text = (
        "Список покупок создается автоматически с помощью нейросети! 🛒\n\n"
        "Откройте приложение, выберите продукты, которые у вас уже есть, и бот сам составит список того, что нужно докупить для идеального блюда."
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

async def main():
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
