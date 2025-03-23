from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# OpenAI API setup
openai.api_key = os.getenv("OPENAI_API_KEY")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, change to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Wger API setup (for exercises)
WGER_API_URL = "https://wger.de/api/v2/exercise/"
WGER_HEADERS = {"Authorization": f"Token {os.getenv('WGER_API_KEY')}"}

# Spoonacular API setup (for nutrition)
SPOONACULAR_API_URL = "https://api.spoonacular.com/recipes/complexSearch"
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# List of muscle groups and nutrients/diets
MUSCLE_GROUPS = ["chest", "back", "legs", "shoulders", "biceps", "triceps", "abs"]
DIETARY_CATEGORIES = [
    "protein", "carbs", "fats", "fiber", "low-calorie", "vegan", "keto", "bulking", "cutting"
]

# Request model
class ChatRequest(BaseModel):
    user_input: str

# Get workout recommendations
def get_workout(muscles):
    exercises = []
    for muscle in muscles:
        try:
            response = requests.get(WGER_API_URL, headers=WGER_HEADERS, params={"muscles": muscle})
            if response.status_code != 200:
                raise Exception(f"Failed to fetch workout data: {response.status_code}")

            data = response.json()
            muscle_exercises = [ex["name"] for ex in data.get("results", [])[:3]]
            if muscle_exercises:
                exercises.append(f"{muscle.capitalize()} exercises: {', '.join(muscle_exercises)}")
            else:
                exercises.append(f"No exercises found for {muscle}.")
        except Exception as e:
            exercises.append(f"Error fetching workout for {muscle}: {str(e)}")
    
    return exercises

# Get meal recommendations
def get_meal(nutrients):
    meals = []
    for nutrient in nutrients:
        try:
            response = requests.get(
                SPOONACULAR_API_URL,
                params={"apiKey": SPOONACULAR_API_KEY, "query": nutrient}
            )
            if response.status_code != 200:
                raise Exception(f"Failed to fetch meal data: {response.status_code}")
            
            data = response.json()
            nutrient_meals = [recipe["title"] for recipe in data.get("results", [])[:3]]
            if nutrient_meals:
                meals.append(f"{nutrient.capitalize()} meal options: {', '.join(nutrient_meals)}")
            else:
                meals.append(f"No meal suggestions found for {nutrient}.")
        except Exception as e:
            meals.append(f"Error fetching meal for {nutrient}: {str(e)}")
    
    return meals

# AI Response using OpenAI
def get_ai_response(user_input, chat_history=[]):
    try:
        chat_history.append({"role": "user", "content": user_input})
        completion = openai.chat.completions.create(
             model="gpt-4",
             messages=[
                 {
                     "role": "user",
                     "content": user_input,
                 },
             ],
         )

        ai_response = completion.choices[0].message.content
        chat_history.append({"role": "assistant", "content": ai_response})
        return ai_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

# Main endpoint
@app.post("/chat")
def chat(request: ChatRequest):
    user_input = request.user_input.lower()
    response_parts = []
    
    # Extract muscle groups and nutrients from input
    muscles = [word for word in MUSCLE_GROUPS if word in user_input]
    nutrients = [word for word in DIETARY_CATEGORIES if word in user_input]
    
    # Get workout suggestions if muscle groups are mentioned
    if muscles:
        workout_response = get_workout(muscles)
        response_parts.extend(workout_response)
    
    # Get meal suggestions if dietary categories are mentioned
    if nutrients:
        meal_response = get_meal(nutrients)
        response_parts.extend(meal_response)
    
    # If no workout/meal found, fall back to AI
    if not response_parts:
        ai_response = get_ai_response(user_input)
        response_parts.append(ai_response)
    
    return {"response": "\n".join(response_parts)}

# Health check
@app.get("/")
async def read_root():
    return {"status": "API is running"}

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
