import asyncio
import datetime
from logging import exception

# Now, import your modules after adding their directories to sys.path
from anyscale import predict_category, summarize_anyscale
from newsData import check_that_news_is_categorized, does_news_has_already_category, fetch_news_by_id, get_news_source_urls, insert_news_category, insert_summary_for_news
from newsService import add_news_to_database
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
        
async def get_news_given_url_and_save(conn_params, url, corporationId, logging=False):
    # API key authorization, Initialize the client with your API key
    api = NewsDataApiClient(apikey="pub_38741469a1fcf444f2b92bb3d3d178a0951e8")
    news_id_added = []
    print("about to get news")

    page=None
    reponse = None
    count = 0
    while True:
        response = api.news_api(page = page, domainurl=url, timeframe=8)
        
        if response.get('status') != 'success':
            print("Failed to fetch news: ", response.get('message'))
            break
        
        # Save the news data to the database
        for news in response.get('results'):
            count += 1
            
            #condition: len(title)> 10 and len(content) > 100 -> to make sure it is not empty
            if len(news.get('title')) < 10 or len(news.get('content')) < 100:
                print(f"WARNING: news title or content is too short: {news.get('title')}")
                continue
            
            try:
                if logging:
                    start_time = datetime.datetime.now()  # Start timing
                news_id = await add_news_to_database(conn_params, corporationId, news.get('title'), news.get('content'), news.get('pubDate'), news.get('link'), news.get('image_url'), logging)
                if logging:
                    end_time = datetime.datetime.now()  # End timing
                    duration = end_time - start_time
                    print(f"Time taken to save news: {duration}")
                news_id_added.append(news_id)
            except Exception as e:
                print(f"Failed to save news: {e}, {news.get('title')}")
        
        page = response.get('nextPage',None)
        if not page:    
            break
    if logging:
        print(f"**********Saved {count} news articles from {url}")
    
    return news_id_added

async def news_for_one_url(conn_params, corporationURL, corporationID, logging=False):
    news_ids_saved = []
    try:
        news_ids_saved_for_one_organization = await get_news_given_url_and_save(conn_params, corporationURL, corporationID, logging)
        news_ids_saved.extend(news_ids_saved_for_one_organization)
    except Exception as e:
        print(f"Failed to get news for {corporationURL}: {e}")
        
    await get_news_summary_and_category(conn_params, news_ids_saved, logging)
                

async def news_for_all_urls(conn_params, logging=False):
    corporationUrls = await get_news_source_urls(conn_params)
    news_ids_saved = []
    
    #step1: get all news from newsdata.io and save to database
    #condition: len(title)> 10 and len(content) > 100 -> to make sure it is not empty
    for corporationUrl in corporationUrls:
        if(corporationUrl["url"] == None or corporationUrl["api-newsdata.io"] == 0):
            continue
        # Remove 'https://www.' from the URL
        clean_url = corporationUrl["url"].replace("https://www.", "")
        corporationId = corporationUrl["CorporationID"]
        try:
            news_ids_saved_for_one_organization = await get_news_given_url_and_save(conn_params, clean_url, corporationId, logging)
            news_ids_saved.extend(news_ids_saved_for_one_organization)
        except Exception as e:
            print(f"Failed to get news for {clean_url}: {e}")
            
    await get_news_summary_and_category(conn_params, news_ids_saved, logging)
      
async def get_news_summary_and_category(conn_params, news_ids_saved, logging=False):    
    for news_id in news_ids_saved:
        news_entry = await fetch_news_by_id(conn_params, news_id)
        title = news_entry.get('title')
        content = news_entry.get('content')
        
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
        
        #step3: categorized the news and save it in the database
        if logging:
            print("inserting category")
        # Insert news category with try-except block
        print("news id: ", news_entry.get('id'))
        if not await does_news_has_already_category(conn_params, news_entry.get('id')):
            print("news does not have category and aboiut to predict category")
            category = -1
            try:
                category_response = predict_category(title+" . "+content)
                print("category_response: ", category_response)
                category = int(category_response)
            except ValueError:
                    # Handle the error (e.g., log it, return an error message, etc.)
                    print("Failed to get and convert category")
            
            try:
                print("insert cat to database")
                await insert_news_category(conn_params, news_entry.get('id'), category)
                print("check that news is categorized")
                await check_that_news_is_categorized(conn_params, news_entry.get('id'))
            except Exception as e:
                print(f"Failed to insert news category: {e}, {title}") 
        else:
            if logging:
                print("news already has category")


# Run the main function using asyncio.run() if your Python version is 3.7+
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    
    environment = os.getenv("ENV","stage")
    loop.run_until_complete(news_for_one_url(conn_params_stage, "cbc.ca", 19, True))
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


    