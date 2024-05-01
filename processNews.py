import asyncio
import datetime
from logging import exception

# Now, import your modules after adding their directories to sys.path
from anyscale import predict_category, summarize_anyscale
from database import check_processed_for_news, check_that_news_is_categorized, does_news_has_already_category, fetch_news_by_id, get_unprocessed_news, insert_news_category, insert_summary_for_news
from newsdataapi import NewsDataApiClient
from dotenv import load_dotenv
import spacy
import os
import json

from archive.stablediffusion import get_news_summary


# Load environment variables from .env file
load_dotenv()


conn_params_stage = {
    "host": os.getenv("DATABASE_HOST_PRODUCTION", "localhost"),
    "port": int(os.getenv("DATABASE_PORT_PRODUCTION", "3306")),  # Convert port to integer
    "user": os.getenv("DATABASE_USERNAME_PRODUCTION", "root"),
    "password": os.getenv("DATABASE_PASSWORD_PRODUCTION", "password"),
    "db": os.getenv("DATABASE_NAME_PRODUCTION", "newsdb"),
}


conn_params_production = {
    "host": os.getenv("DATABASE_HOST_PRODUCTION", "localhost"),
    "port": int(os.getenv("DATABASE_PORT_PRODUCTION", "3306")),  # Convert port to integer
    "user": os.getenv("DATABASE_USERNAME_PRODUCTION", "root"),
    "password": os.getenv("DATABASE_PASSWORD_PRODUCTION", "password"),
    "db": os.getenv("DATABASE_NAME_PRODUCTION", "newsdb"),
}       


async def process_news(conn_params, logging=False):
    unprocessed_news = await get_unprocessed_news(conn_params)
    print("unprocessed news: ", len(unprocessed_news))
    for news in unprocessed_news:
        print("processing news: ", news.get('id'))
        
        #check if news is not summarized, summarize it
        if not news.get('summarized'):
            await get_news_summary(conn_params, news, logging)
        
        #check if news is not categorized, categorize it
        if not await does_news_has_already_category(conn_params, news.get('id')) or not news.get('ProcessedForIdentity'):
            await get_news_category(conn_params, news, logging)
        else:
            print("news already categorized")
        
   
      
async def get_news_summary(conn_params, news_entry, logging=False):
    title = news_entry.get('title')
    content = news_entry.get('content')
    news_id = news_entry.get('id')
    
    #step2: get the summary of each news and save to database
    #Note: make sure to turn on the is summarized on
    if logging:
        print("getting the news summary")
        start_time = datetime.datetime.now()
    
    if not news_entry.get('summarized'):    
        longSummary = summarize_anyscale(title + " - " + content)
        while len(longSummary) < 100:
            print("WARNING: news summary is too short, trying again")
            longSummary = summarize_anyscale(title + " - " + content)
        
        if logging:
            end_time = datetime.datetime.now()
            duration = end_time - start_time
            print("got news summary",len(longSummary),"characters long and it took",duration)
        
        await insert_summary_for_news(conn_params, news_id, longSummary)
    else:
        print("WARNING: news ", news_id, " already has summary")
        

async def get_news_category(conn_params, news_entry, logging=False):
    title = news_entry.get('title')
    content = news_entry.get('content')
    
    #step3: categorized the news and save it in the database
    if logging:
        print("inserting category")
    # Insert news category with try-except block
    if not await does_news_has_already_category(conn_params, news_entry.get('id')):
        print("news does not have category and aboiut to predict category")
        category = -1
        try:
            all_text = title + " . " + content
            category_response = predict_category(all_text[:4000])
            print("category_response: ", category_response)
            category = int(category_response)
        except ValueError:
                # Handle the error (e.g., log it, return an error message, etc.)
                print("Failed to get and convert category")
        
        try:
            print("insert cat to database")
            await insert_news_category(conn_params, news_entry.get('id'), category)
            print("checking that news is categorized")
            await check_processed_for_news(conn_params, news_entry.get('id'))
        except Exception as e:
            print(f"Failed to insert news category: {e}, {title}") 
    else:
        await check_processed_for_news(conn_params, news_entry.get('id'))
        if logging:
            print("news already has category")
        
        
        


# Run the main function using asyncio.run() if your Python version is 3.7+
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    
    environment = os.getenv("ENV","stage")
    loop.run_until_complete(process_news(conn_params_stage, True))
    '''
    if environment == "stage" or environment == "dev":
        print("############################################")
        print("Running in stage environment")
        print("############################################")
        loop.run_until_complete(news_for_all_urls(conn_params_stage, True))
    else:
        print("############################################")
        print("Running in production environment")
        print("############################################")
        loop.run_until_complete(news_for_all_urls(conn_params_production, True))
    '''


    