from flask import Blueprint, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import os
from app import db
from models import ProcessingJob, ProcessingLog, VMRecord, AlarmRecord
from config import Config

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@dashboard_bp.route('/processing-logs')
def processing_logs():
    """Processing logs page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    logs = ProcessingLog.query.order_by(
        ProcessingLog.timestamp.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('processing_logs.html', logs=logs)

@dashboard_bp.route('/jobs')
def jobs():
    """Get processing jobs data"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')
    environment_filter = request.args.get('environment', '')
    client_filter = request.args.get('client', '')
    
    query = ProcessingJob.query
    
    if status_filter:
        query = query.filter(ProcessingJob.status == status_filter)
    if environment_filter:
        query = query.filter(ProcessingJob.vcenter_environment == environment_filter)
    if client_filter:
        query = query.filter(ProcessingJob.client_name == client_filter)
    
    jobs = query.order_by(ProcessingJob.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    jobs_data = []
    for job in jobs.items:
        job_data = {
            'id': job.id,
            'filename': job.filename,
            'status': job.status,
            'vcenter_environment': job.vcenter_environment,
            'client_name': job.client_name,
            'datacenter': job.datacenter,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'vm_count': job.vm_count,
            'alarm_count': job.alarm_count,
            'error_message': job.error_message,
            'output_files': job.output_files or []
        }
        
        # Calculate processing time if available
        if job.started_at and job.completed_at:
            processing_time = (job.completed_at - job.started_at).total_seconds()
            job_data['processing_time_seconds'] = processing_time
        
        jobs_data.append(job_data)
    
    return jsonify({
        'jobs': jobs_data,
        'pagination': {
            'page': jobs.page,
            'pages': jobs.pages,
            'per_page': jobs.per_page,
            'total': jobs.total,
            'has_prev': jobs.has_prev,
            'has_next': jobs.has_next
        }
    })

@dashboard_bp.route('/statistics')
def statistics():
    """Get dashboard statistics"""
    # Job statistics
    total_jobs = ProcessingJob.query.count()
    pending_jobs = ProcessingJob.query.filter_by(status='pending').count()
    processing_jobs = ProcessingJob.query.filter_by(status='processing').count()
    completed_jobs = ProcessingJob.query.filter_by(status='completed').count()
    failed_jobs = ProcessingJob.query.filter_by(status='failed').count()
    
    # Recent activity (last 24 hours)
    last_24h = datetime.utcnow() - timedelta(hours=24)
    recent_jobs = ProcessingJob.query.filter(
        ProcessingJob.created_at >= last_24h
    ).count()
    
    # VM and alarm counts
    total_vms = db.session.query(db.func.sum(ProcessingJob.vm_count)).scalar() or 0
    total_alarms = db.session.query(db.func.sum(ProcessingJob.alarm_count)).scalar() or 0
    
    # Processing success rate
    success_rate = 0
    if total_jobs > 0:
        success_rate = (completed_jobs / total_jobs) * 100
    
    # Recent logs count
    recent_errors = ProcessingLog.query.filter(
        ProcessingLog.level == 'ERROR',
        ProcessingLog.timestamp >= last_24h
    ).count()
    
    # Environment and client statistics
    environment_stats = db.session.query(
        ProcessingJob.vcenter_environment,
        db.func.count(ProcessingJob.id).label('job_count'),
        db.func.sum(ProcessingJob.vm_count).label('vm_count'),
        db.func.sum(ProcessingJob.alarm_count).label('alarm_count')
    ).filter(
        ProcessingJob.vcenter_environment.isnot(None)
    ).group_by(ProcessingJob.vcenter_environment).all()
    
    client_stats = db.session.query(
        ProcessingJob.client_name,
        db.func.count(ProcessingJob.id).label('job_count'),
        db.func.sum(ProcessingJob.vm_count).label('vm_count'),
        db.func.sum(ProcessingJob.alarm_count).label('alarm_count')
    ).filter(
        ProcessingJob.client_name.isnot(None)
    ).group_by(ProcessingJob.client_name).all()
    
    return jsonify({
        'job_statistics': {
            'total': total_jobs,
            'pending': pending_jobs,
            'processing': processing_jobs,
            'completed': completed_jobs,
            'failed': failed_jobs,
            'success_rate': round(success_rate, 2)
        },
        'data_statistics': {
            'total_vms': total_vms,
            'total_alarms': total_alarms,
            'recent_jobs_24h': recent_jobs
        },
        'environment_statistics': [
            {
                'environment': env,
                'job_count': job_count,
                'vm_count': vm_count or 0,
                'alarm_count': alarm_count or 0
            }
            for env, job_count, vm_count, alarm_count in environment_stats
        ],
        'client_statistics': [
            {
                'client': client,
                'job_count': job_count,
                'vm_count': vm_count or 0,
                'alarm_count': alarm_count or 0
            }
            for client, job_count, vm_count, alarm_count in client_stats
        ],
        'system_health': {
            'recent_errors': recent_errors,
            'status': 'healthy' if recent_errors < 5 else 'warning'
        }
    })

@dashboard_bp.route('/download/<int:job_id>/<filename>')
def download_output_file(job_id, filename):
    """Download output file from a processing job"""
    job = ProcessingJob.query.get_or_404(job_id)
    
    if not job.output_files:
        return jsonify({'error': 'No output files available'}), 404
    
    # Find the requested file
    file_path = None
    for output_file in job.output_files:
        if os.path.basename(output_file) == filename:
            file_path = output_file
            break
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, as_attachment=True)

@dashboard_bp.route('/system-info')
def system_info():
    """Get system information"""
    config = Config()
    
    # Directory information
    watch_dir_exists = os.path.exists(config.WATCH_DIRECTORY)
    output_dir_exists = os.path.exists(config.OUTPUT_DIRECTORY)
    processed_dir_exists = os.path.exists(config.PROCESSED_DIRECTORY)
    
    # File counts in directories
    watch_files = 0
    output_files = 0
    processed_files = 0
    
    try:
        if watch_dir_exists:
            watch_files = len([f for f in os.listdir(config.WATCH_DIRECTORY) 
                             if os.path.isfile(os.path.join(config.WATCH_DIRECTORY, f))])
        
        if output_dir_exists:
            output_files = len([f for f in os.listdir(config.OUTPUT_DIRECTORY) 
                              if os.path.isfile(os.path.join(config.OUTPUT_DIRECTORY, f))])
        
        if processed_dir_exists:
            processed_files = len([f for f in os.listdir(config.PROCESSED_DIRECTORY) 
                                 if os.path.isfile(os.path.join(config.PROCESSED_DIRECTORY, f))])
    except Exception as e:
        pass  # Handle permission errors gracefully
    
    return jsonify({
        'directories': {
            'watch_directory': {
                'path': config.WATCH_DIRECTORY,
                'exists': watch_dir_exists,
                'file_count': watch_files
            },
            'output_directory': {
                'path': config.OUTPUT_DIRECTORY,
                'exists': output_dir_exists,
                'file_count': output_files
            },
            'processed_directory': {
                'path': config.PROCESSED_DIRECTORY,
                'exists': processed_dir_exists,
                'file_count': processed_files
            }
        },
        'configuration': {
            'supported_extensions': config.SUPPORTED_EXTENSIONS,
            'max_file_size_mb': config.MAX_FILE_SIZE_MB,
            'processing_interval_minutes': config.PROCESSING_INTERVAL_MINUTES,
            'retention_days': config.RETENTION_DAYS
        }
    })
