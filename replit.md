# vCenter Data Processor

## Overview

This is a Flask-based web application that processes vCenter data from Ansible playbook outputs. The system monitors directories for new files, parses VM and alarm data, and generates reports suitable for Power BI consumption. It features a dashboard for monitoring processing jobs, automated file watching, and scheduled cleanup tasks.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- **2025-01-28**: Added PostgreSQL database support for production scalability
- **2025-01-28**: Enhanced multi-environment support with client segregation
- **2025-01-28**: Created local development setup scripts and documentation
- **2025-01-28**: Added comprehensive README and setup guides for local deployment

## System Architecture

### Backend Architecture
- **Framework**: Flask web application with SQLAlchemy ORM
- **Database**: SQLite by default (configurable via DATABASE_URL environment variable)
- **File Processing**: Multi-threaded approach with file watcher and scheduled batch processing
- **Background Tasks**: APScheduler for periodic job processing and cleanup
- **File Monitoring**: Watchdog library for real-time file system monitoring

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive UI
- **Styling**: Bootstrap dark theme with custom CSS
- **JavaScript**: Chart.js for data visualization and custom dashboard functionality
- **Real-time Updates**: AJAX-based status updates and notifications

### File Processing Pipeline
1. **File Detection**: Watchdog monitors specified directories for new files
2. **Job Queuing**: New files create ProcessingJob records in pending status
3. **Scheduled Processing**: Background scheduler processes pending jobs in batches
4. **Data Parsing**: AnsibleParser extracts VM and alarm data from JSON/YAML files
5. **Data Export**: DataProcessor generates CSV, Excel, and JSON outputs for Power BI
6. **File Management**: Processed files moved to archive directory with retention policies

## Key Components

### Models (models.py)
- **ProcessingJob**: Tracks file processing status, metadata, and execution times
- **VMRecord**: Stores extracted VM information (name, specs, location)
- **AlarmRecord**: Stores VM alarm data with severity and status
- **ProcessingLog**: Database logging for job execution tracking

### Services
- **AnsibleParser**: Parses JSON/YAML files from Ansible vCenter data collection
- **DataProcessor**: Converts parsed data to Power BI-friendly formats (CSV, Excel, JSON)
- **FileWatcher**: Real-time monitoring of input directories using Watchdog
- **Scheduler**: Background job processing and cleanup tasks

### API Endpoints
- **Dashboard Routes**: Web interface for monitoring and management
- **API Routes**: RESTful endpoints for manual job triggering and status queries

## Data Flow

1. **Input**: Ansible playbooks generate JSON/YAML files with vCenter data
2. **Detection**: File watcher detects new files in monitored directories
3. **Queuing**: System creates ProcessingJob records for new files
4. **Processing**: Scheduler picks up pending jobs and processes them
5. **Parsing**: AnsibleParser extracts structured data from files
6. **Export**: DataProcessor creates Power BI-compatible output files
7. **Storage**: Job results and logs stored in database
8. **Cleanup**: Scheduled tasks remove old files and jobs based on retention policy

## External Dependencies

### Core Libraries
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **APScheduler**: Background task scheduling
- **Watchdog**: File system monitoring
- **Pandas**: Data manipulation and export
- **OpenPyXL**: Excel file generation
- **PyYAML**: YAML file parsing

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Chart.js**: Data visualization
- **Font Awesome**: Icons

## Deployment Strategy

### Environment Configuration
- **Configuration**: Environment variables for all configurable settings
- **Directory Structure**: Configurable input, processing, and output directories
- **Database**: SQLite for development, easily configurable for production databases
- **Logging**: Dual logging to console and database

### Directory Structure
- **Watch Directory**: Input location for Ansible output files
- **Processed Directory**: Archive location for completed files
- **Output Directory**: Generated reports for Power BI consumption

### Scalability Considerations
- **Batch Processing**: Configurable batch sizes for job processing
- **File Size Limits**: Configurable maximum file sizes
- **Retention Policies**: Automatic cleanup of old files and job records
- **Database Connection Pooling**: Configured for production reliability

### Production Readiness
- **ProxyFix**: Configured for deployment behind reverse proxies
- **Error Handling**: Comprehensive exception handling and logging
- **Health Monitoring**: Dashboard provides system status visibility
- **Configuration Management**: Environment-based configuration for different deployment environments