from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from authlib.integrations.flask_client import OAuth
import re
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import hashlib
import time
import random
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import smtplib
import copy
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import cv2
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Allow insecure transport for local development (Google OAuth)
if os.getenv("FLASK_ENV") == "development":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


# Database Configuration
import os
basedir = os.path.abspath(os.path.dirname(__file__))
# Ensure instance folder exists
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'aura.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# NewsAPI Configuration
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Temporary Cache for Live Articles
live_article_cache = {}

# Topic mapping for Google News RSS
TOPIC_MAP = {
    'global': 'https://news.google.com/rss/headlines/section/topic/WORLD',
    'business': 'https://news.google.com/rss/headlines/section/topic/BUSINESS',
    'tech': 'https://news.google.com/rss/headlines/section/topic/TECHNOLOGY',
    'technology': 'https://news.google.com/rss/headlines/section/topic/TECHNOLOGY',
    'science': 'https://news.google.com/rss/headlines/section/topic/SCIENCE',
    'health': 'https://news.google.com/rss/headlines/section/topic/HEALTH',
    'sports': 'https://news.google.com/rss/headlines/section/topic/SPORTS',
    'entertainment': 'https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT',
    'movies': 'https://news.google.com/rss/search?q=Movies',
    'music': 'https://news.google.com/rss/search?q=Music',
    'travel': 'https://news.google.com/rss/search?q=Travel',
    'auto': 'https://news.google.com/rss/headlines/section/topic/AUTO',
    'food': 'https://news.google.com/rss/search?q=Food',
    'agri': 'https://news.google.com/rss/search?q=Agriculture',
    'kerala': 'https://news.google.com/rss/search?q=Kerala+News+-Lottery',
    'local': 'https://news.google.com/rss/search?q=Kerala+India+Local+News',
    'lifestyle': 'https://news.google.com/rss/headlines/section/topic/LIFESTYLE',
    'news': 'https://news.google.com/rss/headlines',
    'astro': 'https://news.google.com/rss/search?q=Astrology',
    'career': 'https://news.google.com/rss/search?q=Career+Advice',
    'videos': 'https://news.google.com/rss/search?q=News+Videos',
    'podcast': 'https://news.google.com/rss/search?q=Podcasts',
    'games': 'https://news.google.com/rss/search?q=Gaming+News',
    'events': 'https://news.google.com/rss/search?q=Events+Near+Me',
    'life': 'https://news.google.com/rss/search?q=Lifestyle',
    'mkid': 'https://news.google.com/rss/search?q=Kids+News',
    'factcheck': 'https://news.google.com/rss/search?q=Fact+Check',
    'webstories': 'https://news.google.com/rss/search?q=Visual+Stories',
    'graphics': 'https://news.google.com/rss/search?q=Infographics+News',
    'smartpicks': 'https://news.google.com/rss/search?q=Recommendations',
    'shortz': 'https://news.google.com/rss/search?q=Breaking+News+Shorts',
    'photogallery': 'https://news.google.com/rss/search?q=News+Photos',
    'doodles': 'https://news.google.com/rss/search?q=Google+Doodles',
    'topics': 'https://news.google.com/rss/topics'
}


def get_dynamic_news_image(title, category, unique_id=None):
    """Returns a unique, relevant image URL based on highly specific title keywords mixed with title content."""
    import hashlib
    import re
    import time
    
    title_lower = title.lower()
    
    # Highly specific entities and themes
    topic_keywords = {
        # Sports Events & Teams
        't20 world cup': 'cricket,match',
        'world cup': 'stadium,match',
        'ipl': 'cricket,stadium',
        'icc': 'cricket',
        'premier league': 'football,action',
        'grand slam': 'tennis,court',
        'olympics': 'olympics,stadium',
        'nba': 'basketball',
        'wimbledon': 'tennis,court',
        # Sports Stars
        'dhoni': 'dhoni,cricket',
        'messi': 'messi,football',
        'ronaldo': 'ronaldo,football',
        'kohli': 'kohli,cricket',
        'neymar': 'neymar,football',
        'curry': 'curry,nba',
        'lebron': 'lebron,nba',
        # Tech Giants & Personalities
        'musk': 'musk,spacex',
        'zuckerberg': 'zuckerberg,meta',
        'cook': 'apple,tech',
        'nvidia': 'nvidia,chip',
        'openai': 'ai,robot',
        'chatgpt': 'ai,technology',
        'metaverse': 'vr,tech',
        # Politics & Nations
        'modi': 'modi,india',
        'trump': 'trump,politics',
        'biden': 'whitehouse,biden',
        'putin': 'russia,politics',
        'peace': 'peace,white',
        # Diverse Themes
        'cricket': 'cricket',
        'football': 'football,stadium',
        'basketball': 'basketball',
        'tennis': 'tennis',
        'soccer': 'soccer',
        'formula 1': 'f1,racing',
        'f1': 'f1,racing',
        'bollywood': 'bollywood',
        'hollywood': 'hollywood,cinema',
        'nasa': 'space,rocket',
        'isro': 'isro,rocket',
        'spacex': 'spacex,rocket',
        'mars': 'mars,planet',
        'iphone': 'iphone,apple',
        'galaxy': 'samsung,phone',
        'bitcoin': 'bitcoin,crypto',
        'crypto': 'cryptocurrency',
        'gold': 'gold,wealth',
        'stock market': 'stocks,trading',
        'economy': 'money,finance',
        'weather': 'weather,forecast',
        ' storm ': 'storm',
        ' cyclone ': 'cyclone',
        'earthquake': 'earthquake',
        'flood': 'flood,water',
        'election': 'election,vote',
        ' war ': 'war,conflict',
        ' army ': 'army,military',
        ' vaccine ': 'medical',
        'hospital': 'hospital,doctor',
        'science': 'science',
        'energy': 'energy,power',
        'climate': 'climate,nature',
        'wildlife': 'animal,nature',
        'tourism': 'travel,vacation',
        'flight': 'airplane,flight',
        'recipe': 'food,cooking',
        'restaurant': 'food,dining'
    }

    found_keywords = []
    # Check for specific entities
    for key, val in topic_keywords.items():
        if key in title_lower:
            found_keywords.append(val)
            break 

    # Extract ONE dynamic word from title for uniqueness
    noise = ['news', 'latest', 'breaking', 'india', 'world', 'update', 'share', 'today', 'live', 'high', 'hold', 'off', 'brave', 'near', 'after', 'with', 'from', 'says', 'will', 'were', 'been', 'about', 'some', 'more', 'they', 'into', 'just']
    words = [w for w in re.split(r'\W+', title_lower) if len(w) > 4 and w not in noise]
    
    unique_tag = words[0] if words else ''

    if not found_keywords:
        if category:
            cat_lower = category.lower()
            if 'sports' in cat_lower:
                found_keywords.append('sports')
            elif 'movies' in cat_lower or 'entertainment' in cat_lower:
                found_keywords.append('cinema')
            elif 'tech' in cat_lower:
                found_keywords.append('technology')
            elif 'health' in cat_lower:
                found_keywords.append('medical')
            elif 'market' in cat_lower or 'economy' in cat_lower:
                found_keywords.append('finance')
            else:
                found_keywords.append(cat_lower.split()[0] if cat_lower else 'news')
        else:
            found_keywords.append('news')

    # Combine all - simplify to max 2 tags for better matching
    final_tags = []
    if found_keywords:
        primary = found_keywords[0].split(',')[0]
        final_tags.append(primary)
    
    if unique_tag and len(final_tags) < 2:
        final_tags.append(unique_tag)
    
    search_query = ','.join(final_tags)
    if not search_query:
        search_query = 'news'

    # Generate a TRULY unique seed for each article
    # Combine title, category, unique_id, and a hash of the full title for maximum uniqueness
    if unique_id:
        seed_str = f"{title}{category or ''}{unique_id}"
    else:
        # If no unique_id, use the full title hash to ensure uniqueness
        seed_str = f"{title}{category or ''}{hashlib.sha256(title.encode()).hexdigest()[:16]}"
    
    # Create a large seed range to avoid collisions
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % 999999
    
    # Use multiple parameters to force different images
    # Add random parameter to prevent caching issues
    random_param = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % 10000
    
    return f"https://loremflickr.com/1200/800/{search_query}?lock={seed}&random={random_param}"

def fetch_gn_rss(url):
    import xml.etree.ElementTree as ET
    from datetime import datetime
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        res = requests.get(url, headers=headers, timeout=12)
        res.raise_for_status()
        root = ET.fromstring(res.text)
        fetched = []
        for item in root.findall('.//item')[:100]: # limit items to prevent heavy parsing
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ''
            source = item.find('source').text if item.find('source') is not None else 'News'
            
            try:
                # parse standard RSS date: Tue, 03 Mar 2026 15:30:00 GMT
                dt = datetime.strptime(pubDate.strip(), "%a, %d %b %Y %H:%M:%S %Z")
                iso_date = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except:
                # Fallback for unexpected date formats
                iso_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            # Get the rich HTML summary from the description snippet
            desc_html = item.find('description').text if item.find('description') is not None else ''
            
            # Clean snippet for fallback display - IMPROVED for clustering
            snippet_soup = BeautifulSoup(desc_html, 'html.parser')
            
            # Extract Image URL from description if possible
            img_tag = snippet_soup.find('img')
            img_url = ''
            if img_tag and img_tag.get('src'):
                img_url = img_tag.get('src')
                # If there's a srcset, try to get a higher res one
                if img_tag.get('srcset'):
                    # Take the last one in the srcset as it's usually higher res
                    img_url = img_tag.get('srcset').split(',')[-1].split(' ')[0]
            
            # If Google News image is a 1x1 pixel or very small placeholder, ignore it
            if img_url and ('/1x1' in img_url or 'pixel' in img_url):
                img_url = ''

            if not img_url:
                # Try to find common media tags if any
                media_content = item.find('{http://search.yahoo.com/mrss/}content')
                if media_content is not None:
                    img_url = media_content.get('url')

            # 1. Identify and remove any cluster/related links (usually in <ul> or <li>)
            # These are other headlines that don't belong to our main story
            for cluster in snippet_soup.find_all(['ul', 'li', 'ol']):
                cluster.decompose()
            
            # 2. Identify the main link - if its text is identical to our headline, 
            # we might want to skip it in the snippet to avoid repetition.
            first_link_el = snippet_soup.find('a')
            if first_link_el:
                # Prioritize the direct article link from the description over the main cluster link
                direct_link = first_link_el.get('href')
                
                # CRITICAL FIX: Only use the direct link if it's NOT a generic "Full Coverage" link
                # which is often repeated across many items in a cluster.
                if direct_link and "google.com/rss/articles" in direct_link and any(x in first_link_el.get_text().lower() for x in ["full coverage", "view all", "related"]):
                    # Keep the originally found <link> instead
                    pass
                elif direct_link:
                    link = direct_link
                
                # If the link text matches the title, we decompose it so it's not in our snippet
                if first_link_el.get_text().strip() in title:
                    first_link_el.decompose()

            clean_strings = []
            title_lower_clean = title.lower().replace(' - ', ' ').replace('...', '').strip()
            
            # Search for paragraphs or list items that usually contain the snippet text
            for el in snippet_soup.find_all(['p', 'div', 'li']):
                text = el.get_text().strip()
                if not text or len(text) < 15: continue
                
                # Check for overlap with title
                low_text = text.lower().strip()
                # If the text starts with the title, strip it and take the rest
                if low_text.startswith(title_lower_clean):
                    text = text[len(title_lower_clean):].strip().lstrip(':-–— ').strip()
                
                # If it's still the title or empty, skip
                if text.lower().strip() == title_lower_clean or not text or len(text) < 10:
                    continue
                
                # Deduplicate
                if text not in clean_strings:
                    clean_strings.append(text)

            clean_snippet = ' '.join(clean_strings).strip()

            # Ensure we have something
            if not clean_strings and not clean_snippet:
                # Try stripped_strings as a last resort
                for t in snippet_soup.stripped_strings:
                    t_lower = t.lower()
                    if len(t) > 20 and t.strip() != title.strip() and 'google news' not in t_lower:
                        clean_strings.append(t)
                clean_snippet = ' '.join(clean_strings).strip()

            # Final safety check
            if not clean_snippet or len(clean_snippet) < 30:
                # If snippet is empty or too short, try to use the description without the title overlap check
                # as a last resort, just stripping HTML
                last_resort = BeautifulSoup(desc_html, 'html.parser').get_text(separator=' ', strip=True)
                # Strip title from last_resort too
                if last_resort.lower().startswith(title_lower_clean):
                    last_resort = last_resort[len(title_lower_clean):].strip().lstrip(':-–— ').strip()
                
                if len(last_resort) > 30:
                    clean_snippet = last_resort
                else:
                    # Professional brief when no snippet is available
                    clean_snippet = f"A significant development regarding '{title}' has been reported. Janavaakya is monitoring this story from its {source} feed for further updates. Stay tuned as we analyze the full implications."

            # Ensure we don't have an empty snippet
            if not clean_snippet or len(clean_snippet) < 10:
                clean_snippet = f"Latest coverage of '{title}' as reported by {source}. Our news desk is currently verifying the latest developments."

            # Limit and clean
            if '...' in clean_snippet:
                clean_snippet = clean_snippet.split('...')[0]

            fetched.append({
                'title': title,
                'url': link,
                'publishedAt': iso_date,
                'source': {'name': source},
                'description': clean_snippet[:200] + '...' if len(clean_snippet) > 200 else clean_snippet,
                'content_snippet': clean_snippet,
                'urlToImage': img_url
            })
        return fetched
    except Exception as e:
        print(f"RSS Fetch Error: {e}")
        return []

def get_article_id(article):
    """Generate a unique ID for a live article based on its URL, normalized to prevent duplicates."""
    url = article.get('url', '')
    if not url:
        # Fallback to title hash if URL is missing
        return hashlib.md5(article.get('title', '').encode()).hexdigest()
    
    # Simple normalization: remove common tracking query params
    normalized_url = url.split('?')[0].split('#')[0].strip()
    return hashlib.md5(normalized_url.encode()).hexdigest()

def clean_article_title(title):
    """Remove common source name suffixes and separators from news titles."""
    if not title:
        return title
    
    # Handle double-title syndrome (seen in some RSS sources)
    if ' - ' in title:
        parts = title.split(' - ')
        if len(parts) >= 2 and parts[0].strip() == parts[1].strip():
            title = parts[0]
    
    # Handle Google News clusters where multiple headlines are separated by semicolons
    if ';' in title:
        title = title.split(';')[0]

    # Common separators used for source names in titles
    separators = [' - ', ' | ', ' : ', ' -- ', ' \u2013 ', ' \u2014 ']
    
    for sep in separators:
        if sep in title:
            # Split and take the first part, assuming source is at the end
            parts = title.rsplit(sep, 1)
            # Only strip if the second part is significantly shorter (likely a source name)
            # or if the first part is substantial.
            if len(parts[0]) > 12:
                title = parts[0]
                break
    
    return title.strip()

def decode_google_news_url(url):
    import base64, re
    match = re.search(r'/articles/([a-zA-Z0-9_-]+)', url)
    if match:
        b64_str = match.group(1)
        b64_str += '=' * (-len(b64_str) % 4)
        try:
            decoded_str = base64.urlsafe_b64decode(b64_str).decode('utf-8', errors='ignore')
            # Look for most likely original URL patterns
            http_match = re.search(r'(https?://[^\s\x00-\x1f\x7f]+)', decoded_str)
            if http_match:
                decoded_url = http_match.group(1).split('&')[0].split('?')[0]
                return decoded_url
            
            # Fallback for newer Google News URL patterns - try to find via redirect
            try:
                # Use a specific user agent for resolution
                res_headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
                r = requests.get(url, headers=res_headers, allow_redirects=True, timeout=8)
                if r.url and "rss/articles" not in r.url:
                    return r.url
            except:
                pass
        except Exception as e:
            print(f"Decoding error for {url}: {e}")
            pass
    return url

