from app import app, db
import sqlalchemy as sa

with app.app_context():
    print("Attempting to force sync...")
    # This will drop the table if it exists and recreate it with the correct columns
    db.engine.execute(sa.text('DROP TABLE IF EXISTS subscription_request CASCADE'))
    db.create_all()
    print("Database schema reset successfully!")
