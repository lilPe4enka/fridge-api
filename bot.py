import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Вставьте сюда токен, полученный от @BotFather
BOT_TOKEN = "8972987041:AAHTwVh2FP0Z6L0IAhJbceSODGHXeA1cy-0"
# Ссылка на ваш Frontend (пока можно поставить любую для теста)
WEB_APP_URL = "https://heartfelt-marshmallow-bd176b.netlify.app/?v=4"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Создаем кнопку, открывающую Mini App
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Открой холодильник 🧊",
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    
    await message.answer(
        "Привет! Нажми на кнопку ниже, отметь, что у тебя есть в холодильнике, и я подберу рецепт!",
        reply_markup=builder.as_markup()
    )

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())