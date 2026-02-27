import os
import logging
from dotenv import load_dotenv
from clients.canvas_client import CanvasClient

# Set up logging to see details
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_cookie():
    load_dotenv()
    
    url = os.getenv('CANVAS_API_URL')
    token = os.getenv('CANVAS_API_TOKEN', '')
    cookie = os.getenv('CANVAS_SESSION_COOKIE')

    if not url:
        print("❌ Error: CANVAS_API_URL not found in .env")
        return

    if not cookie:
        print("❌ Error: CANVAS_SESSION_COOKIE not found in .env")
        return

    print(f"--- Canvas Cookie Test ---")
    print(f"URL: {url}")
    print(f"Using Cookie: {cookie[:10]}...{cookie[-10:] if len(cookie) > 20 else ''}")
    print(f"--------------------------")

    try:
        # Initialize client with dummy token and our captured cookie
        client = CanvasClient(url, token or "dummy", session_cookie=cookie)
        
        print("Fetching courses...")
        courses = client.get_active_courses()
        
        if courses:
            print(f"✅ Success! Found {len(courses)} courses:")
            for course in courses:
                print(f" - {course.name}")
        else:
            print("⚠️ Connected, but found 0 active courses. Check if your courses are published.")
            
    except Exception as e:
        print(f"❌ Failed to connect: {e}")

if __name__ == "__main__":
    test_cookie()
