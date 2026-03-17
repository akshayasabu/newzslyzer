from app import app, db, User
from werkzeug.security import generate_password_hash
with app.app_context():
    user = User.query.filter_by(username='user_demo').first()
    if user:
        user.password_hash = generate_password_hash('Password123!')
        db.session.commit()
        print("Password reset for user_demo to 'Password123!'")
    else:
        print("user_demo not found")