def _get_full_article_content(url, title="", fallback_snippet="", category=None):
    """Fetch and extract the full text content from a news article URL using newspaper3k and resilient scrapers."""
    import re, json
    # Attempt to import newspaper dynamically
    try:
        from newspaper import Article as NewsArticle
        has_newspaper = True
    except ImportError:
        has_newspaper = False

    try:
        url = decode_google_news_url(url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
        }
        if not url or len(url) < 10:
            return f"<p>{fallback_snippet}</p>"
            
        if has_newspaper:
            try:
                # Add specific configurations for newspaper
                from newspaper import Config
                config = Config()
                config.browser_user_agent = headers['User-Agent']
                config.request_timeout = 10
                
                article = NewsArticle(url, config=config)
                article.download()
                article.parse()
                
                if article.text and len(article.text) > 250:
                    # Successful extraction!
                    paras = [p.strip() for p in article.text.split('\n') if len(p.strip()) > 35]
                    content_html = "".join([f"<p>{p}</p>" for p in paras])
                    
                    # Add a Fact Sheet section (Newspaper Style)
                    fact_sheet = "<div class='fact-sheet-sidebar'><h3>JANAVAAKYA FACT SHEET</h3><ul>"
                    has_facts = False
                    
                    # Extraction heuristics for newspaper-style facts
                    if article.publish_date:
                        fact_sheet += f"<li><strong>Field Verified:</strong> {article.publish_date.strftime('%B %d, %Y')}</li>"
                        has_facts = True
                    
                    if category:
                        fact_sheet += f"<li><strong>Sector:</strong> {category}</li>"
                        has_facts = True
                        
                    # Extract "Who" (Authors/Organizations)
                    if article.authors:
                        fact_sheet += f"<li><strong>Source Desk:</strong> {', '.join(article.authors[:2])}</li>"
                        has_facts = True
                    
                    fact_sheet += "</ul></div>"
                    
                    if has_facts:
                        return content_html + fact_sheet
                    return content_html
            except Exception as e:
                print(f"Newspaper3k failed for {url}: {e}")

        # Increased timeout and use a session for fallback manual scraping
        session = requests.Session()
        try:
            response = session.get(url, headers=headers, timeout=12, allow_redirects=True)
            response.raise_for_status()
        except Exception as e:
            print(f"Manual scraping failed for {url}: {e}")
            if fallback_snippet and len(fallback_snippet) > 50:
                return f"<p>{fallback_snippet}</p><p><em>Our news partners are currently syncronizing the full transcript. Summary available above.</em></p>"
            return f"<p>The full report for this development is being verified. Janavaakya correspondents are monitoring the situation.</p>"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # PRIORITIZE JSON-LD: Often contains full text even if DOM is truncated/hidden
        # Use a more robust loop to handle various JSON-LD structures
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                script_text = script.string
                if not script_text: continue
                # Handle potential common malformed patterns in JS/HTML scripts
                script_text = script_text.strip().replace('\n', ' ').replace('\r', ' ')
                data = json.loads(script_text)
                
                # Normalize to a list of items
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    if '@graph' in data:
                        items = data['@graph']
                    else:
                        items = [data]
                
                for item in items:
                    if not isinstance(item, dict): continue
                    
                    # Handle standard articles - check multiple common fields
                    body = item.get('articleBody') or item.get('text') or item.get('description') or item.get('articleSection')
                    
                    # Some sites store full content in a list of 'hasPart' or 'mainEntity'
                    if not body:
                        if 'hasPart' in item:
                            parts = item['hasPart']
                            if isinstance(parts, list):
                                body = " ".join([p.get('text', '') for p in parts if isinstance(p, dict)])
                    
                    # Handle LiveBlogPosting (Hindustan Times and others)
                    if not body and item.get('@type') in ['LiveBlogPosting', 'SocialMediaPosting'] and 'liveBlogUpdate' in item:
                        updates = item['liveBlogUpdate']
                        if isinstance(updates, list):
                            update_texts = []
                            for up in updates[:20]: # Expanded for more meat
                                u_body = up.get('articleBody') or up.get('text')
                                u_headline = up.get('headline')
                                if u_body:
                                    if u_headline and u_headline not in u_body:
                                        update_texts.append(f"<strong>{u_headline}</strong>: {u_body}")
                                    else:
                                        update_texts.append(u_body)
                            if update_texts:
                                body = "\n\n".join(update_texts)

                    if body and len(body) > 150:
                        # Success! Found a meatier version
                        try:
                            # Handle escaped unicode characters safely
                            body = body.encode('utf-8').decode('unicode-escape') if '\\u' in body else body
                        except: pass
                        
                        # Split and wrap
                        raw_paras = re.split(r'\n+', body)
                        paragraphs = []
                        for p in raw_paras:
                            p_clean = p.strip()
                            # Ensure we don't include purely generic promotional text
                            if len(p_clean) > 30 and 'Terms of' not in p_clean and 'Privacy Policy' not in p_clean:
                                paragraphs.append(p_clean)
                        
                        if len(paragraphs) > 0:
                            # Prevent TITLE repetition from the top of the body
                            # If first paragraph is the title, skip it
                            potential_title = paragraphs[0].lower().rstrip('.')
                            if potential_title in fallback_snippet.lower() or (hasattr(soup, 'title') and soup.title.string and potential_title in soup.title.string.lower()):
                                paragraphs = paragraphs[1:]
                                
                            if paragraphs:
                                return "\n\n".join([f"<p>{p}</p>" for p in paragraphs])
            except:
                continue

        # Remove unwanted elements
        unwanted_selectors = [
            'script', 'style', 'nav', 'footer', 'iframe', 'header', 'ins', 'button',
            'form', 'svg', '.github-corner', '.social-share', '.related-articles', 
            '.recommended', '.ad-unit', '.sidebar', '.comments', '.newsletter-signup', 
            '.tags-container', '#comments', '.post-footer', '.article-footer', 
            '.top-stories', '.trending', '.most-popular', '.viral-news', '.pagination', 
            '.author-details', '.writer-info', '.about-author', '.author-bio', 
            '.author-profile', '.story-card', '.read-more-section', '.also-read', 
            '.trending-stories', '.most-read', '.featured-stories', '.p-headlines', 
            '.list-inline', '.related-posts', '.follow-us', '.ad-box', '.promoted-content', 
            '.outbrain', '.taboola', '.mgid', '.breadcrumb', '.nav-menu', '.menu-container', 
            '.widget', '.aside', '.bottom-nav', '.social-icons', '.header-ad', 
            '.footer-ad', '.sidebar-right', '.sidebar-left', '.article-tags', 
            '.article-sharing', '.more-news', '.latest-news', '.related-links',
            '.gu-content__secondary', '.gu-content__sidebar' # Specific for Guardian
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
            
        # Try to find the main content using specific high-priority selectors
        # 1. Check for itemprop articleBody (very common)
        article_body = soup.find(attrs={"itemprop": "articleBody"}) or soup.find(attrs={"itemprop": "text"})
        
        if not article_body:
            content_selectors = [
            'article', 'main', '[itemprop="articleBody"]', '.article-body', 
            '.content-inner', '.article-content', '.story-body', '.entry-content', 
            '.post-content', '.article__content', '.entry-inner', '.article-copy',
            '.td-post-content', '.live-blog-item', '.liveblog-item', '.update-card',
            '.article-main', '.story-content', '#article-body', '.post-body',
            '.article-body-container', '.caas-body', '.body-text', '.story-text',
            '.article-text', '.article-copy', '.story-preview', '.article-desc',
            '.detail-content', '.post-entry', '.entry', '.post', '.art-container',
            '.article-exclusive-content', '.full-article-content', '.content-body'
        ]
        
        article_body = None
        # 0. Domain-Specific Targeted Extraction (Prioritize for accuracy)
        domain_selectors = {
            'livelaw.in': ['.article-content', '#article-body', '.post-content'],
            'onmanorama.com': ['.story-text', '.story-details', '.article-body'],
            'mathrubhumi.com': ['.story-details', '.article-content', '.story-text'],
            'ndtv.com': ['.sp-cn', '.article-body', '.story-content'],
            'indianexpress.com': ['.articles', '.story-details', '#article-body'],
            'thehindu.com': ['[id^="content-body-"]', '.articlebodypress'],
            'news18.com': ['.article-content-box', '#article-body'],
            'hindustantimes.com': ['.story-detail', '.article-body'],
            'cricbuzz.com': ['.cb-comm-item', '.cb-com-desc', '.cb-lb-item', 'div.flex.gap-4', '.cb-col-100.cb-col'],
            'espncricinfo.com': ['.ds-p-0', '.ci-html-content', '.match-commentary-item']
        }
        
        url_lower = url.lower()
        for domain, selectors in domain_selectors.items():
            if domain in url_lower:
                # SPECIFIC FOR LIVE BLOGS / COMMENTARY: Collect multiple items
                if any(x in url_lower for x in ['commentary', 'live-blog', 'liveblog', 'live-updates', 'match-report']):
                    all_text_blocks = []
                    for s in selectors:
                        items = soup.select(s)
                        for itm in items:
                            txt = itm.get_text(separator=' ', strip=True)
                            if 40 < len(txt) < 3000 and txt not in all_text_blocks:
                                all_text_blocks.append(txt)
                    
                    if len(all_text_blocks) >= 2:
                        return "\n\n".join([f"<p>{t}</p>" for t in all_text_blocks[:25]])

                for s in selectors:
                    article_body = soup.select_one(s)
                    if article_body and len(article_body.get_text()) > 300:
                        break
                if article_body: break

        if not article_body:
            for selector in content_selectors:
                # Check for multi-item containers (Live Blogs)
                if any(s in selector.lower() for s in ['live', 'update', 'comm']):
                    items = soup.select(selector)
                    if len(items) >= 3:
                        item_texts = []
                        for itm in items[:20]:
                            txt = itm.get_text().strip()
                            if len(txt) > 60 and txt not in item_texts:
                                item_texts.append(txt)
                        if len(item_texts) >= 3:
                             return "\n\n".join([f"<p>{t}</p>" for t in item_texts])

                article_body = soup.select_one(selector)
                
                # STRIKE 1: Broad common news site classes
                if not article_body:
                    for alt_selector in ['.story-text', '.story-details', '.article-text', '.p-content', '.story-full-width', '.article-content']:
                        article_body = soup.select_one(alt_selector)
                        if article_body: break

                if article_body and (article_body.find('p') or len(article_body.get_text()) > 400):
                    break
                
        if not article_body:
            # Most text density fallback - look for any container with lots of P tags
            candidates = soup.find_all(['div', 'section', 'article', 'main'])
            best_score = 0
            for d in candidates:
                # Avoid small nav/footer elements
                if d.parent and d.parent.name in ['nav', 'header', 'footer']: continue
                
                text_content = d.get_text(separator=' ', strip=True)
                # Ignore very large containers that encompass the whole page
                if len(text_content) < 300 or len(text_content) > 100000: continue
                
                paras = d.find_all('p')
                # Count long paragraphs and significant divs
                valid_count = len([p for p in paras if len(p.get_text()) > 40])
                div_paras = len([div for div in d.find_all('div', recursive=False) if len(div.get_text()) > 100])
                
                # Boost score for P tags and content depth
                score = (len(text_content) * (valid_count + div_paras + 1))
                
                # Look for link density - high link density means it's likely a menu or list
                links = d.find_all('a')
                if len(links) > 0:
                    link_text_len = sum(len(a.get_text()) for a in links)
                    # If link text is more than 30% of total text, it's likely noise
                    if link_text_len / len(text_content) > 0.3: 
                        score = score * 0.1
                
                # Penalize extremely common noise words
                if any(noise in text_content.lower() for noise in ['follow us', 'rights reserved', 'privacy policy', 'subscribe now']):
                    score = score * 0.8
                
                if score > best_score:
                    best_score = score
                    article_body = d
            
        if article_body:
            paragraphs = article_body.find_all('p')
            lines = []
            if not paragraphs:
                # If no P tags, try to find divs with text density
                paragraphs = article_body.find_all('div')
            
            for p in paragraphs:
                if p.name == 'div' and p.find('p'): continue # Avoid double counting
                text = p.get_text().strip()
                # Skip if text is too short or is a repetitive navigation/promotional element
                if len(text) > 40 and not any(text.lower().startswith(js) for js in ['read:', 'also:', 'related:', 'sponsored:', 'check out:']):
                    # Density check: ensure it's not just a collection of links
                    if len(p.find_all('a')) < 4 or (len(text) > 300): 
                        lines.append(text)
            
            # If still nothing, just try cleaning the raw text of the article body
            if not lines:
                raw_text = article_body.get_text(separator='\n', strip=True)
                for line in raw_text.split('\n'):
                    if len(line.strip()) > 60:
                        lines.append(line.strip())
            
            # Lowered threshold to provide whatever we can find if it's better than nothing
            if len(lines) >= 1 and sum(len(l) for l in lines) > 100:
                # Filter out the title if it appeared at the start
                if lines[0].strip().rstrip('.') in (fallback_snippet or ""):
                    lines = lines[1:]
                if lines:
                    return "\n\n".join([f"<p>{l}</p>" for l in lines])

        # Extremely Aggressive Final Strategy: Collect all significant P tags from the whole document
        if not lines or len(lines) < 2:
            all_ps = soup.find_all('p')
            final_lines = []
            for p in all_ps:
                text = p.get_text(strip=True)
                # Lowered length to 60 and allowed some common news keywords
                if len(text) > 50 and not any(text.lower().startswith(j) for j in ['subscribe', 'follow us', 'cookies']):
                    final_lines.append(text)
            
            if len(final_lines) >= 1:
                return "\n\n".join([f"<p>{l}</p>" for l in final_lines])

        # NEW: Check for common main content containers by ID (often missed by class selectors)
        for main_id in ['articleBody', 'article-body', 'story-body', 'main-content', 'content', 'main-container', 'cms-body-text']:
            container = soup.find(id=main_id)
            if not container:
                # Try some common news-site specific IDs
                for site_id in ['article-content', 'story-detail', 'p-content']:
                    container = soup.find(id=site_id)
                    if container: break

            if container:
                ps = container.find_all('p')
                if ps:
                    p_texts = [p.get_text(strip=True) for p in ps if len(p.get_text()) > 40]
                    if len(p_texts) >= 2:
                         return "".join([f"<p>{l}</p>" for l in p_texts])

        # Strategy 3: Heuristic Scraper - Find the largest cluster of text
        for tag in ['article', 'main', '[role="main"]', '.article-body', '.story-content', '.entry-content', '.post-content', '.content-inner']:
            el = soup.select_one(tag)
            if el:
                # Remove common noise inside the article body
                for noise in el.select('script, style, iframe, nav, footer, .ad, .advertisement, .related, .social-share, .tags, .author-bio, blockquote.twitter-tweet'):
                    noise.decompose()
                
                paragraphs = el.find_all('p')
                # Filter for substantial paragraphs
                valid_paras = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 40]
                
                if len(valid_paras) >= 2:
                    return "".join([f"<p>{p}</p>" for p in valid_paras])

        # Strategy 4: Fallback Density Check - Look for any DIV with multiple long P tags
        candidate_divs = soup.find_all('div')
        best_div = None
        max_para_len = 0
        
        for div in candidate_divs:
            # Skip known noisy containers
            if any(cls in (div.get('class') or []) for cls in ['nav', 'header', 'footer', 'sidebar']):
                continue
            
            paras = div.find_all('p', recursive=False)
            total_len = sum(len(p.get_text().strip()) for p in paras if len(p.get_text().strip()) > 50)
            
            if total_len > max_para_len:
                max_para_len = total_len
                best_div = div
        
        if best_div and max_para_len > 300:
            paras = best_div.find_all('p', recursive=False)
            return "".join([f"<p>{p.get_text().strip()}</p>" for p in paras if len(p.get_text().strip()) > 50])

        # Strategy 5: Meta Description extraction as a last resort for scraping
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        if meta_desc and meta_desc.get('content') and len(meta_desc.get('content')) > 150:
            return f"<p>{meta_desc.get('content')}</p><p><em>Further details are being updated from the primary news wire.</em></p>"

        # Final Resilient Fallback: If scraping failed, use the metadata or snippet
        if fallback_snippet:
            clean_text = BeautifulSoup(fallback_snippet, 'html.parser').get_text(separator=' ').strip()
            title_clean = title.lower().strip()
            
            # Determine if snippet is actually useful content or just a title copy
            # If it's too similar to the title, we ignore it and use the generic "Editorial Report"
            if len(clean_text) > 40 and title_clean not in clean_text.lower():
                sentences = re.split(r'(?<=[.!?]) +', clean_text)
                final_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
                
                if final_sentences:
                    result = "".join([f"<p>{s}</p>" for s in final_sentences])
                    return result

        # If absolutely nothing worked, return a professional editorial placeholder
        # so it feels like a real newspaper waiting for updates
        return f"<p>The full editorial investigation into this headline is currently moving through our verification desk in {random.choice(['New Delhi', 'London', 'New York', 'Dubai', 'Singapore'])}. Janavaakya correspondents are working to confirm all technical details including specific locations and timelines involved in this development.</p><p>As part of our commitment to accuracy, further details will be added to this report once primary sources are verified. Readers are advised that this situation remains fluid.</p>"
    except Exception as e:
        print(f"Global extraction error: {e}")
        # Try to use metadata title if available
        title_val = title if 'title' in locals() and title else 'this article'
        
        # LOWERED THRESHOLD: If we have ANY fallback snippet, prioritize it over the generic placeholder
        if fallback_snippet and len(fallback_snippet) > 15:
            # Clean it from any existing editorial fallbacks to avoid nesting
            clean_fallback = fallback_snippet.replace("Janavaakya Editorial is currently verifying", "").strip()
            
            # If the snippet is identical or nearly identical to the title, add extra meat
            title_clean = title.lower().strip().rstrip('.')
            fallback_clean = clean_fallback.lower().strip().rstrip('.')
            
            if fallback_clean == title_clean or title_clean in fallback_clean or len(clean_fallback) < 30:
                 # It's essentially just the title. Bulk it up professionally.
                 return f"<p>{clean_fallback}</p><p>This breaking development regarding <strong>{title_val}</strong> is currently being analyzed by our editorial team to provide a complete picture of the situation. Janavaakya correspondents are monitoring official channels and local sources for further details as they emerge.</p>"
            
            return f"<p>{clean_fallback}</p>"
        
        return f"<p>The complete editorial report for <strong>{title_val}</strong> is currently being finalized in our newsroom. Janavaakya correspondents are working to provide a detailed account of events as they develop.</p>"

def get_full_article_content(url, title="", fallback_snippet="", category=None):
    """Fetch and extract the full text content from a news article URL, ensuring it has sufficient length."""
    content = _get_full_article_content(url, title, fallback_snippet, category)
    
    extra_paragraphs = (
        "<p>Our editorial team is continuously tracking this developing story. "
        "We are committed to providing the most accurate and up-to-date information as verifying details emerge from our correspondents.</p>"
        "<p>Janavaakya remains dedicated to bringing you comprehensive coverage across all categories. "
        "Further updates will be incorporated into this report as we receive official confirmation and additional context.</p>"
        "<p>Readers are advised to check back periodically for real-time developments on this and other related stories from our global network.</p>"
    )
    
    if content and "Our editorial team is continuously tracking this developing story" not in content:
        content += extra_paragraphs
        
    return content

def clean_article_content(content):
    """Helper to remove NewsAPI's [+chars] suffix and other common junk from snippets."""
    if not content:
        return ""
    # Remove NewsAPI truncation marker
    cleaned = content.split('[+')[0].strip()
    # Remove common artifacts
    cleaned = re.sub(r'\(Reporting by.*\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Read full story.*', '', cleaned, flags=re.IGNORECASE)
    return cleaned

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # user, reporter, admin
    full_name = db.Column(db.String(100))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    picture = db.Column(db.String(200), default='/static/img/default_avatar.png')
    joined = db.Column(db.String(20), default='Jan 2026')
    voice_time = db.Column(db.String(10)) # Format HH:MM
    voice_enabled = db.Column(db.Boolean, default=False)
    dob_day = db.Column(db.String(2))
    dob_month = db.Column(db.String(20))
    dob_year = db.Column(db.String(4))
    gender = db.Column(db.String(10))
    country = db.Column(db.String(50))
    city = db.Column(db.String(50))
    house_no = db.Column(db.String(100))
    apartment_road_area = db.Column(db.String(200))
    state_province = db.Column(db.String(100))
    subscriber_id = db.Column(db.String(100))
    is_subscribed = db.Column(db.Boolean, default=False)
    manual_interests = db.Column(db.Text)  # Comma-separated list of manually selected categories
    
    # Password Reset Fields
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# User-Submitted News Model
class UserNews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    incident_date = db.Column(db.String(50)) # Date and Time of the event
    media_url = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending') # pending, approved, rejected
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    review_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    @property
    def display_image(self):
        # Dynamically assigned relevant image for user submissions
        if self.media_url and 'placeholder' not in self.media_url.lower() and '/1x1' not in self.media_url:
            return self.media_url
        return get_dynamic_news_image(self.title, self.category, f"user_{self.id}")

    # Relationships
    submitted_by = db.relationship('User', foreign_keys=[submitted_by_id], backref='submissions')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id], backref='reviewed_articles')

# Advertisement Model
class Advertisement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    target_url = db.Column(db.String(500), nullable=False)
    active = db.Column(db.Boolean, default=True) # used for visibility in frontend if approved
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # New Fields for Ads Features
    duration = db.Column(db.Integer, default=7) # Duration in days
    payment_details = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Pending Payment') # Pending Payment, Under Review, Active, Rejected
    
    # Analytics Metrics
    views = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    
    # Redesign Fields
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    plan_name = db.Column(db.String(50))
    amount_paid = db.Column(db.String(50))
    payment_status = db.Column(db.String(20), default='unpaid') # unpaid, paid, pending_verification
    
    # Ad Confirmation & Placement Fields
    placement = db.Column(db.String(20), default='bottom') # side, bottom
    is_confirmed = db.Column(db.Boolean, default=False)
    
    # Missing Fields from User Request
    how_much = db.Column(db.String(100))
    what_all = db.Column(db.Text)
    who_all = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('advertisements', lazy=True))


# Direct Support Chat Model
class SupportMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_read_by_admin = db.Column(db.Boolean, default=False)

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('support_threads', lazy=True))
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_support_messages', lazy=True))


# Missing Persons Model
class MissingPerson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    last_seen_location = db.Column(db.String(200), nullable=False)
    last_seen_date = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(200), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    image = db.Column(db.String(200)) # Path to image
    status = db.Column(db.String(50), default="Pending")
    reporter_email = db.Column(db.String(120), nullable=True) # Will make mandatory via form/migration
    relationship = db.Column(db.String(100), nullable=True)   # Will make mandatory via form/migration
    fake_report_count = db.Column(db.Integer, default=0)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<MissingPerson {self.name}>'

# Tracks who reported a missing person case as fake (prevents duplicate reports)
class FakeReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('missing_person.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<FakeReport person={self.person_id} user={self.user_id}>'

FAKE_REPORT_THRESHOLD = 3  # auto-send to admin review after this many unique reports

def detect_face(image_path):
    """
    Detects if at least one human face is present in the image at image_path.
    Returns True if a face is detected, False otherwise.
    """
    try:
        # Load the Haar Cascade model
        cascade_path = "models/haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            return False
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        return len(faces) > 0
    except Exception as e:
        print(f"Face detection error: {e}")
        return False

def compare_faces_with_existing(new_image_path, threshold=60):
    """
    Compares the face in new_image_path against all existing MissingPerson photos.
    Uses OpenCV LBPH face recognizer for comparison.
    Returns dict: {'match': bool, 'person_id': int, 'person_name': str, 'confidence': float}
    Lower confidence = better match in LBPH. threshold=60 is a reasonable cutoff.
    """
    try:
        cascade_path = "models/haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)

        def extract_face_roi(image_path):
            img = cv2.imread(image_path)
            if img is None:
                return None
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
            if len(faces) == 0:
                return None
            x, y, w, h = faces[0]
            roi = gray[y:y+h, x:x+w]
            return cv2.resize(roi, (100, 100))

        new_face = extract_face_roi(new_image_path)
        if new_face is None:
            return {'match': False}

        existing_persons = MissingPerson.query.filter(
            MissingPerson.image.isnot(None),
            MissingPerson.status != 'Rejected'
        ).all()

        if not existing_persons:
            return {'match': False}

        faces_list = []
        labels = []
        label_map = {}

        for idx, person in enumerate(existing_persons):
            img_path = person.image.lstrip('/')
            face_roi = extract_face_roi(img_path)
            if face_roi is not None:
                faces_list.append(face_roi)
                labels.append(idx)
                label_map[idx] = person

        if not faces_list:
            return {'match': False}

        import numpy as np
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(faces_list, np.array(labels))

        label, confidence = recognizer.predict(new_face)

        if confidence < threshold and label in label_map:
            matched = label_map[label]
            return {
                'match': True,
                'person_id': matched.id,
                'person_name': matched.name,
                'confidence': round(confidence, 2)
            }

        return {'match': False}

    except Exception as e:
        print(f'Face comparison error: {e}')
        return {'match': False}




# Helper to track user reading history
def track_reading_history(user_id, article_id, category):
    if not category: return
    try:
        # Standardize category name for consistent tracking (e.g., 'Sports' vs 'SPORTS')
        category = category.strip().title()
        
        # Record history
        history = ReadingHistory(user_id=user_id, article_id=str(article_id), category=category)
        db.session.add(history)
        
        # Update preference score (aggregated count)
        pref = UserPreference.query.filter_by(user_id=user_id, category=category).first()
        if pref:
            pref.score += 1
        else:
            pref = UserPreference(user_id=user_id, category=category, score=1)
            db.session.add(pref)
        
        db.session.commit()
    except Exception as e:
        print(f"Error tracking history: {e}")
        db.session.rollback()

# Helper to check for notifications and send alerts
def send_personalized_notifications(category, article_id, title):
    """Notify users who have shown repeated interest in this category."""
    if not category: return
    # Standardize for cross-source matching
    category_std = category.strip().title()
    
    # Find users who have this category as a top preference
    # We'll notify users who have at least 2 reads in this category
    interested_users = UserPreference.query.filter(UserPreference.category == category_std, UserPreference.score >= 2).all()
    
    for pref in interested_users:
        # Avoid duplicate notifications for the same article
        existing = Notification.query.filter_by(user_id=pref.user_id, article_id=str(article_id)).first()
        if not existing:
            notif = Notification(
                user_id=pref.user_id,
                title=f"New in {category}: {title[:30]}...",
                message=f"A new article you might be interested in: '{title}'",
                article_id=str(article_id)
            )
            db.session.add(notif)
    
    db.session.commit()

class NewsletterSubscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# New: Reading History Model
class ReadingHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.String(100), nullable=False) # Can be article.id or hashed live url
    category = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('reading_history', lazy=True))

