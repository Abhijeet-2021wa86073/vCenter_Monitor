from flask import Blueprint, request, jsonify
from datetime import datetime
import os
from app import db
from models import ProcessingJob
from services.ansible_parser import AnsibleParser
from services.data_processor import DataProcessor
from config import Config
from utils.logger import get_logger

api_bp = Blueprint('api', __name__)
logger = get_logger(__name__)

@api_bp.route('/process-file', methods=['POST'])
def process_file():
    """Manually trigger processing of a specific file"""
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        
        if not filepath:
            return jsonify({'error': 'filepath is required'}), 400
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Check if already being processed
        existing_job = ProcessingJob.query.filter_by(
            filepath=filepath
        ).filter(ProcessingJob.status.in_(['pending', 'processing'])).first()
        
        if existing_job:
            return jsonify({
                'message': 'File already queued for processing',
                'job_id': existing_job.id
            }), 200
        
        # Create new processing job
        filename = os.path.basename(filepath)
        job = ProcessingJob(
            filename=filename,
            filepath=filepath,
            status='pending'
        )
        
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'message': 'File queued for processing',
            'job_id': job.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error in process_file API: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/job/<int:job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """Get status of a specific processing job"""
    job = ProcessingJob.query.get_or_404(job_id)
    
    job_data = {
        'id': job.id,
        'filename': job.filename,
        'filepath': job.filepath,
        'status': job.status,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'vm_count': job.vm_count,
        'alarm_count': job.alarm_count,
        'error_message': job.error_message,
        'output_files': job.output_files or []
    }
    
    return jsonify(job_data)

@api_bp.route('/job/<int:job_id>/logs', methods=['GET'])
def get_job_logs(job_id):
    """Get logs for a specific processing job"""
    from models import ProcessingLog
    
    job = ProcessingJob.query.get_or_404(job_id)
    
    logs = ProcessingLog.query.filter_by(job_id=job_id).order_by(
        ProcessingLog.timestamp.desc()
    ).all()
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log.id,
            'level': log.level,
            'message': log.message,
            'timestamp': log.timestamp.isoformat()
        })
    
    return jsonify({
        'job_id': job_id,
        'logs': logs_data
    })

@api_bp.route('/job/<int:job_id>/retry', methods=['POST'])
def retry_job(job_id):
    """Retry a failed processing job"""
    job = ProcessingJob.query.get_or_404(job_id)
    
    if job.status != 'failed':
        return jsonify({'error': 'Can only retry failed jobs'}), 400
    
    # Reset job status
    job.status = 'pending'
    job.started_at = None
    job.completed_at = None
    job.error_message = None
    job.output_files = None
    
    db.session.commit()
    
    return jsonify({
        'message': 'Job queued for retry',
        'job_id': job.id
    })

@api_bp.route('/validate-file', methods=['POST'])
def validate_file():
    """Validate an Ansible output file without processing it"""
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        
        if not filepath:
            return jsonify({'error': 'filepath is required'}), 400
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Check file extension
        config = Config()
        file_ext = os.path.splitext(filepath)[1].lower()
        
        if file_ext not in config.SUPPORTED_EXTENSIONS:
            return jsonify({
                'valid': False,
                'error': f'Unsupported file extension: {file_ext}'
            })
        
        # Check file size
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if file_size_mb > config.MAX_FILE_SIZE_MB:
            return jsonify({
                'valid': False,
                'error': f'File too large: {file_size_mb:.2f}MB > {config.MAX_FILE_SIZE_MB}MB'
            })
        
        # Try to parse the file
        parser = AnsibleParser()
        try:
            parsed_data = parser.parse_file(filepath)
            
            return jsonify({
                'valid': True,
                'file_info': {
                    'size_mb': round(file_size_mb, 2),
                    'extension': file_ext,
                    'vm_count': len(parsed_data['vms']),
                    'alarm_count': len(parsed_data['alarms'])
                }
            })
            
        except Exception as parse_error:
            return jsonify({
                'valid': False,
                'error': f'Parse error: {str(parse_error)}'
            })
        
    except Exception as e:
        logger.error(f"Error in validate_file API: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/process', methods=['POST'])
def process_files():
    """Manually trigger processing of all pending files"""
    try:
        from services.scheduler import process_pending_jobs
        process_pending_jobs()
        
        # Get current job counts
        pending_count = ProcessingJob.query.filter_by(status='pending').count()
        processing_count = ProcessingJob.query.filter_by(status='processing').count()
        completed_count = ProcessingJob.query.filter_by(status='completed').count()
        
        return jsonify({
            'message': 'Processing triggered successfully',
            'job_status': {
                'pending': pending_count,
                'processing': processing_count,
                'completed': completed_count
            }
        })
    except Exception as e:
        logger.error(f"Error in process API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        
        # Check directory accessibility
        config = Config()
        directories_ok = all([
            os.path.exists(config.WATCH_DIRECTORY),
            os.path.exists(config.OUTPUT_DIRECTORY),
            os.path.exists(config.PROCESSED_DIRECTORY)
        ])
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'directories': 'accessible' if directories_ok else 'issues detected'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500
