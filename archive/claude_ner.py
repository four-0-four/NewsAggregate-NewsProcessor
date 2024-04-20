import asyncio
import os

from dotenv import load_dotenv
import requests
import json

from entitiesData import add_entity, check_and_add_news_entity, get_any_entities_contain_name
#https://huggingface.co/mrm8488/t5-base-finetuned-summarize-news

claude_secret_key="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"

import anthropic
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

conn_params_stage = {
    "host": os.getenv("DATABASE_HOST_STAGE", "localhost"),
    "port": int(os.getenv("DATABASE_PORT_STAGE", "3306")),  # Convert port to integer
    "user": os.getenv("DATABASE_USERNAME_STAGE", "root"),
    "password": os.getenv("DATABASE_PASSWORD_STAGE", "password"),
    "db": os.getenv("DATABASE_NAME_STAGE", "newsdb"),
}


claude_client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=claude_secret_key,
)


def parse_entities_from_text(text):
    """
    Extracts a list of entities in JSON format from the given text and parses it.
    
    Args:
    text (str): A string containing the entities in JSON format.
    
    Returns:
    list: A list of dictionaries where each dictionary represents an entity.
    """
    # Extracting the JSON part from the text
    # The actual extraction might vary depending on the structure of the input text
    json_str_start = text.find('[')
    json_str_end = text.rfind(']') + 1
    json_str = text[json_str_start:json_str_end]
    
    # Parsing the JSON string into a Python list of dictionaries
    entities = json.loads(json_str)
    
    return entities

async def get_news_entities_claude(title, content):
    prompt = """given the news, identify all the main entities of the news 
    including famous people, sport teams, teams, profession, Landmarks(please do not mention location such as city or country), Religious Group, Political Group, Work of Art (for example, Titles of books, songs, and other artworks), scientific terms, Drug/Pharmaceutical, medical conditions, organizations, festivals, diseases, events, ... (any important entities).
    please do not mention entities without type. do not place illegal or inappropriate entities like 'joint butts'. write the full entities and not abbreviated.\n
    """
    
    
    news = "Here is the News:\n<News>\n"+title+" - "+content+"""\n</News> keep the following in mind while providing the entities:\n
    please do not mention entities without type.if you mention breed of animal create a new entity for the animal category. for {'name': 'Cocker Spaniel', 'type': 'Dog Breed'}, create {'name': 'Dogs', 'type': 'Animal'}. For medical Conditions, (exclude symptoms and only give me name of the medical condition. forexample, except telling {'name': 'Seizures', 'type': 'Medical Condition'}, {'name': 'Stroke', 'type': 'Medical Condition'}, just mention {'name':'Liver Cancer', 'type':'Medical Condition'} or  {'name':'Pot Poisining', 'type':'Medical Condition'} or  {'name':'HIV virus', 'type':'Medical Condition'})\n
    names should be full and complete. For Sports Teams, put the full team name and for type put the type of sport. For {'name': 'Canucks', 'type': 'Sports Team'}, it should be {'name': 'Vancouver Canucks', 'type': 'Hockey Team'}\nFor person name, put the full name if possible and for type put the profession. For {'name': 'J.T. Miller', 'type': 'Person'} should be {'name':'Jonathan Tanner Miller', 'type':'Person'}\n"""
            
                                
    message = claude_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0,
        system=prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": news
                    }
                ]
            }
        ]
    )
    print("****************************************")
    return parse_entities_from_text(message.content[0].text)


