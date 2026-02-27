import yaml
import os
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'courses_to_monitor': [
        'Course Name 1',
        'Course Name 2'
    ],
    'ticktick_list_mappings': {
        'Course Name 1': 'Course 1 Folder Name',
        'Course Name 2': 'Course 2 Folder Name',
        'default': 'Other Coursework'
    },
    'priorities': {
        'high_keywords': ['exam', 'quiz', 'midterm', 'final', 'project'],
        'low_keywords': ['optional', 'extra credit', 'reading'],
        'default': 3 # TickTick priority: 0 is none, 1 is low, 3 is medium, 5 is high
    },
    'tags': {
        'homework_keywords': ['hw', 'homework', 'assignment', 'paper'],
        'exam_keywords': ['exam', 'quiz', 'midterm', 'final'],
        'default': ['Coursework']
    },
    'due_date_offset_hours': 0,
    'ticktick_target_list': 'Coursework' # Parent list name
}

from typing import List, Dict, Any

class ConfigManager:
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_or_create_config()

    def load_or_create_config(self):
        if not os.path.exists(self.config_path):
            logger.info(f"Config file not found. Creating default at {self.config_path}")
            with open(self.config_path, 'w') as f:
                yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
            self.config = DEFAULT_CONFIG
        else:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)

    def is_course_monitored(self, course_name: str) -> bool:
        monitored_courses = self.config.get('courses_to_monitor', [])
        if not monitored_courses: # If empty list, we monitor everything (or default configuration behavior)
            return True
        return course_name in monitored_courses

    def get_list_mapping(self, course_name: str) -> str:
        mappings = self.config.get('ticktick_list_mappings', {})
        return mappings.get(course_name, mappings.get('default', 'Coursework'))

    def get_priority(self, assignment_title: str) -> int:
        title_lower = assignment_title.lower()
        priorities = self.config.get('priorities', {})
        
        for kw in priorities.get('high_keywords', []):
            if kw.lower() in title_lower:
                return 5
                
        for kw in priorities.get('low_keywords', []):
            if kw.lower() in title_lower:
                return 1
                
        return priorities.get('default', 3)

    def get_tags(self, assignment_title: str) -> list:
        title_lower = assignment_title.lower()
        tags_config = self.config.get('tags', {})
        
        tags = []
        for kw in tags_config.get('exam_keywords', []):
            if kw.lower() in title_lower:
                tags.append('Exam')
                break
                
        for kw in tags_config.get('homework_keywords', []):
            if kw.lower() in title_lower:
                tags.append('Homework')
                break
                
        if not tags:
            tags = tags_config.get('default', [])
            
        return tags

    def get_date_offset(self) -> timedelta:
        offset_hours = self.config.get('due_date_offset_hours', 0)
        return timedelta(hours=offset_hours)
    
    def get_target_list(self) -> str:
        return self.config.get('ticktick_target_list', 'Coursework')
