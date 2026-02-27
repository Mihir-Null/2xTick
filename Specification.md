# ELMS to TickTick Sync Specification

## 1. Goal
Automatically synchronize academic assignments from the University of Maryland's ELMS-Canvas (Canvas LMS) into TickTick tasks. This reduces manual data entry and ensures all academic deadlines are centrally tracked in the user's preferred task manager.

## 2. Scope
- **Retrieve Assignments:** Connect to the Canvas API to pull assignments for currently active courses.
- **Filter and Parse:** 
  - Ignore assignments that are already in TickTick.
  - Ignore past assignments, but ensure overdue assignments are still added.
  - Filter out non-graded or optional assignments (if desired).
  - Parse due dates, course names, assignment URLs, and attachments.
- **Create TickTick Tasks:** Push the parsed assignments to TickTick with the following mappings:
  - **List:** Sent to a specific "Coursework" list, nested under a sublist corresponding to the course.
  - **Title:** `{Assignment Title} - {Course Name}`.
  - **Description:** Assignment description, including a link back to the original Canvas assignment.
  - **Due Date:** Matches the assignment due date (with support for due date offsets).
  - **Priority:** 
    - High: Exams or Quizzes.
    - Low: Optional assignments.
    - Medium: Standard assignments.
  - **Tags:** Tagged with "Homework" or "Exam" based on assignment type.
- **Deduplication:** Ensure that running the script multiple times does not create duplicate tasks in TickTick.

## 3. User Flow
1. **Setup:** The user provides a Canvas API token, Canvas Base URL, and TickTick credentials.
2. **Configuration:** The user edits a configuration file to map courses to TickTick lists, define keywords for tags and priorities, and set due date offsets.
3. **Execution:** The user runs the script (manually or via a scheduled cron job).
4. **Synchronization:** The script checks TickTick for existing assignments to prevent duplicates, fetches new assignments from Canvas, applies configuration mappings, and adds them to TickTick.
5. **Completion:** The script logs the number of tasks added and exits.

## 4. Key Requirements
- Securely handle API tokens and credentials.
- Accurately map Canvas `due_at` datetimes to TickTick deadlines.
- Accurately categorize tasks (lists, tags, priorities) based on user configuration.
- Include a configuration file (e.g., `config.yaml` or `config.json`) to edit mappings of course pages to TickTick lists, which course pages to monitor, keywords to tags/priorities, offsets to due dates, and other useful configuration options. This config file should be automatically generated on first run.
- Include a link back to the Canvas assignment within the TickTick task description.
- Run unattended (e.g., via cron or systemd timer) after initial login/setup.

## 5. Optional Features
- Attach or link to files that are present in the Canvas assignment in the TickTick task.