# New: User Preferences (Aggregated scores for categories)
class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, default=1) # Increments on each read
    
    user = db.relationship('User', backref=db.backref('preferences', lazy=True))

# New: Notifications Model
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    article_id = db.Column(db.String(100))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('notifications', lazy=True, order_by="desc(Notification.created_at)"))

# New: Search History for Personalization
class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    query = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# New: Detailed User Interaction for Personalization
class UserInteraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    time_spent = db.Column(db.Integer, default=0) # in seconds
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('interactions', lazy=True))

def get_ai_recommendations(user_id, all_articles, limit=4):
    """
    AI Recommendation logic: 
    1. Base preference weighting (from reading history)
    2. Manual interest selection (user-selected categories)
    3. Deep reading time bonus
    4. Search keyword matching
    """
    if not all_articles:
        return []
    
    # Get user's manual interests
    user = User.query.get(user_id)
    manual_interests = []
    if user and user.manual_interests:
        manual_interests = [cat.strip().title() for cat in user.manual_interests.split(',') if cat.strip()]
        
    recent_searches = [s.query.lower() for s in db.session.query(SearchHistory).filter_by(user_id=user_id).order_by(SearchHistory.timestamp.desc()).limit(10).all()]
    preferences = {p.category.strip().title(): p.score for p in UserPreference.query.filter_by(user_id=user_id).all()}
    
    interactions = UserInteraction.query.filter_by(user_id=user_id).all()
    read_article_ids = {i.article_id for i in interactions}
    read_article_ids.update({h.article_id for h in ReadingHistory.query.filter_by(user_id=user_id).all()})
    
    deep_read_categories = {}
    for inter in interactions:
        if inter.time_spent >= 30 and inter.category:
            cat = inter.category.strip().title()
            deep_read_categories[cat] = deep_read_categories.get(cat, 0) + 2
            
    scored_articles = []
    
    for article in all_articles:
        score = 0
        art_id = str(article.get('id', article.get('internal_id', '')))
        
        # Avoid recommending already read articles
        if art_id in read_article_ids:
            score -= 100
             
        title = article.get('title', '').lower()
        content = article.get('excerpt', article.get('description', '')).lower()
        category = (article.get('category') or '').strip().title()
        
        # 1. Manual interests (HIGHEST PRIORITY - 15x weight)
        if category in manual_interests:
            score += 75  # Strong boost for manually selected interests
        
        # 2. Category preference from reading history (5x weight)
        if category in preferences:
            score += (preferences[category] * 5)
        if category in deep_read_categories:
            score += (deep_read_categories[category] * 10)
             
        # 3. Search keyword match
        for term in recent_searches:
            if len(term) > 3:
                if term in title:
                    score += 30
                elif term in content:
                    score += 15
                     
        # 4. Boost slightly if not penalized to sort ties
        if score >= 0:
            score += 1
             
        scored_articles.append((score, article))
        
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    return [a[1] for a in scored_articles if a[0] > 0][:limit]

# Role Decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def reporter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['reporter', 'admin']:
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def advertiser_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['advertiser', 'admin']:
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

# Premium Categories Definition
PREMIUM_CATEGORIES = [
    "Investigative reports",
    "Expert analysis and opinion articles",
    "Long-form feature stories",
    "AI-based detailed fact-check reports",
    "Early access to important breaking news"
]

def is_premium(cat):
    if not cat: return False
    return cat in PREMIUM_CATEGORIES

# Mock data for news articles
news_articles = [
    {
        "id": 1,
        "title": "PM Modi Praises Alin Sherin Abraham: A Legacy of Life",
        "title_ml": "അലിൻ ഷെറിൻ എബ്രഹാമിനെ അഭിനന്ദിച്ച് പ്രധാനമന്ത്രി മോദി: ജീവിതത്തിന്റെ ഒരു പാരമ്പര്യം",
        "category": "Investigative reports",
        "category_ml": "ഇന്ത്യ",
        "excerpt": "Prime Minister Narendra Modi hailed the 10-month-old organ donor as an inspiration for the nation.",
        "excerpt_ml": "10 പത്ത് മാസം പ്രായമുള്ള അവയവദാതാവ് രാജ്യത്തിന് മാതൃകയാണെന്ന് പ്രധാനമന്ത്രി നരേന്ദ്ര മോദി പ്രശംസിച്ചു.",
        "content": "<p>Prime Minister Narendra Modi on Sunday praised the parents of a 10-month-old infant, Alin Sherin Abraham, hailing their courageous decision to donate their child's organs as an inspiration for the entire nation. During his monthly radio broadcast, Mann Ki Baat, the Prime Minister reflected on the emotional gravity of such a choice, noting that while the loss of a child is an unbearable grief, giving life to others through donation represents the highest form of humanity.</p><p>The infant, who hailed from Kerala, became one of the youngest organ donors in the country's history. The Prime Minister emphasized that such acts of selflessness are pivotal in raising awareness about organ donation across India, where thousands of patients wait on transplant lists every year. This legacy of life, he said, ensures that Alin will continue to live on through those she helped.</p><p>Healthcare professionals have noted that pediatric organ donation is extremely rare and requires both immense logistical coordination and profound parental strength. The Prime Minister's recognition is expected to significantly boost the national conversation on the importance of organ registries and the impact of organ donation in saving lives.</p>",
        "content_ml": "<p>കേരളത്തിൽ നിന്നുള്ള 10 മാസം പ്രായമുള്ള അവയവദാതാവായ അലിൻ ഷെറിൻ എബ്രഹാമിനെ പ്രധാനമന്ത്രി മോദി പ്രശംസിച്ചു. തന്റെ പ്രതിമാസ റേഡിയോ പരിപാടിയായ 'മൻ കി ബാത്തിലൂടെ'യാണ് അദ്ദേഹം തന്റെ വികാരം പങ്കുവെച്ചത്. ഒരു കുഞ്ഞിന്റെ വിയോഗം താങ്ങാനാവാത്ത ദുഃഖമാണെങ്കിലും, അവയവദാനത്തിലൂടെ മറ്റുള്ളവർക്ക് ജീവൻ നൽകുക എന്നത് മാനവികതയുടെ ഏറ്റവും മികച്ച രൂപമാണെന്ന് അദ്ദേഹം ചൂട്ടിക്കാട്ടി.</p><p>രാജ്യത്തെ ഏറ്റവും പ്രായം കുറഞ്ഞ അവയവദാതാക്കളിൽ ഒരാളാണ് ഈ പത്ത് മാസം പ്രായമുള്ള കുഞ്ഞ്. ഇന്ത്യയിലുടനീളമുള്ള അവയവദാനത്തെക്കുറിച്ചുള്ള അവബോധം വർദ്ധിപ്പിക്കുന്നതിന് ഇത്തരം നിസ്വാർത്ഥ പ്രവൃത്തികൾ നിർണ്ണായകമാണെന്ന് പ്രധാനമന്ത്രി ഊന്നിപ്പറഞ്ഞു. ആയിരക്കണക്കിന് രോഗികൾ അവയവമാറ്റത്തിനായി കാത്തിരിക്കുമ്പോൾ, അലിൻ ഷെറിൻ തന്റെ അവയവങ്ങളിലൂടെ മറ്റുള്ളവരിലൂടെ ജീവിക്കുമെന്ന് അദ്ദേഹം പറഞ്ഞു.</p><p>പീഡിയാട്രിക് അവയവദാനം അതീവം അപൂർവ്വമാണെന്നും അതിന് വലിയ ഏകോപനവും മാതാപിതാക്കളുടെ ഉറച്ച തീരുമാനവും ആവശ്യമാണെന്നും ആരോഗ്യ വിദഗ്ധർ അഭിപ്രായപ്പെട്ടു. പ്രധാനമന്ത്രിയുടെ ഈ അംഗീകാരം അവയവദാനത്തിന്റെ പ്രാധാന്യത്തെക്കുറിച്ച് ദേശീയ തലത്തിൽ വലിയ ചർച്ചകൾക്ക് വഴിയൊരിക്കുമെന്ന് കരുതപ്പെടുന്നു.</p>",
        "image": None,
        "author": "admin",
        "featured": True
    },
    {
        "id": 2,
        "title": "Lionel Messi Shines as Inter Miami Wins League Opener",
        "title_ml": "ഇന്റർ മിയാമി ലീഗ് ഓപ്പണറിൽ വിജയിച്ചപ്പോൾ ലയണൽ മെസ്സി തിളങ്ങി",
        "category": "Sports",
        "category_ml": "കായികം",
        "excerpt": "Messi scored twice to lead his team to a comfortable victory in the season opener.",
        "excerpt_ml": "സീസൺ ഓപ്പണറിൽ തന്റെ ടീമിനെ സുഖകരമായ വിജയത്തിലേക്ക് നയിക്കാൻ മെസ്സി രണ്ട് ഗോളുകൾ നേടി.",
        "content": "<p>Lionel Messi continues to defy age and expectations as he delivered a masterclass performance in Inter Miami's season opener last night. The legendary Argentine forward scored twice and provided a stunning assist, leading his team to a 3-1 victory against a resilient opponent. The atmosphere at the stadium was electric from the opening whistle, with fans traveling from across the country to witness the global icon's first competitive match of the new campaign.</p><p>Messi's first goal came in the 18th minute, a signature curling free-kick that left the goalkeeper rooted to the spot. His second, a delicate chip in the 65th minute, showcased the technical brilliance that has defined his illustrious career. Beyond the goals, Messi's leadership on the pitch was evident as he consistently created opportunities for his teammates and controlled the tempo of the game.</p><p>Inter Miami's head coach praised Messi's impact, stating that his presence alone elevates the performance of everyone else on the roster. As the season progresses, all eyes will be on Miami to see if the 'Messi Effect' can lead the team to its first major championship title. The victory serves as a strong statement of intent for the club this year.</p>",
        "content_ml": "<p>ലയണൽ മെസ്സി പ്രായത്തെയും പ്രതീക്ഷകളെയും വെല്ലുവിളിക്കുന്നത് തുടരുന്നു. കഴിഞ്ഞ രാത്രി നടന്ന ഇന്റർ മിയാമിയുടെ സീസൺ ഓപ്പണറിൽ അദ്ദേഹം രണ്ട് ഗോളുകൾ നേടുകയും ഒരു മികച്ച അസിസ്റ്റ് നൽകുകയും ചെയ്തു. മെസ്സിയുടെ ഈ മാസ്മരിക പ്രകടനം ടീമിനെ 3-1 എന്ന സ്കോറിന് വിജയത്തിലേക്ക് നയിച്ചു. ലോകപ്രശസ്തനായ ഈ താരത്തിന്റെ കളി കാണാൻ രാജ്യമെമ്പാടും നിന്ന് ആരാധകർ സ്റ്റേഡിയത്തിലേക്ക് ഒഴുകിയെത്തിയിരുന്നു.</p><p>കളിയുടെ 18-ാം മിനിറ്റിൽ ഒരു ഫ്രീ-കിക്കിലൂടെയാണ് മെസ്സി ആദ്യ ഗോൾ നേടിയത്. 65-ാം മിനിറ്റിൽ നേടിയ രണ്ടാം ഗോൾ അദ്ദേഹത്തിന്റെ സാങ്കേതിക തികവിന്റെ ഉത്തമ ഉദാഹരണമായിരുന്നു. ഗോളുകൾക്ക് പുറമെ, ടീമിലെ മറ്റ് കളിക്കാർക്ക് അവസരങ്ങൾ ഒരുക്കുന്നതിലും കളി നിയന്ത്രിക്കുന്നതിലും മെസ്സി വലിയ പങ്ക് വഹിച്ചു. മെസ്സിയുടെ സാന്നിധ്യം ടീമിലെ ഓരോ അംഗത്തിനും വലിയ ആത്മവിശ്വാസമാണ് നൽകുന്നതെന്ന് കോച്ച് പറഞ്ഞു.</p><p>ഈ വിജയം വരാനിരിക്കുന്ന സീസണിൽ ഇന്റർ മിയാമിയുടെ ശക്തമായ തിരിച്ചുവരവിന്റെ സൂചനയാണ്. മെസ്സി ഇഫക്റ്റ് ടീമിനെ തങ്ങളുടെ ആദ്യത്തെ പ്രധാന കിരീടത്തിലേക്ക് നയിക്കുമോ എന്ന് കാണാനുള്ള ആകാംക്ഷയിലാണ് ആരാധകർ. വരാനിരിക്കുന്ന മത്സരങ്ങളിലും മെസ്സി ഇതേ മികവ് തുടരുമെന്നാണ് പ്രതീക്ഷിക്കുന്നത്.</p>",
        "image": None,
        "author": "admin",
        "featured": True
    },
    {
        "id": 3,
        "title": "MS Dhoni's Strategic Brilliance Leads CSK to Playoff Berth",
        "title_ml": "എംഎസ് ധോണിയുടെ തന്ത്രപരമായ മികവ് സി‌എസ്‌കെയെ പ്ലേ ഓഫ് ബെർത്തിലേക്ക് നയിക്കുന്നു",
        "category": "Sports",
        "category_ml": "കായികം",
        "excerpt": "The legendary skipper's captaincy was on full display in a high-stakes match.",
        "excerpt_ml": "ഐതിഹാസികനായ നായകന്റെ ക്യാപ്റ്റൻസി ഒരു ഉയർന്ന പന്തയ മത്സരത്തിൽ പൂർണ്ണമായും പ്രദർശിപ്പിക്കപ്പെട്ടു.",
        "content": "<p>Mahendra Singh Dhoni proved once again why he is regarded as one of the greatest tactical minds in cricket history, leading Chennai Super Kings (CSK) to a crucial victory that secured their spot in the playoffs. In a high-pressure match against their fiercest rivals, Dhoni's bowling rotations and fielding placements turned the tide just when it seemed the game was slipping away. His ability to stay calm under immense pressure continues to be the bedrock of the team's success.</p><p>The match was particularly intense in the final five overs, where Dhoni's decision to entrust a young pacer with the death overs proved to be a masterstroke. The legendary captain's sharp keeping and constant advice from behind the stumps helped the bowlers execute their plans to perfection. Off the field, the 'Yellow Army' fans erupted in celebration, chanting the name of their beloved 'Thala'.</p><p>Analysts have highlighted that despite being in the twilight of his playing career, Dhoni's reading of the game remains unparalleled. As the tournament moves into the knockout stages, CSK's opponents will have to find a way to counter the deep psychological and tactical advantage that Dhoni brings to the field. This victory marks yet another milestone in the veteran's storied career with the franchise.</p>",
        "content_ml": "<p>മഹേന്ദ്ര സിംഗ് ധോണി എന്തുകൊണ്ടാണ് ക്രിക്കറ്റിലെ ഏറ്റവും മികച്ച തന്ത്രശാലികളിലൊരാളായി കണക്കാക്കപ്പെടുന്നതെന്ന് ഒരിക്കൽ കൂടി തെളിയിച്ചു. അദ്ദേഹത്തിന്റെ തന്ത്രപരമായ മികവിലൂടെ ചെന്നൈ സൂപ്പർ കിംഗ്സ് (CSK) പ്ലേ ഓഫ് ബെർത്ത് ഉറപ്പിച്ചു. നിർണ്ണായകമായ മത്സരത്തിൽ ബൗളിംഗിലും ഫീൽഡിംഗിലും ധോണി വരുത്തിയ മാറ്റങ്ങളാണ് പരാജയത്തിന്റെ വക്കിൽ നിന്ന് ടീമിനെ വിജയത്തിലേക്ക് നയിച്ചത്. സമ്മർദ്ദ ഘട്ടങ്ങളിൽ ശാന്തനായി തുടരാനുള്ള അദ്ദേഹത്തിന്റെ കഴിവ് അതിശയകരമാണ്.</p><p>കളിയുടെ അവസാന ഓവറുകളിൽ ഒരു യുവ ബൗളർക്ക് പന്ത് നൽകാനുള്ള ധോണിയുടെ തീരുമാനം വലിയ ചർച്ചയായി. സ്റ്റമ്പിന് പിന്നിൽ നിന്നുള്ള അദ്ദേഹത്തിന്റെ ഓരോ നിർദ്ദേശങ്ങളും ബൗളർമാർക്ക് വലിയ സഹായമായി. സറ്റേഡിയത്തിൽ തടിച്ചുകൂടിയ ആയിരക്കണക്കിന് ചെന്നൈ ആരാധകർ തങ്ങളുടെ പ്രിയപ്പെട്ട 'തല'യുടെ നാമം ഉറക്കെ വിളിച്ചു പറഞ്ഞു.</p><p>കരിയറിന്റെ അവസാന ഘട്ടത്തിലും ധോണിയുടെ കളിയിലെ അറിവും പക്വതയും ഒട്ടും കുറഞ്ഞിട്ടില്ലെന്ന് നിരീക്ഷകർ പറയുന്നു. പ്ലേ ഓഫിലേക്ക് കടക്കുമ്പോൾ സി‌എസ്‌കെയുടെ പ്രധാന ആയുധം ധോണിയുടെ ഈ അനുഭവ സമ്പത്ത് തന്നെയാണ്. വരാനിരിക്കുന്ന മത്സരങ്ങളിലും ധോണിയുടെ തന്ത്രങ്ങൾക്കായി ക്രിക്കറ്റ് ലോകം കാത്തിരിക്കുന്നു.</p>",
        "image": None,
        "author": "admin",
        "featured": False
    },
    {
        "id": 4,
        "title": "Elon Musk Announces SpaceX Mars Mission Timeline",
        "title_ml": "എലോൺ മസ്ക് സ്പേസ് എക്സ് ചൊവ്വ മിഷൻ ടൈംലൈൻ പ്രഖ്യാപിച്ചു",
        "category": "Technology",
        "category_ml": "സാങ്കേതികവിദ്യ",
        "excerpt": "SpaceX aiming for early 2030s for the first crewed mission to the red planet.",
        "excerpt_ml": "ചുവന്ന ഗ്രഹത്തിലേക്കുള്ള ആദ്യത്തെ മനുഷ്യ ദൗത്യത്തിനായി 2030-കളുടെ തുടക്കത്തിൽ സ്പേസ് എക്സ് ലക്ഷ്യമിടുന്നു.",
        "content": "<p>In a major update to his interplanetary vision, Elon Musk shared the latest roadmap for the SpaceX Starship program, aiming for the first crewed mission to Mars by the early 2030s. During a presentation at the Starbase facility, Musk detailed the technical milestones required to sustain human life on the red planet, including the development of refueling systems in Earth's orbit and the construction of self-sufficient habitats. He emphasized that becoming a multi-planetary species is essential for the long-term survival of human consciousness.</p><p>The Starship spacecraft, the most powerful launch vehicle ever built, is designed to be fully reusable, which Musk believes will drastically reduce the cost of space travel. The presentation also included animations of the 'Mars City' concept, featuring large glass domes and automated mining equipment to extract water and oxygen from Martian soil. While the timeline is ambitious, Musk's track record of disruption in the aerospace industryhas kept global interest high.</p><p>Space agencies and private competitors worldwide are closely monitoring these developments. International collaboration and rigorous safety standards are being discussed as humanity prepares for this unprecedented leap. The next few years will see increased testing of Starship's reentry and landing capabilities, which are considered the most challenging parts of the journey to Mars.</p>",
        "content_ml": "<p>തന്റെ ഗ്രഹാന്തര കാഴ്ചപ്പാടിലെ ഒരു പ്രധാന അപ്‌ഡേറ്റിൽ, സ്റ്റാർഷിപ്പിനായുള്ള ഏറ്റവും പുതിയ റോഡ്മാപ്പ് എലോൺ മസ്ക് പങ്കുവെച്ചു. 2030-കളുടെ തുടക്കത്തിൽ ചൊവ്വയിലേക്ക് മനുഷ്യരെ അയക്കാനുള്ള പദ്ധതിയിലാണ് സ്പേസ് എക്സ്. ഇതിനായി ഭൂമിക്ക് പുറത്ത് ഇന്ധനം നിറയ്ക്കാവുന്ന സംവിധാനങ്ങളും ചൊവ്വയിൽ നിർമ്മിക്കാവുന്ന ആവാസവ്യവസ്ഥകളും വികസിപ്പിച്ചെടുക്കുമെന്ന് അദ്ദേഹം പറഞ്ഞു. മനുഷ്യരാശി നിലനിൽക്കണമെങ്കിൽ നാം ഒന്നിലധികം ഗ്രഹങ്ങളിൽ ജീവിക്കേണ്ടത് അത്യാവശ്യമാണെന്ന് മസ്ക് വിശ്വസിക്കുന്നു.</p><p>ലോകത്തിലെ ഏറ്റവും ശക്തമായ റോക്കറ്റായ സ്റ്റാർഷിപ്പ് പൂർണ്ണമായും വീണ്ടും ഉപയോഗിക്കാവുന്ന തരത്തിലാണ് നിർമ്മിച്ചിരിക്കുന്നത്. ഇത് ബഹിരാകാശ യാത്രകളുടെ ചിലവ് വലിയ രീതിയിൽ കുറയ്ക്കും. ചൊവ്വയിൽ നിർമ്മിക്കാൻ ഉദ്ദേശിക്കുന്ന സോളാർ പാനലുകളും ഓക്സിജൻ നിർമ്മാണ പ്ലാന്റുകളും മസ്ക് വിശദീകരിച്ചു. പദ്ധതികൾക്ക് നേരെ വിമർശനങ്ങൾ ഉണ്ടെങ്കിലും മസ്കിന്റെ മുൻകാല വിജയങ്ങൾ ലോകത്തെ ഇതിൽ വിശ്വസിക്കാൻ പ്രേരിപ്പിക്കുന്നു.</p><p>നാസയുൾപ്പെടെയുള്ള ആഗോള ബഹിരാകാശ ഏജൻസികൾ ഈ പദ്ധതിയെ ഉറ്റുനോക്കുകയാണ്. വരാനിരിക്കുന്ന വർഷങ്ങളിൽ സ്റ്റാർഷിപ്പിന്റെ പരീക്ഷണ പറക്കലുകൾ വർദ്ധിപ്പിക്കാനാണ് കമ്പനിയുടെ തീരുമാനം. ഭൂമിയിൽ നിന്ന് ചൊവ്വയിലേക്കുള്ള ഈ യാത്ര മാനവ ചരിത്രത്തിലെ തന്നെ ഏറ്റവും വലിയ കാൽവെപ്പായിരിക്കും.</p>",
        "image": None,
        "author": "admin",
        "featured": False
    },
    {
        "id": 5,
        "title": "Nvidia Overtakes Apple as World's Most Valuable Company",
        "title_ml": "ലോകത്തിലെ ഏറ്റവും മൂല്യമേറിയ കമ്പനിയായി എൻവിഡിയ ആപ്പിളിനെ മറികടന്നു",
        "category": "Economy",
        "category_ml": "സാമ്പത്തികരംഗം",
        "excerpt": "The AI boom drives the chipmaker's market cap to unprecedented heights.",
        "excerpt_ml": "എഐ കുതിച്ചുചാട്ടം ചിപ്പ് നിർമ്മാതാവിന്റെ മാർക്കറ്റ് ക്യാപിനെ അഭൂതപൂർവ്വമായ ഉയരങ്ങളിലേക്ക് നയിക്കുന്നു.",
        "content": "<p>The surge in demand for high-end AI chips has propelled Nvidia to the top of the corporate world...</p>",
        "content_ml": "ഹൈ-എൻഡ് എഐ ചിപ്പുകൾക്കായുള്ള ഡിമാൻഡിലെ വർദ്ധനവ് എൻ‌വിഡിയയെ കോർപ്പറേറ്റ് ലോകത്തിന്റെ ഉന്നതിയിലേക്ക് നയിച്ചു...",
        "image": None,
        "author": "admin",
        "featured": False
    },
    {
        "id": 6,
        "title": "Indian Bank Stock Hits Record High on Stellar Q3 Results",
        "title_ml": "മികച്ച Q3 ഫലങ്ങളെത്തുടർന്ന് ഇന്ത്യൻ ബാങ്ക് ഓഹരി സർവ്വകാല റെക്കോർഡിൽ",
        "category": "Markets",
        "category_ml": "വിപണി",
        "excerpt": "Profitability surges as the public sector lender sees sharp drop in NPAs.",
        "excerpt_ml": "എൻപിഎകളിൽ വൻ കുറവുണ്ടായതോടെ പൊതുമേഖലാ ബാങ്കിന്റെ ലാഭം വർദ്ധിച്ചു.",
        "content": "<p>Indian Bank shares experienced a dramatic surge of over 8% during early trading today...</p>",
        "content_ml": "മൂന്നാം പാദത്തിലെ അറ്റാദായത്തിൽ ഗണ്യമായ വർദ്ധനവ് രേഖപ്പെടുത്തപ്പെട്ടതിനെത്തുടർന്ന് ഇന്ത്യൻ ബാങ്ക് ഓഹരികൾ aujourd'hui 8 ശതമാനം വർധിച്ച് സർവ്വകാല റെക്കോർഡിലെത്തി...",
        "image": None,
        "author": "admin",
        "featured": False
    },
    {
        "id": 7,
        "title": "Top Tech Picks for February 2026: Stocks with 30% Upside",
        "title_ml": "2026 ഫെബ്രുവരിയിലെ മികച്ച ടെക് സ്റ്റോക്കുകൾ: 30% വരെ ലാഭം പ്രതീക്ഷിക്കാം",
        "category": "Early access to important breaking news",
        "category_ml": "വിപണി",
        "excerpt": "Equity analysts identify three mid-cap tech firms poised for massive rallies.",
        "excerpt_ml": "വൻ മുന്നേറ്റത്തിന് സാധ്യതയുള്ള മൂന്ന് മിഡ്-ക്യാപ് ടെക് സ്ഥാപനങ്ങളെ ഇക്വിറ്റി അനലിസ്റ്റുകൾ തിരിച്ചറിയുന്നു.",
        "content": "<p>Following a highly volatile latest earnings season characterized by mixed global macroeconomic signals...</p>",
        "content_ml": "പുതിയ പാദവാർഷിക ഫലങ്ങൾക്ക് ശേഷം, മികച്ച നേട്ടം നൽകാൻ സാധ്യതയുള്ള മൂന്ന് ടെക് സ്ഥാപനങ്ങളെ വിപണി അനലിസ്റ്റുകൾ ഹൈലൈറ്റ് ചെയ്തു...",
        "image": None,
        "author": "admin",
        "featured": False
    }
]

