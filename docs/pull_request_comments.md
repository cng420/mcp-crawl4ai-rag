Refactor: Organize project documentation and add new data/schema files #1

**Status:** Draft

**cng420** wants to merge 3 commits into `cng-knowledge-base` from `main`.

**Diff:** +29,980 −71
**Conversation:** 38
**Commits:** 3
**Checks:** 0
**Files changed:** 12

---
## Conversation

**@cng420** (Owner)
*cng420 commented 54 minutes ago •*

This commit reorganizes project documentation by moving existing files (`.env.example`, `crawled_pages.sql`) into the 'docs' directory.

It also introduces several new files within the 'docs' directory:

*   SQL files for crawled page data, site page data, and source data, including Google-related sources.
*   JSON files detailing Supabase schema information.
*   Markdown files for tracking fixes/bugs/updates, logs, and a quality audit of Google crawled data.

Additionally, this commit includes modifications to `src/utils.py`.

**Summary by Sourcery**
Organize project documentation into a dedicated `docs` directory and enhance utility functions to support source UUID management and robust embedding workflows.

**New Features:**
*   Introduce `get_or_create_source_uuid` to fetch or create source entries by domain and return their UUID.

**Enhancements:**
*   Refactor `create_embeddings_batch` to filter empty inputs, apply retry/backoff, and map results back to original positions.
*   Update embedding and completion functions to use `max_completion_tokens` instead of `max_tokens`.
*   Modify `add_documents_to_supabase` to fetch and use real source UUIDs for crawled pages.
*   Revise `update_source_info` to perform upserts on domain names and include `table_name` logic.

**Documentation:**
*   Reorganize and expand documentation under `docs`, adding SQL data files, Supabase schema JSON, and markdown files for logs, bug tracking, and quality audits.

---
**@cng420**
*Refactor: Organize project documentation and add new data/schema files (Commit 6fc36d1)*

---
**@cng420**
*cng420 self-assigned this 54 minutes ago*

---
**@sourcery-ai Sourcery AI**
*sourcery-ai bot commented 54 minutes ago •*

### Reviewer's Guide

This PR centralizes all project documentation under the `docs` directory—relocating existing examples and adding new SQL, JSON, and Markdown artifacts—and refactors `src/utils.py` to introduce true UUID-based source tracking, strengthen batch-embedding routines, and simplify source upsert/update operations.

#### File-Level Changes

**Change:** Reorganize and expand project documentation
**Details:**
*   Moved existing files (`.env.example`, `crawled_pages.sql`) into `docs`
*   Added SQL files for crawled page data, site page data, and source lists
*   Introduced JSON schema exports for Supabase tables
*   Created Markdown trackers for fixes/bugs, logs, and a Google-data quality audit
**Files:**
*   `.env.example`
*   `crawled_pages.sql`
*   `docs/*.sql`
*   `docs/*.json`
*   `docs/*.md`

**Change:** Implement UUID management for sources
**Details:**
*   Added `get_or_create_source_uuid` for lookup/insertion of source records
*   Integrated UUID lookup into `add_documents_to_supabase` before inserts
*   Replaced domain-string usage with actual UUIDs for `source_id`
**Files:**
*   `src/utils.py`

**Change:** Refactor batch embedding generation
**Details:**
*   Initialize zero vectors for all inputs and map valid texts by original index
*   Perform batch OpenAI call with retries and exponential backoff
*   Fallback to individual API calls on persistent failure and reintegrate results
**Files:**
*   `src/utils.py`

**Change:** Update embedding and completion calls
**Details:**
*   Replaced deprecated `temperature` and `max_tokens` arguments with `max_completion_tokens`
**Files:**
*   `src/utils.py`

**Change:** Enhance source upsert/update logic
**Details:**
*   Changed `update_source_info` signature to accept `domain_name` and optional table name
*   Built default table name when missing and upsert on `source` column
*   Switched to Supabase `upsert` for atomic insert/update of source records
**Files:**
*   `src/utils.py`

**Tips and commands**
*(This comment was marked as resolved.)*

---
**@qodo-merge-pro qodo-merge-pro bot**
*qodo-merge-pro bot added the `Review effort 4/5` label 50 minutes ago*

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 50 minutes ago*

### PR Reviewer Guide 🔍

Here are some key observations to aid the review process:

*   ⏱️ **Estimated effort to review:** 4 🔵🔵🔵🔵⚪
*   🏅 **Score:** 72
*   🧪 No relevant tests
*   🔒 No security concerns identified
*   🔀 Multiple PR themes
    *   Sub-PR theme: Refactor embedding and source management utilities
    *   Sub-PR theme: Organize documentation and schema files

#### ⚡ Recommended focus areas for review

**Possible Issue**
The `create_embeddings_batch` function has complex retry logic with individual fallback processing, but the `final_embeddings` mapping logic may fail if `embeddings_for_valid_texts` has fewer elements than expected, potentially leaving some positions with zero vectors when they should have valid embeddings.
```python
# Populate final_embeddings with successfully created embeddings at their original positions
for i, original_idx in enumerate(original_indices):
    if i < len(embeddings_for_valid_texts): # Ensure we have an embedding for this index
        final_embeddings[original_idx] = embeddings_for_valid_texts[i]
    # If not, it remains a zero vector (already initialized)

return final_embeddings
```

**Logic Error**
In `add_documents_to_supabase`, the code continues processing even when `current_source_uuid` is `None`, but then skips the record. This could lead to inconsistent batch processing where some records are skipped but the loop continues, potentially causing index mismatches.
```python
if not current_source_uuid:
    print(f"Warning: Missing source UUID for URL {batch_urls[j]}. Skipping this record for crawled_pages.")
    # Or handle by not inserting, or inserting with a null/default source_id if schema allows
    continue 
# --- END MODIFICATION: Use fetched UUID ---
```

**Performance Issue**
The `get_or_create_source_uuid` function is called for every URL in a batch, potentially making many redundant database calls for the same domain. This should be optimized to cache results within a batch or pre-fetch unique domains.
```python
batch_source_uuids = []
for url_in_batch in batch_urls:
    parsed_url_for_source = urlparse(url_in_batch)
    domain_name_for_source = parsed_url_for_source.netloc or parsed_url_for_source.path # Fallback to path if netloc is empty
    if not domain_name_for_source: # Ensure domain_name is not empty
        print(f"Warning: Could not determine domain for URL {url_in_batch}. Skipping source UUID fetch.")
        batch_source_uuids.append(None) # Or a default UUID / error handling
        continue

    # Assuming a generic table_name for sources related to 'crawled_pages'
    # This might need to be more dynamic if sources map to different types of tables.
    table_name_for_this_source = f"crawled_pages_{domain_name_for_source.replace('.', '_').replace('-', '_')}" # Default/example table name

    source_uuid = get_or_create_source_uuid(client, domain_name_for_source, table_name_for_this_source)
    batch_source_uuids.append(source_uuid)
# --- END MODIFICATION for source_id UUID ---
```

---
**@cng420** (Owner, Author)
*cng420 commented 23 minutes ago*

`/improve --pr_code_suggestions.num_code_suggestions_per_chunk="5" --pr_code_suggestions.commitable_code_suggestions=true --pr_code_suggestions.suggestions_score_threshold="0"`

*(This comment was marked as resolved.)*

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 23 minutes ago •*

### PR Analysis 🔬
This screen contains a list of code components that were changed in this PR.
You can initiate specific actions for each component, by checking the relevant boxes.
After you check a box, the action will be performed automatically by PR-Agent.
Results will appear as a comment on the PR, typically after 30-60 seconds.

**File: `utils.py`**

*   **`get_or_create_source_uuid`** (function) `+38/-0`
    *   Actions: Test, Docs, Improve, Similar
*   **`create_embeddings_batch`** (function) `+61/-36`
    *   Actions: Test, Docs, Improve, Similar
*   **`generate_contextual_embedding`** (function) `+2/-3`
    *   Actions: Test, Docs, Improve, Similar
*   **`add_documents_to_supabase`** (function) `+31/-5`
    *   Actions: Test, Docs, Improve, Similar
*   **`generate_code_example_summary`** (function) `+2/-3`
    *   Actions: Test, Docs, Improve, Similar
*   **`add_code_examples_to_supabase`** (function) `+8/-3`
    *   Actions: Test, Docs, Improve, Similar
*   **`update_source_info`** (function) `+46/-22`
    *   Actions: Test, Docs, Improve, Similar
*   **`extract_source_summary`** (function) `+2/-3`
    *   Actions: Test, Docs, Improve, Similar

💡 **Usage guide:**
Using static code analysis capabilities, the analyze tool scans the PR code changes and finds the code components (methods, functions, classes) that changed in the PR.

The tool can be triggered automatically every time a new PR is opened, or can be invoked manually by commenting on any PR:
`/analyze`

Languages that are currently supported: Python, Java, C++, JavaScript, TypeScript, C#.
See more information about the tool in the docs.

*(This comment was marked as resolved.)*

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 23 minutes ago •*

### PR Documentation 📚
Here is a list of the files that were modified in the PR, with docstrings for each altered code component:

#### `utils.py`

##### `get_or_create_source_uuid` (function) `[+38/-0]`
**Component signature:**
```python
def get_or_create_source_uuid(client: Client, domain_name: str, table_name_for_source: str) -> Optional[str]:
```
**Docstring:**
```
"""
Retrieves the UUID of an existing source by its domain name or creates a new source entry
if it doesn't exist, then returns the UUID.

This function first attempts to find an existing source record in the 'sources' table
by matching the domain name. If found, it returns the existing UUID. If not found,
it creates a new source entry with default values and returns the newly generated UUID.

:param client: Supabase client instance for database operations
:type client: Client
:param domain_name: The domain name of the source (e.g., "example.com")
:type domain_name: str
:param table_name_for_source: The name of the table associated with this source
:type table_name_for_source: str

:returns: The UUID string of the source (existing or newly created), or None if an error occurred
:rtype: Optional[str]

:raises Exception: Any database operation errors are caught and logged

.. note::
   When creating a new source, default values are set:
   - summary: "Content from {domain_name}"
   - total_words: 0

.. example::
   >>> client = create_client(url, key)
   >>> uuid = get_or_create_source_uuid(client, "example.com", "content_table")
   >>> print(uuid)  # Returns UUID string or None
"""
```

