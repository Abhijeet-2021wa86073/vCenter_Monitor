#!/usr/bin/env python3
"""
Simplified local version of vCenter Data Processor
This runs without background services to help troubleshoot local issues
"""
import os
import sys
from pathlib import Path

def setup_directories():
    """Create required directories"""
    dirs = ['ansible_outputs', 'powerbi_outputs', 'instance']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Directory: {dir_name}")

def run_simple_app():
    """Run a simplified version of the app"""
    print("🔧 Starting simplified vCenter Data Processor...")
    
    # Setup directories
    setup_directories()
    
    try:
        from flask import Flask, jsonify
        from flask_sqlalchemy import SQLAlchemy
        from sqlalchemy.orm import DeclarativeBase
        
        class Base(DeclarativeBase):
            pass

        db = SQLAlchemy(model_class=Base)
        app = Flask(__name__)
        
        # Configuration
        app.secret_key = "dev-secret-key"
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/vcenter_processor.db"
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
        
        db.init_app(app)
        
        @app.route('/')
        def home():
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>vCenter Data Processor - Local Test</title>
                <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-5">
                    <div class="text-center">
                        <h1><i class="fas fa-server me-2"></i>vCenter Data Processor</h1>
                        <div class="alert alert-success mt-4">
                            <h4>✅ Local setup is working!</h4>
                            <p>Your application is running correctly on localhost:5000</p>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5><i class="fas fa-folder-open me-2"></i>Directory Structure</h5>
                                </div>
                                <div class="card-body">
                                    <p><strong>Input:</strong> ./ansible_outputs/</p>
                                    <p><strong>Output:</strong> ./powerbi_outputs/</p>
                                    <p><strong>Database:</strong> ./instance/vcenter_processor.db</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5><i class="fas fa-play-circle me-2"></i>Test Your Setup</h5>
                                </div>
                                <div class="card-body">
                                    <p>1. Create directory: ./ansible_outputs/client-a/prod-vcenter1/</p>
                                    <p>2. Add a JSON file with VM data</p>
                                    <p>3. Check API status: <a href="/api/health">/api/health</a></p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-code me-2"></i>Sample VM Data File</h5>
                            </div>
                            <div class="card-body">
                                <p>Save this as: <code>./ansible_outputs/client-a/prod-vcenter1/test_vms.json</code></p>
                                <pre class="bg-dark text-light p-3 rounded small">{{
  "vms": [
    {{
      "name": "web-server-01",
      "uuid": "50322a7e-8f9a-4b5c-9d6e-1f2a3b4c5d6e",
      "power_state": "poweredOn",
      "cpu_count": 4,
      "memory_mb": 8192,
      "disk_gb": 100.5,
      "guest_os": "CentOS 8",
      "host_name": "esxi-host-01.company.com",
      "cluster_name": "Production-Cluster",
      "datacenter_name": "Primary-DC"
    }}
  ]
}}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            '''
        
        @app.route('/api/health')
        def health():
            return jsonify({
                "status": "healthy",
                "version": "1.0.0-local",
                "directories": {
                    "ansible_outputs": os.path.exists("./ansible_outputs"),
                    "powerbi_outputs": os.path.exists("./powerbi_outputs"),
                    "instance": os.path.exists("./instance")
                }
            })
        
        @app.route('/api/test')
        def test():
            return jsonify({
                "message": "Local test API is working",
                "directories_created": True,
                "database_ready": True
            })
        
        # Initialize database
        with app.app_context():
            db.create_all()
        
        print("✅ Application started successfully!")
        print("📊 Open your browser to: http://localhost:5000")
        print("🔍 Health check: http://localhost:5000/api/health")
        print("⏹️  Press Ctrl+C to stop")
        print("-" * 50)
        
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except ImportError as e:
        print(f"❌ Missing required packages: {e}")
        print("Run: pip install Flask Flask-SQLAlchemy")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_simple_app()