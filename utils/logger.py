import logging
from app import db
from models import ProcessingLog

class DatabaseHandler(logging.Handler):
    def __init__(self, job_id=None):
        super().__init__()
        self.job_id = job_id
        
    def emit(self, record):
        try:
            from app import app
            with app.app_context():
                log_entry = ProcessingLog(
                    job_id=self.job_id,
                    level=record.levelname,
                    message=self.format(record)
                )
                db.session.add(log_entry)
                db.session.commit()
        except Exception:
            # Don't let logging errors break the application
            pass

def get_logger(name, job_id=None):
    """Get a logger that writes to both console and database"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Database handler if job_id is provided
    if job_id:
        db_handler = DatabaseHandler(job_id)
        db_handler.setLevel(logging.INFO)
        db_handler.setFormatter(formatter)
        logger.addHandler(db_handler)
    
    return logger
