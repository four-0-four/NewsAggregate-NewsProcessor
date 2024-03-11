from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import spacy
from summarizer import summarize

# Define a Pydantic model for the request body
class TextIn(BaseModel):
    text: str

# Initialize FastAPI app
app = FastAPI()

# Load your trained spaCy model
nlp = spacy.load("custom_model_artifacts")

@app.post("/categorize/")
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

class TextInForSummarization(BaseModel):
    text: str

@app.post("/summarize/")
async def perform_summarization(text_in: TextInForSummarization):
    summary = summarize(text_in.text)
    return {"summary": summary}


@app.get("/")
async def root():
    return {"message": "Hello World"}