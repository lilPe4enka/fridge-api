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

class IngredientsRequest(BaseModel):
    ingredient_ids: List[int]

# Расширенная база рецептов с шагами приготовления
MOCK_RECIPES = [
    {
        "id": 1,
        "name": "Яичница с помидорами 🍳",
        "ingredient_ids": [1, 2, 3], # Яйца, Помидоры, Масло
        "steps": [
            "Нарежьте помидоры дольками.",
            "Разогрейте сковороду с маслом.",
            "Обжарьте помидоры 2-3 минуты на среднем огне.",
            "Разбейте яйца к помидорам, посолите и жарьте до готовности белка."
        ]
    },
    {
        "id": 2,
        "name": "Классические драники 🥔",
        "ingredient_ids": [5, 1, 4, 3], # Картошка, Яйца, Мука, Масло
        "steps": [
            "Очистите картофель и натрите его на мелкой терке.",
            "Отожмите лишний сок из картофеля.",
            "Добавьте яйцо, пару ложек муки, соль и хорошо перемешайте.",
            "Выкладывайте массу ложкой на разогретую с маслом сковороду.",
            "Жарьте с двух сторон до золотистой корочки."
        ]
    },
    {
        "id": 3,
        "name": "Паста с курицей и сыром 🍝",
        "ingredient_ids": [8, 7, 9, 3, 12], # Макароны, Курица, Сыр, Масло, Чеснок
        "steps": [
            "Отварите макароны в подсоленной воде до готовности.",
            "Нарежьте куриное филе небольшими кусочками.",
            "Измельчите чеснок и слегка обжарьте его на масле.",
            "Добавьте курицу к чесноку и жарьте до румяной корочки.",
            "Смешайте курицу с макаронами, посыпьте тертым сыром и дайте ему расплавиться."
        ]
    },
    {
        "id": 4,
        "name": "Сырный омлет 🧀",
        "ingredient_ids": [1, 10, 9, 3], # Яйца, Молоко, Сыр, Масло
        "steps": [
            "Взбейте яйца с молоком и щепоткой соли.",
            "Натрите сыр на терке и добавьте половину в яичную смесь.",
            "Вылейте смесь на разогретую сковороду с маслом.",
            "За минуту до готовности посыпьте оставшимся сыром и сложите омлет пополам."
        ]
    },
    {
        "id": 5,
        "name": "Простой куриный суп 🥣",
        "ingredient_ids": [7, 5, 11, 6], # Курица, Картошка, Морковь, Лук
        "steps": [
            "Залейте курицу водой и варите бульон 30-40 минут, снимая пену.",
            "Нарежьте картошку кубиками и добавьте в бульон.",
            "Мелко нарежьте лук, натрите морковь и сделайте зажарку на сковороде.",
            "Добавьте зажарку в суп, посолите и варите до мягкости картофеля.",
            "Достаньте курицу, разделите на кусочки и верните в суп."
        ]
    }
]

@app.post("/api/find-recipes")
async def find_recipes(request: IngredientsRequest):
    user_ingredients = set(request.ingredient_ids)
    results = []

    for recipe in MOCK_RECIPES:
        recipe_ingredients = set(recipe["ingredient_ids"])
        matches = user_ingredients.intersection(recipe_ingredients)
        
        if len(matches) > 0:
            match_percentage = int((len(matches) / len(recipe_ingredients)) * 100)
            missing_ids = list(recipe_ingredients.difference(user_ingredients))
            
            results.append({
                "id": recipe["id"],
                "name": recipe["name"],
                "match_percentage": match_percentage,
                "missing_ingredient_ids": missing_ids,
                "steps": recipe["steps"] # <-- Добавили шаги в ответ сервера
            })
            
    results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return {"recipes": results}