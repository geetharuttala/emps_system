import logging
import signal
import sys
import time
from .folder_watcher import FolderWatcher
from .database import DatabaseManager
from .config import Config


def setup_logging():
    """Setup logging configuration"""
    config = Config()

    # Create logs directory if it doesn't exist
    import os
    log_dir = os.path.dirname(config.LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )


def initialize_database():
    """Initialize database tables"""
    logger = logging.getLogger(__name__)
    logger.info("Initializing database tables...")

    db_manager = DatabaseManager()

    try:
        if not db_manager.connect():
            logger.error("Failed to connect to database for initialization")
            return False

        # Create all necessary tables
        success = db_manager.create_all_tables()

        if success:
            logger.info("Database initialization completed successfully")
        else:
            logger.error("Database initialization failed")

        return success

    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return False
    finally:
        db_manager.disconnect()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger = logging.getLogger(__name__)
    logger.info("Shutdown signal received, stopping folder watcher...")

    if 'watcher' in globals():
        watcher.stop_watching()

    sys.exit(0)


def main():
    """Main function"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Employee Management System - Folder Watcher")

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize database tables
        if not initialize_database():
            logger.error("Database initialization failed. Exiting...")
            sys.exit(1)

        # Create folder watcher instance
        global watcher
        watcher = FolderWatcher()

        # Setup folders
        watcher.setup_folders()

        # Process existing files
        watcher.process_existing_files()

        # Start watching
        watcher.start_watching()

        logger.info("Folder watcher is running. Press Ctrl+C to stop.")

        # Keep the main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        signal_handler(None, None)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()