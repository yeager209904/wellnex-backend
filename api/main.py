from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# OpenAI API setup
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

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

# Get AI response using OpenAI
@app.post("/test_openai")
def test_openai():
    try:
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt="Say this is a test",
            max_tokens=7,
            temperature=0
        )
        return {"response": response.choices[0].text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI request failed: {str(e)}")

# Health check
@app.get("/")
def root():
    return {"status": "API is running"}

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
