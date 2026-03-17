from app import app, db, User

def seed_reporters():
    with app.app_context():
        # List of 7 mock reporters with full details
        reporters_data = [
            {
                "username": "sarah_news",
                "email": "sarah.j@auranews.com",
                "full_name": "Sarah Jenkins",
                "phone": "+1 (555) 010-1234",
                "location": "New York, USA",
                "bio": "Senior investigative journalist covering politics and urban development.",
                "picture": "/static/img/default_avatar.png"
            },
            {
                "username": "rahul_kochi",
                "email": "rahul.v@auranews.com",
                "full_name": "Rahul Varma",
                "phone": "+91 98460 12345",
                "location": "Kochi, Kerala",
                "bio": "Focusing on local Kerala politics and environmental issues.",
                "picture": "/static/img/default_avatar.png"
            },
            {
                "username": "fatima_tech",
                "email": "fatima.z@auranews.com",
                "full_name": "Fatima Zahra",
                "phone": "+971 50 123 4567",
                "location": "Dubai, UAE",
                "bio": "Tech correspondent specializing in AI and emerging markets.",
                "picture": "/static/img/default_avatar.png"
            },
            {
                "username": "david_london",
                "email": "david.b@auranews.com",
                "full_name": "David Baker",
                "phone": "+44 20 7946 0987",
                "location": "London, UK",
                "bio": "Covering European economics and post-Brexit trade deals.",
                "picture": "/static/img/default_avatar.png"
            },
            {
                "username": "mei_ling",
                "email": "mei.l@auranews.com",
                "full_name": "Mei Ling",
                "phone": "+86 10 1234 5678",
                "location": "Shanghai, China",
                "bio": "Lifestyle and cultural reporter for East Asia.",
                "picture": "/static/img/default_avatar.png"
            },
            {
                "username": "carlos_sports",
                "email": "carlos.r@auranews.com",
                "full_name": "Carlos Rodriguez",
                "phone": "+34 91 123 45 67",
                "location": "Madrid, Spain",
                "bio": "Sports analyst covering football and international athletics.",
                "picture": "/static/img/default_avatar.png"
            },
            {
                "username": "aisha_nairobi",
                "email": "aisha.m@auranews.com",
                "full_name": "Aisha Mbogo",
                "phone": "+254 712 345678",
                "location": "Nairobi, Kenya",
                "bio": "Reporting on African innovation and sustainable development.",
                "picture": "/static/img/default_avatar.png"
            }
        ]

        print("--- Seeding Reporters ---")
        for data in reporters_data:
            # Check if user exists
            existing_user = User.query.filter_by(username=data["username"]).first()
            if existing_user:
                print(f"User {data['username']} already exists. Not overwriting details.")
                # Ensure they are still a reporter, just in case
                if existing_user.role != 'reporter':
                     existing_user.role = 'reporter'
            else:
                print(f"Creating new reporter: {data['username']}")
                new_reporter = User(
                    username=data["username"],
                    email=data["email"],
                    full_name=data["full_name"],
                    role='reporter',
                    phone=data["phone"],
                    location=data["location"],
                    bio=data["bio"],
                    picture=data["picture"]
                )
                new_reporter.set_password('Reporter@123') # Default password
                db.session.add(new_reporter)
        
        db.session.commit()
        print("--- Seeding Complete ---")

if __name__ == "__main__":
    seed_reporters()
