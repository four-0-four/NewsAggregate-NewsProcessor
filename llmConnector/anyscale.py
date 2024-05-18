from collections import Counter
import openai


client = openai.OpenAI(
    base_url = "https://api.endpoints.anyscale.com/v1",
    api_key = "esecret_4975vlked3sj5uf664jx5bq4rn"
)

models = {
    1: "meta-llama/Llama-2-13b-chat-hf",#ok categorizer
    2: "mlabonne/NeuralHermes-2.5-Mistral-7B",#aweful categorizer, good summarizer
    3: "mistralai/Mixtral-8x7B-Instruct-v0.1", #good categorizer
    4: "google/gemma-7b-it", #good categorizer
    5: "mistralai/Mistral-7B-Instruct-v0.1"
}

def call_anyscale(query, system_prompt, model_id, temperature=0.5):
    # Note: not all arguments are currently supported and will be ignored by the backend.
    query = query
    system_prompt = system_prompt
    chat_completion = client.chat.completions.create(
        model=models[model_id],
        messages=[{"role": "system", "content": system_prompt}, 
                {"role": "user", "content": query}],
        temperature=temperature
    )
    return chat_completion.choices[0].message.content