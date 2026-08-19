import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from aiogram import Bot

from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot = Bot(token=BOT_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

INGREDIENTS_MAP = {
    1: "Яйца", 3: "Сливочное масло", 9: "Твердый сыр", 10: "Молоко",
    16: "Сметана", 27: "Сливки", 33: "Творог", 42: "Кефир", 53: "Сгущенка",
    68: "Моцарелла / Сыр для пиццы", 69: "Плавленый сырок",
    54: "Куриное филе (грудка)", 55: "Куриные бедра / голени", 56: "Куриные крылышки", 57: "Целая курица",
    58: "Свиная шея / мякоть", 59: "Свиная вырезка / карбонад", 60: "Свиные ребрышки",
    61: "Говяжья мякоть / вырезка", 62: "Говяжий стейк",
    63: "Куриный фарш", 64: "Говяжий фарш", 65: "Свиной фарш", 66: "Домашний фарш (свинина + говядина)",
    21: "Ветчина", 28: "Бекон", 35: "Сосиски / Сардельки", 44: "Колбаса (вареная/копченая)",
    29: "Красная рыба (лосось/форель)", 30: "Креветки", 46: "Крабовые палочки",
    50: "Рыбные консервы / Тунец", 67: "Белая рыба (минтай/треска)",
    5: "Картошка", 6: "Лук репчатый", 11: "Морковь", 12: "Чеснок", 17: "Капуста белокочанная",
    18: "Болгарский перец", 19: "Свежие огурцы", 20: "Зелень (укроп/петрушка)", 25: "Помидоры",
    26: "Грибы (шампиньоны)", 37: "Брокколи / Цветная капуста", 70: "Кабачки / Цукини",
    71: "Баклажаны", 72: "Свекла", 73: "Зеленый лук", 75: "Соленые / маринованные огурцы",
    4: "Мука", 8: "Макароны / Спагетти", 13: "Рис", 23: "Гречка", 34: "Хлеб / Батон",
    41: "Овсянка / Геркулес", 45: "Пельмени / Вареники", 49: "Замороженные овощи",
    74: "Лаваш / Тортилья",
    31: "Лимон", 32: "Яблоки", 36: "Консервированная фасоль", 38: "Майонез",
    39: "Томатная паста / Кетчуп", 40: "Растительное масло", 43: "Соевый соус",
    47: "Консервированная кукуруза", 48: "Консервированный горошек", 51: "Горчица",
    52: "Сахар", 76: "Мёд"
}

# Обновленная модель: добавили калории и режим готовки
class RecipeRequest(BaseModel):
    ingredient_ids: List[int]
    excluded_ids: Optional[List[int]] = []
    time_limit: int
    calorie_limit: int
    cooking_mode: str

class SendBotRequest(BaseModel):
    user_id: int
    text: str

SYSTEM_PROMPT = """
Ты — профессиональный шеф-повар. 
СТРОГИЕ ПРАВИЛА:
1. Указывай точные граммовки. Жидкости от 1000 мл измеряй в литрах.
2. Шаги должны содержать точное время (в минутах) и температуру.
3. Категорически не используй запрещенные продукты и их аналоги.
4. В missing_ingredients добавляй недостающие продукты, но НИКОГДА не добавляй воду, соль, черный перец и базовые специи.

Ты ДОЛЖЕН вернуть ответ СТРОГО в формате JSON по этой структуре:
{
  "recipes": [
    {
      "name": "Название блюда",
      "time": "Время",
      "macros": {"kcal": 450, "protein": 30, "fat": 20, "carbs": 40},
      "missing_ingredients": ["Сливки - 100 мл"],
      "steps": ["1. Шаг 1.", "2. Шаг 2."]
    }
  ]
}
Верни ТОЛЬКО JSON, без маркдауна.
"""

@app.post("/api/find-recipes")
async def find_recipes(req: RecipeRequest):
    user_ingredients = [INGREDIENTS_MAP[i] for i in req.ingredient_ids if i in INGREDIENTS_MAP]
    excluded_ingredients = [INGREDIENTS_MAP[i] for i in req.excluded_ids if i in INGREDIENTS_MAP]
    
    ing_text = ", ".join(user_ingredients)
    
    # Формируем базовый промпт с лимитами
    user_prompt = f"У меня есть: {ing_text}.\n"
    user_prompt += f"Лимит времени: до {req.time_limit} минут.\n"
    user_prompt += f"Лимит калорий (на порцию): до {req.calorie_limit} ккал.\n"
    
    # Применяем режимы готовки
    if req.cooking_mode == "student":
        user_prompt += "СТИЛЬ 'СТУДЕНТ': минимум грязной посуды, максимально простые шаги, желательно всё в одной сковороде или кастрюле.\n"
    elif req.cooking_mode == "chef":
        user_prompt += "СТИЛЬ 'ШЕФ-ПОВАР': ресторанная подача, интересные кулинарные техники, маринады, изысканный вкус.\n"
    elif req.cooking_mode == "kids":
        user_prompt += "СТИЛЬ 'ДЕТСКОЕ МЕНЮ': блюда должны быть привлекательными для детей, полезными, без острых специй, излишнего жира. В missing_ingredients не добавляй ничего вредного.\n"

    if excluded_ingredients:
        user_prompt += f"НЕ ИСПОЛЬЗОВАТЬ (даже в missing_ingredients): {', '.join(excluded_ingredients)}.\n"
    
    user_prompt += "Придумай 8-10 рецептов."
    
    try:
        # Новый рекомендуемый метод вызова Gemini через Chat
        chat = await ai_client.aio.chats.create(
            model='gemini-3.6-flash',
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
                response_mime_type="application/json",
            )
        )
        response = await chat.send_message(user_prompt)
        
        print("✅ Успешный ответ от Gemini")
        return json.loads(response.text)
    except Exception as e:
        print("❌ ОШИБКА ГЕНЕРАЦИИ:", str(e))
        return {"recipes": []}

@app.post("/api/send-to-bot")
async def send_to_bot(req: SendBotRequest):
    try:
        temp_bot = Bot(token=BOT_TOKEN)
        await temp_bot.send_message(chat_id=req.user_id, text=req.text, parse_mode="HTML")
        await temp_bot.session.close()
        return {"success": True}
    except Exception as e:
        print("❌ Ошибка отправки:", str(e))
        return {"success": False, "error": str(e)}
        
        return {"success": True}
    except Exception as e:
        print("❌ Ошибка отправки в бота:", str(e))
        return {"success": False, "error": str(e)}
