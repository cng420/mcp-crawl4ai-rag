"""
Utility functions for the Crawl4AI MCP server.
"""
import os
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple
import json
from supabase import create_client, Client
from urllib.parse import urlparse
import openai
import re
import time

# Load OpenAI API key for embeddings
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_or_create_source_uuid(client: Client, domain_name: str, table_name_for_source: str) -> Optional[str]:
    """
    Retrieves the UUID of an existing source by its domain name or creates a new source entry
    if it doesn't exist, then returns the UUID.

    Args:
        client: Supabase client.
        domain_name: The domain name of the source (e.g., "example.com").
        table_name_for_source: The name of the table associated with this source.

    Returns:
        The UUID string of the source, or None if an error occurred.
    """
    if not domain_name or not domain_name.strip():
        print(f"Error: domain_name cannot be empty or None")
        return None
        
    try:
        # Check if the source already exists
        response = client.table("sources").select("id").eq("source", domain_name).maybe_single().execute()
        
        if response.data:
            return response.data["id"]
        else:
            # Source does not exist, create it
            # 'id' (uuid) and 'source_id' (integer) are auto-generated by the database.
            insert_data = {
                "source": domain_name,
                "table_name": table_name_for_source,
                # Add other fields with defaults if necessary, e.g., summary, total_words
                "summary": f"Content from {domain_name}", # Default summary
                "total_words": 0 # Default word count
            }
            insert_response = client.table("sources").insert(insert_data).execute()
            if insert_response.data and len(insert_response.data) > 0:
                return insert_response.data[0]["id"] # Return the new UUID
            else:
                print(f"Error creating new source {domain_name}: No data returned after insert. Error: {insert_response.error}")
                return None
    except Exception as e:
        print(f"Exception in get_or_create_source_uuid for {domain_name}: {e}")
        return None

def get_supabase_client() -> Client:
    """
    Get a Supabase client with the URL and key from environment variables.
    
    Returns:
        Supabase client instance
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
    
    return create_client(url, key)

def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Create embeddings for multiple texts in a single API call.
    
    Args:
        texts: List of texts to create embeddings for
        
    Returns:
        List of embeddings (each embedding is a list of floats)
    """
    if not texts:
        return []

    # Assuming 1536 is the embedding dimension for "text-embedding-3-small"
    embedding_dim = 1536 
    
    # Initialize final_embeddings with zero vectors, matching the length of the original texts list
    final_embeddings = [[0.0] * embedding_dim for _ in range(len(texts))]

    # Identify valid texts and their original indices
    valid_texts_with_indices = []
    for i, text_content in enumerate(texts):
        if text_content and text_content.strip(): # Check for non-empty and non-whitespace-only
            valid_texts_with_indices.append((i, text_content))

    if not valid_texts_with_indices:
        # All texts were empty or whitespace, return all zero vectors
        return final_embeddings

    original_indices, texts_to_embed_list = zip(*valid_texts_with_indices)
    texts_to_embed = list(texts_to_embed_list) # Ensure it's a list for the API

    max_retries = 3
    retry_delay = 1.0
    embeddings_for_valid_texts = [] # Stores embeddings for non-empty inputs

    if texts_to_embed: # Proceed only if there are valid texts to embed
        for retry in range(max_retries):
            try:
                api_response = openai.embeddings.create(
                    model="text-embedding-3-small",
                    input=texts_to_embed
                )

                if len(api_response.data) == len(texts_to_embed):
                    # This list comprehension will raise AttributeError if any item in api_response.data
                    # does not have an 'embedding' attribute (e.g., it's an error object).
                    # This exception will be caught by the outer 'except Exception as e:' block,
                    # leading to the fallback logic, which is the desired behavior for partial failures.
                    current_embeddings = [item.embedding for item in api_response.data]
                    embeddings_for_valid_texts = current_embeddings
                    break  # Success: batch processing completed and all items yielded embeddings.
                else:
                    # If the API returns a list of a different length than the input,
                    # without the client library raising an exception, this is an unexpected state.
                    # We force a fallback to ensure all texts are processed.
                    print(f"Warning: Batch embedding API returned {len(api_response.data)} items for {len(texts_to_embed)} inputs. Triggering fallback.")
                    raise ValueError("Batch embedding response length mismatch, ensuring all texts are processed individually.")
            except Exception as e:
                if retry < max_retries - 1:
                    print(f"Error creating batch embeddings (attempt {retry + 1}/{max_retries}): {e}")
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"Failed to create batch embeddings after {max_retries} attempts: {e}")
                    # Fallback: try creating embeddings one by one for the valid texts
                    print("Attempting to create embeddings individually for valid texts...")
                    temp_individual_embeddings = []
                    for single_text in texts_to_embed:
                        try:
                            individual_response = openai.embeddings.create(
                                model="text-embedding-3-small",
                                input=[single_text]  # API expects a list even for a single item
                            )
                            temp_individual_embeddings.append(individual_response.data[0].embedding)
                        except Exception as individual_error:
                            print(f"Failed to create individual embedding for text (len {len(single_text)}): {individual_error}")
                            temp_individual_embeddings.append([0.0] * embedding_dim) # Use zero vector on failure
                    embeddings_for_valid_texts = temp_individual_embeddings
                    break # Break from retry loop (after attempting individual embeddings)
    
    # Populate final_embeddings with successfully created embeddings at their original positions
    for i, original_idx in enumerate(original_indices):
        if i < len(embeddings_for_valid_texts): # Ensure we have an embedding for this index
            final_embeddings[original_idx] = embeddings_for_valid_texts[i]
        # If not, it remains a zero vector (already initialized)

    return final_embeddings

