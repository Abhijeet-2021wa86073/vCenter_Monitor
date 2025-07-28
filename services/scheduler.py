from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import os
import shutil
from app import app, db
from models import ProcessingJob, ProcessingLog
from services.ansible_parser import AnsibleParser
from services.data_processor import DataProcessor
from services.file_watcher import scan_existing_files
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)
scheduler = BackgroundScheduler()

def process_pending_jobs():
    """Process all pending jobs"""
    with app.app_context():
        try:
            pending_jobs = ProcessingJob.query.filter_by(status='pending').limit(10).all()
            
            if not pending_jobs:
                return
            
            logger.info(f"Processing {len(pending_jobs)} pending jobs")
            
            parser = AnsibleParser()
            processor = DataProcessor()
            
            for job in pending_jobs:
                process_single_job(job, parser, processor)
                
        except Exception as e:
            logger.error(f"Error in process_pending_jobs: {str(e)}")

def process_single_job(job: ProcessingJob, parser: AnsibleParser, processor: DataProcessor):
    """Process a single job"""
    job_logger = get_logger(f"job_{job.id}", job.id)
    
    try:
        # Update job status
        job.status = 'processing'
        job.started_at = datetime.utcnow()
        db.session.commit()
        
        job_logger.info(f"Starting processing of file: {job.filepath}")
        
        # Check if file still exists
        if not os.path.exists(job.filepath):
            raise FileNotFoundError(f"File not found: {job.filepath}")
        
        # Parse the file
        parsed_data = parser.parse_file(job.filepath)
        
        # Update job with parsed counts
        job.vm_count = len(parsed_data['vms'])
        job.alarm_count = len(parsed_data['alarms'])
        db.session.commit()
        
        job_logger.info(f"Parsed {job.vm_count} VMs and {job.alarm_count} alarms")
        
        # Process and export data
        output_files = processor.process_data(parsed_data, job.id)
        
        # Update job with output files
        job.output_files = output_files
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        db.session.commit()
        
        # Move processed file
        move_processed_file(job.filepath)
        
        job_logger.info(f"Successfully processed job {job.id}")
        
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.session.commit()
        
        job_logger.error(f"Failed to process job {job.id}: {str(e)}")

def move_processed_file(filepath: str):
    """Move processed file to processed directory"""
    try:
        config = Config()
        filename = os.path.basename(filepath)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processed_filename = f"{timestamp}_{filename}"
        processed_path = os.path.join(config.PROCESSED_DIRECTORY, processed_filename)
        
        shutil.move(filepath, processed_path)
        logger.debug(f"Moved processed file to: {processed_path}")
        
    except Exception as e:
        logger.warning(f"Failed to move processed file {filepath}: {str(e)}")

def cleanup_old_records():
    """Clean up old processing records and logs"""
    with app.app_context():
        try:
            config = Config()
            cutoff_date = datetime.utcnow() - timedelta(days=config.RETENTION_DAYS)
            
            # Delete old completed/failed jobs
            old_jobs = ProcessingJob.query.filter(
                ProcessingJob.completed_at < cutoff_date,
                ProcessingJob.status.in_(['completed', 'failed'])
            ).all()
            
            for job in old_jobs:
                # Clean up output files
                if job.output_files:
                    for output_file in job.output_files:
                        try:
                            if os.path.exists(output_file):
                                os.remove(output_file)
                        except Exception as e:
                            logger.warning(f"Failed to delete output file {output_file}: {str(e)}")
                
                # Delete job record
                db.session.delete(job)
            
            # Delete old logs
            old_logs = ProcessingLog.query.filter(
                ProcessingLog.timestamp < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Cleaned up {len(old_jobs)} old jobs and {old_logs} old log entries")
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_records: {str(e)}")
            db.session.rollback()

def init_scheduler(app):
    """Initialize the scheduler"""
    config = Config()
    
    if not scheduler.running:
        # Add job processing task
        scheduler.add_job(
            func=process_pending_jobs,
            trigger=IntervalTrigger(minutes=config.PROCESSING_INTERVAL_MINUTES),
            id='process_pending_jobs',
            name='Process pending Ansible output files',
            replace_existing=True
        )
        
        # Add cleanup task
        scheduler.add_job(
            func=cleanup_old_records,
            trigger=IntervalTrigger(hours=config.CLEANUP_INTERVAL_HOURS),
            id='cleanup_old_records',
            name='Clean up old processing records',
            replace_existing=True
        )
        
        # Add initial file scan
        scheduler.add_job(
            func=scan_existing_files,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=10),
            id='initial_file_scan',
            name='Initial scan for existing files'
        )
        
        scheduler.start()
        logger.info("Scheduler started successfully")
    
    # Shutdown scheduler when app context ends
    import atexit
    atexit.register(lambda: scheduler.shutdown())
