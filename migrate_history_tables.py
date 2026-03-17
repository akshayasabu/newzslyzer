from app import app, db, ReadingHistory, UserPreference, Notification
import os

with app.app_context():
    # Only create new tables if they don't exist
    db.create_all()
    print("New tables (ReadingHistory, UserPreference, Notification) created successfully.")
