from app import db
from datetime import datetime
from sqlalchemy import JSON

class ProcessingJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')  # pending, processing, completed, failed
    vcenter_environment = db.Column(db.String(100))  # Environment identifier (e.g., "prod-vcenter1", "dev-vcenter2")
    client_name = db.Column(db.String(100))  # Client identifier (e.g., "client-a", "client-b")
    datacenter = db.Column(db.String(100))  # Datacenter name from vCenter
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    vm_count = db.Column(db.Integer, default=0)
    alarm_count = db.Column(db.Integer, default=0)
    output_files = db.Column(JSON)  # Store list of generated output files
    
class VMRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('processing_job.id'), nullable=False)
    vm_name = db.Column(db.String(255), nullable=False)
    vm_uuid = db.Column(db.String(255))
    power_state = db.Column(db.String(50))
    cpu_count = db.Column(db.Integer)
    memory_mb = db.Column(db.Integer)
    disk_gb = db.Column(db.Float)
    network_count = db.Column(db.Integer)
    guest_os = db.Column(db.String(255))
    host_name = db.Column(db.String(255))
    cluster_name = db.Column(db.String(255))
    datacenter_name = db.Column(db.String(255))
    vcenter_environment = db.Column(db.String(100))  # Environment identifier
    client_name = db.Column(db.String(100))  # Client identifier
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class AlarmRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('processing_job.id'), nullable=False)
    vm_name = db.Column(db.String(255), nullable=False)
    alarm_name = db.Column(db.String(255), nullable=False)
    alarm_description = db.Column(db.Text)
    severity = db.Column(db.String(50))
    status = db.Column(db.String(50))
    triggered_time = db.Column(db.DateTime)
    acknowledged = db.Column(db.Boolean, default=False)
    vcenter_environment = db.Column(db.String(100))  # Environment identifier
    client_name = db.Column(db.String(100))  # Client identifier
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class ProcessingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('processing_job.id'))
    level = db.Column(db.String(20), nullable=False)  # INFO, WARNING, ERROR
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
