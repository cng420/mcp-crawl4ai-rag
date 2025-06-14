Okay, I've reviewed the `logs.txt` file. It appears there are two main issues:

1.  **Supabase Insertions Failing:** The primary problem is that data insertion into the `crawled_pages` table is failing. The logs show multiple instances of the error:
    `{'message': 'invalid input syntax for type uuid: "facebook.github.io"', 'code': '22P02', 'hint': None, 'details': None}`
    This indicates that the `source_id` column in your `crawled_pages` table is expecting a UUID, but it's receiving the string "facebook.github.io" (the domain name) instead.

2.  **OpenAI API Errors:** There are also errors when calling the OpenAI API:
    `{'message': "Unsupported value: 'temperature' does not support 0.3 with this model. Only the default (1) value is supported.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value'}`
    This means the `temperature` parameter for an OpenAI API call (likely for generating summaries or contextual embeddings) is set to `0.3`, but the specific model being used only supports the default value of `1`.

**Investigating the Supabase Issue:**

The `source_id` error suggests that the application logic for storing crawled pages is not correctly looking up or creating a UUID-based `source_id` in a `sources` table before attempting to insert into `crawled_pages`. Instead, it's directly using the domain name.

To confirm this and understand the table structures, I'll try to find and read the schema files you have in your project: `supabase_schema.json` and `supbase_table_schema.json` (assuming the latter might be `supabase_table_schema.json`).

I'll start by searching for these files.

Ran tool
Ran tool
Okay, I've found both schema files:
*   `supabase_schema.json`
*   `supbase_table_schema.json`

I'll now read their contents to understand the table structures, which will help diagnose the UUID issue.

Read file: supabase_schema.json
Read file: supbase_table_schema.json
Okay, I've read the initial parts of `supabase_schema.json` and `supbase_table_schema.json`.

From `supabase_schema.json`, I can see there's a table named `public.crawled_pages`. I'll need to find its detailed column definitions in `supbase_table_schema.json`. I also expect to find a `public.sources` table.

The initial 250 lines of `supbase_table_schema.json` mostly contained definitions for the `auth` schema. I need to look further down to find the `public` schema tables.

I will continue reading `supbase_table_schema.json` to find the definitions for `public.crawled_pages` and `public.sources`.

Read file: supbase_table_schema.json
Still reading through `supbase_table_schema.json`. The previous chunk was still in the `auth` schema. I'll jump much further to find the `public` schema definitions.

Read file: supbase_table_schema.json
Still reading through `supbase_table_schema.json`. I need to get to the `public` schema definitions. I'll make a larger jump in the file.

Read file: supbase_table_schema.json
Okay, I'm still working my way through `supbase_table_schema.json` to find the definitions for the `public` schema, specifically for `crawled_pages` and a likely `sources` table. The previous chunks were still in the `extensions` schema. I'll jump much further down the file.

Read file: supbase_table_schema.json
Okay, I've finally found the relevant schema definitions in `supbase_table_schema.json` after a few reads.

Here's the crucial part for `public.crawled_pages`:
```json
  {
    "table_schema": "public",
    "table_name": "crawled_pages",
    "column_name": "source_id",
    "data_type": "uuid",
    "is_nullable": "YES",
    "column_default": null
  }
```
This confirms that the `source_id` column in the `crawled_pages` table is indeed of type `uuid`. The error message `invalid input syntax for type uuid: "facebook.github.io"` clearly indicates that the application is trying to insert the string "facebook.github.io" (a domain name) into this `uuid` column.

