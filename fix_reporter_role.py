from app import app, db, User

with app.app_context():
    reporter = User.query.filter_by(username='reporter').first()
    if reporter:
        reporter.role = 'reporter'
        db.session.commit()
        print(f"Fixed role for {reporter.username}. New role: {reporter.role}")
    else:
        print("Reporter user not found.")