##### `create_embeddings_batch` (function) `[+61/-36]`
**Component signature:**
```python
def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
```
**Docstring:**
```
"""
Create embeddings for multiple texts in a single API call using OpenAI's text-embedding-3-small model.

This function efficiently processes a batch of texts to generate embeddings, handling empty/invalid
texts gracefully and providing robust error handling with retry logic and fallback mechanisms.

Args:
    texts (List[str]): List of text strings to create embeddings for. Empty or whitespace-only
                      strings will be handled gracefully by returning zero vectors.

Returns:
    List[List[float]]: List of embeddings where each embedding is a list of 1536 floats.
                      The returned list maintains the same order and length as the input texts.
                      Empty or invalid texts will have corresponding zero vectors in the output.

Raises:
    Exception: May raise exceptions from OpenAI API calls, but these are handled internally
              with retry logic and fallback to individual embedding creation.

Note:
    - Uses OpenAI's "text-embedding-3-small" model with 1536-dimensional embeddings
    - Implements exponential backoff retry strategy (up to 3 attempts)
    - Falls back to individual embedding creation if batch processing fails
    - Returns zero vectors for empty/whitespace-only input texts
    - Preserves input order in the output list

Example:
    >>> texts = ["Hello world", "", "Python programming"]
    >>> embeddings = create_embeddings_batch(texts)
    >>> len(embeddings)  # Returns 3
    3
    >>> len(embeddings[0])  # Each embedding has 1536 dimensions
    1536
    >>> all(x == 0.0 for x in embeddings[1])  # Empty text gets zero vector
    True
"""
```

##### `generate_contextual_embedding` (function) `[+2/-3]`
**Component signature:**
```python
def generate_contextual_embedding(full_document: str, chunk: str) -> Tuple[str, bool]:
```
**Docstring:**
```
"""
Generate contextual information for a chunk within a document to improve retrieval.

This function uses OpenAI's API to generate a succinct contextual description that
situates a specific text chunk within the broader document context. This contextual
information is then prepended to the original chunk to enhance search retrieval
accuracy and relevance.

Args:
    full_document (str): The complete document text. Only the first 25,000 characters
        are used to generate context to stay within API limits.
    chunk (str): The specific chunk of text to generate contextual information for.
        This chunk should be a subset or related portion of the full document.

Returns:
    Tuple[str, bool]: A tuple containing:
        - str: The contextual text that situates the chunk within the document.
          If successful, this will be the generated context followed by "---"
          and the original chunk. If failed, returns the original chunk unchanged.
        - bool: True if contextual embedding was successfully performed using the
          OpenAI API, False if an error occurred and the original chunk was returned.

Environment Variables:
    MODEL_CHOICE: The OpenAI model to use for generating contextual information.
    OPENAI_API_KEY: Required OpenAI API key for authentication.

Raises:
    Exception: Any exceptions during API calls are caught and logged, with the
        function gracefully falling back to returning the original chunk.

Example:
    >>> full_doc = "This is a research paper about machine learning..."
    >>> chunk = "Neural networks are computational models..."
    >>> context_text, success = generate_contextual_embedding(full_doc, chunk)
    >>> if success:
    ...     print("Contextual embedding generated successfully")

Note:
    - The function limits the full document to 25,000 characters to manage API costs
      and token limits.
    - Uses a maximum of 200 completion tokens for the generated context.
    - Implements error handling to ensure the function always returns a usable result.
"""
```

##### `add_documents_to_supabase` (function) `[+31/-5]`
**Component signature:**
```python
def add_documents_to_supabase(client: Client, urls: List[str], chunk_numbers: List[int], contents: List[str], metadatas: List[Dict[str, Any]], url_to_full_document: Dict[str, str], batch_size: int = 20) -> None:
```
**Docstring:**
```
"""
Add documents to the Supabase crawled_pages table in batches.

This function processes document chunks and inserts them into the Supabase database.
It handles deletion of existing records to prevent duplicates, optional contextual
embeddings, and batch processing with retry logic for robust insertion.

:param client: Supabase client instance for database operations
:type client: Client
:param urls: List of URLs corresponding to each document chunk
:type urls: List[str]
:param chunk_numbers: List of chunk numbers for each document piece
:type chunk_numbers: List[int]
:param contents: List of document content strings to be processed
:type contents: List[str]
:param metadatas: List of metadata dictionaries for each document chunk
:type metadatas: List[Dict[str, Any]]
:param url_to_full_document: Dictionary mapping URLs to their complete document content
:type url_to_full_document: Dict[str, str]
:param batch_size: Number of documents to process in each batch, defaults to 20
:type batch_size: int, optional
:rtype: None

.. note::
   The function deletes existing records for the provided URLs before insertion
   to prevent duplicates. It uses batch operations for efficiency.

.. note::
   Contextual embeddings are applied if USE_CONTEXTUAL_EMBEDDINGS environment
   variable is set to "true". This enhances search retrieval by providing
   context for each chunk within the full document.

The function performs the following operations:

1. Deletes existing records for the provided URLs
2. Processes documents in batches to manage memory usage
3. Optionally applies contextual embeddings using parallel processing
4. Creates embeddings for all content chunks
5. Retrieves or creates source UUIDs for each domain
6. Inserts processed data with retry logic and exponential backoff

:raises Exception: Various exceptions may be raised during database operations,
                  embedding generation, or contextual processing. The function
                  includes comprehensive error handling and fallback mechanisms.

.. warning::
   Records with missing source UUIDs will be skipped during insertion.
   Individual record insertion is attempted as a fallback if batch insertion fails.
"""
```

##### `generate_code_example_summary` (function) `[+2/-3]`
**Component signature:**
```python
def generate_code_example_summary(code: str, context_before: str, context_after: str) -> str:
```
**Docstring:**
```
"""
Generate a summary for a code example using its surrounding context.

This function uses OpenAI's API to analyze a code snippet along with its surrounding
context to produce a concise summary that describes what the code demonstrates and
its practical purpose.

Args:
    code (str): The code example to summarize. Will be truncated to 1500 characters
        if longer to fit within API limits.
    context_before (str): Context text that appears before the code example. Will be
        truncated to the last 500 characters if longer.
    context_after (str): Context text that appears after the code example. Will be
        truncated to the first 500 characters if longer.
    
Returns:
    str: A concise summary (2-3 sentences) describing what the code example
        demonstrates and its purpose. Returns a default message if API call fails.
        
Raises:
    Exception: Catches and logs any exceptions from the OpenAI API call, returning
        a fallback summary instead of propagating the error.
        
Note:
    - Requires OPENAI_API_KEY environment variable to be set
    - Uses MODEL_CHOICE environment variable to determine which OpenAI model to use
    - Context is automatically truncated to manage API token limits
    - Falls back to a generic message if the API call fails
"""
```

##### `add_code_examples_to_supabase` (function) `[+8/-3]`
**Component signature:**
```python
def add_code_examples_to_supabase(client: Client, urls: List[str], chunk_numbers: List[int], code_examples: List[str], summaries: List[str], metadatas: List[Dict[str, Any]], batch_size: int = 20):
```
**Docstring:**
```
"""
Add code examples to the Supabase code_examples table in batches.

This function processes code examples by creating embeddings for combined code and summary text,
then inserts them into a Supabase database table. It handles batch processing, embedding creation,
and includes retry logic for robust database operations.

Args:
    client (Client): Supabase client instance for database operations
    urls (List[str]): List of URLs where the code examples were found
    chunk_numbers (List[int]): List of chunk numbers corresponding to each code example
    code_examples (List[str]): List of code example contents to be stored
    summaries (List[str]): List of summaries describing each code example
    metadatas (List[Dict[str, Any]]): List of metadata dictionaries containing additional information
    batch_size (int, optional): Size of each batch for insertion. Defaults to 20.

Returns:
    None

Raises:
    Exception: Various exceptions may be raised during database operations or embedding creation.
              The function includes error handling and retry logic to manage these gracefully.

Note:
    - Existing records for the provided URLs are deleted before inserting new ones
    - Embeddings are created by combining code examples with their summaries
    - The function includes exponential backoff retry logic for failed database operations
    - If batch insertion fails, individual record insertion is attempted as a fallback
    - Zero or invalid embeddings are detected and recreated using fallback methods

Example:
    >>> client = create_client(url, key)
    >>> urls = ["https://example.com/code1", "https://example.com/code2"]
    >>> chunks = [1, 2]
    >>> codes = ["def hello():\\n    print('Hello')", "def world():\\n    print('World')"]
    >>> summaries = ["Simple hello function", "Simple world function"]
    >>> metadata = [{"language": "python"}, {"language": "python"}]
    >>> add_code_examples_to_supabase(client, urls, chunks, codes, summaries, metadata)
"""
```

##### `update_source_info` (function) `[+46/-22]`
**Component signature:**
```python
def update_source_info(client: Client, domain_name: str, summary: str, word_count: int, table_name_for_source: Optional[str] = None):
```
**Docstring:**
```
"""
Update or insert source information in the sources table.

Uses domain_name (source column) as the conflict target for upsert operation.
This function will either insert a new record if the domain doesn't exist,
or update the existing record if it does.

:param client: Supabase client instance for database operations
:type client: Client
:param domain_name: The source domain name (e.g., "example.com"). Used for the 'source' column
:type domain_name: str
:param summary: Summary description of the source content
:type summary: str
:param word_count: Total word count for the source content
:type word_count: int
:param table_name_for_source: The name of the table primarily associated with this source 
                             (e.g., "crawled_pages"). If None, a default will be generated
                             based on the domain name
:type table_name_for_source: Optional[str]

:raises Exception: If database operation fails or other unexpected errors occur

:returns: None
:rtype: None

.. note::
   - Requires a unique constraint on the 'source' column in the sources table
   - If table_name_for_source is None, generates a default name using pattern 'pages_{safe_domain}'
   - Non-alphanumeric characters in domain names are replaced with underscores for table naming
   - The function handles both insert and update operations automatically via upsert

.. warning::
   The domain_name parameter cannot be empty or None, as it's used as the conflict target
"""
```

