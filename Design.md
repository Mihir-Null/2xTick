# Class and Function Design Document

## 1. `CanvasClient`
**File:** `clients/canvas_client.py`
**Purpose:** Handle all communication with the Canvas LMS API.

### `__init__(self, api_url: str, api_token: str)`
- Initializes the `canvasapi.Canvas` object.

### `get_active_courses(self) -> List[Course]`
- Retrieves a list of active courses the user is currently enrolled in.

### `get_assignments(self, course_id: int) -> List[Assignment]`
- Retrieves assignments for a given course.
- Includes logic to fetch Canvas attachables or links if available.
- Optionally filters out assignments that are submitted or don't meet criteria.

---

## 2. `TickTickClient`
**File:** `clients/ticktick_client.py`
**Purpose:** Handle all communication with the TickTick API.

### `__init__(self, username, password, client_id, client_secret)`
- Initializes the `ticktick.api.TickTickClient` object.
- Handles OAuth/login flows.

### `get_all_tasks(self) -> List[dict]`
- Retrieves existing tasks from TickTick to use for deduplication. 

### `get_lists(self) -> dict`
- Retrieves TickTick lists and folders to ensure tasks can be correctly filed under "Coursework" and course sublists.

### `create_task(self, title: str, description: str, due_date: datetime, list_id: str = None, tags: List[str] = None, priority: int = 0) -> dict`
- Submits a new task to TickTick.
- Handles time zone conversions and associates the task with the correct list and priority level.

---

## 3. `ConfigManager`
**File:** `config_manager.py`
**Purpose:** Handle user configurations and mappings.

### `__init__(self, config_path: str = 'config.yaml')`
- Loads the YAML configuration file.
- If the file does not exist, automatically generates a default template.

### `get_priority(self, assignment_title: str) -> int`
- Determines task priority from keywords (e.g., Exam/Quiz -> High (5), Optional -> Low (1), Default -> Medium (3)).

### `get_tags(self, assignment_title: str) -> List[str]`
- Determines task tags (e.g., Homework, Exam).

### `get_list_mapping(self, course_name: str) -> str`
- Maps a Canvas course name to the corresponding TickTick list/sublist name.

### `get_date_offset(self) -> timedelta`
- Gets the user-configured due date offset.

---

## 4. `SyncManager`
**File:** `sync_manager.py`
**Purpose:** Orchestrate the synchronization logic.

### `__init__(self, canvas_client: CanvasClient, ticktick_client: TickTickClient, config_manager: ConfigManager)`
- Injects dependencies for API clients and the configuration manager.

### `run_sync(self)`
1. Retrieve active courses via `canvas_client.get_active_courses()`.
2. Retrieve existing TickTick tasks via `ticktick_client.get_all_tasks()`.
3. Build a set of existing task identifiers.
4. For each course, fetch assignments via `canvas_client.get_assignments()`.
5. For each assignment:
   - Check if the assignment is already in TickTick.
   - Filter out past assignments (unless overdue/unsubmitted).
   - Resolve proper list/sublist using `ticktick_client.get_lists()` and `config_manager`.
   - Resolve priority and tags using `config_manager`.
   - Format Title to `{Assignment Title} - {Course Name}`.
   - Format Description with assignment details, attachments, and Canvas URL.
   - Apply any due date offset from `config_manager`.
   - Call `ticktick_client.create_task()` with assembled parameters.
6. Log a summary of successful and failed syncs.

---

## 5. `main.py`
**Purpose:** Entry point for setting up environmental variables and executing the sync.

### `main()`
- Loads `.env`.
- Instantiates `CanvasClient`, `TickTickClient`, and `ConfigManager`.
- Instantiates `SyncManager` and calls `run_sync()`.
