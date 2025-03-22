from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Groq API setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY_1")
GROQ_API_URL = "https://api.groq.com/v1/chat/completions"

# Wger API setup (for exercises)
WGER_API_URL = "https://wger.de/api/v2/exercise/"
WGER_HEADERS = {"Authorization": f"Token {os.getenv('WGER_API_KEY')}"}

# Spoonacular API setup (for nutrition)
SPOONACULAR_API_URL = "https://api.spoonacular.com/recipes/complexSearch"
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# List of muscle groups and nutrients/diets
MUSCLE_GROUPS = ["chest", "back", "legs", "shoulders", "biceps", "triceps", "abs"]
DIETARY_CATEGORIES = ["protein", "carbs", "fats", "fiber", "low-calorie", "vegan", "keto", "bulking", "cutting"]

# Request model
class ChatRequest(BaseModel):
    user_input: str

# Get AI response using Groq API
@app.post("/test_groq")
def test_groq():
    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": "Say this is a test"}],
            max_tokens=7,
            temperature=0
        )

        # Debugging: Print full response
        print("Groq API Response:", response)

        # Ensure JSON response format
        return {"response": response.choices[0].message.content.strip()}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API request failed: {str(e)}")


# Health check
@app.get("/")
def root():
    return {"status": "API is running"}

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