##### `extract_source_summary` (function) `[+2/-3]`
**Component signature:**
```python
def extract_source_summary(source_id: str, content: str, max_length: int = 500) -> str:
```
**Docstring:**
```
"""
Extract a summary for a source from its content using an LLM.

This function uses the OpenAI API to generate a concise summary of the source content.
The content is truncated to avoid token limits and processed through OpenAI's chat completion
API to generate a 3-5 sentence summary describing what the library/tool/framework accomplishes.

:param source_id: The source ID (domain) used for identification and fallback summary
:type source_id: str
:param content: The content to extract a summary from
:type content: str
:param max_length: Maximum length of the summary, defaults to 500
:type max_length: int

:returns: A concise summary string describing the source content
:rtype: str

:raises Exception: If OpenAI API call fails, returns default summary instead

.. note::
    - Content is truncated to 25,000 characters to avoid token limits
    - Uses MODEL_CHOICE environment variable for OpenAI model selection
    - Falls back to default summary format if content is empty or API fails
    - Summary is truncated with "..." if it exceeds max_length

.. example::
    >>> summary = extract_source_summary("example.com", "This is a Python library for...")
    >>> print(summary)
    "This library provides Python utilities for..."
"""
```

---
**qodo-merge-pro[bot]**
*qodo-merge-pro bot reviewed 22 minutes ago*

**File: `src/utils.py`** (Outdated)
**File: `docs/quality_audit_of_google_crawled.md`** (Outdated)

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 18 minutes ago •*

### Generated tests for `get_or_create_source_uuid` ✏️️
**Function:** `get_or_create_source_uuid` `[+38/-0]`

**Component signature:**
```python
def get_or_create_source_uuid(client: Client, domain_name: str, table_name_for_source: str) -> Optional[str]:
```

**Tests for code changes in `get_or_create_source_uuid` function:**

**[happy path]**
The function should return the existing UUID when a source with the given `domain_name` already exists in the database.
```python
import pytest
from unittest.mock import Mock
from src.utils import get_or_create_source_uuid

def test_get_existing_source_uuid():
    # Given
    mock_client = Mock()
    existing_uuid = "123e4567-e89b-12d3-a456-426614174000"
    mock_response = Mock()
    mock_response.data = {"id": existing_uuid}
    mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_response
    
    domain_name = "example.com"
    table_name = "test_table"
    
    # When
    result = get_or_create_source_uuid(mock_client, domain_name, table_name)
    
    # Then
    assert result == existing_uuid
    mock_client.table.assert_called_with("sources")
    mock_client.table.return_value.select.assert_called_with("id")
    mock_client.table.return_value.select.return_value.eq.assert_called_with("source", domain_name)
```

**[happy path]**
The function should create a new source entry with default summary and `total_words` values when the source doesn't exist and return the new UUID.
```python
import pytest
from unittest.mock import Mock
from src.utils import get_or_create_source_uuid

def test_create_new_source_uuid():
    # Given
    mock_client = Mock()
    new_uuid = "987fcdeb-51a2-43d1-9f12-123456789abc"
    
    # Mock existing source check (returns None)
    mock_select_response = Mock()
    mock_select_response.data = None
    mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_select_response
    
    # Mock insert response
    mock_insert_response = Mock()
    mock_insert_response.data = [{"id": new_uuid}]
    mock_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response
    
    domain_name = "newdomain.com"
    table_name = "new_table"
    
    # When
    result = get_or_create_source_uuid(mock_client, domain_name, table_name)
    
    # Then
    assert result == new_uuid
    expected_insert_data = {
        "source": domain_name,
        "table_name": table_name,
        "summary": f"Content from {domain_name}",
        "total_words": 0
    }
    mock_client.table.return_value.insert.assert_called_with(expected_insert_data)
```

**[edge case]**
The function should return `None` when an exception occurs during database operations or when insert operation fails to return data.
```python
import pytest
from unittest.mock import Mock
from src.utils import get_or_create_source_uuid

def test_handle_database_errors():
    # Given
    mock_client = Mock()
    
    # Mock existing source check (returns None)
    mock_select_response = Mock()
    mock_select_response.data = None
    mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_select_response
    
    # Mock insert response with no data (simulating insert failure)
    mock_insert_response = Mock()
    mock_insert_response.data = []
    mock_insert_response.error = "Insert failed"
    mock_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response
    
    domain_name = "faileddomain.com"
    table_name = "failed_table"
    
    # When
    result = get_or_create_source_uuid(mock_client, domain_name, table_name)
    
    # Then
    assert result is None
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 18 minutes ago •*

### Generated tests for `create_embeddings_batch` ✏️️
**Function:** `create_embeddings_batch` `[+61/-36]`

**Component signature:**
```python
def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
```

**Tests for code changes in `create_embeddings_batch` function:**

**[happy path]**
The function should maintain original text positions in the output when some texts are filtered out for being empty.
```python
import pytest
from unittest.mock import patch, MagicMock
from src.utils import create_embeddings_batch

def test_position_preservation_with_filtered_texts():
    # Given: A list where valid texts are at specific positions
    texts = ["", "first valid", "", "", "second valid", ""]
    
    # Mock the OpenAI API response for the 2 valid texts
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(embedding=[1.0] * 1536),  # For "first valid"
        MagicMock(embedding=[2.0] * 1536)   # For "second valid"
    ]
    
    with patch('openai.embeddings.create', return_value=mock_response):
        # When: Creating embeddings
        result = create_embeddings_batch(texts)
        
        # Then: Valid embeddings should be at their original positions
        assert len(result) == 6
        assert result[0] == [0.0] * 1536  # Position 0: empty
        assert result[1] == [1.0] * 1536  # Position 1: "first valid"
        assert result[2] == [0.0] * 1536  # Position 2: empty
        assert result[3] == [0.0] * 1536  # Position 3: empty
        assert result[4] == [2.0] * 1536  # Position 4: "second valid"
        assert result[5] == [0.0] * 1536  # Position 5: empty
```

**[edge case]**
The function should return zero vectors for empty or whitespace-only texts while preserving their positions in the output list.
```python
import pytest
from unittest.mock import patch, MagicMock
from src.utils import create_embeddings_batch

def test_empty_and_whitespace_texts_handling():
    # Given: A list with empty strings, whitespace-only strings, and valid text
    texts = ["", "   ", "valid text", "\n\t", "another valid text"]
    
    # Mock the OpenAI API response for valid texts only
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(embedding=[0.1] * 1536),  # For "valid text"
        MagicMock(embedding=[0.2] * 1536)   # For "another valid text"
    ]
    
    with patch('openai.embeddings.create', return_value=mock_response):
        # When: Creating embeddings for the mixed list
        result = create_embeddings_batch(texts)
        
        # Then: Should return 5 embeddings with zero vectors for empty/whitespace texts
        assert len(result) == 5
        assert result[0] == [0.0] * 1536  # Empty string
        assert result[1] == [0.0] * 1536  # Whitespace only
        assert result[2] == [0.1] * 1536  # Valid text
        assert result[3] == [0.0] * 1536  # Whitespace only
        assert result[4] == [0.2] * 1536  # Valid text
```

**[edge case]**
The function should return all zero vectors when all input texts are empty or whitespace-only.
```python
import pytest
from src.utils import create_embeddings_batch

def test_all_empty_texts_return_zero_vectors():
    # Given: A list with only empty and whitespace-only strings
    texts = ["", "   ", "\n", "\t\t", "  \n  "]
    
    # When: Creating embeddings (no API call should be made)
    result = create_embeddings_batch(texts)
    
    # Then: Should return zero vectors for all positions without calling OpenAI API
    assert len(result) == 5
    for embedding in result:
        assert embedding == [0.0] * 1536
        assert len(embedding) == 1536
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 18 minutes ago •*

### Generated tests for `generate_contextual_embedding` ✏️️
**Function:** `generate_contextual_embedding` `[+2/-3]`

**Component signature:**
```python
def generate_contextual_embedding(full_document: str, chunk: str) -> Tuple[str, bool]:
```

**Tests for code changes in `generate_contextual_embedding` function:**

**[happy path]**
The function should successfully generate contextual embedding when OpenAI API call succeeds with `max_completion_tokens` parameter instead of deprecated `max_tokens`.
```python
import pytest
from unittest.mock import patch, MagicMock
from src.utils import generate_contextual_embedding

def test_generate_contextual_embedding_success_with_max_completion_tokens():
    # Given
    full_document = "This is a comprehensive document about artificial intelligence and machine learning."
    chunk = "Machine learning is a subset of AI."
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "This chunk discusses machine learning within the context of AI."
    
    with patch('src.utils.openai.chat.completions.create') as mock_create:
        mock_create.return_value = mock_response
        
        # When
        result_text, success = generate_contextual_embedding(full_document, chunk)
        
        # Then
        assert success is True
        assert "This chunk discusses machine learning within the context of AI." in result_text
        assert chunk in result_text
        assert "---" in result_text
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert 'max_completion_tokens' in call_args.kwargs
        assert call_args.kwargs['max_completion_tokens'] == 200
        assert 'temperature' not in call_args.kwargs
        assert 'max_tokens' not in call_args.kwargs
```

**[edge case]**
The function should return original chunk and `False` when OpenAI API call fails, ensuring graceful error handling.
```python
import pytest
from unittest.mock import patch
from src.utils import generate_contextual_embedding

def test_generate_contextual_embedding_api_failure():
    # Given
    full_document = "This is a test document."
    chunk = "This is a test chunk."
    
    with patch('src.utils.openai.chat.completions.create') as mock_create:
        mock_create.side_effect = Exception("API connection failed")
        
        # When
        result_text, success = generate_contextual_embedding(full_document, chunk)
        
        # Then
        assert success is False
        assert result_text == chunk
        mock_create.assert_called_once()
```

**[edge case]**
The function should handle large documents by truncating to 25000 characters and still use `max_completion_tokens` parameter correctly.
```python
import pytest
from unittest.mock import patch, MagicMock
from src.utils import generate_contextual_embedding

def test_generate_contextual_embedding_large_document_truncation():
    # Given
    large_document = "A" * 30000  # Document larger than 25000 characters
    chunk = "This is a small chunk."
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Context for the chunk."
    
    with patch('src.utils.openai.chat.completions.create') as mock_create:
        mock_create.return_value = mock_response
        
        # When
        result_text, success = generate_contextual_embedding(large_document, chunk)
        
        # Then
        assert success is True
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        prompt_content = call_args.kwargs['messages'][1]['content']
        # Verify document was truncated to 25000 characters in the prompt
        assert large_document[:25000] in prompt_content
        assert len(large_document[:25000]) == 25000
        # Verify max_completion_tokens is used instead of max_tokens
        assert 'max_completion_tokens' in call_args.kwargs
        assert call_args.kwargs['max_completion_tokens'] == 200
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 18 minutes ago •*

### Generated tests for `add_documents_to_supabase` ✏️️
**Function:** `add_documents_to_supabase` `[+31/-5]`

**Component signature:**
```python
def add_documents_to_supabase(client: Client, urls: List[str], chunk_numbers: List[int], contents: List[str], metadatas: List[Dict[str, Any]], url_to_full_document: Dict[str, str], batch_size: int = 20) -> None:
```

**Tests for code changes in `add_documents_to_supabase` function:**

**[happy path]**
The function should successfully fetch or create source UUIDs for valid URLs and use them as `source_id` in the inserted records.
```python
import pytest
from unittest.mock import Mock, patch
from src.utils import add_documents_to_supabase

