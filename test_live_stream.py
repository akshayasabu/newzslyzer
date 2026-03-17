#!/usr/bin/env python
"""Test script to verify live stream route is accessible"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_live_stream_route():
    """Test if the live stream route is accessible"""
    
    with app.test_client() as client:
        # Test without authentication (should redirect to landing)
        print("\n" + "="*60)
        print("Test 1: Accessing /live-stream without authentication")
        print("="*60)
        
        response = client.get('/live-stream', follow_redirects=False)
        print(f"Status Code: {response.status_code}")
        print(f"Location: {response.headers.get('Location', 'N/A')}")
        
        if response.status_code == 302:
            print("✓ Correctly redirects to landing page when not authenticated")
        else:
            print("✗ Unexpected response")
        
        # Test with authentication
        print("\n" + "="*60)
        print("Test 2: Accessing /live-stream with authentication")
        print("="*60)
        
        with client.session_transaction() as sess:
            sess['user'] = 'test_user'
            sess['user_id'] = 1
            sess['role'] = 'user'
        
        response = client.get('/live-stream', follow_redirects=False)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Successfully accessed live stream page")
            
            # Check if the response contains expected content
            html = response.data.decode('utf-8')
            
            checks = [
                ('Live Stream title', 'Live Stream' in html or 'live-stream' in html),
                ('YouTube iframe', 'youtube.com/embed' in html),
                ('Video wrapper', 'video-wrapper' in html),
                ('Live badge', 'live-badge' in html or 'LIVE' in html),
            ]
            
            print("\nContent Checks:")
            for check_name, result in checks:
                status = "✓" if result else "✗"
                print(f"  {status} {check_name}: {'Found' if result else 'Not Found'}")
                
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
        
        # Test route registration
        print("\n" + "="*60)
        print("Test 3: Checking route registration")
        print("="*60)
        
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        live_stream_routes = [r for r in routes if 'live-stream' in r or 'live_stream' in r]
        
        if live_stream_routes:
            print("✓ Live stream route is registered:")
            for route in live_stream_routes:
                print(f"  - {route}")
        else:
            print("✗ Live stream route not found in registered routes")
            print("\nAll registered routes:")
            for route in sorted(routes):
                if not route.startswith('/static'):
                    print(f"  - {route}")

if __name__ == "__main__":
    test_live_stream_route()
