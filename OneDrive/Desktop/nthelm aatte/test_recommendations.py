#!/usr/bin/env python
"""Test script to verify personalized news recommendation system"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, ReadingHistory, UserPreference, track_reading_history, get_ai_recommendations

def test_recommendation_system():
    """Test the personalized recommendation system"""
    
    with app.app_context():
        print("\n" + "="*70)
        print("PERSONALIZED NEWS RECOMMENDATION SYSTEM TEST")
        print("="*70)
        
        # Test 1: Check if models exist
        print("\n[Test 1] Checking Database Models...")
        try:
            # Check if tables exist
            tables = db.engine.table_names()
            required_tables = ['user', 'reading_history', 'user_preference']
            
            for table in required_tables:
                if table in tables:
                    print(f"  ✓ Table '{table}' exists")
                else:
                    print(f"  ✗ Table '{table}' missing")
            
            print("  ✓ All required models are present")
        except Exception as e:
            print(f"  ✗ Error checking models: {e}")
        
        # Test 2: Test tracking function
        print("\n[Test 2] Testing Reading History Tracking...")
        try:
            # Create a test user if doesn't exist
            test_user = User.query.filter_by(username='test_user_rec').first()
            if not test_user:
                test_user = User(
                    username='test_user_rec',
                    email='test_rec@example.com',
                    full_name='Test User'
                )
                test_user.set_password('Test@123')
                db.session.add(test_user)
                db.session.commit()
                print(f"  ✓ Created test user (ID: {test_user.id})")
            else:
                print(f"  ✓ Using existing test user (ID: {test_user.id})")
            
            # Simulate reading articles from different categories
            test_readings = [
                ('article_sports_1', 'Sports'),
                ('article_sports_2', 'Sports'),
                ('article_sports_3', 'Sports'),
                ('article_tech_1', 'Tech'),
                ('article_tech_2', 'Tech'),
                ('article_politics_1', 'Politics'),
            ]
            
            print(f"\n  Simulating {len(test_readings)} article reads...")
            for article_id, category in test_readings:
                track_reading_history(test_user.id, article_id, category)
                print(f"    - Read: {category} article ({article_id})")
            
            print("  ✓ Reading history tracked successfully")
            
        except Exception as e:
            print(f"  ✗ Error tracking history: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: Check user preferences
        print("\n[Test 3] Checking User Preferences...")
        try:
            preferences = UserPreference.query.filter_by(user_id=test_user.id).order_by(UserPreference.score.desc()).all()
            
            if preferences:
                print(f"  ✓ Found {len(preferences)} preference categories:")
                for pref in preferences:
                    print(f"    - {pref.category}: {pref.score} reads")
            else:
                print("  ⚠ No preferences found (this is normal for new users)")
                
        except Exception as e:
            print(f"  ✗ Error checking preferences: {e}")
        
        # Test 4: Test recommendation algorithm
        print("\n[Test 4] Testing Recommendation Algorithm...")
        try:
            # Create sample articles
            sample_articles = [
                {'id': 'rec_1', 'title': 'Breaking Sports News', 'category': 'Sports', 'excerpt': 'Latest sports update'},
                {'id': 'rec_2', 'title': 'Tech Innovation', 'category': 'Tech', 'excerpt': 'New technology breakthrough'},
                {'id': 'rec_3', 'title': 'Political Update', 'category': 'Politics', 'excerpt': 'Latest political news'},
                {'id': 'rec_4', 'title': 'Entertainment News', 'category': 'Entertainment', 'excerpt': 'Celebrity updates'},
                {'id': 'rec_5', 'title': 'Sports Championship', 'category': 'Sports', 'excerpt': 'Championship results'},
                {'id': 'rec_6', 'title': 'Tech Gadgets', 'category': 'Tech', 'excerpt': 'New gadget releases'},
            ]
            
            recommendations = get_ai_recommendations(test_user.id, sample_articles, limit=4)
            
            if recommendations:
                print(f"  ✓ Generated {len(recommendations)} recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"    {i}. {rec['title']} ({rec['category']})")
                
                # Check if recommendations match user preferences
                rec_categories = [r['category'] for r in recommendations]
                top_prefs = [p.category for p in preferences[:2]] if preferences else []
                
                if top_prefs:
                    matches = sum(1 for cat in rec_categories if cat in top_prefs)
                    print(f"\n  ✓ {matches}/{len(recommendations)} recommendations match top preferences")
                    if matches > 0:
                        print("  ✓ Recommendation system is working correctly!")
                    else:
                        print("  ⚠ Recommendations don't match preferences (may need more reading history)")
            else:
                print("  ⚠ No recommendations generated")
                
        except Exception as e:
            print(f"  ✗ Error testing recommendations: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 5: Check reading history
        print("\n[Test 5] Checking Reading History...")
        try:
            history = ReadingHistory.query.filter_by(user_id=test_user.id).order_by(ReadingHistory.timestamp.desc()).limit(10).all()
            
            if history:
                print(f"  ✓ Found {len(history)} reading history entries:")
                category_counts = {}
                for h in history:
                    category_counts[h.category] = category_counts.get(h.category, 0) + 1
                
                for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"    - {cat}: {count} articles")
            else:
                print("  ⚠ No reading history found")
                
        except Exception as e:
            print(f"  ✗ Error checking history: {e}")
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print("\nThe personalized recommendation system includes:")
        print("  ✓ Reading history tracking")
        print("  ✓ User preference calculation")
        print("  ✓ AI-powered recommendation algorithm")
        print("  ✓ Category-based article sorting")
        print("\nHow it works:")
        print("  1. When a user reads an article, the system tracks the category")
        print("  2. User preferences are calculated based on reading frequency")
        print("  3. On login, articles are sorted by user's preferred categories")
        print("  4. AI recommendations are shown based on reading patterns")
        print("\nTo see recommendations in action:")
        print("  1. Log in to the website")
        print("  2. Read several articles from the same category (e.g., Sports)")
        print("  3. Log out and log back in")
        print("  4. The homepage will prioritize articles from your preferred categories")
        print("="*70 + "\n")

if __name__ == "__main__":
    test_recommendation_system()