def test_add_documents_with_valid_urls_creates_source_uuids():
    # Given
    mock_client = Mock()
    mock_client.table.return_value.delete.return_value.in_.return_value.execute.return_value = None
    mock_client.table.return_value.insert.return_value.execute.return_value = None
    
    urls = ["https://example.com/page1", "https://test.org/page2"]
    chunk_numbers = [1, 2]
    contents = ["content1", "content2"]
    metadatas = [{}, {}]
    url_to_full_document = {"https://example.com/page1": "full doc 1", "https://test.org/page2": "full doc 2"}
    
    with patch('src.utils.get_or_create_source_uuid') as mock_get_uuid, \
         patch('src.utils.create_embeddings_batch') as mock_embeddings, \
         patch('os.getenv') as mock_getenv:
        
        mock_get_uuid.side_effect = ["uuid-123", "uuid-456"]
        mock_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_getenv.return_value = "false"
        
        # When
        add_documents_to_supabase(mock_client, urls, chunk_numbers, contents, metadatas, url_to_full_document)
        
        # Then
        assert mock_get_uuid.call_count == 2
        mock_get_uuid.assert_any_call(mock_client, "example.com", "crawled_pages_example_com")
        mock_get_uuid.assert_any_call(mock_client, "test.org", "crawled_pages_test_org")
        
        # Verify that the insert was called with the correct source_id UUIDs
        insert_call = mock_client.table.return_value.insert.call_args[0][0]
        assert len(insert_call) == 2
        assert insert_call[0]["source_id"] == "uuid-123"
        assert insert_call[1]["source_id"] == "uuid-456"
```

**[edge case]**
The function should skip records when `get_or_create_source_uuid` returns `None` for a URL, preventing insertion of records with missing source UUIDs.
```python
import pytest
from unittest.mock import Mock, patch
from src.utils import add_documents_to_supabase

def test_add_documents_skips_records_with_missing_source_uuid():
    # Given
    mock_client = Mock()
    mock_client.table.return_value.delete.return_value.in_.return_value.execute.return_value = None
    mock_client.table.return_value.insert.return_value.execute.return_value = None
    
    urls = ["https://example.com/page1", "https://invalid-url"]
    chunk_numbers = [1, 2]
    contents = ["content1", "content2"]
    metadatas = [{}, {}]
    url_to_full_document = {"https://example.com/page1": "full doc 1", "https://invalid-url": "full doc 2"}
    
    with patch('src.utils.get_or_create_source_uuid') as mock_get_uuid, \
         patch('src.utils.create_embeddings_batch') as mock_embeddings, \
         patch('os.getenv') as mock_getenv, \
         patch('builtins.print') as mock_print:
        
        mock_get_uuid.side_effect = ["uuid-123", None]  # Second URL returns None
        mock_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_getenv.return_value = "false"
        
        # When
        add_documents_to_supabase(mock_client, urls, chunk_numbers, contents, metadatas, url_to_full_document)
        
        # Then
        # Verify warning was printed for missing UUID
        mock_print.assert_any_call("Warning: Missing source UUID for URL https://invalid-url. Skipping this record for crawled_pages.")
        
        # Verify only one record was inserted (the one with valid UUID)
        insert_call = mock_client.table.return_value.insert.call_args[0][0]
        assert len(insert_call) == 1
        assert insert_call[0]["source_id"] == "uuid-123"
        assert insert_call[0]["url"] == "https://example.com/page1"
```

**[edge case]**
The function should handle URLs with empty domain names by printing a warning and appending `None` to `batch_source_uuids`, then skip those records during insertion.
```python
import pytest
from unittest.mock import Mock, patch
from src.utils import add_documents_to_supabase

def test_add_documents_handles_urls_with_empty_domain():
    # Given
    mock_client = Mock()
    mock_client.table.return_value.delete.return_value.in_.return_value.execute.return_value = None
    mock_client.table.return_value.insert.return_value.execute.return_value = None
    
    urls = ["https://example.com/page1", ""]  # Empty URL
    chunk_numbers = [1, 2]
    contents = ["content1", "content2"]
    metadatas = [{}, {}]
    url_to_full_document = {"https://example.com/page1": "full doc 1", "": "full doc 2"}
    
    with patch('src.utils.get_or_create_source_uuid') as mock_get_uuid, \
         patch('src.utils.create_embeddings_batch') as mock_embeddings, \
         patch('os.getenv') as mock_getenv, \
         patch('builtins.print') as mock_print:
        
        mock_get_uuid.return_value = "uuid-123"  # Only called once for valid URL
        mock_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_getenv.return_value = "false"
        
        # When
        add_documents_to_supabase(mock_client, urls, chunk_numbers, contents, metadatas, url_to_full_document)
        
        # Then
        # Verify warning was printed for empty domain
        mock_print.assert_any_call("Warning: Could not determine domain for URL . Skipping source UUID fetch.")
        mock_print.assert_any_call("Warning: Missing source UUID for URL . Skipping this record for crawled_pages.")
        
        # Verify get_or_create_source_uuid was only called once (for valid URL)
        assert mock_get_uuid.call_count == 1
        mock_get_uuid.assert_called_with(mock_client, "example.com", "crawled_pages_example_com")
        
        # Verify only one record was inserted
        insert_call = mock_client.table.return_value.insert.call_args[0][0]
        assert len(insert_call) == 1
        assert insert_call[0]["url"] == "https://example.com/page1"
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 18 minutes ago •*

### Generated tests for `generate_code_example_summary` ✏️️
**Function:** `generate_code_example_summary` `[+2/-3]`

**Component signature:**
```python
def generate_code_example_summary(code: str, context_before: str, context_after: str) -> str:
```

**Tests for code changes in `generate_code_example_summary` function:**

**[happy path]**
The function should successfully generate a summary when OpenAI API call succeeds with the updated `max_completion_tokens` parameter instead of deprecated `max_tokens`.
```python
import pytest
from unittest.mock import patch, MagicMock
import os
from src.utils import generate_code_example_summary

def test_generate_summary_with_max_completion_tokens():
    # Given
    code = "print('Hello, World!')"
    context_before = "This is a simple example"
    context_after = "This demonstrates basic output"
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "This code example demonstrates a basic print statement."
    
    # When
    with patch.dict(os.environ, {"MODEL_CHOICE": "gpt-3.5-turbo"}):
        with patch('openai.chat.completions.create', return_value=mock_response) as mock_create:
            result = generate_code_example_summary(code, context_before, context_after)
    
    # Then
    mock_create.assert_called_once()
    call_args = mock_create.call_args
    assert 'max_completion_tokens' in call_args.kwargs
    assert call_args.kwargs['max_completion_tokens'] == 100
    assert 'max_tokens' not in call_args.kwargs
    assert 'temperature' not in call_args.kwargs
    assert result == "This code example demonstrates a basic print statement."
```

**[edge case]**
The function should return the default fallback message when OpenAI API call fails, ensuring the error handling remains unchanged.
```python
import pytest
from unittest.mock import patch
import os
from src.utils import generate_code_example_summary

def test_generate_summary_error_handling_unchanged():
    # Given
    code = "def example(): pass"
    context_before = "Function definition"
    context_after = "End of function"
    
    # When
    with patch.dict(os.environ, {"MODEL_CHOICE": "gpt-3.5-turbo"}):
        with patch('openai.chat.completions.create', side_effect=Exception("API Error")):
            with patch('builtins.print') as mock_print:
                result = generate_code_example_summary(code, context_before, context_after)
    
    # Then
    mock_print.assert_called_once_with("Error generating code example summary: API Error")
    assert result == "Code example for demonstration purposes."
```

**[edge case]**
The function should properly truncate long inputs and construct the prompt with the updated API parameters when processing large code examples.
```python
import pytest
from unittest.mock import patch, MagicMock
import os
from src.utils import generate_code_example_summary

def test_generate_summary_with_long_inputs():
    # Given
    long_code = "x = 1\\n" * 1000  # Creates code longer than 1500 chars
    long_context_before = "context " * 200  # Creates context longer than 500 chars
    long_context_after = "after " * 200  # Creates context longer than 500 chars
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "  Summary with whitespace  "
    
    # When
    with patch.dict(os.environ, {"MODEL_CHOICE": "gpt-4"}):
        with patch('openai.chat.completions.create', return_value=mock_response) as mock_create:
            result = generate_code_example_summary(long_code, long_context_before, long_context_after)
    
    # Then
    call_args = mock_create.call_args
    prompt_content = call_args[1]['messages'][1]['content']
    
    # Verify truncation occurred
    assert len(prompt_content.split('<code_example>')[1].split('</code_example>')[0].strip()) <= 1500
    assert len(prompt_content.split('<context_before>')[1].split('</context_before>')[0].strip()) <= 500
    assert len(prompt_content.split('<context_after>')[1].split('</context_after>')[0].strip()) <= 500
    
    # Verify API call uses new parameter
    assert call_args.kwargs['max_completion_tokens'] == 100
    assert result == "Summary with whitespace"  # Verify .strip() is applied
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 18 minutes ago •*

### Generated tests for `add_code_examples_to_supabase` ✏️️
**Function:** `add_code_examples_to_supabase` `[+8/-3]`

**Component signature:**
```python
def add_code_examples_to_supabase(client: Client, urls: List[str], chunk_numbers: List[int], code_examples: List[str], summaries: List[str], metadatas: List[Dict[str, Any]], batch_size: int = 20):
```

**Tests for code changes in `add_code_examples_to_supabase` function:**

**[happy path]**
The function should correctly extract `source_domain_for_code` from URL `netloc` and use it as `source_id` in batch data.
```python
import pytest
from unittest.mock import Mock, MagicMock
from src.utils import add_code_examples_to_supabase