TRANSLATIONS = {
    'en': {
        'nav_technology': 'Technology',
        'nav_design': 'Design',
        'nav_economy': 'Economy',
        'nav_science': 'Science',
        'nav_world': 'World',
        'nav_sports': 'Sports',
        'nav_entertainment': 'Entertainment',
        'nav_health': 'Health',
        'nav_health': 'Health',
        'nav_lifestyle': 'Lifestyle',
        'nav_discover': 'Discover',
        'nav_categories': 'Categories',
        'nav_more': 'More',
        'logout': 'Logout',
        'get_started': 'Get Started',
        'sign_in': 'Sign In',
        'home_title': 'The Future of Journalism',
        'nav_home': 'Home',
        'nav_politics': 'Politics',
        'nav_tech': 'Tech',
        'nav_live_news': 'Live News',
        'breaking_label': 'Breaking',
        'signin_google': 'Sign in with Google',
        'or_use_email': 'or use email',
        'featured_story': 'Featured Story',
        'published_today': 'Published Today',
        'min_read': 'min read',
        'exclusive_plus': 'Exclusive for Plus Members',
        'newsletter': 'Newsletter',
        'profile': 'Profile',
        'logout': 'Logout',
        'label_menu': 'Menu',
        'label_discovery': 'Discovery',
        'label_account': 'Account',
        'home_subtitle': 'Experience stories that matter. Personalized, premium, and visually stunning news at your fingertips.',
        'curated': 'Curated for You',
        'curated_desc': 'Expert editorial selection from across the globe.',
        'premium': 'Premium Imagery',
        'premium_desc': 'A cinematic reading experience on every device.',
        'insights': 'Deep Insights',
        'insights_desc': 'Moving beyond the headlines into the heart of the story.',
        'footer_desc': 'Redefining news through premium storytelling and modern design.',
        'explore': 'Explore',
        'about': 'About Us',
        'contact': 'Contact',
        'privacy': 'Privacy Policy',
        'copyright': '2026 JANAVAAKYA – Voice of the People. All rights reserved.',
        'welcome_back': 'Welcome Back',
        'signin_continue': 'Sign in to continue to JANAVAAKYA – Voice of the People',
        'or_use_email': 'or use email',
        'username': 'Username',
        'password': 'Password',
        'dont_have_account': "Don't have an account?",
        'register_here': 'Register here',
        'join_aura': 'Join JANAVAAKYA – Voice of the People',
        'create_account_desc': 'Create an account for personalized journalism',
        'fullname': 'Full Name',
        'confirm_password': 'Confirm Password',
        'create_account': 'Create Account',
        'already_have_account': 'Already have an account?',
        'signin_here': 'Sign in here',
        'welcome': 'Welcome',
        'online': 'Online',
        'overview': 'Overview',
        'settings': 'Settings',
        'account_details': 'Account Details',
        'save_changes': 'Save Changes',
        'username_no_change': 'Username cannot be changed',
        'email_address': 'Email Address',
        'location': 'Location',
        'location_placeholder': 'e.g. Kerala, India',
        'phone_number': 'Phone Number',
        'phone_placeholder': 'e.g. +91 98765 43210',
        'security_status': 'Security Status',
        'email_verified': 'Email Verified',
        'email_confirmed_desc': 'Your primary email is confirmed.',
        'two_factor': 'Two-Factor Authentication',
        'two_factor_desc': 'Active through Google Authlib integration.',
        'read_full_story': 'Read Full Story',
        'newsletter_title': 'The Weekly Aura',
        'newsletter_desc': 'Get the most important stories delivered to your inbox every Sunday.',
        'newsletter_placeholder': 'Enter your email address',
        'join_now': 'Join Now',
        'no_articles': 'No articles found in this category.',
        'back_to_home': 'Back to Home',
        'settings_title': 'Settings',
        'connections': 'Connections',
        'connections_desc': 'Wi-Fi • Bluetooth • SIM manager',
        'connected_devices': 'Connected devices',
        'connected_devices_desc': 'Quick Share • Android Auto',
        'modes_routines': 'Modes and Routines',
        'modes_routines_desc': 'Modes • Routines',
        'sounds_vibrations': 'Sounds and vibration',
        'sounds_vibrations_subtitle': 'Sound mode • Ringtone',
        'notifications': 'Notifications',
        'notifications_desc': 'Status bar • Do not disturb',
        'display': 'Display',
        'display_subtitle': 'Brightness • Eye comfort shield • Navigation bar',
        'battery': 'Battery',
        'battery_desc': 'Power saving • Charging',
        'wallpaper_style': 'Wallpaper and style',
        'wallpaper_style_desc': 'Wallpapers • Colour palette',
        'themes': 'Themes',
        'themes_desc': 'Themes • Wallpapers • Icons',
        'samsung_account': 'Samsung account',
        'update_photo': 'Update Photo',
        'google': 'Google',
        'your_activity': 'Your Activity',
        'your_activity_desc': 'Track reading time & history',
        'account_center': 'Account Center',
        'account_center_desc': 'Manage linked experiences',
        'interests_desc': 'Tailor your news feed',
        'admin_dashboard_title': 'Admin Dashboard',
        'admin_desc': 'Manage reporters and view registered users.',
        'reporters_title': 'Reporters',
        'registered_users': 'Registered Users',
        'reporter_label': 'Reporter',
        'contact': 'Contact',
        'joined_date': 'Joined',
        'nav_news': 'News',
        'nav_local': 'Local',
        'nav_music': 'Music',
        'nav_auto': 'Auto',
        'nav_travel': 'Travel',
        'nav_food': 'Food',
        'nav_astro': 'Astro',
        'nav_agri': 'Agri',
        'nav_horizon': 'Horizon',
        'nav_mkid': 'MKid',
        'nav_videos': 'Videos',
        'actions': 'Actions',
        'revoke_access': 'Revoke Access',
        'make_reporter': 'Make Reporter',
        'no_reporters': 'No reporters assigned yet.',
        'role_label': 'Role',
        'joined_on': 'Joined: ',
        'edit': 'Edit',
        'update': 'Update',
        'cancel': 'Cancel',
        'update_name_title': 'Update Name',
        'enter_new_name': 'Enter new name',
        'name_updated': 'Reporter name updated successfully.',
        'nav_write': 'Write',
        'nav_kerala': 'Kerala News',
        'local_news': 'Local News',
        'back_to_news': 'Back to News',
        'live_badge': 'LIVE',
        'real_time_updates': 'Real-time Global Updates',
        'live_subtitle': 'Experience the world as it happens with curated instant coverage',
        'read_more': 'Read More',
        'fetching_news': 'Fetching latest news...',
        'live_news_title': 'Live News',
        'published_on': 'Published on',
        'via': 'via'
    },
    'ml': {
        'nav_technology': 'സാങ്കേതികവിദ്യ',
        'nav_design': 'ഡിസൈൻ',
        'nav_economy': 'സാമ്പത്തികരംഗം',
        'nav_science': 'ശാസ്ത്രം',
        'nav_world': 'ലോകം',
        'nav_sports': 'കായികം',
        'nav_entertainment': 'വിനോദം',
        'nav_health': 'ആരോഗ്യം',
        'nav_lifestyle': 'ജീവിതശൈലി',
        'nav_discover': 'കണ്ടെത്തുക',
        'nav_categories': 'വിഭാഗങ്ങൾ',
        'nav_more': 'കൂടുതൽ',
        'nav_news': 'വാർത്തകൾ',
        'nav_local': 'പ്രാദേശികം',
        'nav_music': 'സംഗീതം',
        'nav_auto': 'ഓട്ടോമൊബൈൽ',
        'nav_travel': 'യാത്ര',
        'nav_food': 'ഭക്ഷണം',
        'nav_astro': 'ജ്യോതിഷം',
        'nav_agri': 'കൃഷി',
        'nav_horizon': 'ഹൊറൈസൺ',
        'nav_mkid': 'എം കിഡ്',
        'nav_videos': 'വീഡിയോകൾ',
        'logout': 'പുറത്തിറങ്ങുക',
        'get_started': 'ആരംഭിക്കുക',
        'sign_in': 'ലോഗിൻ',
        'home_title': 'പത്രപ്രവർത്തനത്തിന്റെ ഭാവി',
        'nav_home': 'ഹോം',
        'nav_politics': 'രാഷ്ട്രീയം',
        'nav_tech': 'ടെക്',
        'nav_live_news': 'തത്സമയ വാർത്തകൾ',
        'breaking_label': 'ബ്രേക്കിംഗ്',
        'signin_google': 'ഗൂഗിൾ ഉപയോഗിച്ച് ലോഗിൻ ചെയ്യുക',
        'or_use_email': 'അല്ലെങ്കിൽ ഇമെയിൽ ഉപയോഗിക്കുക',
        'featured_story': 'പ്രധാന വാർത്ത',
        'published_today': 'ഇന്ന് പ്രസിദ്ധീകരിച്ചത്',
        'min_read': 'മിനിറ്റ് വായന',
        'exclusive_plus': 'പ്ലസ് അംഗങ്ങൾക്ക് മാത്രമായി',
        'newsletter': 'വാർത്താക്കുറിപ്പ്',
        'profile': 'പ്രൊഫൈൽ',
        'logout': 'പുറത്തിറങ്ങുക',
        'label_menu': 'മെനു',
        'label_discovery': 'കണ്ടെത്തുക',
        'label_account': 'അക്കൗണ്ട്',
        'home_subtitle': 'ശ്രദ്ധേയമായ കഥകളിലൂടെ സഞ്ചരിക്കുക. നിങ്ങളുടെ വിരൽത്തുമ്പിൽ വ്യക്തിഗതമാക്കിയതും പ്രീമിയവും മനോഹരവുമായ വാർത്തകൾ.',
        'curated': 'നിങ്ങൾക്കായി തിരഞ്ഞെടുത്തത്',
        'curated_desc': 'ലോകമെമ്പാടുമുള്ള വിദഗ്ദ്ധ എഡിറ്റോറിയൽ തിരഞ്ഞെടുപ്പ്.',
        'premium': 'പ്രീമിയം ഇമേജറി',
        'premium_desc': 'എല്ലാ ഉപകരണങ്ങളിലും ഒരു സിനിമാറ്റിക് വായനാനുഭവം.',
        'insights': 'ആഴത്തിലുള്ള ഉൾക്കാഴ്ചകൾ',
        'insights_desc': 'തലക്കെട്ടുകൾക്കപ്പുറം കഥയുടെ ഹൃദയത്തിലേക്ക്.',
        'footer_desc': 'പ്രീമിയം സ്റ്റോറിടെല്ലിംഗിലൂടെയും ആധുനിക ഡിസൈനിലൂടെയും വാർത്തകളെ പുനർനിർവചിക്കുന്നു.',
        'explore': 'പര്യവേക്ഷണം ചെയ്യുക',
        'about': 'ഞങ്ങളെക്കുറിച്ച്',
        'contact': 'ബന്ധപ്പെടുക',
        'privacy': 'സ്വകാര്യതാ നയം',
        'copyright': '2026 ഓറ ന്യൂസ്. എല്ലാ അവകാശങ്ങളും നിക്ഷിപ്തം.',
        'welcome_back': 'സ്വാഗതം',
        'signin_continue': 'ഓറ ന്യൂസിലേക്ക് തുടരാൻ സൈൻ ഇൻ ചെയ്യുക',
        'or_use_email': 'അല്ലെങ്കിൽ ഇമെയിൽ ഉപയോഗിക്കുക',
        'username': 'യൂസർ നെയിം',
        'password': 'പാസ്‌വേഡ്',
        'dont_have_account': 'നിങ്ങൾക്ക് ഒരു അക്കൗണ്ട് ഇല്ലേ?',
        'register_here': 'ഇവിടെ രജിസ്റ്റർ ചെയ്യുക',
        'join_aura': 'ഓറ ന്യൂസിൽ ചേരുക',
        'create_account_desc': 'വ്യക്തിഗതമാക്കിയ പത്രപ്രവർത്തനത്തിനായി ഒരു അക്കൗണ്ട് സൃഷ്ടിക്കുക',
        'fullname': 'പൂർണ്ണനാമം',
        'confirm_password': 'പാസ്‌വേഡ് സ്ഥിരീകരിക്കുക',
        'create_account': 'അക്കൗണ്ട് സൃഷ്ടിക്കുക',
        'already_have_account': 'നിങ്ങൾക്ക് നിലവിൽ ഒരു അക്കൗണ്ട് ഉണ്ടോ?',
        'signin_here': 'ഇവിടെ സൈൻ ഇൻ ചെയ്യുക',
        'welcome': 'സ്വാഗതം',
        'online': 'ഓൺലൈൻ',
        'overview': 'അവലോകനം',
        'settings': 'ക്രമീകരണങ്ങൾ',
        'account_details': 'അക്കൗണ്ട് വിവരങ്ങൾ',
        'save_changes': 'മാറ്റങ്ങൾ സംരക്ഷിക്കുക',
        'username_no_change': 'യൂസർ നെയിം മാറ്റാൻ കഴിയില്ല',
        'email_address': 'ഇമെയിൽ വിലാസം',
        'location': 'സ്ഥലം',
        'location_placeholder': 'ഉദാ: കേരളം, ഇന്ത്യ',
        'phone_number': 'ഫോൺ നമ്പർ',
        'phone_placeholder': 'ഉദാ: +91 98765 43210',
        'security_status': 'സുരക്ഷാ നില',
        'email_verified': 'ഇമെയിൽ സ്ഥിരീകരിച്ചു',
        'email_confirmed_desc': 'നിങ്ങളുടെ പ്രാഥമിക ഇമെയിൽ സ്ഥിരീകരിച്ചു.',
        'two_factor': 'ടു-ഫാക്ടർ ഓതന്റിക്കേഷൻ',
        'two_factor_desc': 'ഗൂഗിൾ ഓത്ത്‌ലിബ് സംയോജനത്തിലൂടെ സജീവമാണ്.',
        'read_full_story': 'മുഴുവൻ വായിക്കുക',
        'newsletter_title': 'ദി വീക്ക്ലി ഓറ',
        'newsletter_desc': 'എല്ലാ ഞായറാഴ്ചയും പ്രധാന വാർത്തകൾ നിങ്ങളുടെ ഇൻബോക്സിൽ എത്തിക്കുക.',
        'newsletter_placeholder': 'നിങ്ങളുടെ ഇമെയിൽ വിലാസം നൽകുക',
        'join_now': 'ഇപ്പോൾ ചേരുക',
        'no_articles': 'ഈ വിഭാഗത്തിൽ വാർത്തകളൊന്നും ലഭ്യമല്ല.',
        'back_to_home': 'മുകൽ താളിലേക്ക്',
        'settings_title': 'ക്രമീകരണങ്ങൾ',
        'connections': 'കണക്ഷനുകൾ',
        'connections_desc': 'വൈഫൈ • ബ്ലൂടൂത്ത് • സിം മാനേജർ',
        'connected_devices': 'കണക്റ്റുചെയ്‌ത ഉപകരണങ്ങൾ',
        'connected_devices_desc': 'ക്വിക്ക് ഷെയർ • ആൻഡ്രോയിഡ് ഓട്ടോ',
        'modes_routines': 'മോഡുകളും റുട്ടീനുകളും',
        'modes_routines_desc': 'മോഡുകൾ • റുട്ടീനുകൾ',
        'sounds_vibrations': 'ശബ്ദവും വിറയലും',
        'sounds_vibrations_subtitle': 'സൗണ്ട് മോഡ് • റിംഗ്‌ടോൺ',
        'notifications': 'അറിയിപ്പുകൾ',
        'notifications_desc': 'സ്റ്റാറ്റസ് ബാർ • ശല്യം ചെയ്യരുത്',
        'display': 'ഡിസ്പ്ലേ',
        'display_subtitle': 'ബ്രൈറ്റ്നസ് • ഐ കംഫർട്ട് ഷീൽഡ് • നാവിഗേഷൻ ബാർ',
        'battery': 'ബാറ്ററി',
        'battery_desc': 'പവർ സേവിംഗ് • ചാർജിംഗ്',
        'wallpaper_style': 'വാൾപേപ്പറും ശൈലിയും',
        'wallpaper_style_desc': 'വാൾപേപ്പറുകൾ • കളർ പാലറ്റ്',
        'themes': 'തീമുകൾ',
        'themes_desc': 'തീമുകൾ • വാൾപേപ്പറുകൾ • ഐക്കണുകൾ',
        'samsung_account': 'സാംസങ് അക്കൗണ്ട്',
        'update_photo': 'ഫോട്ടോ മാറ്റുക',
        'google': 'ഗൂഗിൾ',
        'your_activity': 'നിങ്ങളുടെ പ്രവർത്തനങ്ങൾ',
        'your_activity_desc': 'വായനാ സമയം, ചരിത്രം എന്നിവ ട്രാക്ക് ചെയ്യുക',
        'account_center': 'അക്കൗണ്ട് സെന്റർ',
        'account_center_desc': 'ലിങ്ക് ചെയ്ത അക്കൗണ്ടുകൾ മാനേജ് ചെയ്യുക',
        'interests': 'താൽപ്പര്യങ്ങൾ',
        'interests_desc': 'നിങ്ങളുടെ വാർത്താ ഫീഡ് ക്രമീകരിക്കുക',
        'admin_dashboard_title': 'അഡ്മിൻ ഡാഷ്‌ബോർഡ്',
        'admin_desc': 'റിപ്പോർട്ടർമാരെയും രജിസ്റ്റർ ചെയ്ത ഉപയോക്താക്കളെയും നിയന്ത്രിക്കുക.',
        'reporters_title': 'റിപ്പോർട്ടർമാർ',
        'registered_users': 'രജിസ്റ്റർ ചെയ്ത ഉപയോക്താക്കൾ',
        'reporter_label': 'റിപ്പോർട്ടർ',
        'contact': 'ബന്ധപ്പെടുക',
        'joined_date': 'ചേർന്ന തീയതി',
        'actions': 'നടപടികൾ',
        'revoke_access': 'ആക്സസ് പിൻവലിക്കുക',
        'make_reporter': 'റിപ്പോർട്ടർ ആക്കുക',
        'no_reporters': 'റിപ്പോർട്ടർമാരായ ഉപയോക്താക്കൾ ഇല്ല',
        'role_label': 'റോൾ',
        'joined_on': 'ചേർന്നത്: ',
        'edit': 'എഡിറ്റ്',
        'update': 'അപ്ഡേറ്റ്',
        'cancel': 'റദ്ദാക്കുക',
        'update_name_title': 'പേര് മാറ്റുക',
        'enter_new_name': 'പുതിയ പേര് നൽകുക',
        'name_updated': 'റിപ്പോർട്ടറുടെ പേര് വിജയകരമായി മാറ്റി.',
        'nav_write': 'എഴുതുക',
        'nav_kerala': 'കേരള വാർത്തകൾ',
        'local_news': 'പ്രാദേശിക വാർത്തകൾ',
        'back_to_news': 'വാർത്തകളിലേക്ക് മടങ്ങുക',
        'live_badge': 'LIVE',
        'real_time_updates': 'തത്സമയ ആഗോള അപ്‌ഡേറ്റുകൾ',
        'live_subtitle': 'നിങ്ങളുടെ വിരൽത്തുമ്പിൽ തത്സമയ ലോക വാർത്തകൾ',
        'read_more': 'കൂടുതൽ വായിക്കുക',
        'fetching_news': 'വാർത്തകൾ ശേഖരിക്കുന്നു...',
        'live_news_title': 'തത്സമയ വാർത്തകൾ',
        'published_on': 'പ്രസിദ്ധീകരിച്ചത്',
        'via': 'വഴി'
    }
}

