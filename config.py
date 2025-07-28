import os

class Config:
    # File watcher settings
    WATCH_DIRECTORY = os.environ.get('WATCH_DIRECTORY', './ansible_outputs')
    PROCESSED_DIRECTORY = os.environ.get('PROCESSED_DIRECTORY', './processed')
    OUTPUT_DIRECTORY = os.environ.get('OUTPUT_DIRECTORY', './powerbi_outputs')
    
    # Multi-environment settings
    ENVIRONMENT_MAPPING = {
        # Map directory patterns or file patterns to environments
        # Format: {"pattern": {"environment": "env_name", "client": "client_name"}}
        "prod-vcenter1": {"environment": "production-vc1", "client": "client-a"},
        "prod-vcenter2": {"environment": "production-vc2", "client": "client-b"},
        "dev-vcenter": {"environment": "development", "client": "internal"},
        "test-vcenter": {"environment": "testing", "client": "internal"}
    }
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = ['.json', '.yaml', '.yml']
    
    # Processing settings
    BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '100'))
    MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', '50'))
    
    # Scheduler settings
    PROCESSING_INTERVAL_MINUTES = int(os.environ.get('PROCESSING_INTERVAL_MINUTES', '5'))
    CLEANUP_INTERVAL_HOURS = int(os.environ.get('CLEANUP_INTERVAL_HOURS', '24'))
    RETENTION_DAYS = int(os.environ.get('RETENTION_DAYS', '30'))
    
    # Export settings
    EXPORT_FORMATS = ['csv', 'excel', 'json']
    INCLUDE_HEADERS = True
    SEPARATE_BY_ENVIRONMENT = True  # Generate separate files per environment/client
    
    @staticmethod
    def ensure_directories():
        """Ensure all required directories exist"""
        import os
        directories = [
            Config.WATCH_DIRECTORY,
            Config.PROCESSED_DIRECTORY,
            Config.OUTPUT_DIRECTORY
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
