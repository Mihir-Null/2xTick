# Implementation Plan

## Goal Description
Build a Python application that fetches assignments from Canvas (ELMS) and synchronizes them to TickTick, utilizing categorization, filtering, and user-defined configuration mapping for tags, lists, and priorities.

## Proposed Changes
We will develop the application in the `2xTick` directory.

### `2xTick`
We will create a new Python environment and project structure.

#### [NEW] `requirements.txt`
Dependencies:
- `canvasapi` (for Canvas integration)
- `ticktick-py` (for TickTick integration)
- `python-dotenv` (for loading environment variables securely)
- `pyyaml` (for configuration management)

#### [NEW] `.env.example`
Template for environment variables:
```env
CANVAS_API_URL=https://myelms.umd.edu
CANVAS_API_TOKEN=your_canvas_token_here
TICKTICK_CLIENT_ID=optional_oauth_id
TICKTICK_CLIENT_SECRET=optional_oauth_secret
TICKTICK_USERNAME=your_email
TICKTICK_PASSWORD=your_password
```

#### [NEW] `config.yaml`
A configuration file for user customization:
- Defining which course pages to monitor.
- Mapping Canvas course names/IDs to TickTick sublists under "Coursework".
- Defining keywords for priority assignment (e.g., "Exam", "Quiz" -> High).
- Defining keywords for tags (e.g., "Homework", "Exam").
- Setting due date offsets.
- **Auto-generated on first run** if it does not already exist with default mappings.

#### [NEW] `clients/canvas_client.py`
A wrapper around `canvasapi` to fetch active courses and assignments, including their attachments and descriptions.

#### [NEW] `clients/ticktick_client.py`
A wrapper around `ticktick-py` to authenticate, fetch existing tasks (for deduplication), fetch lists/folders, and create tasks under specific lists with designated tags and priorities.

#### [NEW] `config_manager.py`
A module to read `config.yaml` and provide helper functions to determine proper task priorities, tags, and mapping logic dynamically based on assignment metadata.

#### [NEW] `sync_manager.py`
The orchestration script that ties the clients together. 
- Retrieves assignments and filters out past ones (leaving overdue).
- Checks TickTick for duplicates.
- Maps fields (Title to `Assignment - Course`, Description to include descriptions and links) based on the configuration logic.
- Creates new tasks.

#### [NEW] `main.py`
The entry point of the application, handling configuration loading and executing the sync manager.

## Verification Plan

### Automated Tests
- Mock `requests` or API responses using `unittest.mock` to ensure `sync_manager.py` correctly maps Canvas assignment objects to TickTick tasks based on `config.yaml` and properly deduplicates them.
- Ensure priority, tagging, and formatting logic work as expected.
- `python -m unittest tests/test_sync.py`

### Manual Verification
1. User provides valid credentials in a `.env` file and defines preferences in `config.yaml`.
2. User runs `python main.py`.
3. User opens TickTick and verifies:
   - Tasks are located in the "Coursework" list under their respective course sublists.
   - Tasks have the correct `Title - Course Name` format, tags, descriptions containing links, and accurately set priorities.
4. User runs `python main.py` a second time to ensure no duplicate tasks are created.