def test_source_id_extraction_from_netloc():
    # Given
    mock_client = Mock()
    mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = None
    mock_client.table.return_value.insert.return_value.execute.return_value = None
    
    urls = ["https://example.com/path/to/code"]
    chunk_numbers = [1]
    code_examples = ["def hello(): pass"]
    summaries = ["A simple hello function"]
    metadatas = [{"type": "function"}]
    
    # Mock the embedding functions to avoid API calls
    import src.utils
    original_create_embeddings_batch = src.utils.create_embeddings_batch
    src.utils.create_embeddings_batch = Mock(return_value=[[0.1] * 1536])
    
    try:
        # When
        add_code_examples_to_supabase(
            mock_client, urls, chunk_numbers, code_examples, summaries, metadatas
        )
        
        # Then
        insert_call = mock_client.table.return_value.insert.call_args[0][0]
        assert len(insert_call) == 1
        assert insert_call[0]['source_id'] == 'example.com'
        assert insert_call[0]['url'] == urls[0]
    finally:
        src.utils.create_embeddings_batch = original_create_embeddings_batch
```

**[happy path]**
The function should maintain consistent variable naming with `source_domain_for_code` throughout the batch processing.
```python
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.utils import add_code_examples_to_supabase

def test_consistent_source_domain_variable_naming():
    # Given
    mock_client = Mock()
    mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = None
    mock_client.table.return_value.insert.return_value.execute.return_value = None
    
    urls = ["https://github.com/repo", "https://gitlab.com/project"]
    chunk_numbers = [1, 2]
    code_examples = ["def func1(): pass", "def func2(): pass"]
    summaries = ["Function 1", "Function 2"]
    metadatas = [{"type": "function"}, {"type": "function"}]
    
    # Mock the embedding functions to avoid API calls
    import src.utils
    original_create_embeddings_batch = src.utils.create_embeddings_batch
    src.utils.create_embeddings_batch = Mock(return_value=[[0.3] * 1536, [0.4] * 1536])
    
    try:
        # When
        add_code_examples_to_supabase(
            mock_client, urls, chunk_numbers, code_examples, summaries, metadatas
        )
        
        # Then
        insert_call = mock_client.table.return_value.insert.call_args[0][0]
        assert len(insert_call) == 2
        assert insert_call[0]['source_id'] == 'github.com'
        assert insert_call[1]['source_id'] == 'gitlab.com'
        # Verify all records have the expected structure
        for i, record in enumerate(insert_call):
            assert 'source_id' in record
            assert record['url'] == urls[i]
            assert record['chunk_number'] == chunk_numbers[i]
    finally:
        src.utils.create_embeddings_batch = original_create_embeddings_batch
```

**[edge case]**
The function should fallback to using URL path as `source_id` when `netloc` is empty.
```python
import pytest
from unittest.mock import Mock, MagicMock
from src.utils import add_code_examples_to_supabase

def test_source_id_fallback_to_path():
    # Given
    mock_client = Mock()
    mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = None
    mock_client.table.return_value.insert.return_value.execute.return_value = None
    
    urls = ["/local/path/to/file.py"]  # URL without netloc
    chunk_numbers = [1]
    code_examples = ["class MyClass: pass"]
    summaries = ["A simple class definition"]
    metadatas = [{"type": "class"}]
    
    # Mock the embedding functions to avoid API calls
    import src.utils
    original_create_embeddings_batch = src.utils.create_embeddings_batch
    src.utils.create_embeddings_batch = Mock(return_value=[[0.2] * 1536])
    
    try:
        # When
        add_code_examples_to_supabase(
            mock_client, urls, chunk_numbers, code_examples, summaries, metadatas
        )
        
        # Then
        insert_call = mock_client.table.return_value.insert.call_args[0][0]
        assert len(insert_call) == 1
        assert insert_call[0]['source_id'] == '/local/path/to/file.py'
        assert insert_call[0]['url'] == urls[0]
    finally:
        src.utils.create_embeddings_batch = original_create_embeddings_batch
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 18 minutes ago •*

### Generated tests for `update_source_info` ✏️️
**Function:** `update_source_info` `[+46/-22]`

**Component signature:**
```python
def update_source_info(client: Client, domain_name: str, summary: str, word_count: int, table_name_for_source: Optional[str] = None):
```

**Tests for code changes in `update_source_info` function:**

**[happy path]**
The function should generate a default table name when `table_name_for_source` is `None`, replacing non-alphanumeric characters with underscores and adding `pages_` prefix.
```python
import pytest
from unittest.mock import Mock, MagicMock
from src.utils import update_source_info

def test_generates_default_table_name_from_domain():
    # Given
    mock_client = Mock()
    mock_response = Mock()
    mock_response.error = None
    mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
    
    domain_name = "docs.github.com"
    summary = "Test summary"
    word_count = 100
    
    # When
    update_source_info(mock_client, domain_name, summary, word_count)
    
    # Then
    expected_data = {
        "source": "docs.github.com",
        "summary": "Test summary", 
        "total_words": 100,
        "table_name": "pages_docs_github_com"
    }
    mock_client.table.assert_called_with("sources")
    mock_client.table.return_value.upsert.assert_called_with(
        expected_data,
        on_conflict="source"
    )
```

**[happy path]**
The function should use the provided `table_name_for_source` parameter instead of generating a default when it is explicitly provided.
```python
import pytest
from unittest.mock import Mock
from src.utils import update_source_info

def test_uses_provided_table_name_parameter():
    # Given
    mock_client = Mock()
    mock_response = Mock()
    mock_response.error = None
    mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
    
    domain_name = "example.com"
    summary = "Custom summary"
    word_count = 250
    custom_table_name = "custom_crawled_pages"
    
    # When
    update_source_info(mock_client, domain_name, summary, word_count, custom_table_name)
    
    # Then
    expected_data = {
        "source": "example.com",
        "summary": "Custom summary",
        "total_words": 250,
        "table_name": "custom_crawled_pages"
    }
    mock_client.table.return_value.upsert.assert_called_with(
        expected_data,
        on_conflict="source"
    )
```

**[edge case]**
The function should return early and print an error message when `domain_name` is empty or `None`.
```python
import pytest
from unittest.mock import Mock
from src.utils import update_source_info
import io
import sys

def test_returns_early_when_domain_name_empty():
    # Given
    mock_client = Mock()
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    # When
    update_source_info(mock_client, "", "summary", 100)
    
    # Then
    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()
    assert "Error: domain_name cannot be empty for update_source_info." in output
    mock_client.table.assert_not_called()
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 18 minutes ago •*

### Generated tests for `extract_source_summary` ✏️️
**Function:** `extract_source_summary` `[+2/-3]`

**Component signature:**
```python
def extract_source_summary(source_id: str, content: str, max_length: int = 500) -> str:
```

**Tests for code changes in `extract_source_summary` function:**

**[happy path]**
The function should successfully generate a summary using the OpenAI API with the new `max_completion_tokens` parameter instead of the deprecated `max_tokens` parameter.
```python
import pytest
import os
from unittest.mock import patch, MagicMock
from src.utils import extract_source_summary

def test_extract_source_summary_with_max_completion_tokens():
    # Given
    source_id = "test-library"
    content = "This is a test library that provides useful functionality for developers."
    expected_summary = "Test library provides useful functionality for developers."
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = expected_summary
    
    # When
    with patch('src.utils.openai.chat.completions.create') as mock_create:
        mock_create.return_value = mock_response
        with patch.dict(os.environ, {'MODEL_CHOICE': 'gpt-3.5-turbo'}):
            result = extract_source_summary(source_id, content)
    
    # Then
    assert result == expected_summary
    mock_create.assert_called_once()
    call_args = mock_create.call_args
    assert 'max_completion_tokens' in call_args.kwargs
    assert call_args.kwargs['max_completion_tokens'] == 150
    assert 'max_tokens' not in call_args.kwargs
    assert 'temperature' not in call_args.kwargs
```

**[edge case]**
The function should return the default summary when OpenAI API call fails, ensuring error handling works correctly with the new parameter configuration.
```python
import pytest
import os
from unittest.mock import patch
from src.utils import extract_source_summary

def test_extract_source_summary_api_failure_returns_default():
    # Given
    source_id = "failing-library"
    content = "Some content that should trigger API call"
    expected_default = f"Content from {source_id}"
    
    # When
    with patch('src.utils.openai.chat.completions.create') as mock_create:
        mock_create.side_effect = Exception("API Error")
        with patch.dict(os.environ, {'MODEL_CHOICE': 'gpt-3.5-turbo'}):
            result = extract_source_summary(source_id, content)
    
    # Then
    assert result == expected_default
    mock_create.assert_called_once()
    call_args = mock_create.call_args
    assert 'max_completion_tokens' in call_args.kwargs
    assert call_args.kwargs['max_completion_tokens'] == 150
```

**[edge case]**
The function should properly truncate long summaries to the specified `max_length` while using the new `max_completion_tokens` parameter.
```python
import pytest
import os
from unittest.mock import patch, MagicMock
from src.utils import extract_source_summary

def test_extract_source_summary_truncates_long_response():
    # Given
    source_id = "verbose-library"
    content = "Library content"
    max_length = 50
    long_summary = "This is a very long summary that exceeds the maximum length limit and should be truncated properly by the function."
    expected_result = long_summary[:max_length] + "..."
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = long_summary
    
    # When
    with patch('src.utils.openai.chat.completions.create') as mock_create:
        mock_create.return_value = mock_response
        with patch.dict(os.environ, {'MODEL_CHOICE': 'gpt-4'}):
            result = extract_source_summary(source_id, content, max_length)
    
    # Then
    assert result == expected_result
    assert len(result) == max_length + 3  # +3 for "..."
    mock_create.assert_called_once()
    call_args = mock_create.call_args
    assert 'max_completion_tokens' in call_args.kwargs
    assert call_args.kwargs['max_completion_tokens'] == 150
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 14 minutes ago •*

### Generated docstring for `get_or_create_source_uuid` 📚
**Function:** `get_or_create_source_uuid` `[+38/-0]`

