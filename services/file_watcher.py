import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from app import app, db
from models import ProcessingJob
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class AnsibleFileHandler(FileSystemEventHandler):
    """Handle file system events for Ansible output files"""
    
    def __init__(self):
        self.config = Config()
        self.config.ensure_directories()
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            filepath = event.src_path if isinstance(event.src_path, str) else event.src_path.decode('utf-8')
            self._process_new_file(filepath)
    
    def on_moved(self, event):
        """Handle file move events"""
        if not event.is_directory:
            filepath = event.dest_path if isinstance(event.dest_path, str) else event.dest_path.decode('utf-8')
            self._process_new_file(filepath)
    
    def _process_new_file(self, filepath: str):
        """Process a new file"""
        try:
            filename = os.path.basename(filepath)
            file_ext = os.path.splitext(filepath)[1].lower()
            
            # Check if file extension is supported
            if file_ext not in self.config.SUPPORTED_EXTENSIONS:
                logger.debug(f"Skipping unsupported file: {filepath}")
                return
            
            # Check file size
            if os.path.getsize(filepath) > self.config.MAX_FILE_SIZE_MB * 1024 * 1024:
                logger.warning(f"File too large, skipping: {filepath}")
                return
            
            # Extract environment and client information from file path
            environment_info = self._extract_environment_info(filepath)
            
            # Wait a moment to ensure file is completely written
            time.sleep(2)
            
            # Create processing job
            with app.app_context():
                existing_job = ProcessingJob.query.filter_by(
                    filepath=filepath, 
                    status__in=['pending', 'processing']
                ).first()
                
                if existing_job:
                    logger.debug(f"Job already exists for file: {filepath}")
                    return
                
                job = ProcessingJob(
                    filename=filename,
                    filepath=filepath,
                    status='pending',
                    vcenter_environment=environment_info.get('environment'),
                    client_name=environment_info.get('client')
                )
                
                db.session.add(job)
                db.session.commit()
                
                logger.info(f"Created processing job {job.id} for file: {filepath} (env: {environment_info.get('environment')}, client: {environment_info.get('client')})")
                
        except Exception as e:
            logger.error(f"Error processing new file {filepath}: {str(e)}")
    
    def _extract_environment_info(self, filepath: str) -> dict:
        """Extract environment and client information from file path"""
        # Default values
        environment_info = {
            'environment': 'unknown',
            'client': 'unknown'
        }
        
        # Check against configured patterns
        for pattern, info in self.config.ENVIRONMENT_MAPPING.items():
            if pattern in filepath:
                environment_info.update(info)
                break
        
        # Try to extract from directory structure
        # Example: ./ansible_outputs/client-a/prod-vcenter1/vm_data.json
        path_parts = filepath.split(os.sep)
        if len(path_parts) >= 3:
            # Look for client and environment indicators in path
            for part in path_parts:
                if part.startswith(('client-', 'Client-')):
                    environment_info['client'] = part
                elif any(env_key in part for env_key in ['prod', 'dev', 'test', 'staging']):
                    environment_info['environment'] = part
        
        return environment_info

def start_file_watcher():
    """Start the file watcher service"""
    config = Config()
    
    logger.info(f"Starting file watcher for directory: {config.WATCH_DIRECTORY}")
    
    event_handler = AnsibleFileHandler()
    observer = Observer()
    observer.schedule(event_handler, config.WATCH_DIRECTORY, recursive=True)
    
    observer.start()
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("File watcher stopped")
    
    observer.join()

def scan_existing_files():
    """Scan for existing files in the watch directory"""
    config = Config()
    
    logger.info(f"Scanning existing files in: {config.WATCH_DIRECTORY}")
    
    with app.app_context():
        for root, dirs, files in os.walk(config.WATCH_DIRECTORY):
            for file in files:
                filepath = os.path.join(root, file)
                file_ext = os.path.splitext(filepath)[1].lower()
                
                if file_ext in config.SUPPORTED_EXTENSIONS:
                    # Check if already processed
                    existing_job = ProcessingJob.query.filter_by(filepath=filepath).first()
                    
                    if not existing_job:
                        try:
                            job = ProcessingJob(
                                filename=file,
                                filepath=filepath,
                                status='pending'
                            )
                            
                            db.session.add(job)
                            db.session.commit()
                            
                            logger.info(f"Added existing file to processing queue: {filepath}")
                            
                        except Exception as e:
                            logger.error(f"Error adding existing file {filepath}: {str(e)}")