def create_embedding(text: str) -> List[float]:
    """
    Create an embedding for a single text using OpenAI's API.
    
    Args:
        text: Text to create an embedding for
        
    Returns:
        List of floats representing the embedding
    """
    try:
        embeddings = create_embeddings_batch([text])
        return embeddings[0] if embeddings else [0.0] * 1536
    except Exception as e:
        print(f"Error creating embedding: {e}")
        # Return empty embedding if there's an error
        return [0.0] * 1536

def generate_contextual_embedding(full_document: str, chunk: str) -> Tuple[str, bool]:
    """
    Generate contextual information for a chunk within a document to improve retrieval.
    
    Args:
        full_document: The complete document text
        chunk: The specific chunk of text to generate context for
        
    Returns:
        Tuple containing:
        - The contextual text that situates the chunk within the document
        - Boolean indicating if contextual embedding was performed
    """
    model_choice = os.getenv("MODEL_CHOICE")
    
    try:
        # Create the prompt for generating contextual information
        prompt = f"""<document> 
{full_document[:25000]} 
</document>
Here is the chunk we want to situate within the whole document 
<chunk> 
{chunk}
</chunk> 
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""

        # Call the OpenAI API to generate contextual information
        response = openai.chat.completions.create(
            model=model_choice,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise contextual information."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=200
        )
        
        # Extract the generated context
        context = response.choices[0].message.content.strip()
        
        # Combine the context with the original chunk
        contextual_text = f"{context}\n---\n{chunk}"
        
        return contextual_text, True
    
    except Exception as e:
        print(f"Error generating contextual embedding: {e}. Using original chunk instead.")
        return chunk, False

def process_chunk_with_context(args):
    """
    Process a single chunk with contextual embedding.
    This function is designed to be used with concurrent.futures.
    
    Args:
        args: Tuple containing (url, content, full_document)
        
    Returns:
        Tuple containing:
        - The contextual text that situates the chunk within the document
        - Boolean indicating if contextual embedding was performed
    """
    url, content, full_document = args
    return generate_contextual_embedding(full_document, content)

def add_documents_to_supabase(
    client: Client, 
    urls: List[str], 
    chunk_numbers: List[int],
    contents: List[str], 
    metadatas: List[Dict[str, Any]],
    url_to_full_document: Dict[str, str],
    batch_size: int = 20
) -> None:
    """
    Add documents to the Supabase crawled_pages table in batches.
    Deletes existing records with the same URLs before inserting to prevent duplicates.
    
    Args:
        client: Supabase client
        urls: List of URLs
        chunk_numbers: List of chunk numbers
        contents: List of document contents
        metadatas: List of document metadata
        url_to_full_document: Dictionary mapping URLs to their full document content
        batch_size: Size of each batch for insertion
    """
    domain_to_uuid_cache: Dict[str, Optional[str]] = {} # Initialize cache for source UUIDs

    # Get unique URLs to delete existing records
    unique_urls_to_delete = list(set(urls))
    
    try:
        if unique_urls_to_delete:
            client.table("crawled_pages").delete().in_("url", unique_urls_to_delete).execute()
    except Exception as e:
        print(f"Batch delete failed: {e}. Trying one-by-one deletion as fallback.")
        for url_del in unique_urls_to_delete:
            try:
                client.table("crawled_pages").delete().eq("url", url_del).execute()
            except Exception as inner_e:
                print(f"Error deleting record for URL {url_del}: {inner_e}")
    
    use_contextual_embeddings = os.getenv("USE_CONTEXTUAL_EMBEDDINGS", "false") == "true"
    print(f"\n\nUse contextual embeddings: {use_contextual_embeddings}\n\n")
    
    for i in range(0, len(contents), batch_size):
        batch_end = min(i + batch_size, len(contents))
        
        # Initial slices for the current main batch
        _current_batch_urls = urls[i:batch_end]
        _current_batch_chunk_numbers = chunk_numbers[i:batch_end]
        _current_batch_contents = contents[i:batch_end]
        _current_batch_metadatas = metadatas[i:batch_end]
        
        # 1. Get source UUIDs for the current batch, using cache
        _current_batch_source_uuids: List[Optional[str]] = []
        for url_in_sub_batch in _current_batch_urls:
            parsed_url_for_source = urlparse(url_in_sub_batch)
            domain_name_for_source = parsed_url_for_source.netloc or parsed_url_for_source.path
            if not domain_name_for_source:
                print(f"Warning: Could not determine domain for URL {url_in_sub_batch}. Will skip this record.")
                _current_batch_source_uuids.append(None)
                continue
            
            source_uuid: Optional[str] = None
            if domain_name_for_source in domain_to_uuid_cache:
                source_uuid = domain_to_uuid_cache[domain_name_for_source]
            else:
                table_name_for_this_source = f"crawled_pages_{domain_name_for_source.replace('.', '_').replace('-', '_')}"
                source_uuid = get_or_create_source_uuid(client, domain_name_for_source, table_name_for_this_source)
                domain_to_uuid_cache[domain_name_for_source] = source_uuid # Cache the result
            
            _current_batch_source_uuids.append(source_uuid)

        # 2. Filter items: only keep those with a valid source_uuid
        final_batch_urls: List[str] = []
        final_batch_chunk_numbers: List[int] = []
        final_batch_contents: List[str] = []
        final_batch_metadatas: List[Dict[str, Any]] = []
        final_batch_source_uuids: List[str] = [] # Guaranteed to be str, not Optional[str]

        for k in range(len(_current_batch_urls)):
            source_uuid_val = _current_batch_source_uuids[k]
            if source_uuid_val:
                final_batch_urls.append(_current_batch_urls[k])
                final_batch_chunk_numbers.append(_current_batch_chunk_numbers[k])
                final_batch_contents.append(_current_batch_contents[k])
                final_batch_metadatas.append(_current_batch_metadatas[k])
                final_batch_source_uuids.append(source_uuid_val)
            else:
                print(f"Warning: URL {_current_batch_urls[k]} is being skipped due to missing source UUID (no embedding/contextualization performed).")

        if not final_batch_contents: # If all items in this batch were filtered out
            print(f"Info: All items in batch starting at original index {i} were skipped due to missing source UUIDs.")
            continue

        # 3. Apply contextual embedding (if enabled) to the filtered batch
        contextual_contents: List[str]
        if use_contextual_embeddings and final_batch_contents:
            contextual_results_ordered = [None] * len(final_batch_contents)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_final_idx = {}
                for j_final, content_final in enumerate(final_batch_contents):
                    url_final = final_batch_urls[j_final]
                    full_document = url_to_full_document.get(url_final, "")
                    future = executor.submit(process_chunk_with_context, (url_final, content_final, full_document))
                    future_to_final_idx[future] = j_final
                
                for future in concurrent.futures.as_completed(future_to_final_idx):
                    j_final_idx = future_to_final_idx[future]
                    try:
                        result_text, success_flag = future.result()
                        contextual_results_ordered[j_final_idx] = result_text
                        if success_flag:
                            final_batch_metadatas[j_final_idx]["contextual_embedding"] = True
                    except Exception as e:
                        print(f"Error processing chunk for URL {final_batch_urls[j_final_idx]} (final index {j_final_idx}): {e}. Using original content.")
                        contextual_results_ordered[j_final_idx] = final_batch_contents[j_final_idx] # Fallback
            contextual_contents = contextual_results_ordered
        elif final_batch_contents: # Not using contextual embeddings, but have content
            contextual_contents = final_batch_contents
        else: # Should have been caught by "if not final_batch_contents" already
            contextual_contents = []


        # 4. Create embeddings for the (filtered and potentially contextualized) batch
        batch_embeddings = create_embeddings_batch(contextual_contents)
        
        # 5. Prepare batch_data for insertion (all items here are valid and have a source_id)
        batch_data_to_insert = []
        for j_final in range(len(contextual_contents)):
            # All lists (final_batch_*, contextual_contents, batch_embeddings) are aligned and filtered
            data = {
                "url": final_batch_urls[j_final],
                "chunk_number": final_batch_chunk_numbers[j_final],
                "content": contextual_contents[j_final],
                "metadata": {
                    "chunk_size": len(contextual_contents[j_final]),
                    **final_batch_metadatas[j_final]
                },
                "source_id": final_batch_source_uuids[j_final], # Guaranteed not None
                "embedding": batch_embeddings[j_final]
            }
            batch_data_to_insert.append(data)
        
        # 6. Insert batch into Supabase (if batch_data_to_insert is not empty)
        if batch_data_to_insert:
            max_retries = 3
            retry_delay = 1.0
            
            for retry in range(max_retries):
                try:
                    client.table("crawled_pages").insert(batch_data_to_insert).execute()
                    break # Success
                except Exception as e:
                    if retry < max_retries - 1:
                        print(f"Error inserting batch into Supabase (attempt {retry + 1}/{max_retries}): {e}")
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        print(f"Failed to insert batch after {max_retries} attempts: {e}. Attempting individual inserts.")
                        successful_inserts = 0
                        for record_idx, record in enumerate(batch_data_to_insert):
                            try:
                                client.table("crawled_pages").insert(record).execute()
                                successful_inserts += 1
                            except Exception as individual_error:
                                print(f"Failed to insert individual record for URL {record.get('url', 'N/A')} (final index {record_idx}): {individual_error}")
                        print(f"Successfully inserted {successful_inserts}/{len(batch_data_to_insert)} records individually after batch failure.")
        else:
            print(f"Info: No data to insert for batch starting at original index {i} after processing.")

def search_documents(
    client: Client, 
    query: str, 
    match_count: int = 10, 
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search for documents in Supabase using vector similarity.
    
    Args:
        client: Supabase client
        query: Query text
        match_count: Maximum number of results to return
        filter_metadata: Optional metadata filter
        
    Returns:
        List of matching documents
    """
    # Create embedding for the query
    query_embedding = create_embedding(query)
    
    # Execute the search using the match_crawled_pages function
    try:
        # Only include filter parameter if filter_metadata is provided and not empty
        params = {
            'query_embedding': query_embedding,
            'match_count': match_count
        }
        
        # Only add the filter if it's actually provided and not empty
        if filter_metadata:
            params['filter'] = filter_metadata  # Pass the dictionary directly, not JSON-encoded
        
        result = client.rpc('match_crawled_pages', params).execute()
        
        return result.data
    except Exception as e:
        print(f"Error searching documents: {e}")
        return []


