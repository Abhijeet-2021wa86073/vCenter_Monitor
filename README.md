# vCenter Data Processor

A Python Flask application that automatically processes scheduled Ansible vCenter outputs and transforms them into Power BI-ready datasets with multi-environment support.

## Features

- **Automated File Monitoring**: Watches for Ansible output files and processes them automatically
- **Multi-Environment Support**: Segregates data by vCenter environments and clients
- **Power BI Integration**: Generates CSV, Excel, and JSON exports optimized for Power BI
- **Web Dashboard**: Real-time monitoring with environment and client filtering
- **Background Processing**: Scheduled processing with APScheduler
- **Database Support**: PostgreSQL for production, SQLite for development

## Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL (for production) or SQLite (for development)
- Git

### Local Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd vcenter-data-processor
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   # Database Configuration
   DATABASE_URL=sqlite:///vcenter_processor.db
   
   # Flask Configuration
   FLASK_ENV=development
   FLASK_DEBUG=True
   SESSION_SECRET=your-secret-key-here
   
   # Directory Configuration
   WATCH_DIRECTORY=./ansible_outputs
   PROCESSED_DIRECTORY=./processed
   OUTPUT_DIRECTORY=./powerbi_outputs
   
   # Processing Configuration
   BATCH_SIZE=100
   MAX_FILE_SIZE_MB=50
   PROCESSING_INTERVAL_MINUTES=5
   CLEANUP_INTERVAL_HOURS=24
   RETENTION_DAYS=30
   ```

5. **Initialize the database:**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

6. **Create required directories:**
   ```bash
   mkdir -p ansible_outputs processed powerbi_outputs
   ```

7. **Start the application:**
   ```bash
   python main.py
   ```

   The application will be available at `http://localhost:5000`

### Production Deployment

For production deployment with PostgreSQL:

1. **Set up PostgreSQL database:**
   ```bash
   # Install PostgreSQL and create database
   sudo apt-get install postgresql postgresql-contrib
   sudo -u postgres createdb vcenter_processor
   sudo -u postgres createuser vcenter_user
   sudo -u postgres psql -c "ALTER USER vcenter_user PASSWORD 'your_password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE vcenter_processor TO vcenter_user;"
   ```

2. **Update environment variables:**
   ```env
   DATABASE_URL=postgresql://vcenter_user:your_password@localhost/vcenter_processor
   FLASK_ENV=production
   FLASK_DEBUG=False
   ```

3. **Install production dependencies:**
   ```bash
   pip install gunicorn psycopg2-binary
   ```

4. **Start with Gunicorn:**
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
   ```

## Multi-Environment Setup

### Directory Structure

Organize your Ansible outputs by client and environment:

```
ansible_outputs/
├── client-a/
│   ├── prod-vcenter1/
│   │   ├── vm_inventory_20250128.json
│   │   └── vm_alarms_20250128.json
│   ├── dev-vcenter/
│   │   ├── vm_inventory_20250128.json
│   │   └── vm_alarms_20250128.json
├── client-b/
│   ├── prod-vcenter2/
│   │   ├── vm_inventory_20250128.json
│   │   └── vm_alarms_20250128.json
```

### Environment Configuration

Edit `config.py` to map your directory patterns to environments:

```python
ENVIRONMENT_MAPPING = {
    "prod-vcenter1": {"environment": "production-vc1", "client": "client-a"},
    "prod-vcenter2": {"environment": "production-vc2", "client": "client-b"},
    "dev-vcenter": {"environment": "development", "client": "client-a"},
    # Add your environments here
}
```

## Ansible Integration

### Sample Ansible Playbook

```yaml
---
- name: Collect vCenter Data
  hosts: localhost
  vars:
    output_dir: "./ansible_outputs/{{ client_name }}/{{ vcenter_env }}"
    timestamp: "{{ ansible_date_time.date }}"
  
  tasks:
    - name: Create output directory
      file:
        path: "{{ output_dir }}"
        state: directory
    
    - name: Collect VM inventory
      vmware.vmware_rest.vcenter_vm_info:
        vcenter_hostname: "{{ vcenter_host }}"
        vcenter_username: "{{ vcenter_user }}"
        vcenter_password: "{{ vcenter_password }}"
      register: vm_data
    
    - name: Save VM inventory
      copy:
        content: "{{ vm_data | to_nice_json }}"
        dest: "{{ output_dir }}/vm_inventory_{{ timestamp }}.json"
    
    - name: Collect VM alarms
      vmware.vmware_rest.vcenter_alarm_info:
        vcenter_hostname: "{{ vcenter_host }}"
        vcenter_username: "{{ vcenter_user }}"
        vcenter_password: "{{ vcenter_password }}"
      register: alarm_data
    
    - name: Save VM alarms
      copy:
        content: "{{ alarm_data | to_nice_json }}"
        dest: "{{ output_dir }}/vm_alarms_{{ timestamp }}.json"
```

### Scheduled Execution

Set up a cron job to run your Ansible playbooks:

```bash
# Run every 4 hours
0 */4 * * * cd /path/to/ansible && ansible-playbook -i inventory vcenter_collect.yml
```

## API Endpoints

### Dashboard
- `GET /` - Main dashboard
- `GET /jobs` - Processing jobs with filtering
- `GET /statistics` - System statistics
- `GET /logs` - Processing logs

### API
- `POST /api/process` - Manually trigger processing
- `GET /api/health` - Health check
- `GET /api/system-info` - System information

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///vcenter_processor.db` |
| `WATCH_DIRECTORY` | Directory to monitor for files | `./ansible_outputs` |
| `OUTPUT_DIRECTORY` | Directory for generated reports | `./powerbi_outputs` |
| `BATCH_SIZE` | Number of files to process per batch | `100` |
| `PROCESSING_INTERVAL_MINUTES` | How often to check for new files | `5` |
| `RETENTION_DAYS` | How long to keep processed files | `30` |

### File Processing

The system supports these file formats:
- JSON (`.json`)
- YAML (`.yaml`, `.yml`)

Maximum file size: 50MB (configurable)

## Troubleshooting

### Common Issues

1. **Database connection errors:**
   - Verify DATABASE_URL is correct
   - Ensure database server is running
   - Check user permissions

2. **File processing not working:**
   - Check directory permissions
   - Verify file formats are supported
   - Check application logs

3. **Dashboard not loading:**
   - Ensure Flask application is running
   - Check firewall settings
   - Verify port 5000 is available

### Logs

Application logs are stored in:
- Console output (development)
- Database `processing_log` table
- System logs (production)

### Support

For issues and questions:
1. Check the logs in the dashboard
2. Verify configuration settings
3. Test with sample data files

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

```bash
black .
flake8 .
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request