from util.chunker import split_text, max_tokens
from llmConnector.anyscale import call_anyscale
from util.slack import send_slack_message_long_summary_warning

def summarize_anyscale(text):
    def summarize(text):
        query = "summarize the news below. at most 300 words and break into paragraphs if necessary. make sure the summary is understandable, contains most of the details and has a good flow. Here is the news: <NEWS>"+text+"</NEWS>"
        system_prompt = "summarize the news below. at most 300 words and break into paragraphs if necessary. make sure the summary is understandable, contains most of the details and has a good flow. provide as much detail as possible in the summary"
        return call_anyscale(query, system_prompt, 2, 0.5)

    # Split the text into chunks
    chunks = split_text(text, max_tokens)

    if len(chunks) == 1:
        return summarize(chunks[0])
    
    # Summarize each chunk
    chunk_summaries = [summarize(chunk) for chunk in chunks]
    
    # Combine chunk summaries into one text
    combined_summary_text = " ".join(chunk_summaries)
    
    # Final summary of the combined summaries
    final_summary = summarize(combined_summary_text)
    
    #send to slack
    send_slack_message_long_summary_warning(text,final_summary)
    
    return final_summary