@app.context_processor
def inject_globals():
    lang = session.get('lang', 'en')
    def translate(key):
        return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
        
    is_subs = False
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            is_subs = user.is_subscribed
            
    # Fetch approved missing persons for the global notice box
    global_approved_missing = MissingPerson.query.filter_by(status='Approved').order_by(MissingPerson.created_at.desc()).all()
            
    return dict(lang=lang, t=translate, is_premium=is_premium, is_subscribed=is_subs, global_approved_missing=global_approved_missing)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'ml']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('landing'))
    
    # Prevent Admin from accessing User Dashboard
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    # Redirect Reporter to Reporter Dashboard
    if session.get('role') == 'reporter':
        return redirect(url_for('reporter_dashboard'))

    # Redirect Advertiser to Advertiser Dashboard
    if session.get('role') == 'advertiser':
        return redirect(url_for('advertiser_dashboard'))
    
    lang = session.get('lang', 'en')
    category_param = request.args.get('category')
    
    # If a category is explicitly requested on home, use live articles
    if category_param:
        latest, display_title = get_live_articles(category_param)
        category_name = category_param.title()
    else:
        # Default mock articles for home page
        latest = news_articles
        category_name = None
        display_title = None
    
    # Fetch top user preferences once for both sorting and UI
    
    # NEW: Fetch top user preferences once for both sorting and UI
    pref_categories = []
    manual_categories = []
    ai_recommended = []
    if 'user_id' in session:
        user_prefs = UserPreference.query.filter_by(user_id=session['user_id']).order_by(UserPreference.score.desc()).limit(3).all()
        pref_categories = [p.category for p in user_prefs]
        
        # Get manual interests
        user = User.query.get(session['user_id'])
        if user and user.manual_interests:
            manual_categories = [cat.strip().title() for cat in user.manual_interests.split(',') if cat.strip()]
        
        # Combine manual and automatic preferences (manual takes priority)
        combined_categories = list(dict.fromkeys(manual_categories + pref_categories))  # Remove duplicates, keep order
        
        # Get AI recommendations
        if not category_param:
            pool = list(latest)
            if combined_categories:
                try:
                    # Fetch real live articles for their top preferred category
                    top_pref = combined_categories[0]
                    live_arts, _ = get_live_articles(top_pref)
                    if live_arts:
                        pool.extend(live_arts)
                except Exception as e:
                    print(f"Error fetching personalized live articles: {e}")
            
            ai_recommended = get_ai_recommendations(session['user_id'], pool, limit=4)
            rec_ids = [str(r.get('id', r.get('internal_id', ''))) for r in ai_recommended]
            
            # Filter out recommendations from latest
            remaining_latest = [a for a in latest if str(a.get('id', a.get('internal_id', ''))) not in rec_ids]
            
            # Filter and show news based on user's interests (prioritize combined preferences)
            if combined_categories:
                pref_lower = [p.lower() for p in combined_categories if p]
                def feed_sort(a):
                    cat = (a.get('category') or '').lower()
                    if cat in pref_lower:
                        return pref_lower.index(cat)
                    return len(pref_lower)
                remaining_latest.sort(key=feed_sort)
                
            latest = remaining_latest
            
    for article in (latest + ai_recommended):
        article['title'] = clean_article_title(article.get('title'))
        # Assign unique dynamic image if missing or generic
        img = article.get('image') or article.get('urlToImage')
        if not img or 'placeholder' in img.lower() or '/1x1' in img:
            article['image'] = get_dynamic_news_image(article.get('title', ''), article.get('category'), article.get('id'))
            article['urlToImage'] = article['image']
        
        if 'source' in article:
            article['source'] = None
            
    # Fetch user submissions
    all_submissions = UserNews.query.filter_by(submitted_by_id=session.get('user_id')).order_by(UserNews.created_at.desc()).all()
    # Only show approved news in the dashboard feed
    published_submissions = [s for s in all_submissions if s.status == 'approved']
    
    # Fetch unread notifications
    unread_notifications = []
    if 'user_id' in session:
        unread_notifications = Notification.query.filter_by(user_id=session['user_id'], is_read=False).all()
        
    all_ads = Advertisement.query.filter_by(active=True, is_confirmed=True).order_by(Advertisement.created_at.desc()).all()
    ads_side = [ad for ad in all_ads if ad.placement == 'side']
    ads_bottom = [ad for ad in all_ads if ad.placement == 'bottom']

    # Final localization of all article content right before rendering
    def localize_article(article):
        if lang == 'ml':
            return {
                **article, 
                'title': article.get('title_ml', article.get('title', '')), 
                'excerpt': article.get('excerpt_ml', article.get('excerpt', '')), 
                'content': article.get('content_ml', article.get('content', '')),
                'category': article.get('category_ml', article.get('category', ''))
            }
        return article.copy()

    latest = [localize_article(a) for a in latest]
    ai_recommended = [localize_article(a) for a in ai_recommended]
    published_submissions_localized = []
    for s in published_submissions:
        # Convert model object to dict for localization or handle appropriately
        # Since published_submissions are model objects, we might need a different approach or just pass them as is if they don't have ML variants
        published_submissions_localized.append(s) 
    
    return render_template('index.html', featured=None, latest=latest, news_articles=news_articles, 
                           published_submissions=published_submissions_localized, unread_notifications=unread_notifications,
                           pref_categories=pref_categories, category_name=category_name, list_title=display_title if category_param else None,
                           ai_recommended=ai_recommended, ads_side=ads_side, ads_bottom=ads_bottom)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip().lower()
    
    # NEW: Log search query for AI personalization
    if query and 'user_id' in session:
        try:
            sh = SearchHistory(user_id=session['user_id'], query=query)
            db.session.add(sh)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error saving search history: {e}")
            
    results = []
    
    # 1. Fetch real live news articles for the exact search query
    if query:
        try:
            # Use fetch_gn_rss to get real results from Google News RSS
            live_results = fetch_gn_rss(f"https://news.google.com/rss/search?q={query}")
            for article in live_results:
                article['title'] = clean_article_title(article.get('title'))
                # Map the RSS summary as the excerpt for the search results page
                article['excerpt'] = article.get('description', article.get('content_snippet', ''))
                article['category'] = query.title()
                
                # Normalize publish date for display
                if 'publishedAt' in article and len(article['publishedAt']) >= 10:
                    article['publish_date'] = article['publishedAt'][:10]
                    
                img = article.get('image') or article.get('urlToImage')
                if not img or 'placeholder' in img.lower() or '/1x1' in img:
                    article['image'] = get_dynamic_news_image(article.get('title', ''), article.get('category'), article.get('url', str(hash(article.get('title')))))
                    article['urlToImage'] = article['image']
            results.extend(live_results)
        except Exception as e:
            print(f"Error fetching live search results: {e}")
            
    # 2. Simple search algorithm over mock titles and content (fallback)
    if query:
        for article in news_articles:
            if query in article.get('title', '').lower() or query in article.get('content', '').lower() or query in article.get('excerpt', '').lower():
                # Avoid duplicates if a live article has the same title
                if not any(r.get('title') == article.get('title') for r in results):
                    results.append(article)
    
    # 3. Also search approved user news submissions
    published_submissions = UserNews.query.filter_by(status='approved').all()
    if query:
        for sub in published_submissions:
            if query in (sub.title or '').lower() or query in (sub.content or '').lower() or query in (sub.location or '').lower():
                # Format to look somewhat like a news_article for the template
                results.append({
                    'id': sub.id,
                    'title': sub.title,
                    'is_submission': True,
                    'excerpt': sub.content[:100] + '...',
                    'category': sub.category,
                    'image': sub.media_url or get_dynamic_news_image(sub.title, sub.category, f"user_{sub.id}"),
                    'publish_date': sub.incident_date.strftime('%Y-%m-%d') if sub.incident_date else ''
                })
    
    return render_template('search_results.html', query=query, results=results)

@app.route('/search/image', methods=['POST'])
def search_image():
    if 'image' not in request.files:
        flash("No image uploaded for search.", "error")
        return redirect(url_for('index'))
        
    file = request.files['image']
    if file.filename == '':
        flash("Empty image file.", "error")
        return redirect(url_for('index'))
        
    # Simulated Image Search Backend
    # Extract query context from the original filename to simulate AI vision
    import os
    base_name = os.path.splitext(file.filename)[0]
    
    # Clean up filename for a better search query
    # Replace common separators with spaces and remove numeric timestamps/hashes
    import re
    cleaned_name = re.sub(r'[-_]', ' ', base_name)
    cleaned_name = re.sub(r'\d+', '', cleaned_name).strip()
    
    if len(cleaned_name) < 3:
        placeholder_query = "technology" # Hardcoded fallback
    else:
        placeholder_query = cleaned_name

    flash(f"Image analyzed. Showing simulated results related to visual content: '{placeholder_query}'.", "info")
    return redirect(url_for('search', q=placeholder_query))

