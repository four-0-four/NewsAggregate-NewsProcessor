import spacy
from spacy.tokens import Span

def initialize_nlp_model():
    """
    Initializes the spaCy NLP model and adds the EntityLinker component.
    """
    nlp = spacy.load("en_core_web_sm")
    if "entity_linker" not in nlp.pipe_names:
        nlp.add_pipe("entity_linker", last=True)
    return nlp

def link_entities_to_kb(doc):
    """
    Processes a document to link entities to a knowledge base.
    Returns a list of entities with their original text, label, KB ID, and full name from the KB.
    """
    linked_entities = []
    for ent in doc.ents:
        entity_data = {
            "original_text": ent.text,
            "label": ent.label_,
            "kb_id": ent.kb_id_,
            "full_name": None  # Will be updated from the KB if available
        }

        # Attempt to get the full name from the KB; handle cases where KB ID is not available
        if ent.kb_id_:
            entity_data["full_name"] = get_entity_full_name_from_kb(ent.kb_id_)
        else:
            entity_data["full_name"] = "Unknown or Unlinked Entity"

        linked_entities.append(entity_data)
    return linked_entities

def get_entity_full_name_from_kb(kb_id):
    """
    Placeholder for a function that fetches the full name of an entity from the knowledge base.
    Implement this function based on your specific knowledge base's API or access method.
    """
    # This is a mock-up. You'll replace it with actual code to query your knowledge base.
    return f"Full Name for KB ID {kb_id}"

def process_article(article_text):
    """
    Main function to process the article text, find entities, and link them to a knowledge base.
    """
    nlp = initialize_nlp_model()
    doc = nlp(article_text)
    linked_entities = link_entities_to_kb(doc)

    # Display linked entities information
    for entity in linked_entities:
        print(f"Original Text: {entity['original_text']}")
        print(f"Label: {entity['label']}")
        print(f"Linked Entity ID: {entity['kb_id']}")
        print(f"Entity Full Name: {entity['full_name']}\n")

# Example usage
if __name__ == "__main__":
    article_text = "Google was founded by Larry Page and Sergey Brin while they were Ph.D. students at Stanford University."
    process_article(article_text)
