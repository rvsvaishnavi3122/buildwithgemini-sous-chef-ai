# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from typing import Any, Dict, List, Optional
from google.adk.tools import ToolContext
from google.cloud import firestore
from google.genai import types

# Hardcoded project ID as string for Firestore and GCP clients
PROJECT_ID = "qwiklabs-gcp-04-f6830db8354b"
# Hardcoded Cloud Storage bucket name for public recipe media
GCS_BUCKET_NAME = "sous-chef-ai-qwiklabs-04-media"
_db: Optional[firestore.Client] = None



def get_db() -> firestore.Client:
    """Lazy initialize Firestore client with explicit project ID string."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def list_recipes(cuisine: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists recipes stored in the cookbook catalog, with optional filtering by cuisine or tag.

    Args:
        cuisine: Optional cuisine filter (e.g., 'Italian', 'Asian', 'Mediterranean').
        tag: Optional dietary or category tag filter (e.g., 'vegan', 'keto-friendly', 'pasta', 'quick').

    Returns:
        A list of matching recipe summaries containing id, title, cuisine, prep_time_minutes,
        difficulty, and tags.
    """
    db = get_db()
    docs = db.collection("recipes").stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        if cuisine and cuisine.lower() not in data.get("cuisine", "").lower():
            continue
        if tag and not any(tag.lower() == t.lower() for t in data.get("tags", [])):
            continue

        results.append({
            "id": data.get("id"),
            "title": data.get("title"),
            "description": data.get("description"),
            "cuisine": data.get("cuisine"),
            "prep_time_minutes": data.get("prep_time_minutes"),
            "cook_time_minutes": data.get("cook_time_minutes"),
            "servings": data.get("servings"),
            "difficulty": data.get("difficulty"),
            "calories_per_serving": data.get("calories_per_serving"),
            "tags": data.get("tags", []),
        })

    return results


def get_recipe_details(recipe_id: str) -> Dict[str, Any]:
    """Retrieves full details for a recipe, including all ingredients and step-by-step instructions.

    Args:
        recipe_id: The unique identifier of the recipe (e.g., 'creamy-tomato-basil-pasta').

    Returns:
        The full recipe dictionary, or an error message if not found.
    """
    db = get_db()
    doc = db.collection("recipes").document(recipe_id).get()
    if not doc.exists:
        return {"error": f"Recipe with ID '{recipe_id}' not found."}

    data = doc.to_dict()
    data["id"] = doc.id
    return data


