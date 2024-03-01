from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import spacy

# Define a Pydantic model for the request body
class TextIn(BaseModel):
    text: str

# Initialize FastAPI app
app = FastAPI()

# Load your trained spaCy model
nlp = spacy.load("custom_model_artifacts")

@app.post("/predict/")
async def predict_category(text_in: TextIn):
    # Process the text through the loaded spaCy model
    doc = nlp(text_in.text)
    
    # Extract the predicted categories and their scores
    # Assuming your model outputs a dictionary in doc.cats with category names as keys and scores as values
    cats = doc.cats
    # Find the category with the highest score
    predicted_category = max(cats, key=cats.get)
    score = cats[predicted_category]

    return {"predicted_category": predicted_category, "score": score}


@app.get("/")
async def root():
    return {"message": "Hello World"}