**Component signature:**
```python
def get_or_create_source_uuid(client: Client, domain_name: str, table_name_for_source: str) -> Optional[str]:
```
**Docstring:**
```
"""
Retrieves the UUID of an existing source by its domain name or creates a new source entry
if it doesn't exist, then returns the UUID.

This function first attempts to find an existing source record in the 'sources' table
by matching the domain name. If found, it returns the existing UUID. If not found,
it creates a new source entry with default values and returns the newly generated UUID.

:param client: Supabase client instance for database operations
:type client: Client
:param domain_name: The domain name of the source (e.g., "example.com")
:type domain_name: str
:param table_name_for_source: The name of the table associated with this source
:type table_name_for_source: str

:returns: The UUID string of the source (existing or newly created), or None if an error occurred
:rtype: Optional[str]

:raises Exception: Catches and logs any exceptions that occur during database operations

.. note::
    When creating a new source, default values are set:
    - summary: "Content from {domain_name}"
    - total_words: 0

.. warning::
    This function prints error messages to stdout. Consider using proper logging
    in production environments.

Example:
    >>> client = create_client(url, key)
    >>> uuid = get_or_create_source_uuid(client, "example.com", "articles")
    >>> print(uuid)  # "550e8400-e29b-41d4-a716-446655440000"
"""
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 14 minutes ago •*

### Generated docstring for `create_embeddings_batch` 📚
**Function:** `create_embeddings_batch` `[+61/-36]`

**Component signature:**
```python
def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
```
**Docstring:**
```
"""
Create embeddings for multiple texts in a single API call using OpenAI's text-embedding-3-small model.

This function efficiently processes a batch of texts to generate embeddings, handling empty/invalid
texts gracefully and providing robust error handling with retry logic and fallback mechanisms.

Args:
    texts (List[str]): List of text strings to create embeddings for. Empty or whitespace-only
                      strings will be assigned zero vectors while valid texts will be processed
                      through the OpenAI API.

Returns:
    List[List[float]]: List of embeddings where each embedding is a list of 1536 floats.
                      The returned list maintains the same order and length as the input texts.
                      Empty or invalid input texts receive zero vectors [0.0] * 1536.

Raises:
    Exception: May raise exceptions from OpenAI API calls, though the function includes
              comprehensive error handling with retry logic and individual fallback processing.

Note:
    - Uses OpenAI's "text-embedding-3-small" model with 1536-dimensional embeddings
    - Implements exponential backoff retry strategy (3 attempts with 1s, 2s, 4s delays)
    - Falls back to individual embedding creation if batch processing fails
    - Preserves input order and handles mixed valid/invalid texts gracefully
    - Requires OPENAI_API_KEY environment variable to be set

Example:
    >>> texts = ["Hello world", "", "Python programming"]
    >>> embeddings = create_embeddings_batch(texts)
    >>> len(embeddings)  # Returns 3
    3
    >>> len(embeddings[0])  # Each embedding has 1536 dimensions
    1536
    >>> all(x == 0.0 for x in embeddings[1])  # Empty text gets zero vector
    True
"""
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 14 minutes ago •*

### Generated docstring for `generate_contextual_embedding` 📚
**Function:** `generate_contextual_embedding` `[+2/-3]`

**Component signature:**
```python
def generate_contextual_embedding(full_document: str, chunk: str) -> Tuple[str, bool]:
```
**Docstring:**
```
"""
Generate contextual information for a chunk within a document to improve retrieval.

This function uses OpenAI's API to generate a succinct contextual description that
situates a specific text chunk within the broader document context. The generated
context is prepended to the original chunk to enhance search retrieval accuracy.

Args:
    full_document (str): The complete document text. Only the first 25,000 characters
        are used to avoid token limits.
    chunk (str): The specific chunk of text to generate context for.
    
Returns:
    Tuple[str, bool]: A tuple containing:
        - str: The contextual text that situates the chunk within the document.
          If successful, this is the generated context followed by "---" and the
          original chunk. If failed, this is just the original chunk.
        - bool: True if contextual embedding was successfully performed using the
          OpenAI API, False if an error occurred and the original chunk was returned.
          
Raises:
    Exception: Any exceptions during API calls are caught and logged, with the
        function gracefully falling back to returning the original chunk.
        
Note:
    - Requires OPENAI_API_KEY environment variable to be set
    - Requires MODEL_CHOICE environment variable to specify the OpenAI model
    - Uses a maximum of 200 completion tokens for the generated context
    - Truncates full_document to 25,000 characters to manage token limits
"""
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 14 minutes ago •*

### Generated docstring for `add_documents_to_supabase` 📚
**Function:** `add_documents_to_supabase` `[+31/-5]`

**Component signature:**
```python
def add_documents_to_supabase(client: Client, urls: List[str], chunk_numbers: List[int], contents: List[str], metadatas: List[Dict[str, Any]], url_to_full_document: Dict[str, str], batch_size: int = 20) -> None:
```
**Docstring:**
```
"""
Add documents to the Supabase crawled_pages table in batches.

This function processes documents by first deleting existing records with the same URLs
to prevent duplicates, then inserting new records in batches. It supports contextual
embeddings and includes retry logic for robust database operations.

:param client: Supabase client instance for database operations
:type client: Client
:param urls: List of URLs corresponding to the documents
:type urls: List[str]
:param chunk_numbers: List of chunk numbers for each document piece
:type chunk_numbers: List[int]
:param contents: List of document content strings to be stored
:type contents: List[str]
:param metadatas: List of metadata dictionaries for each document
:type metadatas: List[Dict[str, Any]]
:param url_to_full_document: Dictionary mapping URLs to their complete document content
:type url_to_full_document: Dict[str, str]
:param batch_size: Number of records to process in each batch, defaults to 20
:type batch_size: int
:returns: None
:rtype: None

:raises Exception: When database operations fail after all retry attempts

.. note::
   The function uses the USE_CONTEXTUAL_EMBEDDINGS environment variable to determine
   whether to apply contextual embedding processing to document chunks.

.. warning::
   Existing records with matching URLs will be deleted before insertion to prevent
   duplicates. This operation cannot be undone.

The function performs the following operations:

1. Deletes existing records with matching URLs from the crawled_pages table
2. Processes documents in batches to manage memory usage
3. Optionally applies contextual embeddings using parallel processing
4. Creates embeddings for all content using the OpenAI API
5. Retrieves or creates source UUIDs for each document's domain
6. Inserts processed data into the crawled_pages table with retry logic

Example:
    >>> client = create_client(url, key)
    >>> urls = ["https://example.com/page1", "https://example.com/page2"]
    >>> contents = ["Content 1", "Content 2"]
    >>> metadatas = [{"title": "Page 1"}, {"title": "Page 2"}]
    >>> url_to_full_document = {"https://example.com/page1": "Full content 1"}
    >>> add_documents_to_supabase(client, urls, [1, 2], contents, metadatas, url_to_full_document)
"""
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 14 minutes ago •*

### Generated docstring for `generate_code_example_summary` 📚
**Function:** `generate_code_example_summary` `[+2/-3]`

**Component signature:**
```python
def generate_code_example_summary(code: str, context_before: str, context_after: str) -> str:
```
**Docstring:**
```
"""
Generate a summary for a code example using its surrounding context.

This function uses OpenAI's API to analyze a code snippet along with its
surrounding context to produce a concise summary describing what the code
demonstrates and its practical purpose.

Args:
    code (str): The code example to summarize. Will be truncated to 1500 
        characters if longer.
    context_before (str): Context text appearing before the code example.
        Will be truncated to last 500 characters if longer.
    context_after (str): Context text appearing after the code example.
        Will be truncated to first 500 characters if longer.
        
Returns:
    str: A concise 2-3 sentence summary describing what the code example
        demonstrates and its purpose. Returns a default message if the
        API call fails.
        
Raises:
    Exception: Catches and logs any exceptions from the OpenAI API call,
        returning a fallback summary instead of propagating the error.
        
Note:
    Requires OPENAI_API_KEY and MODEL_CHOICE environment variables to be set.
    The function limits token usage by truncating input text and setting
    max_completion_tokens to 100.
"""
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 14 minutes ago •*

### Generated docstring for `add_code_examples_to_supabase` 📚
**Function:** `add_code_examples_to_supabase` `[+8/-3]`

**Component signature:**
```python
def add_code_examples_to_supabase(client: Client, urls: List[str], chunk_numbers: List[int], code_examples: List[str], summaries: List[str], metadatas: List[Dict[str, Any]], batch_size: int = 20):
```
**Docstring:**
```
"""
Add code examples to the Supabase code_examples table in batches.

This function processes code examples by creating embeddings for combined code and summary text,
then inserts them into a Supabase database table. It handles batch processing, embedding creation,
and includes retry logic for robust database operations.

Args:
    client (Client): Supabase client instance for database operations
    urls (List[str]): List of URLs where the code examples were found
    chunk_numbers (List[int]): List of chunk numbers corresponding to each code example
    code_examples (List[str]): List of code example contents to be stored
    summaries (List[str]): List of summaries describing each code example
    metadatas (List[Dict[str, Any]]): List of metadata dictionaries containing additional information
    batch_size (int, optional): Size of each batch for insertion. Defaults to 20.

Returns:
    None

Raises:
    Exception: Various exceptions may be raised during database operations or embedding creation.
              The function includes retry logic and fallback mechanisms to handle failures gracefully.

Note:
    - Existing records for the provided URLs are deleted before insertion
    - Embeddings are created by combining code examples with their summaries
    - Invalid or zero embeddings are detected and recreated using fallback methods
    - Batch insertion includes exponential backoff retry logic
    - Individual record insertion is attempted as a last resort if batch insertion fails
    - Progress is logged during the insertion process

Example:
    >>> client = create_client(url, key)
    >>> urls = ["https://example.com/code1", "https://example.com/code2"]
    >>> chunk_numbers = [1, 2]
    >>> code_examples = ["def hello():\\n    print('Hello')", "def world():\\n    print('World')"]
    >>> summaries = ["Simple hello function", "Simple world function"]
    >>> metadatas = [{"language": "python"}, {"language": "python"}]
    >>> add_code_examples_to_supabase(client, urls, chunk_numbers, code_examples, summaries, metadatas)
"""
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 14 minutes ago •*

### Generated docstring for `update_source_info` 📚
**Function:** `update_source_info` `[+46/-22]`

