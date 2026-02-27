from ticktick.oauth2 import OAuth2
from ticktick.api import TickTickClient as BaseTickTickClient
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TickTickClient:
    def __init__(self, username, password, client_id=None, client_secret=None):
        try:
            if client_id and client_secret:
                auth_client = OAuth2(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri="http://127.0.0.1:8080"
                )
                self.client = BaseTickTickClient(username, password, auth_client)
            else:
                # Fallback to direct login if no OAuth client provided
                self.client = BaseTickTickClient(username, password)
            logger.info("Successfully authenticated with TickTick.")
        except Exception as e:
            logger.error(f"Failed to authenticate with TickTick: {e}")
            raise

    def get_all_tasks(self):
        """
        Retrieve all tasks to build a deduplication set.
        """
        try:
            # state.get('tasks') returns all tasks in the current state
            tasks = self.client.state.get('tasks', [])
            return tasks
        except Exception as e:
            logger.error(f"Error fetching tasks from TickTick: {e}")
            return []

    def get_lists(self):
        """
        Retrieve all TickTick lists and folders to map Canvas courses accurately.
        """
        try:
            project_profiles = self.client.state.get('projects', [])
            return project_profiles
        except Exception as e:
            logger.error(f"Error fetching TickTick lists: {e}")
            return []

    def create_list(self, name: str, folder_id: str = None) -> dict:
        """
        Create a new list with the given name, optionally under a specific folder.
        """
        if not name:
            return None
        try:
            new_list = self.client.project.create(name=name, folderId=folder_id)
            logger.info(f"Created new TickTick list: {name}")
            return new_list
        except Exception as e:
            logger.error(f"Failed to create TickTick list {name}: {e}")
            return None

    def create_folder(self, name: str) -> dict:
        """
        Create a new TickTick folder.
        """
        try:
            new_folder = self.client.folder.create(name=name)
            logger.info(f"Created new TickTick folder: {name}")
            return new_folder
        except Exception as e:
            logger.error(f"Failed to create TickTick folder {name}: {e}")
            return None

    def create_task(self, title: str, description: str, due_date: datetime, project_id: str = None, tags: list = None, priority: int = 0) -> dict:
        """
        Create a task in TickTick.
        """
        try:
            # Build the task builder payload
            task_data = {
                'title': title,
                'content': description,
                'priority': priority,
                'tags': tags if tags else []
            }
            if project_id:
                task_data['projectId'] = project_id
            
            # Use TickTick client's built-in time generation where available, or map it manually.
            # Convert due_date from datetime format to appropriate ticktick due date
            # Ensure it is timezone aware
            task_builder = self.client.task.builder(**task_data)
            
            # The builder supports setting dates. 
            # We set the start Date to the same time
            if due_date:
                # ticktick-py builder dates should be aware
                task_builder['dueDate'] = due_date.strftime('%Y-%m-%dT%H:%M:%S%z')
                if not '%z' in due_date.strftime('%z'):
                    task_builder['dueDate'] = due_date.strftime('%Y-%m-%dT%H:%M:%S+0000') # fallback to UTC

            created_task = self.client.task.create(task_builder)
            return created_task
        except Exception as e:
            logger.error(f"Error creating task '{title}': {e}")
            return None
