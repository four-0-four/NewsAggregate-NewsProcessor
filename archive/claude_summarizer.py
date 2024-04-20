import asyncio
import os

from dotenv import load_dotenv
import json
#https://huggingface.co/mrm8488/t5-base-finetuned-summarize-news

claude_secret_key="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"

import anthropic

claude_client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=claude_secret_key,
)

def extract_summary(text):
    # Splitting the text to find the start of the summary
    start_index = text.find("<SUMMARY>") + len("<SUMMARY>")
    end_index = text.find("</SUMMARY>")
    
    # Extracting the text between <SUMMARY> and </SUMMARY> tags
    summary = text[start_index:end_index].strip()
    
    return summary

async def summarize_news_claude(title, content):
    message = claude_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0,
        system="summarize the news article",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "summarize the news. summary should be readable, accurate and understandable. put the summary inside <SUMMARY></SUMMARY>. please use shorter paragraphs if necessary. Summary should be minimum 200 words and maximum 300 words.\nHere is the News:\n<News>\n"+title+" "+content+"\n</News>"
                    }
                ]
            }
        ]
    )
    return extract_summary(message.content[0].text)

async def short_summarize_news_claude(title, content):
    message = claude_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0,
        system="summarize the news article",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "summarize the news. summary should be readable, accurate and understandable. put the summary inside <SUMMARY></SUMMARY>. please use shorter paragraphs if necessary. Summary should be maximum 50 words.\nHere is the News:\n<News>\n"+title+" "+content+"\n</News>"
                    }
                ]
            }
        ]
    )
    return extract_summary(message.content[0].text)

# Run the main function using asyncio.run() if your Python version is 3.7+
if __name__ == "__main__":
    title="Parole board imposes strict conditions on Marissa Shephard's release from prison"
    content="Marissa Shephard has reached her prison release date less than three years after admitting her role in the brutal killing of an 18-year-old Moncton man. Shephard, in her late 20s, is serving a sentence for manslaughter and arson after admitting her involvement in the Dec. 17, 2015, killing of Baylee Wylie. A Feb. 12 decision by the Parole Board of Canada provided to CBC News this week says Shephard is approaching statutory release . That's the point when an offender has served two-thirds of their sentence and must be released. Shephard will remain under supervision and must comply with a long list of conditions. Correctional Service Canada, which runs prisons, says Shephard's statutory release date was Feb. 27. But in an email Tuesday on Tuesday, the service didn't say if she had been released. WATCH | Marissa Shephard involved in brutal killing of 18-year-old Baylee Wylie in 2015 Parole board imposes restrictions on Marissa Shephard’s prison release 25 minutes ago Duration 1:58 Moncton woman convicted of manslaughter described as manipulative, aggressive and intimidating. 'As per the Privacy Act, we are not able to disclose personal information regarding an offender, including their location or whether they are currently serving their sentence in an institution or in the community,' it said. She'll be required to live at a 'community-based residential facility' or a psychiatric facility approved by Correctional Service of Canada. Marissa Shephard sentenced to 12 years in prison 'In assessing your case, and as you approach your legislated release date, the Board has not lost sight of the horrific and violent crimes you, along with your co-accused, committed against the victim; the pain, fear and suffering the victim endured leading up to a cruel and tragic death,' the decision states. 'Furthermore, the Board is sensitive to the trauma and lifelong emotional effects experienced by the victim's family at having lost a loved one in such a violent manner.' Shephard was among three people charged with murdering Wylie. Devin Morningstar was sentenced to life in prison, with no chance of parole for at least 25 years, after being convicted of first-degree murder in 2016. Tyler Noël was sentenced in 2017 to life with no chance of parole for 16 years after pleading guilty to second-degree murder. The body of 18-year-old Baylee Wylie was found in a burned-out townhouse in Moncton in December 2015. (Submitted) Shephard was found guilty of first-degree murder by a jury in 2018. Her conviction was overturned on appeal and a new trial ordered. She pleaded guilty to manslaughter and arson before the trial began. She was sentenced to 12 years in prison in August 2021. That time was reduced by years because she was credited 1½ days for each day spent in custody between her March 2016 arrest and sentencing. The parole board decision says 'during most of your sentence you have demonstrated poor institutional behaviour, have been described as manipulative, using intimidation, aggressive against staff as well as other inmates and have incited violence against other inmates.' Marissa Shephard pleads guilty to manslaughter, arson However, it says her recent behaviour appears to have 'stabilized,' and that she has shown 'early signs of stability and better emotional control.' That change is attributed to participation in programming, including a canine program., and spirituality The decision says Shephard hopes to upgrade her education in the 'canine field,' maintain employment and rely on support from family and her fiancée. A November 2022 psychological risk assessment rated her as a 'moderate' risk to reoffend, and to reoffend violently on day parole as 'low-moderate,' the decision states. The board imposed various conditions, including no contact with Wylie's family, to abstain from alcohol and drugs, report any sexual relationships and follow her treatment plan. The board says some community facilities were unwilling to accept Shephard, though two were. Police in those two areas, the decision states, 'are not supportive.' Devin Morningstar was convicted of first-degree murder in 2016. (Facebook) Her 2021 sentencing included an agreed statement of facts that she admitted. Wylie had been living with Shephard in a townhouse on Sumac Street in Moncton. In the days leading up to Wylie's death, Noël and Morningstar also lived there and consumed drugs. A fight between Wylie and Noël ensued, and Morningstar sided with Noël. Shepherd hit Wylie on the head with a bong during the fight but left while the fighting continued. Tyler Noël was sentenced in 2017 to life with no chance of parole for 16 years. (N.B. Crime Stoppers) Shephard said that when she returned, she panicked and joined in on the attacks against her friend, fearing the other two would turn against her. While Shephard admits taking part in the attack, she said she didn't inflict the fatal wounds. She also admitted helping start a fire to try to hide Wylie's remains in her home. Firefighters discovered Wylie's body beneath a mattress in the burned-out townhouse. Shephard's first trial heard that Wylie had been bound to a chair, beaten and stabbed with multiple objects that included a broken mirror and a box cutter. He suffered more than 140 sharp-force injuries — most while he was still alive."
    loop = asyncio.get_event_loop()
    summary = loop.run_until_complete(summarize_news_claude(title, content))
    print(len(summary)>100)