import tiktoken

max_tokens = 13384

# Initialize the tokenizer for GPT-4
tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    tokens = tokenizer.encode(text)
    return len(tokens), tokens

def split_text(text, max_tokens):
    tokens = tokenizer.encode(text)
    if len(tokens) <= max_tokens:
        return [text]
    
    # Split tokens into chunks
    chunks = []
    current_chunk = []
    current_length = 0
    
    for token in tokens:
        if current_length + 1 > max_tokens:
            chunks.append(tokenizer.decode(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(token)
        current_length += 1
    
    # Append the last chunk
    if current_chunk:
        chunks.append(tokenizer.decode(current_chunk))
    
    return chunks

# Example usage
"""
text = ""

# Count tokens
token_count, tokens = count_tokens(text)
print(f"Token count: {token_count}")

# Split text
chunks = split_text(text, max_tokens)
print(f"Number of chunks: {len(chunks)}")

for i, chunk in enumerate(chunks):
    print(f"Chunk {i + 1}: {chunk[:100]}...")  # Print the first 100 characters of each chunk for brevity
"""