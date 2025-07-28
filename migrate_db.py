#!/usr/bin/env python3
"""
Database migration script to add multi-environment support
"""
import os
import sqlite3
from app import app, db

def migrate_database():
    """Migrate the database to add multi-environment columns"""
    
    with app.app_context():
        # Check if columns already exist
        try:
            # Test if new columns exist by running a simple query
            result = db.session.execute(db.text("SELECT vcenter_environment FROM processing_job LIMIT 1"))
            print("Migration not needed - columns already exist")
            return
        except Exception:
            print("Migration needed - adding new columns")
        
        # Add new columns to processing_job table
        try:
            db.session.execute(db.text("ALTER TABLE processing_job ADD COLUMN vcenter_environment VARCHAR(100)"))
            db.session.execute(db.text("ALTER TABLE processing_job ADD COLUMN client_name VARCHAR(100)"))
            db.session.execute(db.text("ALTER TABLE processing_job ADD COLUMN datacenter VARCHAR(100)"))
            print("Added columns to processing_job table")
        except Exception as e:
            print(f"Error adding columns to processing_job: {e}")
        
        # Add new columns to vm_record table
        try:
            db.session.execute(db.text("ALTER TABLE vm_record ADD COLUMN vcenter_environment VARCHAR(100)"))
            db.session.execute(db.text("ALTER TABLE vm_record ADD COLUMN client_name VARCHAR(100)"))
            print("Added columns to vm_record table")
        except Exception as e:
            print(f"Error adding columns to vm_record: {e}")
        
        # Add new columns to alarm_record table
        try:
            db.session.execute(db.text("ALTER TABLE alarm_record ADD COLUMN vcenter_environment VARCHAR(100)"))
            db.session.execute(db.text("ALTER TABLE alarm_record ADD COLUMN client_name VARCHAR(100)"))
            print("Added columns to alarm_record table")
        except Exception as e:
            print(f"Error adding columns to alarm_record: {e}")
        
        # Commit changes
        db.session.commit()
        print("Database migration completed successfully")

if __name__ == "__main__":
    migrate_database()