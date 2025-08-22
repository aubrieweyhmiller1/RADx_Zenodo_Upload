# Automated Zenodo File Submission Workflow

This repository provides a set of scripts to streamline and automate the process of preparing and publishing files for submission to Zenodo. Built using the Zenodo REST API documentation (https://developers.zenodo.org/#rest-api).

## Overview

The workflow consists of four main steps:

1. **Prepare your input CSV**  
   - Start with a CSV containing required submission information including the file name, resource title, description, resource type, creator, and keywords. Ensure all required fields are filled in and follow proper deposition formatting as defined in https://developers.zenodo.org/#representation.

2. **Clean the CSV**  
   - Run `clean_csv.py` to remove unwanted newlines that may exist in the CSV fields.
   - Output will be a cleaned version of the CSV, ready for scripts.

3. **Test Draft Uploads**  
   - Run `create_draft_submission.py` to create draft uploads in the Zenodo sandbox (test environment).
   - This ensures that files upload correctly before moving to production. User will have to manually edit files and/or input csv to correct failed files.

4. **Publish Files**  
   - Once drafts are confirmed and csv is cleaned to ensure all items will upload, run `publish_files.py`.
   - This will upload files to the production environment and publish them.

## Script Details
NOTE: For all scripts, will have to manually edit input and output filenames and paths in the scripts.

### `scrape_links.py` (Optional)
- **Purpose**: (Optional) Scrapes links or file metadata from staging locations. Used to automate get filenames from links since filenames were not originally provided.
- **Usage**:
  ```bash
  python scrape_links.py 
  ```

### `clean_csv.py`
- **Purpose**: Removes unwanted newlines from fields in the CSV.  
- **Input**: A finalized CSV with required fields.  
- **Output**: A cleaned CSV with the same structure.  
- **Usage**:
  ```bash
  python clean_csv.py
  ```

### `create_draft_submission.py`
- **Purpose**: Tests uploading cleaned CSV data into the sandbox environment.  
- **Input**: A finalized, cleaned CSV from Step 2.  
- **Output**: failed_DRAFT_files.csv, a csv with the Title, deposition_id, and error message for failed draft submissions. successful_DRAFT_files.csv, a csv with the Title and deposition_id for successful draft submissions. 
- **Notes**: This step requires making a Zenodo account, navigating to https://sandbox.zenodo.org/, and creating an access token. The access token should be stored in a .env file. See .env_example.
- **Usage**:
  ```bash
  python create_draft_submission.py 
  ```

### `publish_files.py`
- **Purpose**: Publishes them to the Zenodo production system with the option to add to a community via the communities tag.
- **Input**: A finalized, cleaned CSV from Step 3.  
- **Output**: failed_DRAFT_files.csv, a csv with the Title, deposition_id, and error message for failed draft submissions. successful_DRAFT_files.csv, a csv with the Title and deposition_id for successful draft submissions.
- **Notes**: This step requires getting an access token for the production environment. The access token should be stored in a .env file. See .env_example.
- **Usage**:
  ```bash
  python publish_files.py 
  ```
