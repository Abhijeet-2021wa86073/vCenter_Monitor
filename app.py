import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///vcenter_processor.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import routes after app creation to avoid circular imports
from routes.dashboard import dashboard_bp
from routes.api import api_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp, url_prefix='/api')

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Initialize background services
    from services.scheduler import init_scheduler
    from services.file_watcher import start_file_watcher
    
    # Start scheduler
    init_scheduler(app)
    
    # Start file watcher in a separate thread
    import threading
    watcher_thread = threading.Thread(target=start_file_watcher, daemon=True)
    watcher_thread.start()
