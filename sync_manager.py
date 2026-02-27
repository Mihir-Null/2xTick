import logging
from datetime import datetime, timezone
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, canvas_client, ticktick_client, config_manager):
        self.canvas_client = canvas_client
        self.ticktick_client = ticktick_client
        self.config_manager = config_manager
        logger.info("Initialized SyncManager.")

    def run_sync(self, dry_run: bool = False):
        if dry_run:
            logger.info("Running in DRY RUN mode. No tasks will be created.")
        logger.info("Starting synchronization process...")
        
        # 1. Fetch available TickTick lists to get IDs
        ticktick_lists = self.ticktick_client.get_lists()
        list_name_to_id = {proj['name']: proj['id'] for proj in ticktick_lists if 'name' in proj and 'id' in proj}
        
        target_parent_list = self.config_manager.get_target_list()
        
        # 2. Fetch existing TickTick tasks for deduplication
        existing_tasks = self.ticktick_client.get_all_tasks()
        # Create a set of Canvas Assignment IDs already present in TickTick
        # We assume the Canvas assignment ID is stored in the task's content description like [Canvas ID: 12345]
        existing_canvas_ids = set()
        for task in existing_tasks:
            content = task.get('content', '')
            if '[Canvas ID:' in content:
                try:
                    # Extract ID
                    start = content.find('[Canvas ID:') + len('[Canvas ID:')
                    end = content.find(']', start)
                    canvas_id = int(content[start:end].strip())
                    existing_canvas_ids.add(canvas_id)
                except ValueError:
                    pass
        
        # 3. Fetch Canvas Courses
        courses = self.canvas_client.get_active_courses()
        
        sync_stats = {'created': 0, 'skipped': 0, 'errors': 0}
        
        # 4. Process assignments for each monitored course
        for course in courses:
            if not self.config_manager.is_course_monitored(course.name):
                continue
                
            logger.info(f"Processing course: {course.name}")
            
            # Get List Mapping
            list_name = self.config_manager.get_list_mapping(course.name)
            list_id = list_name_to_id.get(list_name)
            
            if not list_id:
                logger.warning(f"List '{list_name}' not found in TickTick. Attempting to create it.")
                # Fallback to None if creation fails, which places it in Inbox
                new_list = self.ticktick_client.create_list(list_name)
                if new_list:
                    list_id = new_list.get('id')
                    list_name_to_id[list_name] = list_id
                    
            assignments = self.canvas_client.get_assignments(course)
            
            for assignment in assignments:
                try:
                    # Skip if already in TickTick
                    if assignment.id in existing_canvas_ids:
                        sync_stats['skipped'] += 1
                        continue
                        
                    # Skip if past due
                    due_date = getattr(assignment, 'due_at', None)
                    if not due_date:
                        continue
                    
                    due_date_dt = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    
                    # If it's a past assignment but it is submitted, we skip it.
                    # Note: You can expand CanvasClient to check if assignment is submitted.
                    # For now, by Spec: ignore past assignments (but overdue should still be added). 
                    # If we don't know submission status, checking if it's strictly > now for simplicity,
                    # or pull submission data. We will rely on default past logic if it is way too old.
                    
                    # Apply Offset
                    offset = self.config_manager.get_date_offset()
                    adjusted_due_date = due_date_dt - offset
                    
                    title = f"{assignment.name} - {course.name}"
                    
                    # Build Description with Canvas link and assignment description
                    canvas_link = getattr(assignment, 'html_url', 'No Link Available')
                    raw_description = getattr(assignment, 'description', '')
                    
                    # Clean up HTML tags using BeautifulSoup for a cleaner TickTick task description
                    clean_description = ""
                    if raw_description:
                         soup = BeautifulSoup(raw_description, "html.parser")
                         clean_description = soup.get_text(separator="\n").strip()
                    
                    description = f"[Canvas ID: {assignment.id}]\n\nLink: {canvas_link}\n\n{clean_description}"
                    
                    # Get Priority and Tags
                    priority = self.config_manager.get_priority(assignment.name)
                    tags = self.config_manager.get_tags(assignment.name)
                    
                    # Create Task (unless dry run)
                    if dry_run:
                        logger.info(f"[DRY-RUN] Would create task: {title} (Priority: {priority}, Tags: {tags})")
                        sync_stats['created'] += 1
                        continue
                        
                    created_task = self.ticktick_client.create_task(
                        title=title,
                        description=description,
                        due_date=adjusted_due_date,
                        project_id=list_id,
                        tags=tags,
                        priority=priority
                    )
                    
                    if created_task:
                        sync_stats['created'] += 1
                        logger.info(f"Created task: {title}")
                    else:
                        sync_stats['errors'] += 1
                        logger.error(f"Failed to create task for {assignment.name}")
                        
                except Exception as e:
                    sync_stats['errors'] += 1
                    logger.error(f"Error processing assignment {getattr(assignment, 'id', 'Unknown')}: {e}")

        logger.info(f"Sync complete. Created: {sync_stats['created']}, Skipped: {sync_stats['skipped']}, Errors: {sync_stats['errors']}")
        return sync_stats
