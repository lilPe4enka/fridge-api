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

# ПОЛНЫЙ КАТАЛОГ ПРОДУКТОВ
INGREDIENTS_MAP = {
    # Яйца, молочка и сыры
    1: "Яйца", 3: "Сливочное масло", 9: "Твердый сыр", 10: "Молоко",
    16: "Сметана", 27: "Сливки", 33: "Творог", 42: "Кефир", 53: "Сгущенка",
    68: "Моцарелла / Сыр для пиццы", 69: "Плавленый сырок",

    # Курица и птица
    54: "Куриное филе (грудка)", 55: "Куриные бедра / голени", 
    56: "Куриные крылышки", 57: "Целая курица",

    # Свинина и говядина
    58: "Свиная шея / мякоть", 59: "Свиная вырезка / карбонад", 60: "Свиные ребрышки",
    61: "Говяжья мякоть / вырезка", 62: "Говяжий стейк",

    # Фарш
    63: "Куриный фарш", 64: "Говяжий фарш", 65: "Свиной фарш", 
    66: "Домашний фарш (свинина + говядина)",

    # Мясные изделия и колбасы
    21: "Ветчина", 28: "Бекон", 35: "Сосиски / Сардельки", 44: "Колбаса (вареная/копченая)",

    # Рыба и морепродукты
    29: "Красная рыба (лосось/форель)", 30: "Креветки", 46: "Крабовые палочки",
    50: "Рыбные консервы / Тунец", 67: "Белая рыба (минтай/треска)",

    # Овощи, грибы и зелень
    5: "Картошка", 6: "Лук репчатый", 11: "Морковь", 12: "Чеснок", 17: "Капуста белокочанная",
    18: "Болгарский перец", 19: "Свежие огурцы", 20: "Зелень (укроп/петрушка)", 25: "Помидоры",
    26: "Грибы (шампиньоны)", 37: "Брокколи / Цветная капуста", 70: "Кабачки / Цукини",
    71: "Баклажаны", 72: "Свекла", 73: "Зеленый лук", 75: "Соленые / маринованные огурцы",

    # Бакалея, крупы и мучное
    4: "Мука", 8: "Макароны / Спагетти", 13: "Рис", 23: "Гречка", 34: "Хлеб / Батон",
    41: "Овсянка / Геркулес", 45: "Пельмени / Вареники", 49: "Замороженные овощи",
    74: "Лаваш / Тортилья",

    # Консервы, соусы и заправки
    31: "Лимон", 32: "Яблоки", 36: "Консервированная фасоль", 38: "Майонез",
    39: "Томатная паста / Кетчуп", 40: "Растительное масло", 43: "Соевый соус",
    47: "Консервированная кукуруза", 48: "Консервированный горошек", 51: "Горчица",
    52: "Сахар", 76: "Мёд"
}

class RecipeRequest(BaseModel):
    ingredient_ids: List[int]
    excluded_ids: Optional[List[int]] = []
    time_limit: str

class SendBotRequest(BaseModel):
    user_id: int
    text: str

SYSTEM_PROMPT = """
Ты — профессиональный шеф-повар. 
СТРОГИЕ ПРАВИЛА:
1. Указывай точные граммовки (г, мл) для КАЖДОГО ингредиента (даже для соли).
2. Шаги должны содержать точное время (в минутах) и температуру.
3. Категорически не используй запрещенные продукты и их аналоги.
4. Добавь нужные продукты вне списка в missing_ingredients.

Ты ДОЛЖЕН вернуть ответ СТРОГО в формате JSON по этой структуре:
{
  "recipes": [
    {
      "name": "Название блюда",
      "time": "Время",
      "macros": {"kcal": 450, "protein": 30, "fat": 20, "carbs": 40},
      "missing_ingredients": ["Сливки - 100 мл"],
      "steps": [
        "1. Нарежьте филе.",
        "2. Жарьте 5 мин."
      ]
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
    time_text = "Любое" if req.time_limit == "any" else f"до {req.time_limit} минут"
    
    user_prompt = f"У меня есть: {ing_text}. Время: {time_text}."
    if excluded_ingredients:
        user_prompt += f"\nНЕ ИСПОЛЬЗОВАТЬ (даже в missing_ingredients): {', '.join(excluded_ingredients)}."
    
    user_prompt += "\nПридумай 2-3 рецепта."
    
    try:
        response = await ai_client.aio.models.generate_content(
            model='gemini-2.0-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
                response_mime_type="application/json",
            )
        )
        print("✅ Успешный ответ от Gemini получении рецептов")
        return json.loads(response.text)
        
    except Exception as e:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА ГЕНЕРАЦИИ РЕЦЕПТА:", str(e))
        return {"recipes": []}

@app.post("/api/send-to-bot")
async def send_to_bot(req: SendBotRequest):
    try:
        await bot.send_message(chat_id=req.user_id, text=req.text, parse_mode="Markdown")
        return {"success": True}
    except Exception as e:
        print("❌ Ошибка отправки в бота:", str(e))
        return {"success": False, "error": str(e)}
