import spacy
from spacy.pipeline import EntityRuler
from collections import Counter
from nerd import nerd_client
from collections import Counter
import io
import sys
import re
from wikidata.client import Client


text = "Dan Brown\u2019s \u201cThe Da Vinci Code\u201d came out just after I finished my PhD. As a post-doctoral fellow teaching courses in San Diego on the Bible and early Judaism and Christianity, I was invited to give a public lecture discussing the book from a historian\u2019s perspective. I had been giving public lectures for a few years \u2014 graduate students are known to jump at the opportunity to share their knowledge for pennies \u2014 and I was experienced enough to know how to navigate the religious sensibilities of audience members and anticipate certain types of questions. But when I launched into a discussion of what I thought was wrong with Brown\u2019s sensationalist positioning of his fictional account as authentic history, I was utterly unprepared for the backlash and heckling I got from several members of the audience. How did I know that his claims about Jesus, Mary, da Vinci and the Templars weren\u2019t true? Maybe, they said, I was just jealous that he had used his understanding of history to write a bestselling novel, and here I was giving public lectures in community centres for peanuts. What makes my \u201copinion\u201d about what happened 2,000 years ago better than Brown\u2019s? Last week, my union, the Carleton University Academic Staff Association, released a series of \u201c Guidelines on Academic Freedom ,\u201d ostensibly to help members better understand what we can say in the classroom. The \u201cguidelines\u201d state that, \u201cMembers should interpret academic freedom to mean that speech about topics such as the decades-long conflict in Israel/Palestine can be appropriate in a broad range of settings because debates about justice and identity shape the contexts in which we teach and in which students learn.\u201d Furthermore, \u201cMembers should be aware that what is relevant to their pedagogy, educational objectives and course themes can be interpreted broadly, and that censorship in this regard would violate academic freedom.\u201d The document\u2019s introduction explains that it was necessary to develop such guidelines in light of the blow-back that some faculty members were receiving for speaking about \u201ccolonialism and racism in their classrooms; instructors voicing their concerns about genocide have been accused by students of creating a hostile learning environment.\u201d In addition to blithely using terms like \u201ccolonialism\u201d and \u201capartheid\u201d to describe the situation in Israel, and referring to the war against Hamas as a \u201cgenocide,\u201d one of the many shocking examples contained in the \u201cnon-exhaustive list\u201d of items the union considers \u201cto be acceptable speech and of public interest\u201d is \u201ccontextualizing the 10/7 attacks as a part of an ongoing history of violent conflict.\u201d The complete distortion, misinformation and baldly biased premises on which these guidelines are based shouldn\u2019t surprise me after everything I\u2019ve witnessed over the past five months, but somehow, they still do. Under what guise can the union empower professors to teach about issues they have no expertise in? It\u2019s clear that the authors of these guidelines don\u2019t have specific expertise in this subject area, and don\u2019t properly understand terms such as \u201cgenocide,\u201d \u201capartheid\u201d and \u201ccolonialism,\u201d or the ways in which they might accurately be applied to international affairs. How would these zealous defenders of academic freedom feel if I took my PhD in history to entitle myself to speak with authority in a classroom about subjects in which they are experts and I am not? Should I pontificate on media production and design, global social inequality or post-colonial film studies? All this time, I thought I was supposed to teach students the subjects I am an expert in, and leave other topics to those who studied them. But heck, why should I limit myself to only speak to students in my classroom about what I actually know? The union\u2019s mandate is \u201cto promote the well-being of the academic community, to defend academic freedom and to promote the individual interests of its members, as well as to maintain the quality and integrity of the university as an academic institution.\u201d The only aspect of this statement that is served by its new \u201cguidelines\u201d is that of promoting the individual interests of some of its members \u2014 interests that are patently political. This is not what a union is for. There is no universe in which my union dues should support directives that authorize physicists or psychologists to teach students that Israel is an illegitimate country or that savage rapes and massacres committed against citizens of a sovereign state need to be contextualized. Twenty years ago at that community centre in San Diego, I responded to the hecklers by telling them that seven years of work toward a PhD had given me not only deep knowledge of the ancient world, but also an understanding of how to conduct proper research and distinguish fact from fiction, actual events from conspiracy theories and truth from propaganda. And I freely admitted that I was a starving post-doc who would love to have the luxury of time to write historical fiction. Was I jealous that Brown spun some bad historiography into a multi-million dollar enterprise? Sure. But it wasn\u2019t jealousy that drove my critique. Rather, it was a sense of moral responsibility to be as accurate as possible in the information I convey to an audience, and to be as transparent as possible about how I know what I know. Abdicating that moral responsibility is not \u201cacademic freedom,\u201d any more than Israel is a colonial enterprise or an apartheid state committing genocide. Purveying misinformation under the guise of academic freedom is an abuse of academic authority that does nothing to promote the well-being of the academic community or defend academic freedom, and completely undermines the quality and integrity of the university as an academic institution. National Post Shawna Dolansky is an associate professor in the College of the Humanities at Carleton University in Ottawa."
summary = "Following the release of Dan Brown's 'The Da Vinci Code,' a post-doctoral fellow with expertise in the Bible, early Judaism, and Christianity faced backlash during a public lecture critiquing the novel's historical accuracy. This event, occurring shortly after the completion of their PhD, highlights the tension between popular fiction and academic scrutiny, particularly concerning historical claims about figures like Jesus, Mary, and the Templars. The reaction from the audience, ranging from accusations of jealousy to outright heckling, underscored the challenges academics face when confronting widely accepted narratives with scholarly evidence.\n\nFurther complicating matters, the Carleton University Academic Staff Association issued guidelines on academic freedom, advocating for broad interpretive latitude in classroom discussions, including sensitive topics like the Israel/Palestine conflict, colonialism, and racism. These guidelines, however, sparked controversy, suggesting a disconnect between the intent to promote academic freedom and the practical implications of discussing contentious topics without sufficient expertise. Critics argue that such guidelines may inadvertently legitimize misinformation or bias, especially on complex issues requiring specialized knowledge.\n\nThe narrative encapsulates a broader debate within academia and society about the boundaries of academic freedom, the responsibilities of educators, and the impact of literature on historical perceptions. It raises important questions about the role of academic institutions in safeguarding rigorous scholarly standards while fostering open dialogue. Ultimately, the experience shared in the National Post by Shawna Dolansky, an associate professor at Carleton University, underscores the delicate balance between defending academic freedom and ensuring the accuracy and integrity of educational content."
# Load Spacy model
client = Client()
nlp = spacy.load("en_core_web_lg")

