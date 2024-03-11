from transformers import T5ForConditionalGeneration, AutoTokenizer

# Initialize the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("mrm8488/t5-base-finetuned-summarize-news")
model = T5ForConditionalGeneration.from_pretrained("mrm8488/t5-base-finetuned-summarize-news")

def summarize(text, max_length=300):
    # Encode the input text and move the tensor to the same device as the model
    input_ids = tokenizer.encode(text, return_tensors="pt", add_special_tokens=True)
    # Generate the summary using the model
    generated_ids = model.generate(input_ids=input_ids,
                                   num_beams=4,
                                   max_length=max_length,
                                   repetition_penalty=2.5,
                                   length_penalty=1.0,
                                   early_stopping=True)
    # Decode the generated ids to text and return the first (and typically only) item
    preds = [tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=True) for g in generated_ids]
    return preds[0]