def add_recipe(
    title: str,
    description: str,
    cuisine: str,
    prep_time_minutes: int,
    cook_time_minutes: int,
    servings: int,
    difficulty: str,
    calories_per_serving: int,
    ingredients: List[Dict[str, str]],
    instructions: List[str],
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Adds a new custom recipe to the Firestore cookbook collection.

    Args:
        title: Title of the dish (e.g., 'Avocado Toast with Poached Egg').
        description: Brief description of the dish.
        cuisine: Cuisine category (e.g., 'American', 'French', 'Mexican').
        prep_time_minutes: Preparation time in minutes.
        cook_time_minutes: Cooking time in minutes.
        servings: Number of servings this recipe yields.
        difficulty: Complexity level ('Easy', 'Medium', 'Hard').
        calories_per_serving: Approximate calories per portion.
        ingredients: List of ingredient objects with 'name' and 'amount' keys.
        instructions: Ordered list of step-by-step preparation and cooking instructions.
        tags: Optional list of dietary/style tags (e.g., ['breakfast', 'vegetarian']).

    Returns:
        A dictionary with the created recipe ID and status confirmation.
    """
    db = get_db()
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    doc_id = slug if slug else "recipe-custom"

    recipe_data = {
        "id": doc_id,
        "title": title,
        "description": description,
        "cuisine": cuisine,
        "prep_time_minutes": prep_time_minutes,
        "cook_time_minutes": cook_time_minutes,
        "servings": servings,
        "difficulty": difficulty,
        "calories_per_serving": calories_per_serving,
        "ingredients": ingredients,
        "instructions": instructions,
        "tags": tags or [],
    }

    db.collection("recipes").document(doc_id).set(recipe_data)
    return {"status": "success", "id": doc_id, "message": f"Recipe '{title}' saved successfully."}


def check_pantry_match(recipe_id: str, pantry_items: List[str]) -> Dict[str, Any]:
    """Compares the user's available pantry ingredients against a recipe's required ingredients.
    Identifies what ingredients the user already has, what is missing, calculates a match percentage,
    and provides a ready-to-buy shopping list.

    Args:
        recipe_id: The ID of the recipe to check (e.g., 'creamy-tomato-basil-pasta').
        pantry_items: A list of ingredient names currently available in the user's kitchen/pantry
                      (e.g., ['pasta', 'olive oil', 'garlic', 'salt']).

    Returns:
        A dictionary containing:
        - recipe_title: Name of the recipe
        - match_percentage: Percentage of ingredients already available (0-100%)
        - available_ingredients: Ingredients already in the pantry
        - missing_ingredients: Ingredients that need to be bought, with amounts
        - shopping_list: Structured items ready for shopping
    """
    recipe = get_recipe_details(recipe_id)
    if "error" in recipe:
        return recipe

    recipe_ingredients = recipe.get("ingredients", [])
    if not recipe_ingredients:
        return {"error": f"No ingredients found for recipe '{recipe_id}'."}

    normalized_pantry = [item.strip().lower() for item in pantry_items if item.strip()]

    available = []
    missing = []
    shopping_list = []

    for ing in recipe_ingredients:
        ing_name = ing.get("name", "").strip()
        ing_amount = ing.get("amount", "").strip()
        ing_name_lower = ing_name.lower()

        # Check if any pantry item matches the recipe ingredient or vice-versa
        is_matched = any(
            p_item in ing_name_lower or ing_name_lower in p_item
            for p_item in normalized_pantry
        )

        if is_matched:
            available.append({"name": ing_name, "amount": ing_amount})
        else:
            missing.append({"name": ing_name, "amount": ing_amount})
            shopping_list.append({
                "item": ing_name,
                "amount_needed": ing_amount,
                "status": "Need to buy"
            })

    total = len(recipe_ingredients)
    matched_count = len(available)
    match_percentage = round((matched_count / total) * 100, 1) if total > 0 else 0.0

    return {
        "recipe_id": recipe_id,
        "recipe_title": recipe.get("title", ""),
        "match_percentage": match_percentage,
        "total_ingredients": total,
        "available_count": matched_count,
        "available_ingredients": available,
        "missing_count": len(missing),
        "missing_ingredients": missing,
        "shopping_list": shopping_list,
    }


def find_ingredient_substitute(ingredient: str, dietary_preference: Optional[str] = None) -> Dict[str, Any]:
    """Finds practical culinary substitutions for a missing or restricted ingredient.

    Args:
        ingredient: Name of the ingredient to replace (e.g., 'heavy cream', 'egg', 'parmesan').
        dietary_preference: Optional dietary filter (e.g., 'vegan', 'dairy-free', 'gluten-free').

    Returns:
        A dictionary with recommended substitutes, conversion ratios, and culinary tips.
    """
    subs_db = {
        "heavy cream": [
            {"substitute": "Full-fat coconut cream", "ratio": "1:1", "notes": "Rich texture, slight coconut aroma, great for curries and soups (vegan/dairy-free)."},
            {"substitute": "Cashew cream (blended soaked raw cashews + water)", "ratio": "1:1", "notes": "Neutral flavor, velvety finish (vegan/dairy-free)."},
            {"substitute": "Milk + Melted Butter", "ratio": "3/4 cup whole milk + 1/4 cup melted butter for 1 cup heavy cream", "notes": "Good for baking and sauces (vegetarian)."}
        ],
        "parmesan": [
            {"substitute": "Nutritional yeast", "ratio": "1:1", "notes": "Savory, nutty, and cheesy umami kick (vegan/dairy-free)."},
            {"substitute": "Pecorino Romano", "ratio": "1:1", "notes": "Sharper, saltier sheep's milk alternative (vegetarian)."}
        ],
        "butter": [
            {"substitute": "Extra virgin olive oil", "ratio": "3/4 cup oil per 1 cup butter", "notes": "Heart-healthy, excellent for cooking and savory sauces (vegan)."},
            {"substitute": "Coconut oil", "ratio": "1:1", "notes": "Solid at room temp, works well in baking and sauteing (vegan)."}
        ],
        "egg": [
            {"substitute": "Flax egg (1 tbsp ground flaxseed + 2.5 tbsp water)", "ratio": "1 flax egg per 1 whole egg", "notes": "Let sit 5 mins to gel. Excellent binder for baking (vegan)."},
            {"substitute": "Mashed ripe banana or applesauce", "ratio": "1/4 cup per egg", "notes": "Adds moisture and mild sweetness to baked treats (vegan)."},
            {"substitute": "Aquafaba (chickpea liquid)", "ratio": "3 tbsp per egg", "notes": "Whips like egg whites (vegan)."}
        ],
        "soy sauce": [
            {"substitute": "Tamari", "ratio": "1:1", "notes": "Rich fermented soybean flavor without gluten (gluten-free)."},
            {"substitute": "Coconut aminos", "ratio": "1:1", "notes": "Lower sodium, sweeter profile (gluten-free, soy-free)."}
        ],
        "all-purpose flour": [
            {"substitute": "1-to-1 Gluten-Free Baking Flour blend", "ratio": "1:1", "notes": "Blended with xanthan gum for direct replacement (gluten-free)."},
            {"substitute": "Oat flour", "ratio": "1:1 by weight", "notes": "Nutty and dense (gluten-free if certified)."}
        ]
    }

    ing_key = ingredient.lower().strip()
    matched_key = None
    for key in subs_db:
        if key in ing_key or ing_key in key:
            matched_key = key
            break

    if matched_key:
        candidates = subs_db[matched_key]
        if dietary_preference:
            pref = dietary_preference.lower()
            filtered = [c for c in candidates if pref in c["notes"].lower()]
            if filtered:
                candidates = filtered
        return {
            "ingredient": ingredient,
            "matched_item": matched_key,
            "substitutes": candidates,
            "dietary_preference": dietary_preference or "general"
        }

    return {
        "ingredient": ingredient,
        "message": f"No pre-configured substitutes found for '{ingredient}', but you can try neutral cooking oils, plant milks, or vegetable broth depending on whether it provides fat, moisture, or binding."
    }


def generate_recipe_image(
    recipe_title: str,
    tool_context: ToolContext,
    visual_style: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates an AI visual food photograph for a recipe using gemini-3.1-flash-lite-image
    in the global region. Saves the image as a session artifact for the Playground's Artifacts panel,
    and uploads the image bytes directly to the public Cloud Storage bucket, returning its public HTTPS URL.

    Args:
        recipe_title: The name of the recipe (e.g., 'Creamy Tomato Basil Pasta').
        tool_context: Tool context automatically injected by ADK runtime for artifact management.
        visual_style: Optional description of presentation or styling (e.g., 'rustic ceramic bowl with fresh parmesan garnish').

    Returns:
        A dictionary with the public image URL, artifact filename, and status message.
    """
    from google import genai
    from google.cloud import storage
    import uuid

    style_desc = visual_style or "gourmet restaurant plating, soft natural daylight, high-end food magazine photography"
    prompt = f"Professional food photography of {recipe_title}, {style_desc}. Highly detailed, delicious presentation, 4k."

    try:
        # Call gemini-3.1-flash-lite-image in the global region
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        image_bytes = None
        mime_type = "image/jpeg"
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if getattr(part, "inline_data", None) and part.inline_data.data:
                        image_bytes = part.inline_data.data
                        mime_type = part.inline_data.mime_type or "image/jpeg"
                        break
            if image_bytes:
                break

        if not image_bytes:
            return {"error": "Image model did not return image bytes in response."}

        slug = re.sub(r"[^a-z0-9]+", "-", recipe_title.lower()).strip("-")
        ext = "png" if "png" in mime_type else "jpg"
        artifact_filename = f"{slug}-{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save artifact to ToolContext for the Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(
            filename=artifact_filename,
            artifact=artifact_part,
            custom_metadata={"recipe_title": recipe_title, "content_type": mime_type},
        )

        # 2. Upload same image bytes to the public Cloud Storage bucket
        storage_object_path = f"recipes/{artifact_filename}"
        gcs_client = storage.Client(project=PROJECT_ID)
        bucket = gcs_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(storage_object_path)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{storage_object_path}"

        return {
            "status": "success",
            "recipe_title": recipe_title,
            "public_image_url": public_url,
            "artifact_saved": artifact_filename,
            "bucket": GCS_BUCKET_NAME,
            "message": f"Generated presentation image for '{recipe_title}' and saved artifact."
        }
    except Exception as e:
        return {"error": f"Failed to generate recipe image: {str(e)}"}


