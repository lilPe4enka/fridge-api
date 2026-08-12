import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from google import genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Берем ключ API из настроек сервера
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Инициализируем клиент по новому стандарту 
client = genai.Client(api_key=GEMINI_API_KEY)

# Словарь продуктов
INGREDIENTS_MAP = {
    1: "Яйца", 3: "Масло", 4: "Мука", 5: "Картошка", 6: "Лук",
    7: "Курица", 8: "Макароны", 9: "Сыр", 10: "Молоко", 11: "Морковь",
    12: "Чеснок", 13: "Рис", 15: "Мясной фарш", 16: "Сметана",
    17: "Капуста", 18: "Болгарский перец", 19: "Огурцы", 20: "Зелень",
    21: "Ветчина", 22: "Свинина", 23: "Гречка", 24: "Говядина"
}

class IngredientsRequest(BaseModel):
    ingredient_ids: List[int]

@app.post("/api/find-recipes")
async def find_recipes(request: IngredientsRequest):
    user_ingredients = [INGREDIENTS_MAP[i] for i in request.ingredient_ids if i in INGREDIENTS_MAP]
    
    if not user_ingredients:
        return {"recipes": []}

    prompt = f"""
    Пользователь имеет в холодильнике следующие продукты: {', '.join(user_ingredients)}.
    Придумай 3 или 4 вкусных рецепта, которые можно из них приготовить. 
    Ты можешь добавлять в рецепт 1-2 других простых ингредиента, если без них никак (базовые вещи вроде соли, воды и перца не считай).
    
    Верни ответ СТРОГО в формате JSON. Это должен быть массив объектов. Каждый объект должен иметь ключи:
    - "name": строка (название блюда с красивым эмодзи)
    - "match_percentage": число (насколько рецепт совпадает с имеющимися продуктами, от 60 до 100)
    - "missing_ingredients": массив строк (названия продуктов, которые пользователю нужно докупить. Если ничего докупать не нужно, верни пустой массив [])
    - "steps": массив строк (пошаговый рецепт из 4-6 шагов)
    """

    try:
        # Используем современный Interactions API и самую новую модель 3.6-flash
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json"
            }
        )
        
        # Получаем текст ответа
        raw_text = interaction.output_text.strip()
        
        # На всякий случай очищаем от markdown-разметки (```json ... ```)
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        recipes = json.loads(raw_text.strip()) 
        return {"recipes": recipes}
        
    except Exception as e:
        print("====== ОШИБКА GEMINI ======")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Описание: {e}")
        print("===========================")
        return {"recipes": []}