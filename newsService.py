# Import necessary modules
from newsData import fetch_corporation, fetch_news_by_title
from newsData import insert_news, check_news_title_exists
            
async def add_news_to_database(conn_params, corporationId, title, content, pubDate, url,image_url, logging=False):
    if logging:
        print("**********************************************")
    if await check_news_title_exists(conn_params, title):
        if logging:
            print(f"news already exists in the database, {title}")
        news_entry = await fetch_news_by_title(conn_params, title)
    else:
        try:
            corporation = await fetch_corporation(conn_params, corporationId)
            if not corporation:
                print(f"Corporation not found: {corporationId}")
                return "Corporation not found"
            news_entry = await insert_news(conn_params, title, content, pubDate, url, image_url, corporation.get('id'), corporation.get('name'), corporation.get('logo'))
        except Exception as e:
            print(f"Failed to insert news to database: {e}, {title}")
            return "Failed to insert news"
        
    if logging:
        print("inserting the news", news_entry.get('id'))   
        print("getting the categories for news")
    
    if news_entry == -1:
        print(f"Failed to insert news, {title}")
        return "Failed to insert news"
        
    return news_entry.get('id')
            