**Component signature:**
```python
def update_source_info(client: Client, domain_name: str, summary: str, word_count: int, table_name_for_source: Optional[str] = None):
```
**Docstring:**
```
"""
Update or insert source information in the sources table.

Uses domain_name (source column) as the conflict target for upsert operation.
This function will either insert a new record or update an existing one based
on the domain name.

:param client: Supabase client instance for database operations
:type client: Client
:param domain_name: The source domain name (e.g., "example.com"). Used for the 'source' column
:type domain_name: str
:param summary: Summary description of the source content
:type summary: str
:param word_count: Total word count for the source content
:type word_count: int
:param table_name_for_source: The name of the table primarily associated with this source 
                             (e.g., "crawled_pages"). If None, generates a default based on domain
:type table_name_for_source: Optional[str]

:raises Exception: If database operation fails or other unexpected errors occur

:returns: None
:rtype: None

.. note::
   - Requires a unique constraint on the 'source' column in the sources table
   - If table_name_for_source is None, generates default name as "pages_{safe_domain}"
   - Non-alphanumeric characters in domain names are replaced with underscores
   - Prints success/error messages to console for operation feedback

.. warning::
   The function will return early if domain_name is empty or None
"""
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 14 minutes ago •*

### Generated docstring for `extract_source_summary` 📚
**Function:** `extract_source_summary` `[+2/-3]`

**Component signature:**
```python
def extract_source_summary(source_id: str, content: str, max_length: int = 500) -> str:
```
**Docstring:**
```
"""
Extract a summary for a source from its content using an LLM.

This function uses the OpenAI API to generate a concise summary of the source content.
The content is truncated to avoid token limits and processed through OpenAI's chat completion
API to create a meaningful 3-5 sentence summary describing the library/tool/framework.

Args:
    source_id (str): The source ID (domain) used for identification and fallback summary
    content (str): The content to extract a summary from
    max_length (int, optional): Maximum length of the summary. Defaults to 500.
    
Returns:
    str: A summary string describing the source content. Returns a default summary
         if content is empty or if API call fails.
         
Raises:
    Exception: Catches and handles any exceptions from the OpenAI API call,
              returning a default summary instead.
              
Note:
    - Requires OPENAI_API_KEY environment variable to be set
    - Uses MODEL_CHOICE environment variable to determine the OpenAI model
    - Content is truncated to 25,000 characters to avoid token limits
    - Summary is further truncated if it exceeds max_length parameter
"""
```

---
**@qodo-merge-pro Qodo Merge Pro**
*qodo-merge-pro bot commented 12 minutes ago •*

### Generated code suggestions for `get_or_create_source_uuid`
**Function:** `get_or_create_source_uuid` `[+38/-0]`

**Component signature:**
```python
def get_or_create_source_uuid(client: Client, domain_name: str, table_name_for_source: str) -> Optional[str]:
```

**Suggestions and improvements for code changes in `get_or_create_source_uuid` function:**

**Category:** Best practice
**Suggestions:**
*   Replace `print` statements with proper logging for better error handling and monitoring.
*   Replace `print` statements with proper logging to enable better debugging and production monitoring. Using `print` statements in production code makes it difficult to control log levels and destinations.
```diff
-print(f"Error creating new source {domain_name}: No data returned after insert. Error: {insert_response.error}")
-print(f"Exception in get_or_create_source_uuid for {domain_name}: {e}")
+import logging
+logger = logging.getLogger(__name__)
 
+logger.error(f"Error creating new source {domain_name}: No data returned after insert. Error: {insert_response.error}")
+logger.exception(f"Exception in get_or_create_source_uuid for {domain_name}: {e}")
+
```

**Category:** Enhancement
**Suggestions:**
*   Add input validation for domain name to ensure it's not empty and normalize it.
*   Add validation for the `domain_name` parameter to ensure it's a valid domain format before proceeding with database operations. This prevents potential issues with malformed domain names.
```python
 def get_or_create_source_uuid(client: Client, domain_name: str, table_name_for_source: str) -> Optional[str]:
+    if not domain_name or not domain_name.strip():
+        return None
+    
+    domain_name = domain_name.strip().lower()
     try:
         response = client.table("sources").select("id").eq("source", domain_name).maybe_single().execute()
 
Bug	
Add error handling for the database select query to catch potential database errors.
Check for database errors in the initial select query response before proceeding. The
current code only checks if data exists but doesn't handle potential database errors that
could occur during the query.

src/utils.py

 response = client.table("sources").select("id").eq("source", domain_name).maybe_single().execute()
+
+if response.error:
+    logger.error(f"Error querying source {domain_name}: {response.error}")
+    return None
 
 if response.data:
     return response.data["id"]
 
Maintainability	
Separate database errors from empty response handling for better error diagnosis.
Handle the case where the insert operation succeeds but returns an empty data array more
gracefully. The current error message assumes this is always an error, but it might be a
valid response in some database configurations.

src/utils.py

 insert_response = client.table("sources").insert(insert_data).execute()
+if insert_response.error:
+    logger.error(f"Database error creating source {domain_name}: {insert_response.error}")
+    return None
+
 if insert_response.data and len(insert_response.data) > 0:
     return insert_response.data[0]["id"]
 else:
-    print(f"Error creating new source {domain_name}: No data returned after insert. Error: {insert_response.error}")
+    logger.warning(f"Insert succeeded but no data returned for source {domain_name}")
     return None
 
@qodo-merge-proQodo Merge Pro
qodo-merge-pro bot commented 12 minutes ago • 
🔍 Finding similar code for 'get_or_create_source_uuid'
get_or_create_source_uuid (function) [+38/-0]


Component signature:

def get_or_create_source_uuid(client: Client, domain_name: str, table_name_for_source: str) -> Optional[str]:
🏷 Extracted Keywords	supabase , uuid , domain , sources , upsert                                                             
🌍 Search Context	
 Global
 Organization
🔍 Similar Code	Repository: JimtheCreator/claw-backend
License: unknown
Filename: crypto_repository.py
Repository: heyjoenash/brandtrackers-newsletter
License: unknown
Filename: database.py
Repository: CarlosCommits/SimpleDocs
License: unknown
Filename: storage.py
Repository: aemholland/e14z
License: MIT License
Filename: crawler.py
Repository: DiegoLigtenberg/spotify-v3
License: MIT License
Filename: app.py
📂 Relevant Repositories	
Repository: supabase-py

Description:
Official Python client for Supabase that provides database operations similar to the
client.table() pattern used in get_or_create_source_uuid
Repository: postgrest-py

Description:
Python client for PostgREST API that handles database queries and inserts, underlying
technology used by Supabase clients
Repository: supabase-realtime-py

Description:
Python client for Supabase realtime features, part of the Supabase ecosystem for
database operations and UUID management
@qodo-merge-proQodo Merge Pro
qodo-merge-pro bot commented 12 minutes ago • 
Generated code suggestions for 'create_embeddings_batch'
create_embeddings_batch (function) [+61/-36]

Component signature:

def create_embeddings_batch(texts: List[str]) -> List[List[float]]:

Suggestions and improvements for code changes in create_embeddings_batch function:

Category	Suggestions                                                                                                                                               
Maintainability	
Make the embedding dimension configurable instead of hardcoding it.
The hardcoded embedding dimension (1536) should be made configurable or dynamically
determined from the model. Different embedding models have different dimensions, and
hardcoding this value makes the code brittle when switching models.

src/utils.py

-# Assuming 1536 is the embedding dimension for "text-embedding-3-small"
-embedding_dim = 1536
+# Get embedding dimension from model or make it configurable
+embedding_dim = self._get_embedding_dimension("text-embedding-3-small")
+# Or use a constant/config: embedding_dim = EMBEDDING_DIMENSIONS.get("text-embedding-3-small", 1536)
 
Best practice	
Extract hardcoded model name to a constant to improve maintainability.
The model name "text-embedding-3-small" is hardcoded in multiple places. This should be
extracted to a constant or parameter to improve maintainability and make it easier to
switch models.

src/utils.py

+EMBEDDING_MODEL = "text-embedding-3-small"
 response = openai.embeddings.create(
-    model="text-embedding-3-small",
+    model=EMBEDDING_MODEL,
     input=texts_to_embed
 )
 
Possible issue	
Add validation to ensure embedding count matches expected valid text count.
The individual embedding fallback logic has a potential index mismatch issue. If some
individual embeddings fail and zero vectors are added, the final mapping to original
indices could be incorrect since the loop assumes all embeddings in
embeddings_for_valid_texts correspond to the same order as original_indices.

src/utils.py

+# Ensure we have exactly the right number of embeddings
+if len(embeddings_for_valid_texts) != len(original_indices):
+    print(f"Warning: Mismatch between valid texts ({len(original_indices)}) and embeddings ({len(embeddings_for_valid_texts)})")
 for i, original_idx in enumerate(original_indices):
     if i < len(embeddings_for_valid_texts):
         final_embeddings[original_idx] = embeddings_for_valid_texts[i]
 
Enhancement	
Add text length validation and truncation to prevent API token limit errors.
The text validation logic only checks for empty strings and whitespace, but doesn't handle
very long texts that might exceed the model's token limit. This could cause API errors
that aren't properly handled.

src/utils.py

-if text_content and text_content.strip(): # Check for non-empty and non-whitespace-only
+if text_content and text_content.strip():
+    # Truncate if text is too long (approximate token limit check)
+    if len(text_content) > 8000:  # Conservative estimate for token limit
+        text_content = text_content[:8000] + "..."
     valid_texts_with_indices.append((i, text_content))
 
@qodo-merge-proQodo Merge Pro
qodo-merge-pro bot commented 12 minutes ago • 
🔍 Finding similar code for 'create_embeddings_batch'
create_embeddings_batch (function) [+61/-36]


Component signature:

def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
🏷 Extracted Keywords	embeddings , vectorization , openai , batch , retry                                             
🌍 Search Context	
 Global
 Organization
🔍 Similar Code	Repository: DimaJoyti/DataMCPServerAgent
License: MIT License
Filename: base_embedder.py
Repository: cybas/mtr-normalization-system-2
License: unknown
Filename: embeddings.py
Repository: aditya3w3733/ifyouareblank
License: unknown
Filename: new_embeddings.py
Repository: Diep-Xuan-Son/MMV
License: unknown
Filename: openai.py
Repository: pije76/nevolvi
License: unknown
Filename: vectorization.py
📂 Relevant Repositories	
Repository: langchain

Description:
Framework for developing applications with language models, includes comprehensive
embedding utilities and batch processing for various embedding providers including
OpenAI
Repository: sentence-transformers

Description:
Python framework for state-of-the-art sentence, text and image embeddings with batch
processing capabilities and fallback mechanisms
Repository: openai-python

