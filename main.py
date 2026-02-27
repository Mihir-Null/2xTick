import os
import sys
import logging
from dotenv import load_dotenv

from config_manager import ConfigManager
from clients.canvas_client import CanvasClient
from clients.ticktick_client import TickTickClient
from sync_manager import SyncManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
    canvas_url = os.getenv('CANVAS_API_URL')
    canvas_token = os.getenv('CANVAS_API_TOKEN')
    canvas_session_cookie = os.getenv('CANVAS_SESSION_COOKIE')
    canvas_username = os.getenv('CANVAS_USERNAME')
    canvas_password = os.getenv('CANVAS_PASSWORD')
    
    ticktick_user = os.getenv('TICKTICK_USERNAME')
    ticktick_pass = os.getenv('TICKTICK_PASSWORD')
    ticktick_client_id = os.getenv('TICKTICK_CLIENT_ID')
    ticktick_client_secret = os.getenv('TICKTICK_CLIENT_SECRET')

    state_file_path = "canvas_state.json"

    if not all([canvas_url, ticktick_user, ticktick_pass]):
        logger.error("Missing required environment variables for TickTick or Canvas URL. Please check your .env file.")
        sys.exit(1)

    import argparse
    parser = argparse.ArgumentParser(description="Sync Canvas assignments to TickTick.")
    parser.add_argument('--dry-run', action='store_true', help="Run the sync without creating tasks in TickTick.")
    parser.add_argument('--login', action='store_true', help="Launch browser to log in to Canvas and save session state.")
    args = parser.parse_args()

    if args.login:
        from clients.canvas_auth import login_and_save_state
        logger.info("Running interactive Canvas login flow...")
        login_and_save_state(canvas_url, canvas_username, canvas_password, state_file_path)
        
    state_file_arg = state_file_path if os.path.exists(state_file_path) else None
    
    if not (canvas_token or canvas_session_cookie or state_file_arg):
        logger.error("No Canvas authentication method found. Please set CANVAS_API_TOKEN, CANVAS_SESSION_COOKIE, or run with --login to log in via browser.")
        sys.exit(1)

    try:
        # Initialize Config Manager (will auto-generate config.yaml if it doesn't exist)
        configManager = ConfigManager('config.yaml')
        
        # Initialize API Clients
        logger.info("Connecting to Canvas...")
        canvasClient = CanvasClient(canvas_url, canvas_token or "", session_cookie=canvas_session_cookie, state_file=state_file_arg)
        
        logger.info("Connecting to TickTick...")
        ticktickClient = TickTickClient(
            username=ticktick_user, 
            password=ticktick_pass,
            client_id=ticktick_client_id, 
            client_secret=ticktick_client_secret
        )
        
        # Initialize and Run Sync Manager
        syncManager = SyncManager(canvasClient, ticktickClient, configManager)
        syncManager.run_sync(dry_run=args.dry_run)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