def extract_code_blocks(markdown_content: str, min_length: int = 1000) -> List[Dict[str, Any]]:
    """
    Extract code blocks from markdown content along with context.
    
    Args:
        markdown_content: The markdown content to extract code blocks from
        min_length: Minimum length of code blocks to extract (default: 1000 characters)
        
    Returns:
        List of dictionaries containing code blocks and their context
    """
    code_blocks = []
    
    # Skip if content starts with triple backticks (edge case for files wrapped in backticks)
    content = markdown_content.strip()
    start_offset = 0
    if content.startswith('```'):
        # Skip the first triple backticks
        start_offset = 3
        print("Skipping initial triple backticks")
    
    # Find all occurrences of triple backticks
    backtick_positions = []
    pos = start_offset
    while True:
        pos = markdown_content.find('```', pos)
        if pos == -1:
            break
        backtick_positions.append(pos)
        pos += 3
    
    # Process pairs of backticks
    i = 0
    while i < len(backtick_positions) - 1:
        start_pos = backtick_positions[i]
        end_pos = backtick_positions[i + 1]
        
        # Extract the content between backticks
        code_section = markdown_content[start_pos+3:end_pos]
        
        # Check if there's a language specifier on the first line
        lines = code_section.split('\n', 1)
        if len(lines) > 1:
            # Check if first line is a language specifier (no spaces, common language names)
            first_line = lines[0].strip()
            if first_line and not ' ' in first_line and len(first_line) < 20:
                language = first_line
                code_content = lines[1].strip() if len(lines) > 1 else ""
            else:
                language = ""
                code_content = code_section.strip()
        else:
            language = ""
            code_content = code_section.strip()
        
        # Skip if code block is too short
        if len(code_content) < min_length:
            i += 2  # Move to next pair
            continue
        
        # Extract context before (1000 chars)
        context_start = max(0, start_pos - 1000)
        context_before = markdown_content[context_start:start_pos].strip()
        
        # Extract context after (1000 chars)
        context_end = min(len(markdown_content), end_pos + 3 + 1000)
        context_after = markdown_content[end_pos + 3:context_end].strip()
        
        code_blocks.append({
            'code': code_content,
            'language': language,
            'context_before': context_before,
            'context_after': context_after,
            'full_context': f"{context_before}\n\n{code_content}\n\n{context_after}"
        })
        
        # Move to next pair (skip the closing backtick we just processed)
        i += 2
    
    return code_blocks


