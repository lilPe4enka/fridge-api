import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Вставьте сюда токен, полученный от @BotFather
BOT_TOKEN = "8972987041:AAHTwVh2FP0Z6L0IAhJbceSODGHXeA1cy-0"
# Ссылка на ваш Frontend (пока можно поставить любую для теста)
WEB_APP_URL = "https://heartfelt-marshmallow-bd176b.netlify.app/?v=2.2"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Список случайных советов для кнопки
CHEF_TIPS = [
    "💡 *Совет:* Чтобы макароны не слипались, варите их в большом количестве воды (1 литр на 100 г) и не промывайте холодной водой после!",
    "💡 *Совет:* Если пересолили суп, положите в него очищенную целую картофелину на 10-15 минут — она впитает лишнюю соль.",
    "💡 *Совет:* Чтобы мясо при жарке было сочным, не выкладывайте его из холодильника сразу на сковороду. Дайте ему полежать 15 минут при комнатной температуре.",
    "💡 *Совет:* Свежая зелень дольше сохранится, если поставить ее в стакан с водой, как букет цветов, и убрать в холодильник."
]

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    
    # Главная кнопка Web App
    builder.button(
        text="Открой холодильник 🧊",
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    # Дополнительные Inline-кнопки (callback_data - это скрытый код, который получит бот при нажатии)
    builder.button(text="Как это работает? ❓", callback_data="help")
    builder.button(text="Совет от шефа 💡", callback_data="tip")
    
    # Настраиваем расположение кнопок: 1 в первом ряду, 2 во втором ряду
    builder.adjust(1, 2)
    
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я — твой умный кулинарный помощник. Не знаешь, что приготовить из того, что завалялось в холодильнике? Я помогу!\n\n"
        "Нажми на главную кнопку ниже, чтобы начать ⬇️"
    )
    
    await message.answer(
        text=welcome_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# Обработчик нажатия на кнопку "Как это работает?"
@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    help_text = (
        "🛠 *Как пользоваться приложением:*\n\n"
        "1. Нажми кнопку «Открой холодильник».\n"
        "2. Выбери продукты, которые у тебя сейчас есть.\n"
        "3. Выбери желаемое время готовки.\n"
        "4. Нажми «Найти рецепты» и подожди пару секунд.\n"
        "5. Нейросеть придумает блюда, посчитает калории и составит список того, чего не хватает!\n\n"
        "Понравился рецепт? Нажми на ❤️, и он сохранится в облаке."
    )
    # Отправляем сообщение в чат
    await callback.message.answer(help_text, parse_mode="Markdown")
    # Обязательно "закрываем" callback, чтобы на кнопке не крутились часики загрузки
    await callback.answer()

# Обработчик нажатия на кнопку "Совет от шефа"
@dp.callback_query(F.data == "tip")
async def tip_callback(callback: CallbackQuery):
    # Выбираем случайный совет из списка
    random_tip = random.choice(CHEF_TIPS)
    
    await callback.message.answer(random_tip, parse_mode="Markdown")
    # Можно отправить всплывающее уведомление (alert) прямо поверх кнопок!
    await callback.answer("Приятного аппетита! 👨‍🍳")

async def main():
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())