def search_web_recipes(query: str) -> Dict[str, Any]:
    """Searches the open-web culinary database (TheMealDB public API) for real recipes,
    ingredients, and cooking instructions matching a dish name or ingredient keyword.

    Args:
        query: Name of the dish, cuisine, or main ingredient to search for (e.g., 'curry', 'pasta', 'chicken', 'tacos').

    Returns:
        A dictionary with real matching recipes, including ingredients, measurements,
        instructions, cuisine origin, and thumbnail images.
    """
    import json
    import os
    import urllib.parse
    import urllib.request

    # Reads custom API key from environment if provided, otherwise uses free test tier '1'
    api_key = os.getenv("THEMEALDB_API_KEY", "1")
    encoded_query = urllib.parse.quote(query.strip())
    url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SousChefAI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        meals = data.get("meals")
        if not meals:
            return {"query": query, "found": 0, "message": f"No global web recipes found for '{query}'."}

        formatted_recipes = []
        for meal in meals[:3]:  # Top 3 matching recipes
            # Gather paired ingredients and measurements from TheMealDB schema
            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                meas = meal.get(f"strMeasure{i}")
                if ing and ing.strip():
                    measure_text = f" ({meas.strip()})" if meas and meas.strip() else ""
                    ingredients.append(f"{ing.strip()}{measure_text}")

            formatted_recipes.append({
                "id": meal.get("idMeal"),
                "title": meal.get("strMeal"),
                "category": meal.get("strCategory"),
                "cuisine": meal.get("strArea"),
                "instructions": (meal.get("strInstructions") or "")[:500] + "...",
                "ingredients": ingredients,
                "thumbnail_url": meal.get("strMealThumb"),
                "source_url": meal.get("strSource"),
            })

        return {
            "query": query,
            "found": len(formatted_recipes),
            "recipes": formatted_recipes,
        }
    except Exception as e:
        return {"error": f"Failed to fetch recipes from TheMealDB: {str(e)}"}