async def match_news_entities_with_db(entities, db_entities, logging=False):
    did_not_find_match_in_db = []
    claude_entities_no_match = []
    processed_entities = []
    
    if logging:
        print("***************************input")
        print("db:")
        print(db_entities)
        print("claude:")
        print(entities)
    
    # Normalize entity names for comparison and handle duplicates
    db_entities_normalized = {}
    for entity in db_entities:
        # Normalize name and type for consistent comparison
        normalized_name = entity['name'].strip().lower()
        entity_type = entity['type'].strip().lower()
        
        # Use tuple of name and type as key to handle duplicates
        db_entities_normalized[(normalized_name, entity_type)] = entity
    
    for entity in entities:
        normalized_name = entity['name'].strip().lower()
        entity_type = entity['type'].strip().lower()
        key = (normalized_name, entity_type)
        
        if key in db_entities_normalized:
            # Exact match found, add to processed_entities
            matched_entity = db_entities_normalized[key]
            processed_entities.append({
                'name': entity['name'],
                'type': entity['type'],
                'id': matched_entity['id']
            })
            # Remove matched entity to track unmatched db entities
            del db_entities_normalized[key]
        else:
            # No exact match found
            claude_entities_no_match.append(entity)
    
    # Remaining unmatched entities in the DB
    did_not_find_match_in_db = list(db_entities_normalized.values())
    
    if logging:
        print("***************************preporcessing")
        print("db:")
        print(did_not_find_match_in_db)
        print("claude:")
        print(claude_entities_no_match)
        print("processed:")
        print(processed_entities)
    
    # Prepare for Claude API call with unmatched entities
    prompt = """given the entities provided by claudeapi:\n
    <CLAUDE ENTITIES>\n
    """ + json.dumps(claude_entities_no_match) + """
    \n</CLAUDE ENTITIES>\n\n
    and the entities provided by my database after searching for the above entities in my db:\n
    <DB ENTITIES>\n
    """ + json.dumps(did_not_find_match_in_db) + """
    \n</DB ENTITIES>\n\n
    compare them and return a list of entities in json with format name, type, id\n
    if the claude entities exists in the database entities and they match definition wise and logic wise. return the id of database\n
    if they don't match or claude entities does not exists in db entities return -1 for id"""
    
    # Assume claude_client.messages.create() and parse_entities_from_text() are defined elsewhere
    message = claude_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0,
        system="find the entities already in the database",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    # Parse the response and integrate with processed_entities
    additional_processed_entities = parse_entities_from_text(message.content[0].text)
    processed_entities.extend(additional_processed_entities)
    
    if logging:
        print("***************************after")
        print("processed:")
        print(processed_entities)
    
    return processed_entities


async def add_entities_to_database(conn_params, processed_entities):
    for entity in processed_entities:
        await add_entity(conn_params, entity['name'], entity['type'])

async def get_ner_and_save(conn_params, news_id,  title, content):
    entites = await get_news_entities_claude(title, content)
    
    all_db_entities = []
    unique_entity_names = set()  # Set to track unique entity names or identifiers

    for entity in entites:
        db_response = await get_any_entities_contain_name(conn_params, entity["name"])
        for db_entity in db_response:
            # Create a tuple of (name, type) to uniquely identify entities
            entity_key = (db_entity['name'], db_entity['type'])
            
            # Check if this unique key has not been added yet
            if entity_key not in unique_entity_names:
                unique_entity_names.add(entity_key)
                all_db_entities.append(db_entity)
            
    #change this to contained and uncontained entities in db
    parsed_entities = await match_news_entities_with_db(entites, all_db_entities, True)
    
    #add the entities to the entities table
    #get their id and store in parsed_entities
    for entity in parsed_entities:
        if entity['id'] == -1:
            entity_id = await add_entity(conn_params, entity['name'], entity['type'])
            entity['id'] = entity_id
    
    #save the news_id and entity_id in the news_entities table
    #for entity in parsed_entities:
    #    await check_and_add_news_entity(conn_params, news_id, entity['id'])

