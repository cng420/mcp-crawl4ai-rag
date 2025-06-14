# Project Tasks

This document tracks ongoing and future tasks for the Crawl4AI RAG MCP Server project, derived from pull requests, reviews, and planning sessions.

## From PR #1: Refactor: Organize project documentation and add new data/schema files

### Code Implementation & Improvement Tasks

*   **`create_embeddings_batch` Function:**
    *   [ ] **Possible Issue:** Address potential failure in `final_embeddings` mapping logic if `embeddings_for_valid_texts` has fewer elements than expected. (Qodo Merge Pro)
    *   [ ] **Maintainability:** Make the embedding dimension (1536) configurable instead of hardcoding. (Qodo Merge Pro)
    *   [ ] **Best Practice:** Extract the hardcoded model name "text-embedding-3-small" to a constant. (Qodo Merge Pro)
    *   [ ] **Possible Issue:** Add validation to ensure embedding count matches the expected valid text count in the individual embedding fallback logic. (Qodo Merge Pro)
    *   [ ] **Enhancement:** Add text length validation and truncation to prevent API token limit errors (currently only checks for empty/whitespace). (Qodo Merge Pro)
*   **`add_documents_to_supabase` Function:**
    *   [ ] **Logic Error:** Handle cases where `current_source_uuid` is `None` more consistently to avoid potential index mismatches during batch processing. (Qodo Merge Pro)
    *   [ ] **Best Practice:** Extract domain name parsing logic into a dedicated function with better error handling and validation. (Qodo Merge Pro)
    *   [ ] **Enhancement:** Improve table name sanitization to handle all special characters and ensure valid database table names (current uses simple string replacement). (Qodo Merge Pro)
    *   [ ] **Performance:** Handle missing source UUIDs more efficiently by filtering invalid URLs earlier or providing fallback options. (Qodo Merge Pro)
    *   [ ] **Possible Issue:** Ensure proper index alignment between batch arrays when records are skipped due to missing source UUIDs. (Qodo Merge Pro)
*   **`get_or_create_source_uuid` Function:**
    *   [ ] **Performance Issue:** Optimize to avoid redundant database calls for the same domain within a batch (cache results or pre-fetch unique domains). (Qodo Merge Pro)
    *   [ ] **Best Practice:** Replace `print` statements with proper logging. (Qodo Merge Pro)
    *   [ ] **Enhancement:** Add input validation for `domain_name` (ensure not empty, normalize). (Qodo Merge Pro)
    *   [ ] **Bug:** Add error handling for the database select query to catch potential database errors (check `response.error`). (Qodo Merge Pro)
    *   [ ] **Maintainability:** Separate database error handling from empty response handling for better diagnosis in insert operations. (Qodo Merge Pro)
*   **`generate_contextual_embedding` Function:**
    *   [ ] **Best Practice:** Add an explicit `temperature` parameter (e.g., low value like 0.1-0.3) for consistent contextual embedding generation. (Qodo Merge Pro)
    *   [ ] **Enhancement:** Add fallback handling for OpenAI API parameter compatibility (`max_tokens` vs. `max_completion_tokens`) across different client versions. (Qodo Merge Pro)
    *   [ ] **Enhancement:** Add timeout and retry logic to the OpenAI API call to improve reliability. (Qodo Merge Pro)
    *   [ ] **Performance:** Consider dynamic token allocation for `max_completion_tokens` based on content complexity/chunk size instead of a fixed value. (Qodo Merge Pro)

### Testing Tasks

*   [ ] Write unit tests for all new and modified functions in `src/utils.py` if not already covered by the auto-generated tests.
    *   [ ] `get_or_create_source_uuid`
    *   [ ] `create_embeddings_batch`
    *   [ ] `generate_contextual_embedding`
    *   [ ] `add_documents_to_supabase`
    *   [ ] `generate_code_example_summary`
    *   [ ] `add_code_examples_to_supabase`
    *   [ ] `update_source_info`
    *   [ ] `extract_source_summary`
*   [ ] Review and integrate auto-generated tests from Qodo Merge Pro for the above functions, ensuring they cover happy paths, edge cases, and error conditions thoroughly.

### Documentation Tasks

*   [ ] Review and refine auto-generated docstrings from Qodo Merge Pro for all modified functions in `src/utils.py`. Ensure accuracy, completeness, and adherence to project documentation standards.
*   [ ] Update `README.md` to reflect the changes from PR #1 (documentation reorganization, utility function enhancements). *(Partially addressed by this current overarching task)*
*   [ ] Ensure `PLANNING.md`, `TASKS.md`, and `CHANGELOG.md` are updated based on PR #1. *(This current overarching task)*
*   [ ] Verify all `Project Rules` documentation is up-to-date and reflects current practices.

### Project & Process Tasks

*   [ ] Address "Outdated" file statuses reported by Qodo Merge Pro for `src/utils.py` and `docs/quality_audit_of_google_crawled.md`.
*   [ ] Investigate and integrate findings from "Similar Code" and "Relevant Repositories" sections provided by Qodo Merge Pro for potential improvements and best practices. 