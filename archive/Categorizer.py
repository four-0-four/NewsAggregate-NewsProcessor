import asyncio
import requests
from pydantic import BaseModel
import spacy
from collections import Counter
import logging
import os

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


api = "7rTSZ5vBbK16GjuSbWMmQhmvYaw5NJQmCpNzPpac52FumYbjbJw0hc2rMD0G"
url = "https://modelslab.com/api/v5/uncensored_chat"
claude_secret_key="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"

# Assuming the anthropic client is setup similarly to other HTTP clients
try:
    import anthropic
    claude_client = anthropic.Anthropic(api_key=claude_secret_key)
except ImportError:
    logging.error("Anthropic module not found. Ensure it's installed and imported correctly.")
    claude_client = None

CATEGORIES_TABLE = {
    0: 'Politics',
    1: 'Business & Economy',
    2: 'Health',
    3: 'Art & Culture',
    4: 'Technology',
    5: 'Science',
    6: 'Society & Lifestyle',
    7: 'Sports',
    8: 'Environment',
}

def find_category_in_text(text, categories):
    reversed_categories = {value: key for key, value in categories.items()}
    for category_name in reversed_categories.keys():
        if category_name in text:
            start_index = text.rfind(category_name)
            for i in range(start_index, -1, -1):
                if text[i].isdigit():
                    end_index = i
                    while i > 0 and text[i-1].isdigit():
                        i -= 1
                    category_index = int(text[i:end_index+1])
                    if category_index == reversed_categories[category_name]:
                        return category_index, category_name
    return None, None

async def predict_category_ourtrainedModel(nlp, text: str):
    doc = nlp(text)
    cats = doc.cats
    predicted_category = max(cats, key=cats.get)
    score = cats[predicted_category]
    return {"predicted_category": predicted_category, "score": score}