Description:
Official OpenAI Python library with embedding creation methods, batch processing, and
retry logic for API calls
Repository: txtai

Description:
All-in-one embeddings database for semantic search, LLM orchestration and language
model workflows with batch embedding creation
@qodo-merge-proQodo Merge Pro
qodo-merge-pro bot commented 12 minutes ago • 
Generated code suggestions for 'generate_contextual_embedding'
generate_contextual_embedding (function) [+2/-3]

Component signature:

def generate_contextual_embedding(full_document: str, chunk: str) -> Tuple[str, bool]:

Suggestions and improvements for code changes in generate_contextual_embedding function:

Category	Suggestions                                                                                                                                               
Best practice	
Add explicit temperature parameter for consistent contextual embedding generation.
The removal of the temperature parameter may lead to less consistent and potentially more
creative responses from the OpenAI API. For contextual embedding tasks that require
deterministic and focused outputs, explicitly setting a low temperature (like 0.1-0.3) is
recommended to ensure consistent results across multiple calls.

src/utils.py

 response = openai.chat.completions.create(
     model="gpt-3.5-turbo",
     messages=[
         {"role": "system", "content": "You are a helpful assistant that provides concise contextual information."},
         {"role": "user", "content": prompt}
     ],
+    temperature=0.1,
     max_completion_tokens=200
 )
 
Enhancement	
Add fallback handling for OpenAI API parameter compatibility across different client versions.
The parameter name change from max_tokens to max_completion_tokens is correct for newer
OpenAI API versions, but consider adding error handling for potential API compatibility
issues. Some older OpenAI client versions might not recognize this parameter, which could
cause runtime errors.

src/utils.py

-response = openai.chat.completions.create(
-    model="gpt-3.5-turbo",
-    messages=[
-        {"role": "system", "content": "You are a helpful assistant that provides concise contextual information."},
-        {"role": "user", "content": prompt}
-    ],
-    max_completion_tokens=200
-)
+try:
+    response = openai.chat.completions.create(
+        model="gpt-3.5-turbo",
+        messages=[
+            {"role": "system", "content": "You are a helpful assistant that provides concise contextual information."},
+            {"role": "user", "content": prompt}
+        ],
+        max_completion_tokens=200
+    )
+except TypeError as e:
+    # Fallback for older OpenAI client versions
+    response = openai.chat.completions.create(
+        model="gpt-3.5-turbo",
+        messages=[
+            {"role": "system", "content": "You are a helpful assistant that provides concise contextual information."},
+            {"role": "user", "content": prompt}
+        ],
+        max_tokens=200
+    )
 
Add timeout and retry logic to improve API call reliability and handle transient failures.
The OpenAI API call lacks timeout and retry mechanisms, which could cause the function to
hang indefinitely or fail on temporary network issues. Adding timeout and retry logic
would improve reliability, especially when processing multiple chunks concurrently.

src/utils.py

-response = openai.chat.completions.create(
-    model="gpt-3.5-turbo",
-    messages=[
-        {"role": "system", "content": "You are a helpful assistant that provides concise contextual information."},
-        {"role": "user", "content": prompt}
-    ],
-    max_completion_tokens=200
-)
+import time
+from openai import OpenAI
 
+max_retries = 3
+for attempt in range(max_retries):
+    try:
+        response = openai.chat.completions.create(
+            model="gpt-3.5-turbo",
+            messages=[
+                {"role": "system", "content": "You are a helpful assistant that provides concise contextual information."},
+                {"role": "user", "content": prompt}
+            ],
+            max_completion_tokens=200,
+            timeout=30
+        )
+        break
+    except Exception as e:
+        if attempt == max_retries - 1:
+            raise
+        time.sleep(2 ** attempt)
+
Performance	
Implement dynamic token allocation based on content complexity for more efficient API usage.
Consider adding validation to ensure the max_completion_tokens value is appropriate for
the task. A fixed value of 200 tokens might be insufficient for complex contextual
embeddings or too much for simple ones. Dynamic token allocation based on chunk size or
document complexity would be more efficient.

src/utils.py

+# Calculate appropriate token limit based on chunk size
+chunk_length = len(chunk.split())
+max_tokens = min(max(100, chunk_length // 2), 300)
+
 response = openai.chat.completions.create(
     model="gpt-3.5-turbo",
     messages=[
         {"role": "system", "content": "You are a helpful assistant that provides concise contextual information."},
         {"role": "user", "content": prompt}
     ],
-    max_completion_tokens=200
+    max_completion_tokens=max_tokens
 )
 
@qodo-merge-proQodo Merge Pro
qodo-merge-pro bot commented 12 minutes ago • 
🔍 Finding similar code for 'generate_contextual_embedding'
generate_contextual_embedding (function) [+2/-3]


Component signature:

def generate_contextual_embedding(full_document: str, chunk: str) -> Tuple[str, bool]:
🏷 Extracted Keywords	contextual , embedding , retrieval , chunking , situate                                     
🌍 Search Context	
 Global
 Organization
🔍 Similar Code	Repository: Steven-Luo/MasteringRAG
License: MIT License
Filename: explanatory_contextual_retrieval.py
Repository: handrew/wordcel
License: MIT License
Filename: contextual_retrieval.py
Repository: mindsdb/mindsdb
License: non-standard
Filename: document_preprocessor.py
Repository: agdev/RAG
License: Apache License 2.0
Filename: contextual_retrieval.py
Repository: Abiorh001/Contextual_rag
License: unknown
Filename: contextual_rag.py
📂 Relevant Repositories	
Repository: langchain

Description:
Framework for developing applications with language models, includes contextual
retrieval and document chunking capabilities similar to the
generate_contextual_embedding function.
Repository: llama-index

Description:
Data framework for LLM applications with advanced retrieval techniques including
contextual embeddings and document processing for improved search accuracy.
Repository: semantic-kernel

Description:
Microsoft's SDK for integrating AI services with contextual understanding and
embedding generation for enhanced document retrieval systems.
Repository: haystack

Description:
End-to-end NLP framework featuring document processing, contextual embeddings, and
retrieval-augmented generation similar to the contextual embedding approach.
Repository: txtai

Description:
All-in-one embeddings database with contextual search capabilities and document
chunking strategies that enhance retrieval performance like the
generate_contextual_embedding function.
@qodo-merge-proQodo Merge Pro
qodo-merge-pro bot commented 12 minutes ago • 
Generated code suggestions for 'add_documents_to_supabase'
add_documents_to_supabase (function) [+31/-5]

Component signature:

def add_documents_to_supabase(client: Client, urls: List[str], chunk_numbers: List[int], contents: List[str], metadatas: List[Dict[str, Any]], url_to_full_document: Dict[str, str], batch_size: int = 20) -> None:

Suggestions and improvements for code changes in add_documents_to_supabase function:

Category	Suggestions                                                                                                                                               
Best practice	
Extract domain name parsing logic into a dedicated function with better error handling and validation.
The domain name extraction logic should be more robust to handle edge cases like empty
netloc and path, malformed URLs, and provide consistent fallback behavior. Consider using
a dedicated function to extract domain names with proper validation.

src/utils.py

-parsed_url_for_source = urlparse(url_in_batch)
-domain_name_for_source = parsed_url_for_source.netloc or parsed_url_for_source.path
+def extract_domain_name(url: str) -> Optional[str]:
+    try:
+        parsed = urlparse(url)
+        domain = parsed.netloc
+        if not domain and parsed.path:
+            # Handle file:// or other schemes
+            domain = parsed.path.split('/')[0] if '/' in parsed.path else parsed.path
+        return domain.lower() if domain else None
+    except Exception:
+        return None
+
+domain_name_for_source = extract_domain_name(url_in_batch)
 if not domain_name_for_source:
     print(f"Warning: Could not determine domain for URL {url_in_batch}. Skipping source UUID fetch.")
     batch_source_uuids.append(None)
     continue
 
Enhancement	
Improve table name sanitization to handle all special characters and ensure valid database table names.
The table name generation logic uses simple string replacement which may not handle all
special characters properly and could create invalid table names. Consider using a more
robust sanitization approach or a predefined mapping strategy.

src/utils.py

-table_name_for_this_source = f"crawled_pages_{domain_name_for_source.replace('.', '_').replace('-', '_')}"
+def sanitize_table_name(domain: str) -> str:
+    # Remove or replace invalid characters for table names
+    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', domain)
+    # Ensure it starts with a letter or underscore
+    if sanitized and sanitized[0].isdigit():
+        sanitized = f"_{sanitized}"
+    return f"crawled_pages_{sanitized}"
 
+table_name_for_this_source = sanitize_table_name(domain_name_for_source)
+
Performance	
Handle missing source UUIDs more efficiently by avoiding unnecessary processing or providing fallback options.
The code continues processing when source UUID is None but then skips the record later,
which is inefficient. Consider filtering out invalid URLs earlier or handling the None
case more gracefully to avoid unnecessary processing.

src/utils.py

 if not current_source_uuid:
-    print(f"Warning: Missing source UUID for URL {batch_urls[j]}. Skipping this record for crawled_pages.")
+    print(f"Warning: Missing source UUID for URL {batch_urls[j]}. Using default source or skipping batch processing.")
+    # Option 1: Use a default/fallback source UUID
+    # current_source_uuid = get_default_source_uuid(client)
+    # Option 2: Skip this record but track skipped count
+    skipped_records += 1
     continue
 
Possible issue	
Maintain proper index alignment between batch arrays when some records are skipped due to missing source UUIDs.
The batch processing logic doesn't account for skipped records when None source UUIDs are
encountered, which can cause index misalignment between batch_source_uuids and other batch
arrays. Consider using a different approach to maintain array synchronization.

src/utils.py

 batch_source_uuids = []
-for url_in_batch in batch_urls:
+valid_batch_indices = []
+for idx, url_in_batch in enumerate(batch_urls):
     # ... processing logic ...
     if not domain_name_for_source:
         batch_source_uuids.append(None)
-        continue
-    source_uuid = get_or_create_source_uuid(client, domain_name_for_source, table_name_for_this_source)
-    batch_source_uuids.append(source_uuid)
+    else:
+        source_uuid = get_or_create_source_uuid(client, domain_name_for_source, table_name_for_this_source)
+        batch_source_uuids.append(source_uuid)
    
    # Track which indices have valid source UUIDs for later processing
    if batch_source_uuids[-1] is not None:
        valid_batch_indices.append(idx)
 
