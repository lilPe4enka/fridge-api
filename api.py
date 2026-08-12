import os
import json
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

INGREDIENTS_MAP = {
    1: "Яйца", 3: "Масло", 4: "Мука", 5: "Картошка", 6: "Лук",
    7: "Курица", 8: "Макароны", 9: "Сыр", 10: "Молоко", 11: "Морковь",
    12: "Чеснок", 13: "Рис", 15: "Мясной фарш", 16: "Сметана",
    17: "Капуста", 18: "Болгарский перец", 19: "Огурцы", 20: "Зелень",
    21: "Ветчина", 22: "Свинина", 23: "Гречка", 24: "Говядина"
}

class IngredientsRequest(BaseModel):
    ingredient_ids: List[int]
    time_limit: str

class SendToBotRequest(BaseModel):
    user_id: int
    text: str

@app.get("/")
async def root():
    return {"status": "ok", "message": "API работает отлично!"}

@app.post("/api/find-recipes")
async def find_recipes(request: IngredientsRequest):
    print("\n====== 1. ПРИШЕЛ ЗАПРОС ОТ ПРИЛОЖЕНИЯ ======")
    print(f"Полученные ID: {request.ingredient_ids}")
    
    user_ingredients = [INGREDIENTS_MAP[i] for i in request.ingredient_ids if i in INGREDIENTS_MAP]
    print(f"Распознанные продукты: {user_ingredients}")
    
    if not user_ingredients:
        print("====== ОШИБКА: СПИСОК ПРОДУКТОВ ПУСТ ======")
        return {"recipes": []}

    time_text = "Любое время." if request.time_limit == "any" else f"Максимальное время готовки: {request.time_limit} минут."
    
    prompt = f"""
    Пользователь имеет: {', '.join(user_ingredients)}.
    {time_text}
    Придумай 3 вкусных рецепта. Можно добавлять 1-2 простых ингредиента.
    Верни ответ СТРОГО в формате JSON - массив объектов:
    - "name": строка (название с эмодзи)
    - "match_percentage": число 
    - "missing_ingredients": массив строк 
    - "steps": массив строк 
    - "time": строка 
    - "macros": объект с ключами "kcal", "protein", "fat", "carbs"
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    print("====== 2. ОТПРАВЛЯЕМ ЗАПРОС В GOOGLE ======")
    try:
        response = requests.post(url, json=payload)
        print(f"Статус ответа Google: {response.status_code}")
        
        data = response.json()
        
        if "candidates" in data:
            print("====== 3. GOOGLE УСПЕШНО ВЕРНУЛ РЕЦЕПТЫ ======")
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            if raw_text.startswith("```json"): raw_text = raw_text[7:]
            if raw_text.endswith("```"): raw_text = raw_text[:-3]
                
            recipes = json.loads(raw_text.strip())
            print(f"Сгенерировано рецептов: {len(recipes)}")
            return {"recipes": recipes}
        else:
            print("====== 4. ОШИБКА В ОТВЕТЕ GOOGLE ======")
            print(data)
            return {"recipes": []}
            
    except Exception as e:
        print("====== 5. КРИТИЧЕСКАЯ ОШИБКА СЕРВЕРА ======")
        print(repr(e))
        return {"recipes": []}

@app.post("/api/send-to-bot")
async def send_to_bot(request: SendToBotRequest):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": request.user_id, "text": request.text, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, json=payload)
        return {"success": resp.ok}
    except Exception as e:
        return {"success": False, "error": str(e)}
