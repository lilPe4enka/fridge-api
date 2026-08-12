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
    user_ingredients = [INGREDIENTS_MAP[i] for i in request.ingredient_ids if i in INGREDIENTS_MAP]
    if not user_ingredients:
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

    # Прямая ссылка на актуальную модель Gemini 3.6 Flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        # Если ответ успешный, достаем текст
        if "candidates" in data:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Очистка маркдауна
            if raw_text.startswith("```json"): raw_text = raw_text[7:]
            if raw_text.endswith("```"): raw_text = raw_text[:-3]
                
            return {"recipes": json.loads(raw_text.strip())}
        else:
            print("====== ОТВЕТ С ОШИБКОЙ ОТ GOOGLE ======")
            print(data)
            return {"recipes": []}
            
    except Exception as e:
        print("====== ОШИБКА СЕРВЕРА ======")
        print(repr(e))
        return {"recipes": []}

@app.post("/api/send-to-bot")
async def send_to_bot(request: SendToBotRequest):
    if not BOT_TOKEN:
        return {"success": False, "error": "Токен бота не настроен на сервере"}
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": request.user_id,
        "text": request.text,
        "parse_mode": "Markdown"
    }
    
    try:
        resp = requests.post(url, json=payload)
        return {"success": resp.ok}
    except Exception as e:
        return {"success": False, "error": str(e)}