# Run the main function using asyncio.run() if your Python version is 3.7+
if __name__ == "__main__":
    #title="Parole board imposes strict conditions on Marissa Shephard's release from prison"
    #content="Marissa Shephard has reached her prison release date less than three years after admitting her role in the brutal killing of an 18-year-old Moncton man. Shephard, in her late 20s, is serving a sentence for manslaughter and arson after admitting her involvement in the Dec. 17, 2015, killing of Baylee Wylie. A Feb. 12 decision by the Parole Board of Canada provided to CBC News this week says Shephard is approaching statutory release . That's the point when an offender has served two-thirds of their sentence and must be released. Shephard will remain under supervision and must comply with a long list of conditions. Correctional Service Canada, which runs prisons, says Shephard's statutory release date was Feb. 27. But in an email Tuesday on Tuesday, the service didn't say if she had been released. WATCH | Marissa Shephard involved in brutal killing of 18-year-old Baylee Wylie in 2015 Parole board imposes restrictions on Marissa Shephard’s prison release 25 minutes ago Duration 1:58 Moncton woman convicted of manslaughter described as manipulative, aggressive and intimidating. 'As per the Privacy Act, we are not able to disclose personal information regarding an offender, including their location or whether they are currently serving their sentence in an institution or in the community,' it said. She'll be required to live at a 'community-based residential facility' or a psychiatric facility approved by Correctional Service of Canada. Marissa Shephard sentenced to 12 years in prison 'In assessing your case, and as you approach your legislated release date, the Board has not lost sight of the horrific and violent crimes you, along with your co-accused, committed against the victim; the pain, fear and suffering the victim endured leading up to a cruel and tragic death,' the decision states. 'Furthermore, the Board is sensitive to the trauma and lifelong emotional effects experienced by the victim's family at having lost a loved one in such a violent manner.' Shephard was among three people charged with murdering Wylie. Devin Morningstar was sentenced to life in prison, with no chance of parole for at least 25 years, after being convicted of first-degree murder in 2016. Tyler Noël was sentenced in 2017 to life with no chance of parole for 16 years after pleading guilty to second-degree murder. The body of 18-year-old Baylee Wylie was found in a burned-out townhouse in Moncton in December 2015. (Submitted) Shephard was found guilty of first-degree murder by a jury in 2018. Her conviction was overturned on appeal and a new trial ordered. She pleaded guilty to manslaughter and arson before the trial began. She was sentenced to 12 years in prison in August 2021. That time was reduced by years because she was credited 1½ days for each day spent in custody between her March 2016 arrest and sentencing. The parole board decision says 'during most of your sentence you have demonstrated poor institutional behaviour, have been described as manipulative, using intimidation, aggressive against staff as well as other inmates and have incited violence against other inmates.' Marissa Shephard pleads guilty to manslaughter, arson However, it says her recent behaviour appears to have 'stabilized,' and that she has shown 'early signs of stability and better emotional control.' That change is attributed to participation in programming, including a canine program., and spirituality The decision says Shephard hopes to upgrade her education in the 'canine field,' maintain employment and rely on support from family and her fiancée. A November 2022 psychological risk assessment rated her as a 'moderate' risk to reoffend, and to reoffend violently on day parole as 'low-moderate,' the decision states. The board imposed various conditions, including no contact with Wylie's family, to abstain from alcohol and drugs, report any sexual relationships and follow her treatment plan. The board says some community facilities were unwilling to accept Shephard, though two were. Police in those two areas, the decision states, 'are not supportive.' Devin Morningstar was convicted of first-degree murder in 2016. (Facebook) Her 2021 sentencing included an agreed statement of facts that she admitted. Wylie had been living with Shephard in a townhouse on Sumac Street in Moncton. In the days leading up to Wylie's death, Noël and Morningstar also lived there and consumed drugs. A fight between Wylie and Noël ensued, and Morningstar sided with Noël. Shepherd hit Wylie on the head with a bong during the fight but left while the fighting continued. Tyler Noël was sentenced in 2017 to life with no chance of parole for 16 years. (N.B. Crime Stoppers) Shephard said that when she returned, she panicked and joined in on the attacks against her friend, fearing the other two would turn against her. While Shephard admits taking part in the attack, she said she didn't inflict the fatal wounds. She also admitted helping start a fire to try to hide Wylie's remains in her home. Firefighters discovered Wylie's body beneath a mattress in the burned-out townhouse. Shephard's first trial heard that Wylie had been bound to a chair, beaten and stabbed with multiple objects that included a broken mirror and a box cutter. He suffered more than 140 sharp-force injuries — most while he was still alive."
    title="Canucks crush Jets 5-0, but lose Demko in second period"
    content="Casey DeSmith didn't expect to be in net for the Vancouver Canucks on Saturday. By the end of the night, though, the goaltender had turned away 10 shots and registered his second shutout of the season as the Canucks (42-17-7) blanked the Winnipeg Jets 5-0. The victory may be a costly one for Vancouver, however, as all-star goalie Thatcher Demko left midway through the second period. \u201cObviously not the circumstances I like to be a part of a game, but that's a heck of a win against a really good team,\u201d DeSmith said. \u201cAnd just to go drop of the puck all the way to the end of the game and really take it to them, that was an impressive win for the team.\u201d The unexpected lineup change came 6:40 into the middle frame when Demko left the ice and headed directly down the tunnel. He stopped all 12 shots he faced before departing. Canucks head coach Rick Tocchet did not say why his goalie left the ice. \u201cI haven't talked to the doctor. I don't think it's too serious, but I don't know. I can't speculate,\u201d Tocchet said after the game. Heading into Saturday's matchup, Demko sat tied with Alexandar Georgiev of the Colorado Avalanche with 33 wins on the season, the most in the NHL. Getting Demko more rest is something the Canucks want to do ahead of playoffs, Tocchet said. \u201cWe're going to have to really manage it,\u201d he said. \u201cI think we play three games in 11 days or something, so there's a lot of time for him to get some rest and whatever we got to do to get him healthy again. But yeah, we've got to manage him for sure.\u201d Vancouver's offensive onslaught started early on Saturday, with J.T. Miller putting away his 32nd goal of the season 2:05 into the game. Elias Pettersson, Nils Hoglander and Pius Suter each scored and notched an assist, while Phillip Di Giuseppe added a goal and Quinn Hughes had a pair of helpers. Connor Hellebuyck stopped 32-of-37 shots for Winnipeg (40-18-5), who were coming off a 3-0 win over the Kraken in Seattle on Friday. For Jets head coach Rick Bowness, the loss was less about what the Canucks did than what his team didn't do. \u201cListen, the bottom line is that's the worst game we have played in my two years here. By far. Because we didn't have one player play a good game. Not one,\u201d he said. \u201cIt starts there. And it ends there. It's as simple as that.\u201d Hoglander gave the home side a two-goal lead 13:47 into the first, tossing a puck on net that bounced in off Hellebuyck. The goal was the Swedish forward's 20th of the season. The Canucks took a 3-0 lead into the first intermission, thanks in part to Demko. The netminder denied Mason Appleton with his left pad and the rebound bounced to Teddy Blueger in the slot. The Vancouver centre took off down the ice, then dished the puck to Di Giuseppe who tapped a shot through Hellebuyck's pads with three minutes to go in the opening frame. Vancouver went up 4-0 early in the second period when Pettersson registered his 31st goal of the year on a power play. Hughes unleashed a blast from the point, hitting Conor Garland in the slot. The puck fell to Pettersson, who backhanded a shot in around Hellebuyck's outstretched skate 4:04 into the second. Vancouver was 1-for-2 with the man advantage Saturday, while Winnipeg went 0-for-1. The score was sealed 15:06 into the third when Hoglander chipped a pass in from the boards and Suter, facing away from the net, swept it in. A stingy Canucks defence helped DeSmith keep Winnipeg off the board, but the backup was tested late in the game. He denied Kyle Connor from in tight, then turned away the Jets star's second chance on the ensuing rebound. DeSmith said he simply warmed up as fast as he could after getting the nod. \u201cIt was nice that I got a shot fairly early. I think it was first shift, so that's always nice, to get the first save out of the way,\u201d he said. \u201cAnd then just go from there, try to get the body feeling good.\u201d The victory extended Vancouver's win streak to four games and kept the squad atop the Western Conference standings. The season series between the two sides is now tied at a game apiece after the Jets downed the Canucks 4-2 on Feb. 17. The teams will face off once again in Winnipeg on April 18 when they close out their regular-season campaigns."
    #asyncio.run(get_ner_and_save(conn_params_stage, title, content))
    asyncio.run(get_ner_and_save(conn_params_stage, 30860, title, content))
    
    
    
    