async def predict_category_stable_diffusion_model(text):
    headers = {"Content-Type": "application/json"}
    CATEGORIES_STR = "CATEGORIES_TABLE = {0: 'Politics', 1: 'Business & Economy', 2: 'Health', 3: 'Art & Culture', 4: 'Technology', 5: 'Science', 6: 'Society & Lifestyle', 7: 'Sports', 8: 'Environment',}"
    
    data = {
        "key": api,
        "messages": [
            {
                "role": "user",
                "content": f"""between the categories provided {CATEGORIES_STR} which category the following news belong to? please provide the index of category for answer and do not provide explanation for why you chose the category <NEWS>{text}</NEWS>"""
            }
        ],
        "max_tokens": 2000
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "success":
            return data["message"]
        else:
            logging.error("Stable diffusion model response was not successful.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Request to Stable Diffusion Model failed: {e}")
        return None


async def predict_category_nlp_cloude(text):
    nlp_cloud_endpoint = "https://api.nlpcloud.io/v1/bart-large-mnli-yahoo-answers/classification"
    nlp_cloud_api_key = ""
    #nlp_cloud_api_key = "d5c437840586f3e10af9e9b9eea290531b21f028"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {nlp_cloud_api_key}"
    }
    
    data = {
        "text": text,
        "labels": ['Politics', 'Business & Economy', 'Health', 'Art & Culture', 'Technology', 'Science', 'Society & Lifestyle', 'Sports', 'Environment'],
        "multi_class": True
    }
    try:
        response = requests.post(nlp_cloud_endpoint, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
            # Find the category with the highest score
        max_score_index = data['scores'].index(max(data['scores']))
        # Return the index of the category in CATEGORIES_TABLE
        return max_score_index
    except requests.exceptions.RequestException as e:
        logging.error(f"Request to Stable Diffusion Model failed: {e}")
        return None

async def predict_category(nlp, text: str):
    response_ourtrainedModel = await predict_category_ourtrainedModel(nlp, text)
    predicted_category_1 = int(response_ourtrainedModel["predicted_category"].replace("label_", ""))

    #try stable diffusion three times until we get a response
    trial = 0
    response_stable_diffusion_model = await predict_category_stable_diffusion_model(text[:1700])
    while trial < 3 and not response_stable_diffusion_model:
        response_stable_diffusion_model = await predict_category_stable_diffusion_model(text[:1700])
        trial += 1
    
    if response_stable_diffusion_model:
        try:
            predicted_category_2 = int(response_stable_diffusion_model.split(':')[0].strip())
        except ValueError:
            logging.error("Error extracting category index from stable diffusion model response.")
            predicted_category_2 = None
    else:
        predicted_category_2 = None

    if predicted_category_2 and predicted_category_1 == predicted_category_2:
        return predicted_category_1

    response_nlp_cloud = await predict_category_nlp_cloude(text[:1700])
    predicted_category_3 = response_nlp_cloud if response_nlp_cloud is not None else None
    
    # Aggregate the results and decide the final category
    categories = [predicted_category_1, predicted_category_2, predicted_category_3]
    categories_filtered = [cat for cat in categories if cat is not None]

    # Use Counter to find the most common category among the predictions
    if categories_filtered:
        most_common_category, count = Counter(categories_filtered).most_common(1)[0]
        
        # Check if the most common category is clearly more common than the others
        if count > 1:
            final_category = most_common_category
        else:
            # If there's no clear consensus (e.g., all categories are different),
            # fallback to Claude's response
            final_category = predicted_category_3
    else:
        # If no categories were predicted (all were None), you might want to define a default behavior
        final_category = None  # or any other default action

    return final_category

if __name__ == "__main__":
    # Load your trained spaCy model
    nlp = spacy.load("custom_model_artifacts")
    # Example usage
    title = "Shawna Dolansky: Carleton union empowers profs to teach lies about Israel"
    content = "Dan Brown\u2019s \u201cThe Da Vinci Code\u201d came out just after I finished my PhD. As a post-doctoral fellow teaching courses in San Diego on the Bible and early Judaism and Christianity, I was invited to give a public lecture discussing the book from a historian\u2019s perspective. I had been giving public lectures for a few years \u2014 graduate students are known to jump at the opportunity to share their knowledge for pennies \u2014 and I was experienced enough to know how to navigate the religious sensibilities of audience members and anticipate certain types of questions. But when I launched into a discussion of what I thought was wrong with Brown\u2019s sensationalist positioning of his fictional account as authentic history, I was utterly unprepared for the backlash and heckling I got from several members of the audience. How did I know that his claims about Jesus, Mary, da Vinci and the Templars weren\u2019t true? Maybe, they said, I was just jealous that he had used his understanding of history to write a bestselling novel, and here I was giving public lectures in community centres for peanuts. What makes my \u201copinion\u201d about what happened 2,000 years ago better than Brown\u2019s? Last week, my union, the Carleton University Academic Staff Association, released a series of \u201c Guidelines on Academic Freedom ,\u201d ostensibly to help members better understand what we can say in the classroom. The \u201cguidelines\u201d state that, \u201cMembers should interpret academic freedom to mean that speech about topics such as the decades-long conflict in Israel/Palestine can be appropriate in a broad range of settings because debates about justice and identity shape the contexts in which we teach and in which students learn.\u201d Furthermore, \u201cMembers should be aware that what is relevant to their pedagogy, educational objectives and course themes can be interpreted broadly, and that censorship in this regard would violate academic freedom.\u201d The document\u2019s introduction explains that it was necessary to develop such guidelines in light of the blow-back that some faculty members were receiving for speaking about \u201ccolonialism and racism in their classrooms; instructors voicing their concerns about genocide have been accused by students of creating a hostile learning environment.\u201d In addition to blithely using terms like \u201ccolonialism\u201d and \u201capartheid\u201d to describe the situation in Israel, and referring to the war against Hamas as a \u201cgenocide,\u201d one of the many shocking examples contained in the \u201cnon-exhaustive list\u201d of items the union considers \u201cto be acceptable speech and of public interest\u201d is \u201ccontextualizing the 10/7 attacks as a part of an ongoing history of violent conflict.\u201d The complete distortion, misinformation and baldly biased premises on which these guidelines are based shouldn\u2019t surprise me after everything I\u2019ve witnessed over the past five months, but somehow, they still do. Under what guise can the union empower professors to teach about issues they have no expertise in? It\u2019s clear that the authors of these guidelines don\u2019t have specific expertise in this subject area, and don\u2019t properly understand terms such as \u201cgenocide,\u201d \u201capartheid\u201d and \u201ccolonialism,\u201d or the ways in which they might accurately be applied to international affairs. How would these zealous defenders of academic freedom feel if I took my PhD in history to entitle myself to speak with authority in a classroom about subjects in which they are experts and I am not? Should I pontificate on media production and design, global social inequality or post-colonial film studies? All this time, I thought I was supposed to teach students the subjects I am an expert in, and leave other topics to those who studied them. But heck, why should I limit myself to only speak to students in my classroom about what I actually know? The union\u2019s mandate is \u201cto promote the well-being of the academic community, to defend academic freedom and to promote the individual interests of its members, as well as to maintain the quality and integrity of the university as an academic institution.\u201d The only aspect of this statement that is served by its new \u201cguidelines\u201d is that of promoting the individual interests of some of its members \u2014 interests that are patently political. This is not what a union is for. There is no universe in which my union dues should support directives that authorize physicists or psychologists to teach students that Israel is an illegitimate country or that savage rapes and massacres committed against citizens of a sovereign state need to be contextualized. Twenty years ago at that community centre in San Diego, I responded to the hecklers by telling them that seven years of work toward a PhD had given me not only deep knowledge of the ancient world, but also an understanding of how to conduct proper research and distinguish fact from fiction, actual events from conspiracy theories and truth from propaganda. And I freely admitted that I was a starving post-doc who would love to have the luxury of time to write historical fiction. Was I jealous that Brown spun some bad historiography into a multi-million dollar enterprise? Sure. But it wasn\u2019t jealousy that drove my critique. Rather, it was a sense of moral responsibility to be as accurate as possible in the information I convey to an audience, and to be as transparent as possible about how I know what I know. Abdicating that moral responsibility is not \u201cacademic freedom,\u201d any more than Israel is a colonial enterprise or an apartheid state committing genocide. Purveying misinformation under the guise of academic freedom is an abuse of academic authority that does nothing to promote the well-being of the academic community or defend academic freedom, and completely undermines the quality and integrity of the university as an academic institution. National Post Shawna Dolansky is an associate professor in the College of the Humanities at Carleton University in Ottawa."
    response = asyncio.run(predict_category(nlp, title + " . " + content))