def generate_code_example_summary(code: str, context_before: str, context_after: str) -> str:
    """
    Generate a summary for a code example using its surrounding context.
    
    Args:
        code: The code example
        context_before: Context before the code
        context_after: Context after the code
        
    Returns:
        A summary of what the code example demonstrates
    """
    model_choice = os.getenv("MODEL_CHOICE")
    
    # Create the prompt
    prompt = f"""<context_before>
{context_before[-500:] if len(context_before) > 500 else context_before}
</context_before>

<code_example>
{code[:1500] if len(code) > 1500 else code}
</code_example>

<context_after>
{context_after[:500] if len(context_after) > 500 else context_after}
</context_after>

Based on the code example and its surrounding context, provide a concise summary (2-3 sentences) that describes what this code example demonstrates and its purpose. Focus on the practical application and key concepts illustrated.
"""
    
    try:
        response = openai.chat.completions.create(
            model=model_choice,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise code example summaries."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=100
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error generating code example summary: {e}")
        return "Code example for demonstration purposes."


def add_code_examples_to_supabase(
    client: Client,
    urls: List[str],
    chunk_numbers: List[int],
    code_examples: List[str],
    summaries: List[str],
    metadatas: List[Dict[str, Any]],
    batch_size: int = 20
):
    """
    Add code examples to the Supabase code_examples table in batches.
    
    Args:
        client: Supabase client
        urls: List of URLs
        chunk_numbers: List of chunk numbers
        code_examples: List of code example contents
        summaries: List of code example summaries
        metadatas: List of metadata dictionaries
        batch_size: Size of each batch for insertion
    """
    if not urls:
        return
        
    # Delete existing records for these URLs
    unique_urls = list(set(urls))
    for url in unique_urls:
        try:
            client.table('code_examples').delete().eq('url', url).execute()
        except Exception as e:
            print(f"Error deleting existing code examples for {url}: {e}")
    
    # Process in batches
    total_items = len(urls)
    for i in range(0, total_items, batch_size):
        batch_end = min(i + batch_size, total_items)
        batch_texts = []
        
        # Create combined texts for embedding (code + summary)
        for j in range(i, batch_end):
            combined_text = f"{code_examples[j]}\n\nSummary: {summaries[j]}"
            batch_texts.append(combined_text)
        
        # Create embeddings for the batch
        embeddings = create_embeddings_batch(batch_texts)
        
        # Check if embeddings are valid (not all zeros)
        valid_embeddings = []
        for embedding in embeddings:
            if embedding and not all(v == 0.0 for v in embedding):
                valid_embeddings.append(embedding)
            else:
                print(f"Warning: Zero or invalid embedding detected, creating new one...")
                # Try to create a single embedding as fallback
                single_embedding = create_embedding(batch_texts[len(valid_embeddings)])
                valid_embeddings.append(single_embedding)
        
        # Prepare batch data
        batch_data = []
        for j, embedding in enumerate(valid_embeddings):
            idx = i + j
            
            # Extract source_id from URL
            parsed_url = urlparse(urls[idx])
            source_domain_for_code = parsed_url.netloc or parsed_url.path # This is correct if code_examples.source_id is TEXT
            
            # current_code_source_id_val = batch_code_source_uuids[j] # If it were UUID
            # if not current_code_source_id_val: # If it were UUID
            #     print(f"Warning: Missing source UUID for code example URL {urls[idx]}. Skipping.")
            #     continue

            batch_data.append({
                'url': urls[idx],
                'chunk_number': chunk_numbers[idx],
                'content': code_examples[idx],
                'summary': summaries[idx],
                'metadata': metadatas[idx],  # Store as JSON object, not string
                'source_id': source_domain_for_code, # Kept as domain string, assuming TEXT type in code_examples.source_id
                'embedding': embedding
            })
        
        # Insert batch into Supabase with retry logic
        max_retries = 3
        retry_delay = 1.0  # Start with 1 second delay
        
        for retry in range(max_retries):
            try:
                client.table('code_examples').insert(batch_data).execute()
                # Success - break out of retry loop
                break
            except Exception as e:
                if retry < max_retries - 1:
                    print(f"Error inserting batch into Supabase (attempt {retry + 1}/{max_retries}): {e}")
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Final attempt failed
                    print(f"Failed to insert batch after {max_retries} attempts: {e}")
                    # Optionally, try inserting records one by one as a last resort
                    print("Attempting to insert records individually...")
                    successful_inserts = 0
                    for record in batch_data:
                        try:
                            client.table('code_examples').insert(record).execute()
                            successful_inserts += 1
                        except Exception as individual_error:
                            print(f"Failed to insert individual record for URL {record['url']}: {individual_error}")
                    
                    if successful_inserts > 0:
                        print(f"Successfully inserted {successful_inserts}/{len(batch_data)} records individually")
        print(f"Inserted batch {i//batch_size + 1} of {(total_items + batch_size - 1)//batch_size} code examples")


def update_source_info(client: Client, domain_name: str, summary: str, word_count: int, table_name_for_source: Optional[str] = None):
    """
    Update or insert source information in the sources table.
    Uses domain_name (source column) as the conflict target for upsert.

    Args:
        client: Supabase client
        domain_name: The source domain name (e.g., "example.com"). This is used for the 'source' column.
        summary: Summary of the source.
        word_count: Total word count for the source.
        table_name_for_source: The name of the table primarily associated with this source (e.g., "crawled_pages").
                               If None, a default will be generated.
    """
    if not domain_name:
        print("Error: domain_name cannot be empty for update_source_info.")
        return

    # Determine table_name if not provided
    if table_name_for_source is None:
        # Generate a default table name based on the domain.
        # This matches the pattern observed in some schema table names like 'crawled_pages_docs_github_com'.
        # Replace non-alphanumeric characters (besides '_') with '_' for valid table name components.
        safe_domain_part = re.sub(r'[^a-zA-Z0-9_]', '_', domain_name)
        table_name_for_source = f"pages_{safe_domain_part}" # Generic prefix 'pages_'

    try:
        data_to_upsert = {
            "source": domain_name,  # The domain name itself
            "summary": summary,
            "total_words": word_count, # Ensure this matches your 'sources' table column (e.g., total_words or total_word_count)
            "table_name": table_name_for_source, # Required field for the 'sources' table
            # 'updated_at' can often be handled by database default triggers on update.
            # If not, add: 'updated_at': 'now()'
        }

        # Upsert into the 'sources' table.
        # This will insert if no row with the given 'source' (domain_name) exists,
        # or update the existing row if it does.
        # A unique constraint on the 'source' column is required for on_conflict.
        response = client.table("sources").upsert(
            data_to_upsert, 
            on_conflict="source" # Assumes 'source' column has a unique constraint
        ).execute()

        if response.error:
            print(f"Error upserting source info for {domain_name}: {response.error}")
        else:
            # Upsert might not return data on success depending on PostgREST version/config
            # and whether it was an insert or update.
            # Checking for presence of data and specific count might be too strict.
            # The absence of an error is the primary success indicator here.
            print(f"Successfully upserted source info for: {domain_name}")
            
    except Exception as e:
        print(f"Exception during update_source_info for {domain_name}: {e}")


def extract_source_summary(source_id: str, content: str, max_length: int = 500) -> str:
    """
    Extract a summary for a source from its content using an LLM.
    
    This function uses the OpenAI API to generate a concise summary of the source content.
    
    Args:
        source_id: The source ID (domain)
        content: The content to extract a summary from
        max_length: Maximum length of the summary
        
    Returns:
        A summary string
    """
    # Default summary if we can't extract anything meaningful
    default_summary = f"Content from {source_id}"
    
    if not content or len(content.strip()) == 0:
        return default_summary
    
    # Get the model choice from environment variables
    model_choice = os.getenv("MODEL_CHOICE")
    
    # Limit content length to avoid token limits
    truncated_content = content[:25000] if len(content) > 25000 else content
    
    # Create the prompt for generating the summary
    prompt = f"""<source_content>
{truncated_content}
</source_content>

The above content is from the documentation for '{source_id}'. Please provide a concise summary (3-5 sentences) that describes what this library/tool/framework is about. The summary should help understand what the library/tool/framework accomplishes and the purpose.
"""
    
    try:
        # Call the OpenAI API to generate the summary
        response = openai.chat.completions.create(
            model=model_choice,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise library/tool/framework summaries."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=150
        )
        
        # Extract the generated summary
        summary = response.choices[0].message.content.strip()
        
        # Ensure the summary is not too long
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
            
        return summary
    
    except Exception as e:
        print(f"Error generating summary with LLM for {source_id}: {e}. Using default summary.")
        return default_summary


def search_code_examples(
    client: Client, 
    query: str, 
    match_count: int = 10, 
    filter_metadata: Optional[Dict[str, Any]] = None,
    source_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for code examples in Supabase using vector similarity.
    
    Args:
        client: Supabase client
        query: Query text
        match_count: Maximum number of results to return
        filter_metadata: Optional metadata filter
        source_id: Optional source ID to filter results
        
    Returns:
        List of matching code examples
    """
    # Create a more descriptive query for better embedding match
    # Since code examples are embedded with their summaries, we should make the query more descriptive
    enhanced_query = f"Code example for {query}\n\nSummary: Example code showing {query}"
    
    # Create embedding for the enhanced query
    query_embedding = create_embedding(enhanced_query)
    
    # Execute the search using the match_code_examples function
    try:
        # Only include filter parameter if filter_metadata is provided and not empty
        params = {
            'query_embedding': query_embedding,
            'match_count': match_count
        }
        
        # Only add the filter if it's actually provided and not empty
        if filter_metadata:
            params['filter'] = filter_metadata
            
        # Add source filter if provided
        if source_id:
            params['source_filter'] = source_id
        
        result = client.rpc('match_code_examples', params).execute()
        
        return result.data
    except Exception as e:
        print(f"Error searching code examples: {e}")
        return []