import asyncio
import datetime
from logging import exception

# Now, import your modules after adding their directories to sys.path
from categorizer.v0 import predict_category as predict_category_v0
from summarizer.v0 import summarize_anyscale as summarize_anyscale_v0
from database import check_processed_for_news, check_that_news_is_categorized, does_news_has_already_category, fetch_news_by_id, get_unprocessed_news, insert_news_category, insert_summary_for_news
from dotenv import load_dotenv
import os

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


######################################categories################################
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
##################################################################################


async def process_news(conn_params, logging=False):
    unprocessed_news = await get_unprocessed_news(conn_params)
    print("unprocessed news: ", len(unprocessed_news))
    for news in unprocessed_news:
        print("***************************************")
        print("processing news: ", news.get('id'))
        longSummary = None
        #check if news is not summarized, summarize it
        if not news.get('summarized'):
            longSummary = await get_news_summary(conn_params, news, logging)
        
        #check if news is not categorized, categorize it
        if not await does_news_has_already_category(conn_params, news.get('id')) or not news.get('ProcessedForIdentity'):
            await get_news_category(conn_params, news, longSummary, logging)
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
        longSummary = summarize_anyscale_v0(title + " - " + content)
        while len(longSummary) < 100:
            print("WARNING: news summary is too short, trying again")
            longSummary = summarize_anyscale_v0(title + " - " + content)
        
        if logging:
            end_time = datetime.datetime.now()
            duration = end_time - start_time
            print("got news summary",len(longSummary),"characters long and it took",duration)
        
        success = await insert_summary_for_news(conn_params, news_id, longSummary)
        if success:
            print(f"Successfully inserted summary for news ID {news_id}")
            return longSummary
        else:
            print(f"Failed to insert summary for news ID {news_id}")
            return news_entry.get('longSummary')
    else:
        print("WARNING: news ", news_id, " already has summary")
        return news_entry.get('longSummary')
        

async def get_news_category(conn_params, news_entry, longSummary=None, logging=False):
    title = news_entry.get('title')
    
    #since the news category uses the summary, we need to make sure that the news has summary
    while not longSummary:
        print(f"WARNING: news does not have summary, trying to get summary. News id: {news_entry.get('id')}")
        longSummary = await get_news_summary(conn_params, news_entry, logging)
    
    #step3: categorized the news and save it in the database
    if logging:
        print("inserting category")
    # Insert news category with try-except block
    if not await does_news_has_already_category(conn_params, news_entry.get('id')):
        print("news does not have category and aboiut to predict category")
        category = -1
        try:
            #all_text = title + " . " + content
            category_response = predict_category_v0(longSummary[:4000], CATEGORIES_TABLE)
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
    
    #news = """In Iran, Bahai minority faces persecution even after death\nParis (AFP) – A flattened patch of earth is all that remains of where the graves once stood –- evidence, Iran's Bahais say, that their community is subjected to persecution even in death.\n\nIssued on: 22/03/2024 - 11:57\nModified: 22/03/2024 - 11:56\n\n3 min\nOne of the Bahai faith's major temples is in Haifa, Israel, although its spiritual roots are in 19th century Iran\nOne of the Bahai faith's major temples is in Haifa, Israel, although its spiritual roots are in 19th century Iran © RONALDO SCHEMIDT / AFP/File\nBeneath the ground in the Khavaran cemetery in the southeastern outskirts of Tehran lie the remains of at least 30 and potentially up to 45 recently-deceased Bahais, according to the Bahai International Community (BIC).\n\nBut their resting places are no longer marked by headstones, plaques and flowers, as they once were, because, said the BIC, this month Iranian authorities destroyed them and then levelled the site with a bulldozer.\n\nThe desecration of the graves represents a new attack against Iran's biggest non-Muslim religious minority which has, according to its representatives, been subjected to systematic persecution and discrimination since the foundation of the Islamic republic in 1979.\n\nThe alleged destruction has been condemned by the United States, which has also criticised the ongoing persecution of the Bahais, as have United Nations officials.\n\nUnlike other minorities, Bahais do not have their faith recognised by Iran's constitution and have no reserved seats in parliament. They are unable to access the country's higher education and they suffer harassment ranging from raids against their businesses to confiscation of assets and arrest.\n\nEven death does not bring an end to the persecution, the BIC says.\n\nAccording to the community, following the 1979 Islamic revolution in Iran, the authorities confiscated two Bahai-owned burial sites and now forcibly bury their dead in Khavaran.\n\nThe cemetery is the site of a mass grave where political prisoners executed in 1988 are buried.\n\n"They want to put pressure on the Bahai community in every way possible," Simin Fahandej, the BIC representative to the United Nations, told AFP.\n\n"These people have faced persecution all their lives, were deprived of the right to go to university, and now their graves are levelled."\n\nThe US State Department's Office of International Religious Freedom said it condemned the "destruction" of the graves at the cemetery, adding that Bahais "in Iran continue to face violations of funeral and burial rights".\n\n'Going after the dead'\nThe razing of the graves comes at a time of intensified repression of the Bahai community in Iran, which representatives believe is still hundreds of thousands strong.\n\nSenior community figures Mahvash Sabet, a 71-year-old poet, and Fariba Kamalabadi, 61, were both arrested in July 2022 and are serving 10-year jail sentences.\n\nBoth were previously jailed by the authorities in the last two decades.\n\n"We have also seen the regime dramatically increase Bahai property seizures and use sham trials to subject Bahais to extended prison sentences," said the US State Department.\n\nAt least 70 Bahais are currently in detention or are serving prison sentences, while an additional 1,200 are facing court proceedings or have been sentenced to prison sentences, according to the United Nations.\n\nThe Bahai faith is a relatively young monotheistic religion with spiritual roots dating back to the early 19th century in Iran.\n\nMembers have repeatedly faced charges of being agents of Iran's arch-foe Israel, which activists say are without any foundation.\n\nThe Bahais have a spiritual centre in the Israeli port city of Haifa, but its history dates back to well before the establishment of the state of Israel in 1948.\n\n"The fact that they are going after the dead shows that they are motivated by religious persecution and not by a perceived threat to national security or society," said Fahandej.\n\nRepression of the Bahais, 200 of whom were executed in the aftermath of the Islamic revolution, has varied in strength over the last four-and-a-half decades but has been in one of its most intense phases in recent years, community members and observers say.\n\nThe UN special rapporteur on human rights in Iran, Javaid Rehman, told the UN Human Rights Council in Geneva this week he was "extremely distressed and shocked at the persistent persecution, arbitrary arrests and harassment of members of the Bahai community".\n\nFahandej said it was not clear what had prompted the current crackdown but noted it came as the authorities seek to stamp out dissent of all kinds in the wake of the nationwide protests that erupted in September 2022.\n\n"The treatment of the Bahais is very much connected with the overall situation of human rights in the country," she said."""
    #print("**************************************")
    #summary = summarize_anyscale_v0(news)
    #print("summary: ", summary)
    #category = predict_category_v0(summary, CATEGORIES_TABLE)
    #print("category: ", category)
    #print(predict_category(news))

    