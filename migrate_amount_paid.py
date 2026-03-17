from app import app, db, Advertisement
import sqlalchemy as sa

def migrate():
    with app.app_context():
        # Check if column exists
        inspector = sa.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('advertisement')]
        
        if 'amount_paid' not in columns:
            print("Adding 'amount_paid' column...")
            db.session.execute(sa.text('ALTER TABLE advertisement ADD COLUMN amount_paid VARCHAR(50)'))
            db.session.commit()
            print("Column added successfully.")
        else:
            print("'amount_paid' column already exists.")

if __name__ == "__main__":
    migrate()
