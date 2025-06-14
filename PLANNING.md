# Project Planning

This document outlines the strategic planning, future development directions, and areas of focus for the Crawl4AI RAG MCP Server project.

## Phase 1: Foundational Refactoring and Documentation (Completed via PR #1)

*   **Goal:** Establish a well-organized documentation structure and refactor core utility functions for robustness and future scalability.
*   **Key Activities:**
    *   Centralize all project documentation (SQL schemas, examples, tracking files) into a `/docs` directory.
    *   Implement true UUID-based source tracking (`get_or_create_source_uuid`).
    *   Enhance batch embedding generation (`create_embeddings_batch`) with improved error handling, retry logic, and preservation of input order.
    *   Update OpenAI API calls to use current parameters (`max_completion_tokens`).
    *   Refactor Supabase data ingestion functions (`add_documents_to_supabase`, `update_source_info`, `add_code_examples_to_supabase`) for clarity, robustness, and use of source UUIDs.
*   **Outcomes:**
    *   Improved project organization and maintainability.
    *   More robust and reliable data processing and embedding workflows.
    *   Clearer and more comprehensive documentation.

## Phase 2: Addressing PR Feedback and Enhancements

*   **Goal:** Implement suggestions and fix issues identified during the review of PR #1 to further improve code quality, performance, and reliability.
*   **Key Focus Areas (Derived from Qodo Merge Pro feedback):**
    *   **Performance Optimization:**
        *   Optimize `get_or_create_source_uuid` to reduce redundant database calls (caching/pre-fetching).
        *   Evaluate and potentially implement dynamic token allocation in `generate_contextual_embedding`.
        *   Improve efficiency in `add_documents_to_supabase` for handling missing source UUIDs.
    *   **Robustness and Error Handling:**
        *   Strengthen error handling in database operations (e.g., `get_or_create_source_uuid` select query).
        *   Add more comprehensive input validation (e.g., `domain_name` format, text length for embeddings).
        *   Improve API call reliability in `generate_contextual_embedding` with timeouts and retries.
        *   Address potential index mismatches in `create_embeddings_batch` and `add_documents_to_supabase`.
    *   **Maintainability & Best Practices:**
        *   Replace `print` statements with a proper logging framework across `src/utils.py`.
        *   Extract hardcoded values (e.g., embedding model names, dimensions) into constants or configurations.
        *   Improve table name sanitization logic.
        *   Add explicit `temperature` settings for LLM calls where consistency is key.
    *   **Testing:**
        *   Develop comprehensive unit tests for all refactored and new utility functions, integrating auto-generated tests where appropriate.
*   **Expected Outcomes:**
    *   More performant and resilient utility functions.
    *   Increased code clarity and adherence to best practices.
    *   Higher test coverage ensuring stability.

## Phase 3: Advanced RAG Capabilities and Feature Expansion (Future)

*   **Goal:** Expand the RAG capabilities of the server and integrate more advanced techniques.
*   **Potential Features & Enhancements:**
    *   **Configurable Embedding Models:** Allow users to select different embedding models, including local options via Ollama.
    *   **Advanced RAG Strategies:** Explore and implement techniques like late chunking, sentence window retrieval, etc.
    *   **Improved Chunking:** Refine the chunking strategy, possibly inspired by Context 7, for better semantic segmentation.
    *   **UI/Dashboard:** A simple interface for managing sources, viewing crawl status, and testing RAG queries.
    *   **Integration with Archon:** Deepen the integration as a core knowledge engine.
    *   **Broader Toolset:** Consider adding more specialized tools based on user needs.

## Long-Term Vision

*   To create a highly configurable, performant, and intelligent MCP server that serves as a powerful knowledge backbone for AI agents and coding assistants, enabling them to leverage vast amounts of crawled information effectively and efficiently.
*   To contribute to the Archon project by providing a robust data ingestion and RAG component. 