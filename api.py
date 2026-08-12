import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from google import genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

INGREDIENTS_MAP = {
    1: "Яйца", 3: "Масло", 4: "Мука", 5: "Картошка", 6: "Лук",
    7: "Курица", 8: "Макароны", 9: "Сыр", 10: "Молоко", 11: "Морковь",
    12: "Чеснок", 13: "Рис", 15: "Мясной фарш", 16: "Сметана",
    17: "Капуста", 18: "Болгарский перец", 19: "Огурцы", 20: "Зелень",
    21: "Ветчина", 22: "Свинина", 23: "Гречка", 24: "Говядина"
}

class IngredientsRequest(BaseModel):
    ingredient_ids: List[int]
    time_limit: str  # Принимаем время готовки

@app.post("/api/find-recipes")
async def find_recipes(request: IngredientsRequest):
    user_ingredients = [INGREDIENTS_MAP[i] for i in request.ingredient_ids if i in INGREDIENTS_MAP]
    
    if not user_ingredients:
        return {"recipes": []}

    time_text = "Любое время." if request.time_limit == "any" else f"Максимальное время готовки: {request.time_limit} минут."

    prompt = f"""
    Продукты пользователя: {', '.join(user_ingredients)}.
    {time_text}
    Придумай 3 вкусных рецепта. Можно добавлять 1-2 простых ингредиента, если без них никак (базовые специи и масло не считай).
    
    Верни ответ СТРОГО в формате JSON - массив объектов:
    - "name": строка (название с эмодзи)
    - "match_percentage": число (совпадение от 60 до 100)
    - "missing_ingredients": массив строк (что докупить, или пустой массив)
    - "steps": массив строк (шаги)
    - "time": строка (например "25 мин")
    - "macros": объект с ключами "kcal", "protein", "fat", "carbs" (числа - примерная калорийность и БЖУ на порцию).
    """

    try:
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json"
            }
        )
        
        raw_text = interaction.output_text.strip()
        if raw_text.startswith("```json"): raw_text = raw_text[7:]
        if raw_text.endswith("```"): raw_text = raw_text[:-3]
            
        recipes = json.loads(raw_text.strip()) 
        return {"recipes": recipes}
        
    except Exception as e:
        print("====== ОШИБКА GEMINI ======")
        print(e)
        return {"recipes": []}