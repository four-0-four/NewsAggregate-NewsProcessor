import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize a Web API client
client = WebClient(token="xoxb-6821142320225-7183085937776-3VlTaXBgCqunJgJQXi32jrS3")

def create_text_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(content)
        
def delete_text_file(filename):
    if os.path.exists(filename):
        os.remove(filename)

# Function to send the initial warning message and follow-up replies
def send_slack_message_long_summary_warning(long_text, summary_text):
    channel_id = "C074HK22SVC"
    
    # Create text files
    long_text_filename = "long_text.txt"
    summary_text_filename = "summary_text.txt"
    create_text_file(long_text_filename, long_text)
    create_text_file(summary_text_filename, summary_text)
    
    
    try:
        # Send the initial warning message
        response = client.chat_postMessage(
            channel=channel_id,
            text=f"[WARNING] ⚠️ long text to summarize!"  # Adjust the preview length as needed
        )
        
        # Extract the timestamp of the initial message
        thread_ts = response['ts']
        
        # Upload the long text file
        response_long_text = client.files_upload_v2(
            channels=[channel_id],
            file=long_text_filename,
            title="Long Text",
            initial_comment="Here is the long text:",
            thread_ts=thread_ts
        )
        
        # Upload the summary text file
        response_summary_text = client.files_upload_v2(
            channels=[channel_id],
            file=summary_text_filename,
            title="Summary Text",
            initial_comment="Here is the summary:",
            thread_ts=thread_ts
        )
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")
    finally:
        # Delete the text files after uploading
        delete_text_file(long_text_filename)
        delete_text_file(summary_text_filename)