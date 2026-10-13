import json
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-f6830db8354b"

SEEDED_RECIPES = [
    {
        "id": "creamy-tomato-basil-pasta",
        "title": "Creamy Tomato Basil Pasta",
        "description": "Rich, comforting pasta tossed in a savory garlic tomato sauce finished with fresh basil and cream.",
        "cuisine": "Italian",
        "prep_time_minutes": 15,
        "cook_time_minutes": 20,
        "servings": 4,
        "difficulty": "Easy",
        "calories_per_serving": 480,
        "ingredients": [
            {"name": "penne pasta", "amount": "400g"},
            {"name": "canned crushed tomatoes", "amount": "1 can (400g)"},
            {"name": "heavy cream", "amount": "1/2 cup"},
            {"name": "garlic", "amount": "3 cloves, minced"},
            {"name": "olive oil", "amount": "2 tbsp"},
            {"name": "fresh basil", "amount": "1/4 cup, chopped"},
            {"name": "parmesan cheese", "amount": "1/3 cup, grated"},
            {"name": "salt and pepper", "amount": "to taste"}
        ],
        "instructions": [
            "Boil penne pasta in salted water until al dente; reserve 1/2 cup pasta water.",
            "Heat olive oil in a skillet over medium heat, sauté minced garlic for 1 minute until fragrant.",
            "Stir in crushed tomatoes, simmer for 10 minutes until thickened.",
            "Lower heat, stir in heavy cream and parmesan until smooth.",
            "Toss pasta and fresh basil into the sauce. Adjust seasoning and serve warm."
        ],
        "tags": ["vegetarian", "comfort food", "pasta", "quick"]
    },
    {
        "id": "lemon-garlic-herb-chicken",
        "title": "Lemon Garlic Herb Roasted Chicken",
        "description": "Juicy pan-seared chicken breasts infused with lemon juice, rosemary, and golden garlic cloves.",
        "cuisine": "Mediterranean",
        "prep_time_minutes": 10,
        "cook_time_minutes": 25,
        "servings": 4,
        "difficulty": "Easy",
        "calories_per_serving": 380,
        "ingredients": [
            {"name": "chicken breast", "amount": "4 boneless breasts"},
            {"name": "lemon", "amount": "2 (juiced and zested)"},
            {"name": "garlic", "amount": "4 cloves, minced"},
            {"name": "olive oil", "amount": "3 tbsp"},
            {"name": "fresh rosemary", "amount": "1 tbsp, chopped"},
            {"name": "fresh thyme", "amount": "1 tsp, chopped"},
            {"name": "salt and pepper", "amount": "to taste"}
        ],
        "instructions": [
            "Season chicken breasts generously with salt, pepper, minced garlic, and herbs.",
            "Heat 2 tbsp olive oil in an oven-safe skillet over medium-high heat.",
            "Sear chicken for 4-5 minutes on each side until golden.",
            "Drizzle lemon juice and zest over chicken, then transfer to a 375°F (190°C) oven for 10-12 minutes until internal temp reaches 165°F (74°C).",
            "Rest for 5 minutes before slicing and serving with pan juices."
        ],
        "tags": ["high-protein", "keto-friendly", "gluten-free", "dinner"]
    },
    {
        "id": "crispy-tofu-veggie-stirfry",
        "title": "Crispy Tofu & Sesame Veggie Stir-Fry",
        "description": "Golden crispy tofu cubes and crunchy bell peppers and broccoli coated in a savory sesame ginger glaze.",
        "cuisine": "Asian",
        "prep_time_minutes": 20,
        "cook_time_minutes": 15,
        "servings": 3,
        "difficulty": "Medium",
        "calories_per_serving": 340,
        "ingredients": [
            {"name": "extra-firm tofu", "amount": "1 block (14 oz), pressed and cubed"},
            {"name": "cornstarch", "amount": "2 tbsp"},
            {"name": "broccoli florets", "amount": "2 cups"},
            {"name": "bell pepper", "amount": "1 red, sliced"},
            {"name": "soy sauce / tamari", "amount": "3 tbsp"},
            {"name": "sesame oil", "amount": "1 tbsp"},
            {"name": "fresh ginger", "amount": "1 tbsp, grated"},
            {"name": "sesame seeds", "amount": "1 tbsp, for garnish"}
        ],
        "instructions": [
            "Toss pressed tofu cubes with cornstarch and a pinch of salt.",
            "Pan-fry tofu in 2 tbsp vegetable oil over medium-high heat until golden on all sides (about 8 mins); set aside.",
            "In the same pan, stir-fry broccoli and sliced bell peppers for 4-5 minutes until tender-crisp.",
            "Whisk soy sauce, sesame oil, and grated ginger together.",
            "Return tofu to skillet, pour sauce over, and toss for 1-2 minutes until glazed. Garnish with sesame seeds."
        ],
        "tags": ["vegan", "dairy-free", "healthy", "stir-fry"]
    }
]

def seed_database():
    print(f"Connecting to Firestore with project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("recipes")
    
    for recipe in SEEDED_RECIPES:
        doc_id = recipe["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(recipe)
        print(f"Seeded recipe: {recipe['title']} (id: {doc_id})")
        
    print("Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
