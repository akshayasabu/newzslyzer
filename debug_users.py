from app import app, db, User

with app.app_context():
    users = User.query.all()
    print(f"{'Username':<20} | {'Role':<10} | {'Email'}")
    print("-" * 50)
    for user in users:
        print(f"{user.username:<20} | {user.role:<10} | {user.email}")