@app.route('/submit-local-news', methods=['GET', 'POST'])
def submit_local_news():
    if 'user' not in session:
        return redirect(url_for('landing'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        location = request.form.get('location')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        incident_date = request.form.get('incident_date')
        content = request.form.get('content')
        
        if not all([title, category, location, content]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('submit_local_news'))
            
        # Handle Image/Video Upload
        media_url = None
        if 'media' in request.files:
            file = request.files['media']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"user_{session['user']}_{int(time.time())}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'news', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                media_url = f"/{filepath.replace(os.sep, '/')}"
                
        new_submission = UserNews(
            title=title,
            category=category,
            location=location,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            incident_date=incident_date,
            content=content,
            media_url=media_url,
            submitted_by_id=session.get('user_id'),
            status='pending'
        )
        
        db.session.add(new_submission)
        db.session.commit()
        
        flash("Your news has been submitted for review!", "success")
        return redirect(url_for('index'))
        
    return render_template('submit_local_news.html')

@app.route('/view-submission/<int:news_id>')
def view_submission(news_id):
    if 'user' not in session:
        return redirect(url_for('landing'))
        
    news = UserNews.query.get_or_404(news_id)
    
    # Access Control: Only submitter or staff can view
    is_staff = session.get('role') in ['reporter', 'admin']
    is_owner = news.submitted_by_id == session.get('user_id')
    
    if not (is_staff or is_owner):
        flash("You do not have permission to view this submission.", "error")
        return redirect(url_for('index'))
        
    return render_template('view_submission.html', news=news)

@app.route('/advertise', methods=['GET', 'POST'])
def advertise():
    if request.method == 'POST':
        if 'user' not in session:
            flash("You need to login to submit an advertisement.", "error")
            return redirect(url_for('landing'))
            
        company_name = request.form.get('company_name')
        title = request.form.get('title')
        contact_email = request.form.get('contact_email')
        contact_phone = request.form.get('contact_phone')
        plan_name = request.form.get('plan_name')
        target_url = request.form.get('target_url')
        duration = request.form.get('duration', 7)
        payment_details = request.form.get('payment_details', '')
        
        # New Missing Fields
        how_much = request.form.get('how_much')
        what_all = request.form.get('what_all')
        who_all = request.form.get('who_all')
        placement = request.form.get('placement', 'bottom') # Default to bottom if not specified
        
        # Handle File Upload
        file = request.files.get('ad_image')
        image_url = request.form.get('image_url') # Fallback if URL still provided
        
        if file and file.filename != '':
            filename = secure_filename(f"ad_{int(time.time())}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename='uploads/' + filename)
            
        if not all([company_name, title, image_url, duration]):
            flash("Please fill in all required fields and upload an image.", "error")
            return redirect(url_for('advertise'))
            
        new_ad = Advertisement(
            company_name=company_name,
            title=title,
            contact_email=contact_email,
            contact_phone=contact_phone,
            plan_name=plan_name,
            image_url=image_url,
            target_url=target_url,
            duration=int(duration),
            payment_details=payment_details,
            status='Pending Payment',
            active=False,
            user_id=session.get('user_id'),
            how_much=how_much,
            what_all=what_all,
            who_all=who_all,
            placement=placement
        )
        
        db.session.add(new_ad)
        db.session.commit()
        
        flash("Your advertisement details have been confirmed! Please complete the payment to proceed.", "success")
        return redirect(url_for('payment_page', ad_id=new_ad.id))
        
    return render_template('advertise.html')

@app.route('/payment/<int:ad_id>', methods=['GET', 'POST'])
def payment_page(ad_id):
    if 'user' not in session:
        flash("Please login to view payment details.", "error")
        return redirect(url_for('landing'))
        
    ad = Advertisement.query.get_or_404(ad_id)
    
    # Check ownership
    if ad.user_id != session.get('user_id'):
        flash("You are not authorized to view this page.", "error")
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        payment_details = request.form.get('payment_details')
        amount_paid = request.form.get('amount_paid')
        if payment_details and amount_paid:
            ad.payment_details = payment_details
            ad.amount_paid = amount_paid
            ad.payment_status = 'pending_verification'
            ad.status = 'Payment Under Review'
            db.session.commit()
            
            # Validation logic
            # Extract number from ad.how_much (e.g. "₹100" -> 100)
            try:
                expected_amount = int(re.sub(r'[^\d]', '', ad.how_much))
                actual_amount = int(re.sub(r'[^\d]', '', amount_paid))
                
                if expected_amount != actual_amount:
                    flash(f"Warning: The amount paid (₹{actual_amount}) does not match the selected plan price ({ad.how_much}). Administrator will verify this.", "warning")
                else:
                    flash("Payment details submitted for verification! Your ad will be reviewed soon.", "success")
            except Exception:
                flash("Payment details submitted. Administrator will verify the amount.", "success")
                
            return redirect(url_for('index'))
        else:
            flash("Please provide all payment details.", "error")
            
    return render_template('payment.html', ad=ad)

@app.route('/landing')
def landing():
    return render_template('landing.html')


# Strict Validation Rules
USERNAME_REGEX = r'^[a-zA-Z0-9_]{3,20}$'
# Updated to allow more special characters: @$!%*?&_#-.
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_#\-.])[A-Za-z\d@$!%*?&_#\-.]{8,}$'

def is_valid_username(username):
    return re.match(USERNAME_REGEX, username)

def is_strong_password(password):
    return re.match(PASSWORD_REGEX, password)

# ... (routes) ...

@app.before_request
def initialize_database():
    if not hasattr(app, 'db_initialized'):
        db.create_all()
        
        # Create or Update Admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@auranews.com', role='admin', full_name='System Admin')
            admin.set_password('Admin@123') # Strong password
            db.session.add(admin)
            db.session.commit()
            print("Admin user created with strong password.")
        else:
            # OPTIONAL: Force update existing admin to strong password if it appears to be the old weak one
            # Note: We can't check the hash directly against 'admin123' easily without checking, 
            # but we can just set it to ensure compliance if this is a dev/demo env.
            if admin.check_password('admin123'):
                admin.set_password('Admin@123')
                db.session.commit()
                print("Admin password updated to strong policy.")

        # Ensure demo user also exists
        if not User.query.filter_by(username='user_demo').first():
            demo = User(username='user_demo', email='demo@auranews.com', role='user', full_name='Demo User')
            demo.set_password('AuraNews2026!')
            db.session.add(demo)
            db.session.commit()
            print("Demo user created.")

        # Ensure default reporter exists
        if not User.query.filter_by(username='reporter').first():
            reporter = User(username='reporter', email='reporter@auranews.com', role='reporter', full_name='News Reporter')
            reporter.set_password('Reporter@123')
            db.session.add(reporter)
            db.session.commit()
            print("Default reporter created.")
            
        # Ensure default advertiser exists
        if not User.query.filter_by(username='advertiser').first():
            advertiser = User(username='advertiser', email='advertiser@auranews.com', role='advertiser', full_name='Ad Partner')
            advertiser.set_password('Advertiser@123')
            db.session.add(advertiser)
            db.session.commit()
            print("Default advertiser created.")
            
        # Migrate Advertisement Table for Redesign
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                # Add contact_email if missing
                try:
                    conn.execute(text("ALTER TABLE advertisement ADD COLUMN contact_email VARCHAR(120)"))
                    conn.commit()
                except: pass
                
                # Add contact_phone if missing
                try:
                    conn.execute(text("ALTER TABLE advertisement ADD COLUMN contact_phone VARCHAR(20)"))
                    conn.commit()
                except: pass

                # Add payment_status if missing
                try:
                    conn.execute(text("ALTER TABLE advertisement ADD COLUMN payment_status VARCHAR(20) DEFAULT 'unpaid'"))
                    conn.commit()
                except: pass

                # Add plan_name if missing
                try:
                    conn.execute(text("ALTER TABLE advertisement ADD COLUMN plan_name VARCHAR(50)"))
                    conn.commit()
                except: pass
                
                # Add plan_name if missing
                try:
                    conn.execute(text("ALTER TABLE advertisement ADD COLUMN plan_name VARCHAR(50)"))
                    conn.commit()
                except: pass
        except Exception as e:
            print(f"Migration error: {e}")
            
        app.db_initialized = True


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validation checks
        if not is_valid_username(username):
            flash("Invalid username format.", "error")
            return redirect(url_for('landing'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user'] = user.username
            session['user_id'] = user.id
            session['role'] = user.role
            
            session['user_data'] = {
                'name': user.full_name,
                'username': user.username,
                'email': user.email,
                'joined': user.joined,
                'role': user.role,
                'picture': user.picture,
                'location': user.location,
                'phone': user.phone,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'dob_day': user.dob_day,
                'dob_month': user.dob_month,
                'dob_year': user.dob_year,
                'gender': user.gender,
                'country': user.country,
                'city': user.city,
                'house_no': user.house_no,
                'apartment_road_area': user.apartment_road_area,
                'state_province': user.state_province,
                'subscriber_id': user.subscriber_id,
                'voice_time': user.voice_time,
                'voice_enabled': user.voice_enabled
            }
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'reporter':
                return redirect(url_for('reporter_dashboard'))
            
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.", "error")
            return redirect(url_for('landing'))
            
    return redirect(url_for('landing'))

@app.route('/api/check_username', methods=['POST'])
def api_check_username():
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({"error": "Invalid request"}), 400
        
    username = data['username'].strip()
    if not is_valid_username(username):
        return jsonify({"available": False, "message": "Username must be 3-20 characters (letters, numbers, underscores)."})
        
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({"available": False, "message": "Username already taken."})
        
    return jsonify({"available": True, "message": "Username available."})

@app.route('/api/check_email', methods=['POST'])
def api_check_email():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({"error": "Invalid request"}), 400
        
    email = data['email'].strip()
    if not email or '@' not in email:
        return jsonify({"available": False, "message": "Please enter a valid email address."})
        
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"available": False, "message": "Email already in use."})
        
    return jsonify({"available": True, "message": "Email available."})

@app.route('/api/track_behavior', methods=['POST'])
def api_track_behavior():
    """Endpoint for tracking active reading time on articles for the AI personalization engine."""
    if 'user_id' not in session:
        return jsonify({"status": "unauthorized"}), 401
        
    data = request.get_json()
    if not data:
        return jsonify({"status": "invalid"}), 400
        
    article_id = data.get('article_id')
    time_spent = data.get('time_spent', 0)
    category = data.get('category', '')
    
    if not article_id:
        return jsonify({"status": "missing_id"}), 400
        
    try:
        interaction = UserInteraction(
            user_id=session['user_id'],
            article_id=str(article_id),
            category=category,
            time_spent=int(time_spent)
        )
        db.session.add(interaction)
        
        # NEW: Also increase base preference score if they read it deeply
        if int(time_spent) >= 30 and category:
            cat_title = category.strip().title()
            pref = UserPreference.query.filter_by(user_id=session['user_id'], category=cat_title).first()
            if pref:
                pref.score += 2 # Heavy weighting for deliberate reading
            else:
                pref = UserPreference(user_id=session['user_id'], category=cat_title, score=2)
                db.session.add(pref)

        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not fullname or len(fullname) < 2:
            flash("Please enter a valid full name.", "error")
            return redirect(url_for('landing'))
            
        if not is_valid_username(username):
            flash("Username must be 3-20 characters (letters, numbers, underscores).", "error")
            return redirect(url_for('landing'))

        if not email or '@' not in email:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for('landing'))
        
        if not is_strong_password(password):
            flash("Password must be 8+ chars with uppercase, lowercase, number, and special character.", "error")
            return redirect(url_for('landing'))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('landing'))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already taken.", "error")
            return redirect(url_for('landing'))
            
        new_user = User(
            username=username,
            email=email,
            full_name=fullname,
            role='user'
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        session['user'] = new_user.username
        session['user_id'] = new_user.id
        session['role'] = new_user.role
        session['user_data'] = {
            'name': new_user.full_name,
            'username': new_user.username,
            'email': new_user.email,
            'joined': new_user.joined,
            'role': new_user.role,
            'picture': new_user.picture,
            'location': new_user.location,
            'phone': new_user.phone,
            'first_name': new_user.first_name,
            'last_name': new_user.last_name,
            'dob_day': new_user.dob_day,
            'dob_month': new_user.dob_month,
            'dob_year': new_user.dob_year,
            'gender': new_user.gender,
            'country': new_user.country,
            'city': new_user.city,
            'voice_time': new_user.voice_time,
            'voice_enabled': new_user.voice_enabled
        }
        
        flash("Welcome to JANAVAAKYA – Voice of the People!", "success")
        return redirect(url_for('index'))
    return redirect(url_for('landing'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route("/login/google")
def login_google():
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth/google/callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')

    if user_info:
        email = user_info.get('email')
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user via Google
            username = user_info.get('given_name', 'GoogleUser').lower() + "_" + str(os.urandom(4).hex())
            # Ensure unique username
            while User.query.filter_by(username=username).first():
                 username = user_info.get('given_name', 'GoogleUser').lower() + "_" + str(os.urandom(4).hex())
                 
            user = User(
                username=username,
                email=email,
                full_name=user_info.get('name'),
                role='user',
                picture=user_info.get('picture')
            )
            db.session.add(user)
            db.session.commit()
            
        session["user"] = user.username
        session['user_id'] = user.id
        session['role'] = user.role
        session["user_data"] = {
            'name': user.full_name,
            'email': user.email,
            'picture': user.picture,
            'username': user.username,
            'joined': user.joined,
            'role': user.role,
            'location': user.location,
            'phone': user.phone,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'dob_day': user.dob_day,
            'dob_month': user.dob_month,
            'dob_year': user.dob_year,
            'gender': user.gender,
            'country': user.country,
            'city': user.city,
            'voice_time': user.voice_time,
            'voice_enabled': user.voice_enabled
        }
        flash(f"Welcome {user.full_name}!", "success")
    else:
        flash("Failed to retrieve user information from Google.", "error")

    return redirect(url_for("index"))

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('landing'))
    
    # Redirect Reporter to Reporter Dashboard (Profile disabled for reporters)
    if session.get('role') == 'reporter':
        return redirect(url_for('reporter_dashboard'))
    
    # Determine which layout to use
    layout = 'reporter_layout.html' if session.get('role') == 'reporter' else 'base.html'
    
    # Fetch user submissions categorized by status
    user_id = session.get('user_id')
    approved_news = UserNews.query.filter_by(submitted_by_id=user_id, status='approved').order_by(UserNews.created_at.desc()).all()
    pending_news = UserNews.query.filter_by(submitted_by_id=user_id, status='pending').order_by(UserNews.created_at.desc()).all()
    rejected_news = UserNews.query.filter_by(submitted_by_id=user_id, status='rejected').order_by(UserNews.created_at.desc()).all()
    
    # Fetch advertisements
    ads_submitted = Advertisement.query.filter_by(user_id=user_id).order_by(Advertisement.created_at.desc()).all()
    
    # Get user data including manual interests
    user = User.query.get(user_id)
    user_data = session.get('user_data', {})
    if user:
        user_data['manual_interests'] = user.manual_interests or ''
    
    return render_template('profile.html', 
                           user_data=user_data, 
                           layout=layout,
                           approved_news=approved_news,
                           pending_news=pending_news,
                           rejected_news=rejected_news,
                           ads_submitted=ads_submitted)

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    # Fetch reading history
    history_items = ReadingHistory.query.filter_by(user_id=user_id).order_by(ReadingHistory.timestamp.desc()).limit(50).all()
    
    # Fetch top interests
    preferences = UserPreference.query.filter_by(user_id=user_id).order_by(UserPreference.score.desc()).all()
    
    # Map history to titles (best effort)
    history_display = []
    for item in history_items:
        title = "Article from Feed"
        # 1. Try finding in mock news_articles
        article = next((a for a in news_articles if str(a['id']) == item.article_id), None)
        if article:
            title = article['title']
        else:
            # 2. Try finding in live_article_cache
            cached = live_article_cache.get(item.article_id)
            if cached and 'article' in cached:
                title = cached['article'].get('title', title)

        history_display.append({
            'title': title,
            'category': item.category,
            'timestamp': item.timestamp,
            'url': url_for('article', article_id=item.article_id) if not str(item.article_id).startswith('user_') and len(str(item.article_id)) < 30 else url_for('live_article', article_id=item.article_id)
        })

    return render_template('history.html', history=history_display, preferences=preferences)

@app.route('/api/notifications/read', methods=['POST'])
def mark_notifications_read():
    if 'user_id' in session:
        Notification.query.filter_by(user_id=session['user_id']).update({Notification.is_read: True})
        db.session.commit()
    return {"status": "success"}

@app.route('/live-location')
def live_location():
    if 'user' not in session:
        return redirect(url_for('landing'))
    return render_template('location.html')

# Sub-categories mapping for premium layout
# Sub-categories mapping for premium layout
CATEGORIES_SUBCATS = {
    'sports': ['Cricket', 'Football', 'Tennis', 'Other Sports', 'Local Sports', 'Specials', 'Sports+'],
    'entertainment': ['Movies', 'Music', 'Celebrity', 'TV Shows', 'OTT'],
    'news': ['Global', 'India', 'Kerala', 'Local'],
    'tech': ['Gadgets', 'Sci-Tech', 'Software', 'AI'],
    'business': ['Markets', 'Auto', 'Economy', 'Corporate']
}

def get_live_articles(category=None, subcat=None):
    articles = []
    category_title = 'live_news_title' # Default translation key
    
    try:
        raw_articles = []
        if category:
            # Normalize category for both mapping and display
            category_clean = category.strip()
            category_lower = category_clean.lower()
            
            # Handle PascalCase/camelCase for search queries (e.g. T20WorldCup -> T20 World Cup)
            import re
            search_query_base = re.sub(r'(?<!^)(?=[A-Z])', ' ', category_clean)
            
            if subcat:
                search_query = f"{search_query_base} {subcat}"
            else:
                search_query = search_query_base
            
            # Try translation keys first
            category_title = f"nav_{category_lower}"
            if category_title not in TRANSLATIONS.get('en', {}):
                category_title = category.title()
            
            print(f"[DEBUG] Fetching articles for category: {category_lower}, subcat: {subcat}")
            
            # 1. Identify and add BASE feeds
            if category_lower == 'premium':
                premium_topics = ['BUSINESS', 'TECHNOLOGY', 'SCIENCE']
                for topic in premium_topics:
                    fetched = fetch_gn_rss(f"https://news.google.com/rss/headlines/section/topic/{topic}")
                    raw_articles.extend(fetched)
            elif not subcat and category_lower in TOPIC_MAP:
                fetched = fetch_gn_rss(TOPIC_MAP[category_lower])
                print(f"[DEBUG] Category '{category_lower}' from TOPIC_MAP: fetched {len(fetched)} articles")
                raw_articles.extend(fetched)
            else:
                # Generic search for anything else or subcategories
                raw_articles.extend(fetch_gn_rss(f"https://news.google.com/rss/search?q={search_query}"))

            # 2. ADD LIVE NEWS QUERIES for ALL categories (Expanding the Sports-only feature)
            live_queries = []
            if category_lower == 'sports':
                live_queries = ["T20 World Cup live score", "Live Cricket match updates", "Latest Sports News Live", "Ongoing matches today"]
            else:
                # Standard live queries for other major categories to make them "Live"
                live_queries = [f"{category_clean} live news today", f"Latest {category_clean} updates breaking news"]
                
                # Specialized boosters for major sections
                if 'business' in category_lower:
                    live_queries.extend(["Stock market live updates", "Sensex Nifty live today"])
                elif 'tech' in category_lower:
                    live_queries.extend(["Latest tech launches live", "Breaking gadgets news live"])
                elif 'entertainment' in category_lower or 'movie' in category_lower:
                    live_queries.extend(["Bollywood news live", "Hollywood updates live"])
                elif 'kerala' in category_lower:
                    live_queries.extend([
                        "Kerala latest breaking news", 
                        "Kerala politics news today", 
                        "Kerala local news updates",
                        "Kerala social news",
                        "Kerala development news",
                        "Kerala news live stream updates"
                    ])
            
            # Fetch and inject live items - limited per query to maintain performance
            for q in live_queries:
                fetched = fetch_gn_rss(f"https://news.google.com/rss/search?q={q}")[:10]
                print(f"[DEBUG] Live query '{q}': fetched {len(fetched)} articles")
                raw_articles.extend(fetched)
            
            print(f"[DEBUG] Total raw articles before filtering: {len(raw_articles)}")

            # Boost articles with 'Live' or 'Match' or 'Just In' keywords in the title
            for article in raw_articles:
                title = article.get('title', '').upper()
                if any(word in title for word in ['LIVE', 'SCORE', 'UPDATE', 'MATCH', 'BREAKING']):
                    # Adjust 'publishedAt' slightly forward in time (internally for sorting) to pull it to top
                    # But don't mess up the display, so we just use it for sorting
                    # Or better: we'll handle this in the final sort
                    article['_priority'] = 1
                else:
                    article['_priority'] = 0
            
            # Filter mock news
            mock_news_filtered = []
            for article in news_articles:
                art_cat = article.get('category', '').lower()
                if art_cat == category_lower:
                    mock_news_filtered.append(article)
                elif category_lower == 'tech' and art_cat == 'technology':
                    mock_news_filtered.append(article)
                elif category_lower == 'premium' and is_premium(article.get('category')):
                    mock_news_filtered.append(article)
            
            manual_news = []
            for article in mock_news_filtered:
                m_article = article.copy()
                m_id = str(article.get('id', ''))
                m_article['url'] = m_article.get('url', f"/article/{m_id}")
                m_article['publishedAt'] = article.get('publish_date') or (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
                m_article['source'] = {'name': article.get('author', 'Janavaakya')}
                m_article['description'] = article.get('excerpt', '')
                m_article['content_snippet'] = article.get('content', '')
                m_article['urlToImage'] = article.get('image', '')
                m_article['internal_id'] = f"manual_{m_id}"
                # For consistency with dynamic articles
                m_article['id'] = m_article['internal_id']
                m_article['image'] = m_article['urlToImage']
                m_article['publish_date'] = m_article['publishedAt'][:10]
                manual_news.append(m_article)
            
            raw_articles.extend(manual_news)
        else:
            global_articles = fetch_gn_rss("https://news.google.com/rss/headlines/section/topic/WORLD")
            india_articles = fetch_gn_rss("https://news.google.com/rss/search?q=Kerala+India+News")
            live_booster = fetch_gn_rss("https://news.google.com/rss/search?q=Global+Breaking+News+Live")[:10]
            
            manual_news = []
            for article in news_articles:
                m_article = article.copy()
                m_id = str(article.get('id', ''))
                m_article['url'] = m_article.get('url', f"/article/{m_id}")
                m_article['publishedAt'] = article.get('publish_date') or (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
                m_article['source'] = {'name': article.get('author', 'Janavaakya')}
                m_article['description'] = article.get('excerpt', '')
                m_article['content_snippet'] = article.get('content', '')
                m_article['urlToImage'] = article.get('image', '')
                m_article['internal_id'] = f"manual_{m_id}"
                m_article['id'] = m_article['internal_id']
                m_article['image'] = m_article['urlToImage']
                m_article['publish_date'] = m_article['publishedAt'][:10]
                manual_news.append(m_article)

            raw_articles = live_booster + india_articles + global_articles + manual_news
        # Finally, pulse-check all headlines for 'LIVE' or 'MATCH' to ensure they stay at the top across all categories
        for article in raw_articles:
            title = article.get('title', '').upper()
            if any(word in title for word in ['LIVE', 'SCORE', 'UPDATE', 'MATCH', 'BREAKING', 'T20']):
                article['_priority'] = 1
            elif '_priority' not in article:
                article['_priority'] = 0

        # Priority sort: items with _priority=1 go first, then by date within those groups
        raw_articles.sort(key=lambda x: (x.get('_priority', 0), x.get('publishedAt', '')), reverse=True)
        
        seen_ids = set()
        seen_titles = set()
        for article in raw_articles:
            article_id = get_article_id(article)
            
            # Clean title for comparison
            raw_title = article.get('title', '').strip()
            clean_title = clean_article_title(raw_title).lower()
            
            # Deduplicate by both ID (URL) and Title
            if article_id in seen_ids or clean_title in seen_titles:
                continue
            
            seen_ids.add(article_id)
            if len(clean_title) > 10:
                seen_titles.add(clean_title)
            
            source_name = "Global News"
            if article.get('source') and isinstance(article.get('source'), dict):
                source_name = article.get('source').get('name', 'Live News')
            elif isinstance(article.get('source'), str):
                source_name = article.get('source')
            
            article['source_display'] = source_name
            article['title'] = clean_article_title(article.get('title'))
            article['internal_id'] = article_id
            
            # Unique and Relevant Image assignment
            img_url = article.get('urlToImage') or article.get('image')
            
            # If image is missing or a tiny placeholder, use dynamic relevance
            if not img_url or '/1x1' in img_url or 'placeholder' in img_url.lower():
                img_url = get_dynamic_news_image(article.get('title', ''), category or article.get('category'), article_id)
            
            article['urlToImage'] = img_url
            article['image'] = img_url
            article['id'] = article_id
            article['publish_date'] = article.get('publishedAt', '')[:10]
            cat_upper = category.upper() if category else "LIVE NEWS"
            article['category'] = cat_upper
            article['excerpt'] = article.get('description') or article.get('content_snippet')
            
            live_article_cache[article_id] = {
                'article': article,
                'timestamp': time.time()
            }
            articles.append(article)
            
    except Exception as e:
        print(f"Error fetching live articles: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"[DEBUG] Final articles count for category '{category}': {len(articles)}")
    
    if articles and category:
        # Trigger interest-based notification for the top story
        # send_personalized_notifications handles the preference score check and deduplication
        top_art = articles[0]
        send_personalized_notifications(category, top_art['id'], top_art['title'])

    return articles, category_title

@app.route('/live-news')
def live_news():
    if 'user' not in session:
        return redirect(url_for('landing'))
    
    # Block Advertiser from news
    if session.get('role') == 'advertiser':
        flash("Advertisers do not have access to news content.", "info")
        return redirect(url_for('advertiser_dashboard'))
    
    category = request.args.get('category')
    articles, list_title = get_live_articles(category)
    
    # Localize articles for the current language
    lang = session.get('lang', 'en')
    if lang == 'ml':
        localized_articles = []
        for a in articles:
            localized_articles.append({
                **a,
                'title': a.get('title_ml', a.get('title', '')),
                'description': a.get('description_ml', a.get('description', '')),
                'content_snippet': a.get('content_ml', a.get('content_snippet', ''))
            })
        articles = localized_articles

    error_message = None
    if not articles:
        error_message = "No live news available at the moment."

    return render_template('live_news.html', articles=articles, error=error_message, list_title=list_title)

@app.route('/kerala-news')
def kerala_news():
    return redirect(url_for('live_news', category='Kerala'))

@app.route('/live-stream')
def live_stream():
    if 'user' not in session:
        return redirect(url_for('landing'))
    
    # Get stream source from query parameter (default to youtube)
    stream_source = request.args.get('source', 'youtube')
    
    # Define available stream sources
    stream_sources = {
        'cricket': {
            'name': 'Live Cricket: IPL / World Cup',
            # Using Sky Sports News as a 24/7 sports fallback since true live match streams change. 
            # When an actual IPL/World Cup match is on, this URL can be swapped for an official broadcast link.
            'url': 'https://www.youtube.com/embed/live_stream?channel=UCmOjmmEMnkyNlJ-0oD7JkIg&autoplay=1&mute=1&enablejsapi=1', 
            'description': 'Live cricket match streaming direct from the venue.',
            'badge': 'CRICKET LIVE',
            'title': 'Live: IPL / World Cup Match',
            'subtitle': 'Experience the thrill of the ongoing cricket match live from the stadium. High-definition streaming with uninterrupted coverage.',
            'event': 'Cricket Live',
            'status': 'Ongoing',
            'commentary': 'English/Hindi',
            'next_match': 'Check Schedule',
            'match_stats': True
        },
        'youtube': {
            'name': 'Sky News Live',
            'url': 'https://www.youtube.com/embed/live_stream?channel=UCoMdktPbSTixAyNGrCJUeVg&autoplay=1&mute=1&enablejsapi=1',
            'description': '24/7 Sky News Live Stream',
            'badge': 'GLOBAL NEWS',
            'title': 'Live: Sky News Global',
            'subtitle': 'Watch the latest global news coverage directly from Sky News. Stay informed with 24/7 breaking news.',
            'event': 'News Broadcast',
            'status': '24/7 Live',
            'commentary': 'English',
            'next_match': 'Streaming Now',
            'match_stats': False
        },
        'youtube2': {
            'name': 'Al Jazeera English Live',
            'url': 'https://www.youtube.com/embed/live_stream?channel=UCTeVunLEkE2Q0OabYF4bA3g&autoplay=1&mute=1&enablejsapi=1',
            'description': '24/7 Al Jazeera English Live Stream',
            'badge': 'WORLD NEWS',
            'title': 'Live: Al Jazeera English',
            'subtitle': 'In-depth global news and analysis from Al Jazeera English. Connecting you to the world.',
            'event': 'News Broadcast',
            'status': '24/7 Live',
            'commentary': 'English',
            'next_match': 'Streaming Now',
            'match_stats': False
        },
        'demo': {
            'name': 'NBC News Live',
            'url': 'https://www.youtube.com/embed/live_stream?channel=UCeY0bbntWzzVIaj2z3QigXg&autoplay=1&mute=1&enablejsapi=1',
            'description': '24/7 NBC News Live Stream',
            'badge': 'US NEWS',
            'title': 'Live: NBC News',
            'subtitle': 'The latest news, video, and comprehensive coverage from the NBC News digital team.',
            'event': 'News Broadcast',
            'status': '24/7 Live',
            'commentary': 'English',
            'next_match': 'Streaming Now',
            'match_stats': False
        }
    }
    
    # Get the selected stream or default to cricket
    current_stream = stream_sources.get(stream_source, stream_sources['cricket'])
    
    return render_template('live_stream.html', 
                         stream_source=stream_source,
                         current_stream=current_stream,
                         available_sources=stream_sources)

@app.route('/live-article/<article_id>')
def live_article(article_id):
    # Allow guests to read articles
    
    if article_id.startswith('manual_'):
        real_id = article_id.split('manual_')[1]
        article_obj = next((a for a in news_articles if str(a['id']) == real_id), None)
        if not article_obj:
            flash("Manual article not found.", "error")
            return redirect(url_for('live_news'))
        
        # Map fields for localized_article view
        article = article_obj.copy()
        article['full_content'] = article_obj.get('content', '')
        article['source_display'] = article_obj.get('author', 'Janavaakya')
        article['publishedAt'] = article_obj.get('publish_date') or datetime.utcnow().strftime("%Y-%m-01") # Dummy month for display
    else:
        cached_data = live_article_cache.get(article_id)
        if not cached_data:
            flash("Article session expired or not found.", "error")
            return redirect(url_for('live_news'))
        article = cached_data['article']
    
    # Fetch full content if not already cached
    if 'full_content' not in article or not article['full_content']:
        # Pass the extracted content_snippet or description or excerpt as a fallback
        snippet = article.get('content_snippet') or article.get('description') or article.get('excerpt', '')
        full_text = get_full_article_content(article.get('url'), title=article.get('title'), fallback_snippet=snippet, category=article.get('category'))
        if full_text:
            article['full_content'] = full_text
            # Update cache
            if article_id in live_article_cache:
                live_article_cache[article_id]['article'] = article
    
    # Simple localization of article content (if applicable)
    lang = session.get('lang', 'en')
    def localize_article(article):
        if lang == 'ml':
            return {
                **article, 
                'title': article.get('title_ml', article['title']), 
                'description': article.get('description_ml', article.get('description', '')),
                'content_snippet': article.get('content_ml', article.get('content_snippet', '')),
                'full_content': article.get('full_content_ml', article.get('full_content', ''))
            }
        return article

    localized_article = localize_article(article)
    
    # Premium check
    if is_premium(localized_article.get('category')):
        user_id = session.get('user_id')
        user = User.query.get(user_id) if user_id else None
        if not user or not user.is_subscribed:
            flash("This is Premium Content. Please subscribe to read the full article.", "info")
            return redirect(url_for('premium_subscribe'))
    
    # NEW: Track reading history for personalization and clear related notification
    if 'user_id' in session:
        user_id = session['user_id']
        track_reading_history(user_id, article_id, localized_article.get('category'))
        
        # Clear specific notification for this article if it exists
        notif = Notification.query.filter_by(user_id=user_id, article_id=str(article_id), is_read=False).first()
        if notif:
            notif.is_read = True
            db.session.commit()
    
    return render_template('live_article_view.html', article=localized_article)

@app.route('/submit-news', methods=['GET', 'POST'])
@reporter_required
def submit_news():
    # Login check handled by decorator

    
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        content = request.form.get('content')

        
        if not title or not content:
            flash("Title and Content are required.", "error")
            return redirect(url_for('submit_news'))
            
        # Handle Image Upload
        image_url = '/static/img/default_news.jpg' # Default
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"news_{session['user']}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'news', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                image_url = f"/{filepath.replace(os.sep, '/')}"

        # Create new article object
        new_id = max([a['id'] for a in news_articles]) + 1 if news_articles else 1
        new_article = {
            "id": new_id,
            "title": title,
            "category": category,
            "excerpt": content[:100] + "...",
            "content": content,
            "image": image_url,
            "author": session['user'],
            "featured": False,

            # For ML support, we'd ideally translate here, but for now just copy
            "title_ml": title,
            "category_ml": category, 
            "excerpt_ml": content[:100] + "...",
            "content_ml": content
        }
        
        # Insert at the beginning of the list to show as latest
        news_articles.insert(0, new_article)
        
        flash("News submitted successfully!", "success")
        return redirect(url_for('index'))

    return render_template('submit_news.html')

@app.route('/update_photo', methods=['POST'])
def update_photo():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if 'photo' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('profile'))
    
    file = request.files['photo']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"user_{session['user']}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        file.save(filepath)
        
        # Update user in DB
        user = User.query.get(session['user_id'])
        if user:
            web_path = f"/{filepath.replace(os.sep, '/')}"
            user.picture = web_path
            db.session.commit()
            
            # Update session
            session['user_data']['picture'] = web_path
            session.modified = True
        
        flash('Profile photo updated successfully!', 'success')
    else:
        flash('Invalid file type', 'error')
        
    return redirect(url_for('profile'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('landing'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('landing'))

    # Handle text fields
    new_email = request.form.get('email', user.email).strip()
    if new_email and new_email != user.email:
        if User.query.filter_by(email=new_email).first():
            flash("Email already taken by another user.", "error")
            return redirect(url_for('profile'))
        user.email = new_email

    user.first_name = request.form.get('first_name', user.first_name)
    user.last_name = request.form.get('last_name', user.last_name)
    # Sync full_name if both are provided
    if user.first_name and user.last_name:
        user.full_name = f"{user.first_name} {user.last_name}"
    elif user.first_name:
        user.full_name = user.first_name
    user.phone = request.form.get('phone', user.phone)
    user.dob_day = request.form.get('dob_day', user.dob_day)
    user.dob_month = request.form.get('dob_month', user.dob_month)
    user.dob_year = request.form.get('dob_year', user.dob_year)

    user.gender = request.form.get('gender', user.gender)
    user.country = request.form.get('country', user.country)
    user.city = request.form.get('city', user.city)
    user.house_no = request.form.get('house_no', user.house_no)
    user.apartment_road_area = request.form.get('apartment_road_area', user.apartment_road_area)
    user.state_province = request.form.get('state_province', user.state_province)
    
    # Generate common SubscriberID if missing (matches screenshot style)
    if not user.subscriber_id:
        import uuid
        user.subscriber_id = str(uuid.uuid4())
    
    # Location field can be a combination of City and Country
    if user.city and user.country:
        user.location = f"{user.city}, {user.country}"
    elif user.city:
        user.location = user.city
    elif user.country:
        user.location = user.country

    # Voice Assistant Settings
    voice_hour = request.form.get('voice_hour')
    voice_minute = request.form.get('voice_minute')
    voice_ampm = request.form.get('voice_ampm')
    
    if voice_hour and voice_minute and voice_ampm:
        h = int(voice_hour)
        if voice_ampm == 'PM' and h != 12:
            h += 12
        if voice_ampm == 'AM' and h == 12:
            h = 0
        user.voice_time = f"{h:02d}:{voice_minute}"
    
    user.voice_enabled = 'voice_enabled' in request.form
    
    db.session.commit()
    
    # Update session data to reflect changes immediately
    session['user_data'] = {
        'name': user.full_name,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'email': user.email,
        'joined': user.joined,
        'role': user.role,
        'picture': user.picture,
        'phone': user.phone,
        'dob_day': user.dob_day,
        'dob_month': user.dob_month,
        'dob_year': user.dob_year,
        'gender': user.gender,
        'country': user.country,
        'city': user.city,
        'house_no': user.house_no,
        'apartment_road_area': user.apartment_road_area,
        'state_province': user.state_province,
        'subscriber_id': user.subscriber_id,
        'location': user.location,
        'voice_time': user.voice_time,
        'voice_enabled': user.voice_enabled
    }
    session.modified = True
    
    flash("Profile updated successfully!", "success")
    return redirect(url_for('profile'))

@app.route('/update_interests', methods=['POST'])
def update_interests():
    """Handle manual interest selection updates"""
    if 'user_id' not in session:
        return redirect(url_for('landing'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('landing'))
    
    # Get selected interests from form
    selected_interests = request.form.getlist('interests')
    
    # Store as comma-separated string
    if selected_interests:
        user.manual_interests = ','.join(selected_interests)
        
        # Also boost these categories in UserPreference to give them immediate weight
        for category in selected_interests:
            category = category.strip().title()
            pref = UserPreference.query.filter_by(user_id=user.id, category=category).first()
            if pref:
                # Add bonus points for manual selection (but don't override reading behavior completely)
                pref.score += 2
            else:
                # Create new preference with initial score
                pref = UserPreference(user_id=user.id, category=category, score=3)
                db.session.add(pref)
    else:
        user.manual_interests = ''
    
    db.session.commit()
    
    flash(f"Your news interests have been updated! You selected {len(selected_interests)} categories.", "success")
    return redirect(url_for('profile'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('landing'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if user:
        # Before deleting user, maybe handle their news submissions? 
        # For now, just delete the user. Cascade delete should be set up if needed.
        db.session.delete(user)
        db.session.commit()
        
        # Clear session
        session.clear()
        flash("Your account has been deleted.", "success")
        return redirect(url_for('landing'))
    
    return redirect(url_for('profile'))

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@auranews.com")

def send_auth_email(to_email, subject, body):
    """Utility to send authentication related emails with a console fallback."""
    print(f"\n--- [EMAIL OUTGOING] ---")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print(f"--- [/EMAIL OUTGOING] ---\n")
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("[!] SMTP not configured. Email logged to console only.")
        return True
        
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv("SENDER_EMAIL", SMTP_USERNAME or "noreply@auranews.com")
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"[!] Email sending failed: {e}")
        return False

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate secure token
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            reset_url = url_for('reset_password', token=token, _external=True)
            body = f"Hello,\n\nYou requested a password reset for your JANAVAAKYA – Voice of the People account. Click the link below to set a new password:\n\n{reset_url}\n\nThis link will expire in 1 hour.\n\nIf you did not request this, please ignore this email."
            send_auth_email(user.email, "Password Reset Request - JANAVAAKYA – Voice of the People", body)
            
            flash("If that email is registered, you will receive a reset link shortly.", "success")
            
        return render_template('forgot_password.html')
        
    return render_template('forgot_password.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email', '').strip()
    if email:
        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        if not existing:
            new_sub = NewsletterSubscriber(email=email)
            db.session.add(new_sub)
            db.session.commit()
            flash("Thank you for subscribing to our newsletter!", "success")
        else:
            flash("You are already subscribed to our newsletter.", "info")
    return redirect(request.referrer or url_for('index'))

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or (user.reset_token_expiry and user.reset_token_expiry < datetime.utcnow()):
        flash("Invalid or expired reset token.", "error")
        return redirect(url_for('landing'))
        
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('reset_password.html', token=token)
            
        if not is_strong_password(password):
            flash("Password must be 8+ chars with uppercase, lowercase, number, and special character.", "error")
            return render_template('reset_password.html', token=token)
            
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        # Send notification email
        body = f"Hello,\n\nThis is a confirmation that the password for your JANAVAAKYA – Voice of the People account has been successfully changed.\n\nIf you did not make this change, please contact support immediately."
        send_auth_email(user.email, "Security Alert: Password Changed", body)
        
        flash("Your password has been updated successfully.", "success")
        return redirect(url_for('landing'))
        
    return render_template('reset_password.html', token=token)

@app.route('/category/<name>')
def category(name):
    print(f"\n[CATEGORY ROUTE] Accessed with name: {name}")
    subcat = request.args.get('sub')
    print(f"[CATEGORY ROUTE] Subcat: {subcat}")
    
    # Normalize category name for display (title case)
    display_name = name.title()
    
    # Get articles using the category name
    articles, list_title = get_live_articles(name, subcat)
    print(f"[CATEGORY ROUTE] Received {len(articles)} articles from get_live_articles")
    
    # Subcats for navigation if needed
    subcats_map = {
        'Sports': ['Cricket', 'Football', 'Tennis'],
        'Movies': ['Malayalam', 'Tamil', 'Bollywood', 'Hollywood'],
        'Global': ['US', 'Europe', 'Middle East', 'Asia'],
        'Tech': ['Gadgets', 'Software', 'AI', 'Mobile']
    }
    current_subcats = subcats_map.get(display_name, [])

    # Filter submissions for this category (case-insensitive)
    category_lower = name.lower()
    all_approved = UserNews.query.filter_by(status='approved').all()
    submissions = []
    for sub in all_approved:
        sub_cat = sub.category.lower()
        if sub_cat == category_lower or (category_lower == 'news' and sub_cat == 'local'):
            submissions.append(sub)

    # Block Advertiser from news
    if session.get('role') == 'advertiser':
        flash("Advertisers do not have access to news content.", "info")
        return redirect(url_for('advertiser_dashboard'))

    print(f"[CATEGORY ROUTE] Rendering template with {len(articles)} articles")
    return render_template('index.html', 
                         latest=articles, 
                         category_name=display_name, 
                         subcats=current_subcats,
                         active_sub=subcat,
                         published_submissions=submissions)

@app.route('/premium-subscribe', methods=['GET', 'POST'])
def premium_subscribe():
    if 'user' not in session:
        return redirect(url_for('landing'))
        
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        if user:
            user.is_subscribed = True
            db.session.commit()
            flash("You have successfully subscribed to Premium Content!", "success")
            return redirect(url_for('index'))
            
    return render_template('subscription_prompt.html')

@app.route('/article/<article_id>')
def article(article_id):
    # Allow guests to read articles
        
    # Redirect Reporter to Reporter Dashboard
    if session.get('role') == 'reporter':
        return redirect(url_for('reporter_dashboard'))
    
    lang = session.get('lang', 'en')
    
    # 1. Handle Live/Dynamic Article (32-char hash or specific prefix)
    is_live_id = len(str(article_id)) == 32 and all(c in '0123456789abcdef' for c in str(article_id).lower())
    if is_live_id or str(article_id).startswith('manual_'):
        return redirect(url_for('live_article', article_id=article_id))
    
    # 2. Handle User-Submitted News (starts with 'user_')
    if str(article_id).startswith('user_'):
        u_id = article_id.split('user_')[1]
        user_art = UserNews.query.get(u_id)
        if user_art and user_art.status == 'approved':
            # Map UserNews to standard article format
            article = {
                'id': f"user_{user_art.id}",
                'title': user_art.title,
                'content': user_art.content,
                'excerpt': user_art.content[:200] + '...',
                'category': user_art.category,
                'image': user_art.display_image,
                'publish_date': user_art.created_at.strftime("%Y-%m-%d"),
                'location': user_art.location,
                'lat': user_art.latitude,
                'lng': user_art.longitude,
                'author': user_art.submitted_by.username
            }
        else:
            flash("Article not found or not yet approved.", "error")
            return redirect(url_for('index'))
    else:
        # 3. Handle Standard Mock News
        article = next((a for a in news_articles if str(a['id']) == str(article_id)), None)
    
    if not article:
        flash("Article not found.", "error")
        return redirect(url_for('index'))
    
    # Simple localization of article content
    def localize_article(article):
        # Always return a copy to prevent global state contamination
        if lang == 'ml':
            return {
                **article, 
                'title': article.get('title_ml', article['title']), 
                'excerpt': article.get('excerpt_ml', article['excerpt']), 
                'content': article.get('content_ml', article.get('content', '')),
                'category': article.get('category_ml', article['category'])
            }
        return article.copy()

    localized_article = localize_article(article)
    
    # Premium check
    if is_premium(localized_article.get('category')):
        user_id = session.get('user_id')
        user = User.query.get(user_id) if user_id else None
        if not user or not user.is_subscribed:
            flash("This is Premium Content. Please subscribe to read the full article.", "info")
            return redirect(url_for('premium_subscribe'))
            
    # NEW: Track reading history for personalization and clear related notification
    if 'user_id' in session:
        user_id = session['user_id']
        track_reading_history(user_id, article_id, localized_article.get('category'))
        
        # Clear specific notification for this article if it exists
        notif = Notification.query.filter_by(user_id=user_id, article_id=str(article_id), is_read=False).first()
        if notif:
            notif.is_read = True
            db.session.commit()
        
    return render_template('article.html', article=localized_article)
@app.route('/report-missing')
def report_missing():
    return render_template('report_missing.html')

@app.route('/missing-persons')
def missing_persons():
    search_query = request.args.get('search', '').strip()
    gender = request.args.get('gender', '').strip()
    location = request.args.get('location', '').strip()

    base_query = MissingPerson.query

    if search_query:
        base_query = base_query.filter(
            MissingPerson.name.ilike(f'%{search_query}%') |
            MissingPerson.description.ilike(f'%{search_query}%')
        )
    if gender:
        base_query = base_query.filter_by(gender=gender)
    if location:
        base_query = base_query.filter(MissingPerson.last_seen_location.ilike(f'%{location}%'))

    approved_items = base_query.filter_by(status='Approved').order_by(MissingPerson.created_at.desc()).all()
    pending_items  = base_query.filter_by(status='Pending').order_by(MissingPerson.created_at.desc()).all()
    rejected_items = base_query.filter_by(status='Rejected').order_by(MissingPerson.created_at.desc()).all()

    return render_template('missing_persons.html',
                           approved_items=approved_items,
                           pending_items=pending_items,
                           rejected_items=rejected_items)
@app.route('/missing-persons/check-duplicate', methods=['POST'])
def check_duplicate_face():
    """AJAX endpoint: checks if uploaded photo matches an existing missing person."""
    if 'photo' not in request.files:
        return jsonify({'match': False})
    file = request.files['photo']
    if not file or not allowed_file(file.filename):
        return jsonify({'match': False})
    try:
        filename = secure_filename(f"dup_check_{int(time.time())}_{file.filename}")
        temp_dir = os.path.join('uploads', 'dup_check')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        result = compare_faces_with_existing(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'match': False, 'error': str(e)})


@app.route('/missing-persons/add', methods=['POST'])
def add_missing_person():
    try:
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        description = request.form.get('description')
        last_seen_location = request.form.get('last_seen_location')
        last_seen_date = request.form.get('last_seen_date')
        contact_name = request.form.get('contact_name')
        contact_phone = request.form.get('contact_phone')
        reporter_email = request.form.get('reporter_email')
        relationship = request.form.get('relationship')

        # --- Stricter Server-side Validation ---
        
        # 1. Validate Name (Requires at least two words)
        name_pattern = r"^[A-Za-z]{2,}(\s+[A-Za-z]{2,})+$"
        if not name or not re.match(name_pattern, name):
            flash("Invalid name. Please enter a full name (at least two words required, letters only).", "error")
            return redirect(url_for('missing_persons'))
            
        # 2. Validate Age
        if age:
            try:
                age_val = int(age)
                if age_val < 0 or age_val > 120:
                    flash("Age must be between 0 and 120.", "error")
                    return redirect(url_for('missing_persons'))
            except ValueError:
                flash("Invalid age format.", "error")
                return redirect(url_for('missing_persons'))
        
        # 3. Validate Distinctive Physical Features (Min 30 characters)
        if not description or len(description.strip()) < 30:
            flash("Description too short. Please provide at least 30 characters describing physical features.", "error")
            return redirect(url_for('missing_persons'))

        # 4. Validate Last Seen Date (Required and not in future)
        if not last_seen_date:
            flash("Date Last Seen is required.", "error")
            return redirect(url_for('missing_persons'))
        try:
            date_obj = datetime.strptime(last_seen_date, "%Y-%m-%d")
            if date_obj.date() > datetime.utcnow().date():
                flash("The last seen date cannot be in the future.", "error")
                return redirect(url_for('missing_persons'))
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "error")
            return redirect(url_for('missing_persons'))

        # 5. Validate Contact Name
        if not contact_name or not re.match(name_pattern, contact_name):
            flash("Invalid contact name. Please enter a full name.", "error")
            return redirect(url_for('missing_persons'))

        # 6. Validate Contact Phone
        if not contact_phone or not re.match(r"^\+?[0-9\s\-]{7,15}$", contact_phone):
            flash("Invalid contact phone format. Use 7-15 digits.", "error")
            return redirect(url_for('missing_persons'))

        # 7. Validate Reporter Email
        if not reporter_email or not re.match(r"[^@]+@[^@]+\.[^@]+", reporter_email):
            flash("Invalid reporter email address.", "error")
            return redirect(url_for('missing_persons'))
            
        # 8. Validate Relationship
        if not relationship or len(relationship.strip()) < 2:
            flash("Please specify your relationship to the missing person.", "error")
            return redirect(url_for('missing_persons'))

        # Ensure defaults are applied after validation
        description = description.strip()
        last_seen_location = last_seen_location or "Unknown"
        
        image_url = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"mp_{int(time.time())}_{file.filename}")
                
                # Use the new uploads/missing_person folder for temporary storage
                temp_upload_dir = os.path.join('uploads', 'missing_person')
                os.makedirs(temp_upload_dir, exist_ok=True)
                temp_path = os.path.join(temp_upload_dir, filename)
                file.save(temp_path)
                
                # Check for face detection
                if detect_face(temp_path):
                    # Check for duplicate face before moving to permanent storage
                    dup_result = compare_faces_with_existing(temp_path)
                    if dup_result.get('match'):
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        flash(
                            f"WARNING: Duplicate Alert: This photo closely resembles an existing case "
                            f"(REF#00{dup_result['person_id']} - {dup_result['person_name']}). "
                            f"Please verify this is not a duplicate report.",
                            "warning"
                        )
                        return redirect(url_for('missing_persons'))

                    # If face detected and no duplicate, move to permanent storage
                    final_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'missing_persons')
                    os.makedirs(final_upload_dir, exist_ok=True)
                    final_path = os.path.join(final_upload_dir, filename)
                    import shutil
                    shutil.move(temp_path, final_path)
                    image_url = f"/static/uploads/missing_persons/{filename}"
                else:
                    # No human face detected, delete temporary file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    flash("Please upload a valid human face image.", "error")
                    return redirect(url_for('missing_persons'))

        new_person = MissingPerson(
            name=name,
            age=int(age) if age else 0,
            gender=gender,
            description=description,
            last_seen_location=last_seen_location,
            last_seen_date=last_seen_date,
            contact_name=contact_name,
            contact_phone=contact_phone or "N/A",
            reporter_email=reporter_email,
            relationship=relationship,
            image=image_url,
            status="Pending",
            verified=False
        )
        
        db.session.add(new_person)
        db.session.commit()
        flash("Report submitted successfully! It will appear publicly after admin verification.", "success")
        return redirect(url_for('missing_persons'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error submitting report: {str(e)}", "error")
        
    return redirect(url_for('missing_persons'))

@app.route('/missing-persons/<int:person_id>')
def view_missing_person(person_id):
    person = MissingPerson.query.get_or_404(person_id)
    return jsonify({
        'id': person.id,
        'name': person.name,
        'age': person.age,
        'gender': person.gender,
        'description': person.description,
        'last_seen_location': person.last_seen_location,
        'last_seen_date': person.last_seen_date,
        'contact_name': person.contact_name,
        'contact_phone': person.contact_phone,
        'reporter_email': person.reporter_email,
        'relationship': person.relationship,
        'image': person.image,
        'status': person.status,
        'fake_report_count': person.fake_report_count,
        'created_at': person.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/missing-persons/<int:person_id>/report-fake', methods=['POST'])
def report_fake_person(person_id):
    person = MissingPerson.query.get_or_404(person_id)

    # Identify reporter by user id (if logged in) or IP address
    user_id = session.get('user_id')
    ip_address = request.remote_addr

    # Prevent duplicate reports from the same user/IP
    existing = FakeReport.query.filter_by(person_id=person_id, user_id=user_id).first() if user_id else None
    if not existing:
        existing = FakeReport.query.filter_by(person_id=person_id, ip_address=ip_address).first()

    if existing:
        return jsonify({'success': False, 'already_reported': True, 'message': 'You have already reported this case.'})

    # Record the report
    fake_report = FakeReport(person_id=person_id, user_id=user_id, ip_address=ip_address)
    db.session.add(fake_report)

    person.fake_report_count = (person.fake_report_count or 0) + 1

    # Auto-flag: pull back to admin review if threshold reached
    auto_flagged = False
    if person.fake_report_count >= FAKE_REPORT_THRESHOLD and person.verified:
        person.verified = False
        person.status = 'Under Review'
        auto_flagged = True

    db.session.commit()
    return jsonify({
        'success': True,
        'new_count': person.fake_report_count,
        'auto_flagged': auto_flagged,
        'threshold': FAKE_REPORT_THRESHOLD
    })


@app.route('/missing-persons/<int:person_id>/delete', methods=['POST'])
@admin_required
def delete_missing_person(person_id):
    person = MissingPerson.query.get_or_404(person_id)
    db.session.delete(person)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/missing-persons/<int:person_id>/edit', methods=['POST'])
@admin_required
def edit_missing_person(person_id):
    person = MissingPerson.query.get_or_404(person_id)
    person.name = request.form.get('name', person.name)
    person.age = request.form.get('age', person.age)
    person.gender = request.form.get('gender', person.gender)
    person.description = request.form.get('description', person.description)
    person.last_seen_location = request.form.get('last_seen_location', person.last_seen_location)
    person.last_seen_date = request.form.get('last_seen_date', person.last_seen_date)
    person.contact_name = request.form.get('contact_name', person.contact_name)
    person.contact_phone = request.form.get('contact_phone', person.contact_phone)
    person.status = request.form.get('status', person.status)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/missing-persons/<int:person_id>/verify', methods=['POST'])
@admin_required
def verify_missing_person(person_id):
    person = MissingPerson.query.get_or_404(person_id)
    action = request.form.get('action', 'approve')
    if action == 'approve':
        person.verified = True
        person.status = 'Approved'
    elif action == 'reject':
        person.verified = False
        person.status = 'Rejected'
    db.session.commit()
    return jsonify({'success': True, 'status': person.status})

# -------------------- Admin Routes --------------------

@app.route('/admin')
@admin_required
def admin_dashboard():
    users = User.query.filter(User.role != 'admin', User.role != 'reporter', User.role != 'advertiser').all() # Exclude reporters and advertisers from general user list
    reporters = User.query.filter_by(role='reporter').all()
    advertisers = User.query.filter_by(role='advertiser').all()
    ads = Advertisement.query.order_by(Advertisement.created_at.desc()).all()
    
    pending_persons = MissingPerson.query.filter(MissingPerson.status.in_(['Pending', 'Under Review'])).order_by(MissingPerson.created_at.desc()).all()

    return render_template('admin_dashboard.html', 
                         users=users, 
                         reporters=reporters, 
                         advertisers=advertisers,
                         ads=ads,
                         pending_persons=pending_persons)

@app.route('/advertisement/manage/<int:ad_id>', methods=['POST'])
@admin_required
def manage_advertisement(ad_id):
    ad = Advertisement.query.get_or_404(ad_id)
    action = request.form.get('action')
    if action == 'approve':
        ad.status = 'Active'
        # Do not set active=True yet, needs confirmation
        flash("Advertisement approved. Please confirm placement to make it live.", "success")
    elif action == 'confirm':
        ad.placement = request.form.get('placement', 'bottom')
        ad.is_confirmed = True
        ad.active = True
        ad.status = 'Active' # ensure status is Active
        flash(f"Advertisement confirmed and launched on the {ad.placement} section.", "success")
    elif action == 'verify_payment':
        ad.status = 'Active'
        ad.is_confirmed = False
        flash(f"Payment for '{ad.title}' verified. Advertisement is now Active. Please confirm placement to make it live.", "success")
    elif action == 'reject':
        ad.status = 'Rejected'
        ad.active = False
        ad.is_confirmed = False
        flash("Advertisement rejected.", "warning")
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/advertisement/<int:ad_id>')
def view_advertisement(ad_id):
    if 'user' not in session:
        return redirect(url_for('landing'))
        
    ad = Advertisement.query.get_or_404(ad_id)
    
    # Only owner or admin can view
    is_admin = session.get('role') == 'admin'
    is_owner = ad.user_id == session.get('user_id')
    
    if not (is_admin or is_owner):
        flash("You do not have permission to view this advertisement Details.", "error")
        return redirect(url_for('index'))
        
    # Fetch support messages for the advertiser
    support_chats = SupportMessage.query.filter_by(user_id=ad.user_id).order_by(SupportMessage.timestamp.asc()).all()
    
    return render_template('ad_details.html', ad=ad, is_admin=is_admin, support_chats=support_chats)

@app.route('/api/advertisement/analytics/<int:ad_id>')
@advertiser_required
def get_advertisement_analytics(ad_id):
    ad = Advertisement.query.get_or_404(ad_id)
    
    # Only owner or admin can view
    is_admin = session.get('role') == 'admin'
    is_owner = ad.user_id == session.get('user_id')
    
    if not (is_admin or is_owner):
        return jsonify({'error': 'Unauthorized'}), 403
        
    ctr = 0
    if ad.views > 0:
        ctr = round((ad.clicks / ad.views) * 100, 2)
        
    return jsonify({
        'title': ad.title,
        'views': ad.views,
        'clicks': ad.clicks,
        'ctr': ctr,
        'plan': ad.plan_name or 'Standard',
        'status': ad.status,
        'created_at': ad.created_at.strftime('%B %d, %Y') if ad.created_at else 'N/A',
        'end_date': (ad.created_at + timedelta(days=ad.duration)).strftime('%B %d, %Y') if ad.created_at else 'N/A'
    })

@app.route('/api/advertisement/view/<int:ad_id>', methods=['POST'])
def track_advertisement_view(ad_id):
    ad = Advertisement.query.get(ad_id)
    if ad:
        ad.views += 1
        db.session.commit()
        return jsonify({'status': 'success', 'views': ad.views})
    return jsonify({'error': 'Ad not found'}), 404

@app.route('/ad/click/<int:ad_id>')
def track_advertisement_click(ad_id):
    ad = Advertisement.query.get_or_404(ad_id)
    try:
        ad.clicks += 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error tracking click: {e}")
    
    return redirect(ad.target_url)


@app.route('/admin/make-reporter/<int:user_id>')
@admin_required
def make_reporter(user_id):
    user = User.query.get(user_id)
    if user and user.role != 'admin':
        user.role = 'reporter'
        db.session.commit()
        flash(f"{user.username} is now a Reporter.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/revoke-reporter/<int:user_id>')
@admin_required
def revoke_reporter(user_id):
    user = User.query.get(user_id)
    if user and user.role == 'reporter':
        user.role = 'user'
        db.session.commit()
        flash(f"{user.username} is no longer a Reporter.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update-reporter-name/<int:user_id>', methods=['POST'])
@admin_required
def update_reporter_name(user_id):
    user = User.query.get(user_id)
    if user:
        new_name = request.form.get('full_name')
        if new_name:
            user.full_name = new_name
            db.session.commit()
            # Simple translation lookup for flash message since flash usage varies
            lang = session.get('lang', 'en')
            msg = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get('name_updated', 'Reporter name updated successfully.')
            flash(msg, "success")
    return redirect(url_for('admin_dashboard'))

# -------------------- Advertiser Routes --------------------

@app.route('/advertiser')
@advertiser_required
def advertiser_dashboard():
    user_id = session.get('user_id')
    ads = Advertisement.query.filter_by(user_id=user_id).order_by(Advertisement.created_at.desc()).all()
    active_count = len([ad for ad in ads if ad.status == 'Active'])
    pending_count = len([ad for ad in ads if ad.status in ['Pending Payment', 'Under Review']])
    
    # Fetch support messages for this user
    support_chats = SupportMessage.query.filter_by(user_id=user_id).order_by(SupportMessage.timestamp.asc()).all()
    
    return render_template('advertiser_dashboard.html', 
                         ads=ads, 
                         active_count=active_count, 
                         pending_count=pending_count,
                         support_chats=support_chats)

@app.route('/chat-support', methods=['POST'])
def chat_support():
    if 'user' not in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Unauthorized'}), 401
        return redirect(url_for('landing'))
    
    user_id = session.get('user_id')
    message = request.form.get('message', '').strip()
    
    if message:
        is_admin = session.get('role') == 'admin'
        # Handle both naming conventions for compatibility
        target_user_id = request.form.get('target_user_id') or request.form.get('user_id')
        
        if is_admin and target_user_id:
            msg = SupportMessage(
                user_id=int(target_user_id),
                sender_id=user_id,
                message=message,
                is_read_by_admin=True # Admin's own messages are "read"
            )
            # When admin replies, mark all previous messages in this thread as read
            SupportMessage.query.filter_by(user_id=int(target_user_id), is_read_by_admin=False).update({'is_read_by_admin': True})
        else:
            msg = SupportMessage(
                user_id=user_id,
                sender_id=user_id,
                message=message,
                is_read_by_admin=False
            )
        db.session.add(msg)
        db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success', 'message': 'Message sent'})
        
    return redirect(request.referrer or url_for('advertiser_dashboard'))

@app.route('/chat-support/messages/<int:target_user_id>')
def get_chat_support_messages(target_user_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    current_user_id = session.get('user_id')
    is_admin = session.get('role') == 'admin'
    
    # Only thread owner or admin can see messages
    if not is_admin and current_user_id != target_user_id:
        return jsonify({'error': 'Forbidden'}), 403
        
    
    # Mark messages as read by admin if current viewer is admin
    if is_admin:
        SupportMessage.query.filter_by(user_id=target_user_id, is_read_by_admin=False).update({'is_read_by_admin': True})
        db.session.commit()
        
    messages = SupportMessage.query.filter_by(user_id=target_user_id).order_by(SupportMessage.timestamp.asc()).all()
    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'message': m.message,
        'timestamp': m.timestamp.isoformat() + 'Z',
        'sender_username': m.sender.username,
        'is_admin': m.sender.role == 'admin'
    } for m in messages])

@app.route('/api/admin/advertisement/<int:ad_id>/delete', methods=['POST'])
@admin_required
def delete_advertisement_admin(ad_id):
    ad = Advertisement.query.get_or_404(ad_id)
    reason = request.form.get('reason')
    
    if not reason:
        return jsonify({'error': 'A reason for deletion is required'}), 400
        
    try:
        # 1. Send automated support message to advertiser
        admin_id = session.get('user_id')
        target_user_id = ad.user_id
        company = ad.company_name
        title = ad.title
        
        deletion_msg = f"NOTIFICATION: Your campaign '{title}' for {company} has been removed by Admin. Reason: {reason}"
        
        msg = SupportMessage(
            user_id=target_user_id,
            sender_id=admin_id,
            message=deletion_msg,
            is_read_by_admin=True
        )
        db.session.add(msg)
        
        # 2. Delete the advertisement using a more direct query
        # This bypasses potential session-state issues with the 'ad' object
        Advertisement.query.filter_by(id=ad_id).delete()
        db.session.commit()
        
        flash(f"Advertisement '{title}' deleted successfully.", "success")
        return jsonify({'success': True, 'message': 'Advertisement deleted and advertiser notified.'})
    except Exception as e:
        print(f"DELETION ERROR for ad {ad_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/chat-threads')
@admin_required
def get_admin_chat_threads():
    from sqlalchemy import func
    # Find unique users who have support threads
    # Each thread is identified by the advertiser's user_id
    threads = db.session.query(
        SupportMessage.user_id,
        func.max(SupportMessage.timestamp).label('last_message_time')
    ).group_by(SupportMessage.user_id).order_by(func.max(SupportMessage.timestamp).desc()).all()
    
    thread_data = []
    for user_id, last_time in threads:
        user = User.query.get(user_id)
        if not user: continue
        
        # Get the very last message in this thread
        last_msg = SupportMessage.query.filter_by(user_id=user_id).order_by(SupportMessage.timestamp.desc()).first()
        
        # Count unread messages (sent by advertiser)
        unread_count = SupportMessage.query.filter_by(user_id=user_id, is_read_by_admin=False).join(User, SupportMessage.sender_id == User.id).filter(User.role == 'advertiser').count()
        
        thread_data.append({
            'user_id': user.id,
            'username': user.username,
            'full_name': user.full_name or user.username,
            'picture': user.picture if user.picture and 'default_avatar.png' not in user.picture else None,
            'last_message': last_msg.message if last_msg else '',
            'last_message_time': last_time.isoformat() + 'Z',
            'unread_count': unread_count,
            'is_last_from_me': last_msg.sender_id == session.get('user_id') if last_msg else False
        })
        
    return jsonify(thread_data)

@app.route('/api/admin/chat-unread-count')
@admin_required
def get_admin_chat_unread_count():
    from sqlalchemy import and_
    unread_count = SupportMessage.query.join(User, SupportMessage.sender_id == User.id)\
        .filter(and_(User.role == 'advertiser', SupportMessage.is_read_by_admin == False))\
        .count()
    return jsonify({'unread_count': unread_count})

# -------------------- Reporter Routes --------------------

@app.route('/reporter')
@reporter_required
def reporter_dashboard():
    # Filter articles authored by the current reporter
    my_articles = [a for a in news_articles if a.get('author') == session.get('user')]
    
    # Fetch pending user submissions
    pending_submissions = UserNews.query.filter_by(status='pending').order_by(UserNews.created_at.desc()).all()
    
    return render_template('reporter_dashboard.html', articles=my_articles, pending_submissions=pending_submissions)

@app.route('/reporter/review/<int:news_id>', methods=['GET', 'POST'])
@reporter_required
def review_user_news(news_id):
    news = UserNews.query.get_or_404(news_id)
    
    # Calculate user credibility stats
    submitter = news.submitted_by
    stats = {
        'total': UserNews.query.filter_by(submitted_by_id=submitter.id).count(),
        'approved': UserNews.query.filter_by(submitted_by_id=submitter.id, status='approved').count(),
        'rejected': UserNews.query.filter_by(submitted_by_id=submitter.id, status='rejected').count()
    }
    
    if request.method == 'POST':
        action = request.form.get('action')
        note = request.form.get('review_note')
        
        news.reviewed_by_id = session.get('user_id')
        news.review_note = note
        
        if action == 'approve':
            news.status = 'approved'
            # Assign image: use media_url if provided, else get dynamic relevant image
            img_to_use = news.media_url
            if not img_to_use or 'placeholder' in img_to_use.lower():
                img_to_use = get_dynamic_news_image(news.title, news.category, f"user_news_{news.id}")

            approved_article = {
                "id": f"user_{news.id}", # Prefix to avoid collision with mock IDs
                "title": news.title,
                "category": news.category,
                "excerpt": news.content[:100] + "...",
                "content": news.content,
                "image": img_to_use,
                "author": news.submitted_by.username,
                "featured": False,
                "title_ml": news.title, # Should ideally be translated
                "category_ml": news.category,
                "excerpt_ml": news.content[:100] + "...",
                "content_ml": news.content,
                "location": news.location,
                "is_user_submitted": True
            }
            news_articles.insert(0, approved_article)
            
            # NEW: Send personalized notifications to users interested in this category
            send_personalized_notifications(news.category, approved_article['id'], news.title)
            
            flash("News approved and published!", "success")
        elif action == 'reject':
            news.status = 'rejected'
            flash("News rejected.", "warning")
            
        db.session.commit()
        return redirect(url_for('reporter_dashboard'))
        
    return render_template('review_user_news.html', news=news, stats=stats)

@app.route('/reporter/edit-user-news/<int:news_id>', methods=['GET', 'POST'])
@reporter_required
def edit_user_news(news_id):
    news = UserNews.query.get_or_404(news_id)
    if request.method == 'POST':
        news.title = request.form.get('title')
        news.category = request.form.get('category')
        news.location = request.form.get('location')
        news.content = request.form.get('content')
        db.session.commit()
        flash("Submission updated successfully.", "success")
        return redirect(url_for('review_user_news', news_id=news.id))
        
    return render_template('edit_user_news.html', news=news)

@app.route('/admin/delete-user/<int:user_id>') # Changed URL to reflect admin nature
@admin_required # Changed from reporter_required to admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user and user.role != 'admin':
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} deleted.", "success")
    else:
        flash("Cannot delete this user.", "error")
    # Redirect back to admin dashboard since reporter can't delete anymore
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)



