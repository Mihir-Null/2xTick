import json
from canvasapi import Canvas
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class CanvasClient:
    def __init__(self, api_url: str, api_token: str, session_cookie: str = None, state_file: str = None):
        self.canvas = Canvas(api_url, api_token)
        
        cookie_parts = []
        
        if state_file:
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    for cookie in state.get('cookies', []):
                        if cookie['name'] in ['canvas_session', '_csrf_token']:
                            cookie_parts.append(f"{cookie['name']}={cookie['value']}")
                logger.info(f"Loaded Canvas auth state from {state_file}.")
            except Exception as e:
                logger.error(f"Failed to load state file {state_file}: {e}")
        elif session_cookie:
            cookie_parts.append(f"canvas_session={session_cookie}")
            logger.info("Using fallback session cookie from environment.")

        if cookie_parts:
            # Set access_token to None to prevent canvasapi from adding the Authorization header
            self.canvas._Canvas__requester.access_token = None
            # Ensure the session doesn't have an Authorization header
            self.canvas._Canvas__requester._session.headers.pop('Authorization', None)
            
            # Inject the session cookies directly into the session headers
            cookie_string = "; ".join(cookie_parts)
            self.canvas._Canvas__requester._session.headers.update({
                'Cookie': cookie_string
            })
            
            # Also set the X-CSRF-Token header if we have the cookie, since Canvas API 
            # often requires it when using cookie-based auth.
            for part in cookie_parts:
                if part.startswith('_csrf_token='):
                    csrf_val = part.split('=', 1)[1]
                    self.canvas._Canvas__requester._session.headers.update({
                        'X-CSRF-Token': csrf_val
                    })
                    break
                    
            logger.info("Injected browser cookies for Canvas authentication.")
        else:
            logger.info("Initialized Canvas client with API token.")

    def get_active_courses(self):
        """
        Retrieves a list of courses the user is currently enrolled in as a student
        and that are available (published).
        """
        active_courses = []
        try:
            # Only get courses where user is a student and the course is available
            courses = self.canvas.get_courses(enrollment_type='student', enrollment_state='active')
            for course in courses:
                # Sometimes courses are returned without names or properties
                if hasattr(course, 'name'):
                    active_courses.append(course)
            logger.info(f"Found {len(active_courses)} active courses.")
        except Exception as e:
            logger.error(f"Error fetching active courses: {e}")
        return active_courses

    def get_assignments(self, course):
        """
        Retrieves assignments for a given course.
        """
        assignments = []
        try:
            # We fetch all assignments for the course.
            course_assignments = course.get_assignments()
            for assignment in course_assignments:
                # We only want assignments with a due date and that can be submitted
                if hasattr(assignment, 'due_at') and assignment.due_at:
                    if getattr(assignment, 'has_submitted_submissions', False) or getattr(assignment, 'submission_types', ['none']) == ['none']:
                         continue
                    assignments.append(assignment)
        except Exception as e:
            logger.error(f"Error fetching assignments for course {course.name}: {e}")
            
        return assignments
