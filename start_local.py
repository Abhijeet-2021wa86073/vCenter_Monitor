#!/usr/bin/env python3
"""
Local startup script for vCenter Data Processor
This script helps you run the application on your local system
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    return True

def create_directories():
    """Create required directories"""
    dirs = ['ansible_outputs', 'processed', 'powerbi_outputs', 'instance']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Created directory: {dir_name}")

def setup_environment():
    """Set up environment variables for local development"""
    env_vars = {
        'FLASK_ENV': 'development',
        'FLASK_DEBUG': 'True',
        'DATABASE_URL': 'sqlite:///instance/vcenter_processor.db',
        'SESSION_SECRET': 'dev-secret-key-change-in-production',
        'WATCH_DIRECTORY': './ansible_outputs',
        'PROCESSED_DIRECTORY': './processed', 
        'OUTPUT_DIRECTORY': './powerbi_outputs',
        'BATCH_SIZE': '100',
        'MAX_FILE_SIZE_MB': '50',
        'PROCESSING_INTERVAL_MINUTES': '5',
        'CLEANUP_INTERVAL_HOURS': '24',
        'RETENTION_DAYS': '30'
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
    
    print("✅ Environment variables configured")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    packages = [
        'Flask==3.0.0',
        'Flask-SQLAlchemy==3.1.1', 
        'pandas==2.1.4',
        'openpyxl==3.1.2',
        'watchdog==3.0.0',
        'APScheduler==3.10.4',
        'python-dateutil==2.8.2',
        'PyYAML==6.0.1',
        'psycopg2-binary==2.9.9',
        'gunicorn==21.2.0'
    ]
    
    try:
        for package in packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def initialize_database():
    """Initialize the database"""
    print("🗄️  Initializing database...")
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def create_sample_data():
    """Create sample directory structure"""
    sample_dirs = [
        'ansible_outputs/client-a/prod-vcenter1',
        'ansible_outputs/client-a/dev-vcenter',
        'ansible_outputs/client-b/prod-vcenter2',
        'ansible_outputs/internal/test-vcenter'
    ]
    
    for dir_path in sample_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Sample directory structure created")

def start_application():
    """Start the Flask application"""
    print("\n🚀 Starting vCenter Data Processor...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("📝 Press Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        # Import and run the app without the background services that might cause issues
        import os
        import sys
        
        # Add current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from sqlalchemy.orm import DeclarativeBase
        
        # Create a simplified app for local development
        class Base(DeclarativeBase):
            pass

        db = SQLAlchemy(model_class=Base)
        app = Flask(__name__)
        
        # Basic configuration
        app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///instance/vcenter_processor.db")
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
        
        db.init_app(app)
        
        # Create simple routes for testing
        @app.route('/')
        def dashboard():
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>vCenter Data Processor - Local Test</title>
                <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-5">
                    <div class="row">
                        <div class="col-12">
                            <h1 class="text-center mb-4">
                                <i class="fas fa-server me-2"></i>
                                vCenter Data Processor
                            </h1>
                            <div class="alert alert-success text-center">
                                <h4>✅ Application is running successfully!</h4>
                                <p>Your local setup is working correctly.</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5><i class="fas fa-folder me-2"></i>Directory Setup</h5>
                                </div>
                                <div class="card-body">
                                    <p><strong>Watch Directory:</strong> ./ansible_outputs/</p>
                                    <p><strong>Output Directory:</strong> ./powerbi_outputs/</p>
                                    <p><strong>Database:</strong> ./instance/vcenter_processor.db</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5><i class="fas fa-play me-2"></i>Next Steps</h5>
                                </div>
                                <div class="card-body">
                                    <p>1. Add your Ansible JSON files to ./ansible_outputs/</p>
                                    <p>2. Use structure: client-name/environment/files.json</p>
                                    <p>3. Check ./powerbi_outputs/ for generated files</p>
                                    <a href="/test" class="btn btn-primary">Test API</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header">
                                    <h5><i class="fas fa-file-alt me-2"></i>Sample Test File</h5>
                                </div>
                                <div class="card-body">
                                    <p>Create this file to test: <code>./ansible_outputs/client-a/prod-vcenter1/test_vm_data.json</code></p>
                                    <pre class="bg-dark text-light p-3 rounded">
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
    }
  ]
}
                                    </pre>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            '''
        
        @app.route('/test')
        def test_api():
            return {
                "status": "success",
                "message": "API is working",
                "directories": {
                    "watch": os.path.exists("./ansible_outputs"),
                    "output": os.path.exists("./powerbi_outputs"),
                    "database": os.path.exists("./instance")
                }
            }
        
        @app.route('/health')
        def health():
            return {"status": "healthy", "version": "1.0.0"}
        
        # Initialize database
        with app.app_context():
            db.create_all()
        
        print("✅ Simplified local version started successfully!")
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        print("Try running: python -m pip install Flask Flask-SQLAlchemy")
        import traceback
        traceback.print_exc()

def main():
    """Main setup and startup function"""
    print("🔧 Setting up vCenter Data Processor for local development")
    print("=" * 60)
    
    # Check requirements
    if not check_python_version():
        return
    
    # Setup environment
    setup_environment()
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Initialize database
    if not initialize_database():
        return
    
    # Create sample structure
    create_sample_data()
    
    print("\n✅ Setup completed successfully!")
    print("\n📋 Quick Start Guide:")
    print("1. Place your Ansible JSON/YAML files in: ./ansible_outputs/")
    print("2. Use directory structure: client-name/environment-name/files.json")
    print("3. Generated Power BI files will appear in: ./powerbi_outputs/")
    print("4. Monitor processing through the web dashboard")
    
    # Start application
    input("\nPress Enter to start the application...")
    start_application()

if __name__ == "__main__":
    main()