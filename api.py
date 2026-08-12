from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Разрешаем Frontend-у отправлять запросы к нашему Backend-у
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Разрешает запросы с любых сайтов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngredientsRequest(BaseModel):
    ingredient_ids: List[int]

MOCK_RECIPES = [
    {
        "id": 1,
        "name": "Яичница с помидорами",
        "ingredient_ids": [1, 2, 3],
        "image": "https://example.com/egg.jpg"
    },
    {
        "id": 2,
        "name": "Вареники с картошкой",
        "ingredient_ids": [4, 5, 6, 3],
        "image": "https://example.com/vareniki.jpg"
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
                "image": recipe["image"]
            })
            
    results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return {"recipes": results}