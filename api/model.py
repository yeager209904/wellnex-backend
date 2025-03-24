from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import joblib
import numpy as np

# Initialize FastAPI
app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, change to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Load the trained model
model_path = "optimized_powerlifting_rf_model.pkl"
model = joblib.load(model_path)

# Define request model
class LiftInput(BaseModel):
    Squat1Kg: float
    Bench1Kg: float
    Deadlift1Kg: float


@app.post("/predict")
def predict_lifts(data: LiftInput):
    # Convert input data to a NumPy array (2D array required for model)
    input_array = np.array([[data.Squat1Kg, data.Bench1Kg, data.Deadlift1Kg]])
    
    # Make a prediction
    prediction = model.predict(input_array)
    
    # Return results as JSON
    return {
        "Best3SquatKg": prediction[0][0],
        "Best3BenchKg": prediction[0][1],
        "Best3DeadliftKg": prediction[0][2]
    }


# Health check
@app.get("/")
async def read_root():
    return {"status": "API is running"}

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

