# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - YYYY-MM-DD

### Added

*   **Documentation (`docs/`)**:
    *   Centralized project documentation into the `docs` directory.
    *   Moved existing `.env.example` and `crawled_pages.sql` to `docs/`.
    *   Added SQL files for crawled page data (`docs/crawled_pages_data.sql`), site page data (`docs/site_pages_data.sql`), and source data including Google-related sources (`docs/sources_google_data.sql`, `docs/sources_data.sql`).
    *   Added JSON files detailing Supabase schema information (`docs/supabase_schema_crawled_pages.json`, `docs/supabase_schema_code_examples.json`, `docs/supabase_schema_sources.json`).
    *   Added Markdown files for tracking fixes/bugs/updates (`docs/fixes_bugs_updates.md`), logs (`docs/logs.md`), and a quality audit of Google crawled data (`docs/quality_audit_of_google_crawled.md`).
*   **Source UUID Management (`src/utils.py`)**:
    *   Introduced `get_or_create_source_uuid` function to fetch an existing source UUID by domain name or create a new source entry if it doesn't exist, returning the UUID. This replaces previous string-based domain identification with true UUIDs for `source_id`.

### Changed

*   **Embedding Generation (`src/utils.py`)**:
    *   Refactored `create_embeddings_batch`:
        *   Filters empty or whitespace-only input texts, returning zero vectors for them.
        *   Initializes zero vectors for all inputs and maps valid text embeddings back to their original positions, preserving order.
        *   Implements a robust retry mechanism with exponential backoff for batch OpenAI API calls.
        *   Includes a fallback to individual API calls for texts if batch processing fails persistently.
    *   Updated `generate_contextual_embedding`, `generate_code_example_summary`, and `extract_source_summary` to use `max_completion_tokens` instead of the deprecated `max_tokens` and `temperature` arguments in OpenAI API calls.
*   **Supabase Data Ingestion (`src/utils.py`)**:
    *   Modified `add_documents_to_supabase`:
        *   Integrated `get_or_create_source_uuid` to fetch and use actual `source_id` (UUID) for crawled pages before insertion.
        *   Skips records if a source UUID cannot be determined for a URL, with a warning.
        *   Generates a default `table_name` for the source based on the domain if not explicitly provided during UUID fetching.
    *   Revised `update_source_info`:
        *   Function signature now accepts `domain_name` and an optional `table_name_for_source`.
        *   Performs an upsert operation on the `sources` table using `domain_name` (the `source` column) as the conflict target.
        *   If `table_name_for_source` is not provided, a default table name is generated based on the `domain_name`.
    *   Modified `add_code_examples_to_supabase`:
        *   Extracts `source_domain_for_code` from URL `netloc` (with fallback to URL path if `netloc` is empty) and uses it as `source_id`.
*   **General (`src/utils.py`)**:
    *   Various functions updated to use `max_completion_tokens` instead of `max_tokens` for OpenAI API calls. 