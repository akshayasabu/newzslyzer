from app import app, db, User, Advertisement
from werkzeug.security import generate_password_hash
import sys

with app.app_context():
    u = User.query.filter_by(username='test_adv').first()
    if not u:
        u = User(username='test_adv', email='test@adv.com', password_hash=generate_password_hash('Test@123'), role='advertiser', full_name='Test Advertiser')
        db.session.add(u)
        db.session.commit()
        print('User test_adv created')
    else:
        print('User test_adv already exists')
    
    ad = Advertisement.query.filter_by(user_id=u.id).first()
    if not ad:
        ad = Advertisement(
            company_name='Test Co', 
            title='Test Active Campaign', 
            image_url='https://placehold.co/600x400', 
            target_url='https://example.com', 
            active=True, 
            user_id=u.id, 
            status='approved', 
            plan_name='Plan 1'
        )
        db.session.add(ad)
        db.session.commit()
        print('One ad created for test_adv')
    else:
        print('Ad already exists for test_adv')
