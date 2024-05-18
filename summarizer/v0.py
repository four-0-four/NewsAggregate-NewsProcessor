from llmConnector.anyscale import call_anyscale

def summarize_anyscale(text):
    # Note: not all arguments are currently supported and will be ignored by the backend.
    query = "summarize the news below. at most 300 words and break into paragraphs if necessary. make sure the summary is understandable, contains most of the details and has a good flow. Here is the news: <NEWS>"+text+"</NEWS>"
    system_prompt = "summarize the news below. at most 300 words and break into paragraphs if necessary. make sure the summary is understandable, contains most of the details and has a good flow. provide as much detail as possible in the summary"
    return call_anyscale(query, system_prompt, 2, 0.5)