# Assuming 'entityLinker' is added here with appropriate setup
if "entityLinker" not in nlp.pipe_names:
    # Setup for entityLinker if needed, adjust based on actual use
    nlp.add_pipe("entityLinker", last=True)

def get_unprocessed_entities(text):
    # Process the text and summary
    doc_text = nlp(text)
    
    # Example to iterate over sentences if your entityLinker supports pretty_print or similar functionality
    entities_info = []
    for sent in doc_text.sents:
        if hasattr(sent._, 'linkedEntities'):
            for ent in sent._.linkedEntities:
                # Temporarily redirect stdout to capture the pretty_print output
                old_stdout = sys.stdout  # Save the current stdout to restore later
                result = io.StringIO()  # Create a string buffer to capture the output
                sys.stdout = result
                ent.pretty_print()  # This will print to the 'result' buffer instead of the console
                sys.stdout = old_stdout  # Restore the original stdout
                
                # Store the captured output in a variable
                entity_info = result.getvalue()
                entities_info.append(entity_info)
                
                # Close the StringIO buffer
                result.close()
    return entities_info

def get_entity_codes(entities):
    code = []
    pattern = r"https://www.wikidata.org/wiki/(Q\d+)"
    for entity in entities:
        match = re.search(pattern, entity)

        # Extract the matched group if a match is found
        if match:
            wikidata_code = match.group(1)
            code.append(wikidata_code)
        else:
            print("No match found")
    return code

def get_wikidata_entity(wikidata_codes):
    for wikidata_code in wikidata_codes:
        entity = client.get(wikidata_code, load=True)
        #print(entity.data)
        entity_nlp = nlp(str(entity.label))
        if len(entity_nlp.ents):
            print(wikidata_code, ": ",entity.label, " - ", wikidata_codes[wikidata_code], " type:", entity_nlp.ents[0].label_)
        
possible_entities_codes = []
#get all the entities codes of general text
unprocessed_entries = get_unprocessed_entities(text)
entities_codes = get_entity_codes(unprocessed_entries)
possible_entities_codes.extend(entities_codes)

#get all the entities codes of different section
#first 1/3 get 3x value
#second 1/3 get 2x value
#last 1/3 get 1x value(nothing needs to be changed)
length_text = len(text)
unprocessed_entries_1st3 = get_unprocessed_entities(text[:length_text//3])
entities_codes_1st3 = get_entity_codes(unprocessed_entries_1st3)
possible_entities_codes.extend(entities_codes_1st3)
possible_entities_codes.extend(entities_codes_1st3)

# get the summary entities 
# summary is 3x value as well
unprocessed_entries_summary = get_unprocessed_entities(summary)
entities_codes_summary = get_entity_codes(unprocessed_entries_summary)
possible_entities_codes.extend(entities_codes_summary)
possible_entities_codes.extend(entities_codes_summary)
possible_entities_codes.extend(entities_codes_summary)

#count all the enntities in the list
# Count the occurrences of each code
code_counts = Counter(possible_entities_codes)
codes_more_than_5 = {code: count for code, count in code_counts.items() if count > 5}

get_wikidata_entity(codes_more_than_5)
 