Now, I need to find the schema definition for the `sources` table (assuming it's named `sources` or something similar) to see how it's structured and how it relates to `crawled_pages`. I'll continue reading `supbase_table_schema.json` to locate it.

Read file: supbase_table_schema.json
I'm still searching for the `public.sources` table definition in `supbase_table_schema.json`. The previous chunks showed definitions for various `crawled_pages_` tables but not the `sources` table itself. I'll continue reading from where I left off.

Read file: supbase_table_schema.json
I'm still looking for the `public.sources` table definition in `supbase_table_schema.json`. The last chunk showed various other tables in the `public` schema. I'll read the next part of the file.

Read file: supbase_table_schema.json
I'm still searching for the `public.sources` table definition in `supbase_table_schema.json`. I'll read the next chunk.

Read file: supbase_table_schema.json
Okay, I'm still on the hunt for the `public.sources` table definition within `supbase_table_schema.json`. The previous chunks showed many other tables. I'll continue reading from where I left off (around line 3749).
Read file: supbase_table_schema.json
Okay, I'm still working through `supbase_table_schema.json` to find the `public.sources` table definition. I will read the next chunk of the file, getting closer to the end.

Read file: supbase_table_schema.json
Okay, I'm still searching for the `public.sources` table definition in `supbase_table_schema.json`. I will read the next chunk of the file, which should take me closer to the end.

Read file: supbase_table_schema.json
Okay, I'm still working through `supbase_table_schema.json` to find the `public.sources` table definition. I'll read the final chunk of the file.

Read file: supbase_table_schema.json
The logs you've provided highlight two main issues that are causing problems with your data processing and storage: an error with OpenAI API calls and, more critically, errors with how data is being inserted and updated in your Supabase database.

Here's a breakdown of the issues and the recommended solutions:

**Issue 1: OpenAI API Call Error (Temperature Parameter)**

*   **Error Log Snippet:**
    ```
    Error generating summary with LLM for facebook.github.io: Error code: 400 - {'error': {'message': "Unsupported value: 'temperature' does not support 0.3 with this model. Only the default (1) value is supported.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value'}}
    ```
*   **Cause:** Your application is making a call to an OpenAI API (likely for generating text summaries or embeddings) and is setting the `temperature` parameter to `0.3`. The specific OpenAI model being used in this context does not support this value and only accepts the default value, which is typically `1.0`.
*   **Solution:**
    1.  Identify the section in your application's codebase where this OpenAI API call is made.
    2.  Modify the call to either:
        *   Change the `temperature` parameter to `1.0`.
        *   Remove the `temperature` parameter entirely if `1.0` is an acceptable default for your use case.

**Issue 2: Supabase Database Errors (UUID Mismatch and Incorrect Update Query)**

This is the more severe issue as it's preventing crawled data from being correctly stored.

*   **Error Log Snippet (Insertion into `crawled_pages`):**
    ```
    Failed to insert batch after 3 attempts: {'message': 'invalid input syntax for type uuid: "facebook.github.io"', 'code': '22P02', 'hint': None, 'details': None}
    ```
*   **Error Log Snippet (Updating `sources`):**
    ```
    Error updating source facebook.github.io: {'message': 'invalid input syntax for type integer: "facebook.github.io"', 'code': '22P02', 'hint': None, 'details': None}
    ```
    This corresponds to a `PATCH` request in the logs like: `PATCH .../rest/v1/sources?source_id=eq.facebook.github.io`

*   **Cause Analysis (Based on Schema and Logs):**
    1.  **`crawled_pages.source_id` Type Mismatch:**
        *   Your `public.crawled_pages` table has a column `source_id`. My investigation of your `supbase_table_schema.json` confirmed this column is of type `uuid`.
        *   This `source_id` is meant to be a foreign key referencing the `id` column in your `public.sources` table.
        *   The `public.sources` table has an `id` column which is of type `uuid` and set to auto-generate using `uuid_generate_v4()`. This is its primary key.
        *   The error `invalid input syntax for type uuid: "facebook.github.io"` occurs because your application is attempting to insert the *textual domain name* (e.g., "facebook.github.io") directly into the `crawled_pages.source_id` column, which expects a UUID.
    2.  **Incorrect `sources` Table Update Query:**
        *   The `public.sources` table has two ID-like columns:
            *   `source_id`: An `integer` column, likely an older auto-incrementing key (`nextval('sources_id_seq'::regclass)`).
            *   `id`: A `uuid` column, the primary key (`uuid_generate_v4()`).
            *   It also has a `source` column of type `text` to store the domain name.
        *   The `PATCH` request `.../sources?source_id=eq.facebook.github.io` is trying to find a record in `sources` by matching the `integer` column `source_id` with the *string* "facebook.github.io". This causes the "invalid input syntax for type integer" error.

*   **Solution for Supabase Database Errors:**
    Your application's logic for handling website sources and storing crawled page data needs to be revised as follows:

    1.  **Revised Logic for Obtaining/Creating a Source Record and its UUID:**
        *   When your crawler processes a URL (e.g., `http://facebook.github.io/prophet/docs/`):
            a.  **Extract the base domain name** (e.g., "facebook.github.io").
            b.  **Check if this domain already exists in the `public.sources` table:**
                *   Query: `SELECT id FROM public.sources WHERE source = 'your_domain_name_here';`
            c.  **If the domain exists in `public.sources`:**
                *   Retrieve its `id` (this will be the UUID).
            d.  **If the domain does NOT exist in `public.sources`:**
                *   Insert a new record: `INSERT INTO public.sources (source) VALUES ('your_domain_name_here') RETURNING id;`
                *   The `id` column (UUID) will be automatically generated by the database. Use this returned `id`.
            e.  Let's call the UUID obtained from step (c) or (d) the `correct_source_uuid`.

    2.  **Correctly Inserting into `crawled_pages`:**
        *   When inserting a record into `public.crawled_pages`, use the `correct_source_uuid` (obtained above) as the value for the `crawled_pages.source_id` column.

    3.  **Correcting the `PATCH` (Update) Operation on `public.sources`:**
        *   The erroneous PATCH request was: `.../sources?source_id=eq.facebook.github.io`.
        *   If the goal is to update a source record based on its domain name, the query parameter should target the `source` column (which stores the text domain):
            `PATCH .../rest/v1/sources?source=eq.facebook.github.io` (and include the fields to update in the request body).
        *   Alternatively, and often more reliably if the UUID is known, update using the UUID primary key:
            `PATCH .../rest/v1/sources?id=eq.<the-actual-uuid-of-the-source>`

**Implementation Steps:**

1.  **Review Your Application Code:** You'll need to locate the parts of your application (e.g., Python scripts, server-side functions) that are responsible for:
    *   Making calls to the OpenAI API.
    *   Interacting with the `public.sources` table (fetching, inserting, updating).
    *   Inserting data into the `public.crawled_pages` table.
2.  **Apply the Logical Changes:** Modify your code to implement the solutions described above. This involves:
    *   Adjusting the OpenAI `temperature` parameter.
    *   Implementing the "get or create" logic for the `public.sources` table to ensure you're always working with the correct UUID (`sources.id`).
    *   Ensuring this UUID is used for the `source_id` foreign key in `public.crawled_pages`.
    *   Correcting the query parameters used in `PATCH` requests to the `public.sources` table.

By addressing these points, your application should correctly associate crawled pages with their sources using the proper UUID linkage and resolve the OpenAI API errors.