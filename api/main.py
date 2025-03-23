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
    api_successful = False
    
    for muscle in muscles:
        try:
            # Get the muscle ID(s) from our mapping
            muscle_ids = MUSCLE_ID_MAP.get(muscle)
            
            if not muscle_ids:
                continue  # Skip this muscle if no mapping found
                
            if isinstance(muscle_ids, list):
                all_exercises = []
                for muscle_id in muscle_ids:
                    response = requests.get(
                        WGER_API_URL, 
                        headers=WGER_HEADERS, 
                        params={"language": 2, "muscles": muscle_id}
                    )
                    if response.status_code != 200:
                        continue  # Skip this ID if request failed
                    
                    data = response.json()
                    for ex in data.get("results", [])[:2]:
                        if isinstance(ex, dict) and "name" in ex:
                            all_exercises.append(ex["name"])
                
                if all_exercises:
                    exercises.append(f"{muscle.capitalize()} exercises: {', '.join(all_exercises[:3])}")
                    api_successful = True
            else:
                # Single muscle ID
                response = requests.get(
                    WGER_API_URL, 
                    headers=WGER_HEADERS, 
                    params={"language": 2, "muscles": muscle_ids}
                )
                if response.status_code != 200:
                    continue  # Skip if request failed
                
                data = response.json()
                muscle_exercises = []
                for ex in data.get("results", [])[:3]:
                    if isinstance(ex, dict) and "name" in ex:
                        muscle_exercises.append(ex["name"])
                
                if muscle_exercises:
                    exercises.append(f"{muscle.capitalize()} exercises: {', '.join(muscle_exercises)}")
                    api_successful = True
        except Exception:
            pass  # Silently continue to fallback
    
    # If no exercises were found from API, provide fallback recommendations
    if not api_successful:
        if "biceps" in muscles:
            exercises.append("Biceps exercises: Barbell Curls, Hammer Curls, Preacher Curls")
        if "triceps" in muscles:
            exercises.append("Triceps exercises: Tricep Pushdowns, Skull Crushers, Dips")
        if "chest" in muscles:
            exercises.append("Chest exercises: Bench Press, Push-ups, Dumbbell Flyes")
        if "back" in muscles:
            exercises.append("Back exercises: Pull-ups, Bent-over Rows, Lat Pulldowns")
        if "shoulders" in muscles:
            exercises.append("Shoulders exercises: Military Press, Lateral Raises, Face Pulls")
        if "legs" in muscles:
            exercises.append("Legs exercises: Squats, Leg Press, Lunges")
        if "abs" in muscles:
            exercises.append("Abs exercises: Crunches, Leg Raises, Planks")
    
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
    
    # Extract muscle groups and nutrients from input
    muscles = [word for word in MUSCLE_GROUPS if word in user_input]
    nutrients = [word for word in DIETARY_CATEGORIES if word in user_input]
    
    response_parts = []
    
    # Get workout suggestions if muscle groups are mentioned
    if muscles:
        workout_response = get_workout(muscles)
        if workout_response:
            response_parts.append("Workout Recommendations:")
            response_parts.extend(workout_response)
    
    # Get meal suggestions if dietary categories are mentioned
    if nutrients:
        meal_response = get_meal(nutrients)
        if meal_response:
            if response_parts:  # Add a separator if we already have workout content
                response_parts.append("\n")
            response_parts.append("Meal Recommendations:")
            response_parts.extend(meal_response)
    
    # If no workout/meal found, fall back to AI
    if not response_parts:
        ai_response = get_ai_response(user_input)
        response_parts.append(ai_response)
    else:
        # Add a helpful conclusion
        response_parts.append("\nLet me know if you need more specific details about any of these recommendations!")
    
    return {"response": "\n".join(response_parts)}

# Health check
@app.get("/")
async def read_root():
    return {"status": "API is running"}

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


