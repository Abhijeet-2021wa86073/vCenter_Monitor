# Local Development Setup Guide

## Quick Start (Recommended)

The easiest way to run the vCenter Data Processor on your local system:

### Option 1: Quick Test (Recommended)

If you're having issues with the white page, try this simplified version first:

1. **Download the project files** to your local machine
2. **Open terminal/command prompt** in the project directory
3. **Run the simple test:**
   ```bash
   python simple_local.py
   ```

This will start a simplified version that tests if your basic setup is working.

### Option 2: Full Setup Script

1. **Download the project files** to your local machine
2. **Open terminal/command prompt** in the project directory
3. **Run the setup script:**
   ```bash
   python start_local.py
   ```

This script will automatically:
- Check Python version compatibility
- Install all required dependencies
- Create necessary directories
- Initialize the database
- Set up environment variables
- Start the application

### Option 2: Manual Setup

If you prefer manual setup or the script doesn't work:

1. **Install Python 3.11+** (if not already installed)
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install Flask Flask-SQLAlchemy pandas openpyxl watchdog APScheduler python-dateutil PyYAML psycopg2-binary gunicorn
   ```

4. **Create directories:**
   ```bash
   mkdir ansible_outputs processed powerbi_outputs instance
   ```

5. **Set environment variables** (create `.env` file or set manually):
   ```bash
   export DATABASE_URL="sqlite:///instance/vcenter_processor.db"
   export FLASK_DEBUG="True"
   export WATCH_DIRECTORY="./ansible_outputs"
   export OUTPUT_DIRECTORY="./powerbi_outputs"
   ```

6. **Initialize database:**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

7. **Start the application:**
   ```bash
   python main.py
   ```

## Accessing the Application

Once started, open your web browser and go to:
- **Dashboard**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/health

## Testing with Sample Data

### Create Test Directory Structure

```bash
mkdir -p ansible_outputs/client-a/prod-vcenter1
mkdir -p ansible_outputs/client-b/prod-vcenter2
```

### Sample VM Data File

Create `ansible_outputs/client-a/prod-vcenter1/vm_inventory_test.json`:

```json
{
  "vms": [
    {
      "name": "web-server-01",
      "uuid": "50322a7e-8f9a-4b5c-9d6e-1f2a3b4c5d6e",
      "power_state": "poweredOn",
      "cpu_count": 4,
      "memory_mb": 8192,
      "disk_gb": 100.5,
      "network_count": 2,
      "guest_os": "CentOS 8",
      "host_name": "esxi-host-01.company.com",
      "cluster_name": "Production-Cluster",
      "datacenter_name": "Primary-DC"
    },
    {
      "name": "db-server-01", 
      "uuid": "60433b8f-9a0b-5c6d-ae7f-2g3h4i5j6k7l",
      "power_state": "poweredOn",
      "cpu_count": 8,
      "memory_mb": 16384,
      "disk_gb": 500.0,
      "network_count": 1,
      "guest_os": "Windows Server 2019",
      "host_name": "esxi-host-02.company.com", 
      "cluster_name": "Production-Cluster",
      "datacenter_name": "Primary-DC"
    }
  ]
}
```

### Sample Alarm Data File

Create `ansible_outputs/client-a/prod-vcenter1/vm_alarms_test.json`:

```json
{
  "alarms": [
    {
      "vm_name": "web-server-01",
      "alarm_name": "High CPU Usage",
      "alarm_description": "CPU usage is above 80%",
      "severity": "warning",
      "status": "active",
      "triggered_time": "2025-01-28T10:30:00Z",
      "acknowledged": false
    },
    {
      "vm_name": "db-server-01",
      "alarm_name": "Low Disk Space",
      "alarm_description": "Disk space is below 10%",
      "severity": "critical", 
      "status": "active",
      "triggered_time": "2025-01-28T11:15:00Z",
      "acknowledged": false
    }
  ]
}
```

## What Happens Next

1. **File Detection**: The application will automatically detect your test files
2. **Processing**: Files will be processed within 5 minutes (or immediately via dashboard)
3. **Output Generation**: Power BI files will be created in `powerbi_outputs/`
4. **Dashboard Updates**: View processing status in the web dashboard

## Directory Structure After Setup

```
your-project/
├── ansible_outputs/          # Input files from Ansible
│   ├── client-a/
│   │   └── prod-vcenter1/
│   └── client-b/
│       └── prod-vcenter2/
├── processed/                # Archived processed files
├── powerbi_outputs/          # Generated Power BI files
├── instance/                 # SQLite database
├── app.py                    # Flask application
├── main.py                   # Application entry point
├── config.py                 # Configuration settings
├── models.py                 # Database models
└── start_local.py            # Local setup script
```

## Stopping the Application

Press `Ctrl+C` in the terminal where the application is running.

## Troubleshooting

### Common Issues

1. **Port 5000 already in use:**
   ```bash
   # Find and kill process using port 5000
   sudo lsof -i :5000
   sudo kill -9 <PID>
   ```

2. **Permission errors:**
   ```bash
   # Make sure you have write permissions
   chmod 755 ansible_outputs processed powerbi_outputs
   ```

3. **Python version issues:**
   ```bash
   # Use specific Python version
   python3.11 start_local.py
   ```

4. **Dependencies not installing:**
   ```bash
   # Upgrade pip first
   python -m pip install --upgrade pip
   ```

### Log Files

Check application logs in:
- Terminal output (when running with `python main.py`)
- Dashboard logs page: http://localhost:5000/logs

## Next Steps

1. **Configure your environments** in `config.py`
2. **Set up your Ansible playbooks** to save files in the correct structure  
3. **Schedule regular Ansible runs** using cron or task scheduler
4. **Import generated files** into Power BI for visualization

## Production Deployment

For production deployment, see the main README.md file for:
- PostgreSQL database setup
- Gunicorn configuration
- Environment variable management
- Security considerations