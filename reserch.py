import requests
import time
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode
import hashlib
import os
import csv
from io import StringIO
from scrapers import SmartResearchAutomator
from dashboard_generator import update_index
from view_results_html import generate_html_report

class GeneralResearchAutomator:
    def __init__(self, cache_dir: str = "research_cache", status_callback=None):
        """
        Initialize the general research automator for ANY topic
        """
        self.cache_dir = cache_dir
        self.status_callback = status_callback
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        self.research_dir = "" # Will be set during research()
        self.smart_scraper = SmartResearchAutomator(headless=True)
            
        self.research_data = {
            'query': '',
            'timestamp': '',
            'expanded_terms': [],
            'sources': {
                'web_results': [],
                'news': [],
                'blogs': [],
                'wikipedia': [],
                'definitions': [],
                'statistics': [],
                'expert_opinions': [],
                'case_studies': [],
                'deep_dive': []
            },
            'key_points': [],
            'facts': [],
            'quotes': [],
            'statistics': [],
            'trends': [],
            'resources': []
        }
        
        # Rate limiting tracking
        self.last_request_time = {}
        
        # User agents to rotate
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ]
        
    def _rate_limit(self, api_name: str, min_interval: float = 1.0):
        """Simple rate limiting"""
        current_time = time.time()
        if api_name in self.last_request_time:
            elapsed = current_time - self.last_request_time[api_name]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        self.last_request_time[api_name] = time.time()
    
    def _get_cache_key(self, query: str, source: str) -> str:
        """Generate cache key"""
        hash_input = f"{source}:{query}".encode('utf-8')
        return hashlib.md5(hash_input).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Retrieve cached response"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < 604800:  # 7 days
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
        return None
    
    def _cache_response(self, cache_key: str, data: Dict):
        """Cache response"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def _get_headers(self):
        """Get random user agent headers"""
        import random
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def generate_search_terms(self, topic: str) -> List[str]:
        """
        Generate comprehensive search terms for ANY topic
        """
        print(f"📋 Generating search terms for: {topic}")
        
        base_terms = [topic]
        
        # Add variations based on topic type
        variations = [
            f"what is {topic}",
            f"{topic} definition",
            f"{topic} explained",
            f"{topic} examples",
            f"{topic} types",
            f"{topic} benefits",
            f"{topic} challenges",
            f"{topic} statistics",
            f"{topic} trends",
            f"{topic} future",
            f"{topic} guide",
            f"{topic} tutorial",
            f"{topic} best practices",
            f"{topic} case study",
            f"{topic} research",
            f"{topic} latest news",
            f"{topic} expert insights",
            f"{topic} analysis",
            f"{topic} overview",
            f"{topic} introduction"
        ]
        
        # Add question-based variations
        questions = [
            f"why {topic}",
            f"how {topic} works",
            f"when {topic} started",
            f"who uses {topic}",
            f"where to learn {topic}"
        ]
        
        all_terms = base_terms + variations + questions
        
        # Remove duplicates and return
        all_terms = list(set(all_terms))
        self.research_data['expanded_terms'] = all_terms
        print(f"  Generated {len(all_terms)} search terms")
        return all_terms
    
    def search_wikipedia(self, query: str) -> Dict:
        """
        Search Wikipedia for comprehensive information
        """
        print(f"  📚 Searching Wikipedia for: {query[:50]}...")
        
        cache_key = self._get_cache_key(f"wiki_{query}", "wikipedia")
        cached = self._get_cached_response(cache_key)
        if cached:
            print(f"    Using cached Wikipedia results")
            return cached
        
        result = {
            'title': '',
            'summary': '',
            'url': '',
            'sections': [],
            'infobox': {},
            'categories': [],
            'references': []
        }
        
        try:
            # Search for the page
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'format': 'json',
                'srlimit': 1
            }
            
            self._rate_limit('wikipedia', 0.5)
            response = requests.get(search_url, params=search_params, timeout=10)
            
            if response.status_code == 200:
                search_data = response.json()
                search_results = search_data.get('query', {}).get('search', [])
                
                if search_results:
                    page_title = search_results[0]['title']
                    
                    # Get page content
                    content_params = {
                        'action': 'query',
                        'titles': page_title,
                        'prop': 'extracts|info|pageimages|categories',
                        'exintro': True,
                        'explaintext': True,
                        'inprop': 'url',
                        'format': 'json',
                        'pithumbsize': 400
                    }
                    
                    self._rate_limit('wikipedia', 0.5)
                    content_response = requests.get(search_url, params=content_params, timeout=10)
                    
                    if content_response.status_code == 200:
                        content_data = content_response.json()
                        pages = content_data.get('query', {}).get('pages', {})
                        
                        for page_id, page in pages.items():
                            if page_id != '-1':
                                result['title'] = page.get('title', '')
                                result['summary'] = page.get('extract', '')
                                result['url'] = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                                
                                # Get categories
                                categories = page.get('categories', [])
                                result['categories'] = [cat['title'] for cat in categories if 'title' in cat][:20]
                                
                                # Try to get infobox (requires different API)
                                self._get_wikipedia_infobox(page_title, result)
        
        except Exception as e:
            print(f"    Error searching Wikipedia: {e}")
        
        # Cache results
        self._cache_response(cache_key, result)
        return result
    
    def _get_wikipedia_infobox(self, page_title: str, result: Dict):
        """Helper to get Wikipedia infobox"""
        try:
            params = {
                'action': 'parse',
                'page': page_title,
                'format': 'json',
                'prop': 'wikitext',
                'section': 0
            }
            
            url = "https://en.wikipedia.org/w/api.php"
            self._rate_limit('wikipedia', 0.5)
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                wikitext = data.get('parse', {}).get('wikitext', {}).get('*', '')
                
                # Parse infobox
                infobox_pattern = r'\{\{Infobox(.*?)\}\}'
                match = re.search(infobox_pattern, wikitext, re.DOTALL)
                if match:
                    infobox_text = match.group(1)
                    lines = infobox_text.split('|')
                    for line in lines:
                        if '=' in line:
                            key, value = line.split('=', 1)
                            result['infobox'][key.strip()] = value.strip()
        
        except:
            pass
    
    def search_news(self, query: str) -> List[Dict]:
        """
        Search news using free RSS feeds
        """
        print(f"  📰 Searching news for: {query[:50]}...")
        
        cache_key = self._get_cache_key(f"news_{query}", "news")
        cached = self._get_cached_response(cache_key)
        if cached:
            print(f"    Using cached news results ({len(cached)} articles)")
            return cached
        
        articles = []
        
        # Use Google News RSS
        rss_urls = [
            f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en",
            f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en&when:1d"
        ]
        
        for rss_url in rss_urls:
            try:
                self._rate_limit('news_rss', 1)
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[:10]:
                    article = {
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'source': entry.get('source', {}).get('title', 'Unknown'),
                        'category': 'news'
                    }
                    
                    # Clean summary (remove HTML)
                    if article['summary']:
                        soup = BeautifulSoup(article['summary'], 'html.parser')
                        article['summary'] = soup.get_text()[:500] + '...' if len(soup.get_text()) > 500 else soup.get_text()
                    
                    articles.append(article)
                
                if articles:
                    break
                    
            except Exception as e:
                print(f"    Error with news RSS: {e}")
        
        # Cache results
        if articles:
            self._cache_response(cache_key, articles)
            print(f"    Found {len(articles)} news articles")
        
        return articles
    
    def search_blog_posts(self, query: str) -> List[Dict]:
        """
        Search blog posts using RSS feeds
        """
        print(f"  📝 Searching blog posts for: {query[:50]}...")
        
        cache_key = self._get_cache_key(f"blogs_{query}", "blogs")
        cached = self._get_cached_response(cache_key)
        if cached:
            print(f"    Using cached blog results ({len(cached)} posts)")
            return cached
        
        posts = []
        
        # Medium RSS search
        medium_url = f"https://medium.com/feed/tag/{quote(query.replace(' ', '-'))}"
        
        # WordPress.com search
        wordpress_url = f"https://public-api.wordpress.com/rest/v1.1/read/tags/{quote(query)}/posts"
        
        # Dev.to search
        devto_url = f"https://dev.to/search/feed?q={quote(query)}"
        
        rss_sources = [
            ('medium', medium_url),
            ('wordpress', wordpress_url),
            ('devto', devto_url)
        ]
        
        for source_name, url in rss_sources:
            try:
                self._rate_limit('blog_rss', 1)
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:5]:
                    post = {
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', entry.get('description', '')),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', entry.get('pubDate', '')),
                        'author': entry.get('author', 'Unknown'),
                        'source': source_name,
                        'category': 'blog'
                    }
                    
                    # Clean summary
                    if post['summary']:
                        soup = BeautifulSoup(post['summary'], 'html.parser')
                        post['summary'] = soup.get_text()[:500] + '...' if len(soup.get_text()) > 500 else soup.get_text()
                    
                    posts.append(post)
                    
            except Exception as e:
                print(f"    Error with {source_name} RSS: {e}")
        
        # Cache results
        if posts:
            self._cache_response(cache_key, posts)
            print(f"    Found {len(posts)} blog posts")
        
        return posts
    
    def search_web_results(self, query: str) -> List[Dict]:
        """
        Simulate web search results using free APIs
        """
        print(f"  🌐 Searching web for: {query[:50]}...")
        
        cache_key = self._get_cache_key(f"web_{query}", "web")
        cached = self._get_cached_response(cache_key)
        if cached:
            print(f"    Using cached web results ({len(cached)} results)")
            return cached
        
        results = []
        
        # Use DuckDuckGo API (free, no key needed)
        ddg_url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
        
        try:
            self._rate_limit('duckduckgo', 1)
            response = requests.get(ddg_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Abstract
                if data.get('Abstract'):
                    results.append({
                        'title': data.get('Heading', 'Summary'),
                        'summary': data.get('Abstract', ''),
                        'url': data.get('AbstractURL', ''),
                        'source': 'DuckDuckGo Abstract',
                        'type': 'summary'
                    })
                
                # Related topics
                for topic in data.get('RelatedTopics', [])[:10]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        results.append({
                            'title': topic.get('Text', '')[:100],
                            'summary': topic.get('Text', ''),
                            'url': topic.get('FirstURL', ''),
                            'source': 'DuckDuckGo',
                            'type': 'related'
                        })
        
        except Exception as e:
            print(f"    Error with DuckDuckGo: {e}")
        
        # Fallback to HTML scraping if results are low
        if len(results) < 3:
            self._search_duckduckgo_html(query, results)
        
        # Try to get more results from alternative sources
        self._search_wikidata(query, results)
        
        # Cache results
        if results:
            self._cache_response(cache_key, results)
            print(f"    Found {len(results)} web results")
        
        return results
    
    def _search_duckduckgo_html(self, query: str, results: List):
        """Fallback to DuckDuckGo HTML interface for better discovery"""
        print(f"    🔍 Falling back to DuckDuckGo HTML for: {query[:30]}...")
        try:
            url = "https://html.duckduckgo.com/html/"
            params = {'q': query}
            headers = self._get_headers()
            
            self._rate_limit('duckduckgo_html', 2)
            response = requests.post(url, data=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = soup.find_all('div', class_='result')
                
                for res in search_results[:10]:
                    title_elem = res.find('a', class_='result__a')
                    snippet_elem = res.find('a', class_='result__snippet')
                    
                    if title_elem:
                        title = title_elem.get_text()
                        link = title_elem.get('href')
                        # Handle proxy links if necessary
                        if link.startswith('//'): link = 'https:' + link
                        
                        snippet = snippet_elem.get_text() if snippet_elem else ""
                        
                        results.append({
                            'title': title,
                            'summary': snippet,
                            'url': link,
                            'source': 'DuckDuckGo Search',
                            'type': 'web'
                        })
        except Exception as e:
            print(f"    Error with DuckDuckGo HTML: {e}")

    def _search_wikidata(self, query: str, results: List):
        """Helper to search Wikidata"""
        try:
            wikidata_url = "https://www.wikidata.org/w/api.php"
            params = {
                'action': 'wbsearchentities',
                'search': query,
                'language': 'en',
                'format': 'json',
                'limit': 5
            }
            
            self._rate_limit('wikidata', 0.5)
            response = requests.get(wikidata_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('search', []):
                    results.append({
                        'title': item.get('label', ''),
                        'summary': item.get('description', ''),
                        'url': f"https://www.wikidata.org/wiki/{item.get('id', '')}",
                        'source': 'Wikidata',
                        'type': 'structured data'
                    })
        
        except Exception as e:
            print(f"    Error with Wikidata: {e}")
    
    def extract_definitions(self, texts: List[str]) -> List[str]:
        """Extract definitions from texts with improved accuracy"""
        definitions = []
        
        # Improved patterns for definition detection
        definition_patterns = [
            (r'\b(is|are) defined as\b', 'is defined as'),
            (r'\b(refers? to|referring to)\b', 'refers to'),
            (r'\b(is|are) a type of\b', 'is a type of'),
            (r'\b(can be|is) defined as\b', 'defined as'),
            (r'\bmeans?\b', 'means'),
            (r'\b(is|are) understood as\b', 'understood as'),
            (r'\b(consists?|comprises?) of\b', 'consists of'),
            (r'\bdescribes?\b', 'describes'),
            (r'\bencompasses?\b', 'encompasses'),
            (r'\bdefines?\b', 'defines'),
            (r'\b(is|are) often called\b', 'called'),
            (r'\b(is|are) basically\b', 'basically'),
            (r'\b(is|are) essentially\b', 'essentially')
        ]
        
        for text in texts:
            # Better sentence splitting
            sentences = re.split(r'(?<!\b[A-Z][a-z]\.)(?<!\b[A-Z]\.)(?<=[.!?]) +', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if 15 < len(sentence) < 300: # Filter out noise and too long fragments
                    for pattern, label in definition_patterns:
                        if re.search(pattern, sentence, re.IGNORECASE):
                            # Ensure it's not just a passing mention
                            if len(sentence.split()) > 6:
                                definitions.append(sentence)
                                break
        
        return list(set(definitions))[:15]

    def extract_statistics(self, texts: List[str]) -> List[str]:
        """Extract statistics with more robust patterns"""
        statistics = []
        
        stat_patterns = [
            r'\d+(\.\d+)?%', 
            r'\d+(\.\d+)? percent',
            r'\b(statistics|data|survey|report|study|research|analysis)\b.*?\d+',
            r'\b(increased|decreased|growth|declined?|rose|dropped)\b.*?\d+',
            r'\b(average|median|mean|total|majority|minority)\b.*?\d+',
            r'\b(\d+\s+out\s+of\s+\d+)\b',
            r'\b(approximately|roughly|nearly|more than|less than|over|under)\s+\d+\b'
        ]
        
        for text in texts:
            sentences = re.split(r'(?<!\b[A-Z][a-z]\.)(?<!\b[A-Z]\.)(?<=[.!?]) +', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if 15 < len(sentence) < 350:
                    for pattern in stat_patterns:
                        if re.search(pattern, sentence, re.IGNORECASE):
                            statistics.append(sentence)
                            break
        
        return list(set(statistics))[:20]
    
    def extract_quotes(self, texts: List[str]) -> List[str]:
        """Extract quotes from texts with better context filtering"""
        quotes = []
        
        # Look for quoted text
        quote_patterns = [
            r'"([^"]{10,250})"',
            r'“([^”]{10,250})”',
            r'‘([^’]{10,250})’'
        ]
        
        for text in texts:
            for pattern in quote_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    # Filter out short fragments or navigation elements
                    words = match.split()
                    if 5 < len(words) < 50:
                        quotes.append(match.strip())
        
        return list(set(quotes))[:15]

    def extract_case_studies(self, texts: List[str]) -> List[str]:
        """Extract potential case study references and examples"""
        case_studies = []
        
        case_patterns = [
            r'\bcase\s+stud(y|ies)\b',
            r'\breal-world\s+examples?\b',
            r'\bexample\s+of\b',
            r'\bfor\s+instance\b',
            r'\bsuch\s+as\b',
            r'\bdemonstrated\s+by\b',
            r'\billustrated\s+by\b',
            r'\bshown\s+in\b',
            r'\bas\s+seen\s+in\b',
            r'\bin\s+the\s+case\s+of\b'
        ]
        
        for text in texts:
            sentences = re.split(r'(?<!\b[A-Z][a-z]\.)(?<!\b[A-Z]\.)(?<=[.!?]) +', text)
            for i in range(len(sentences)):
                sentence = sentences[i].strip()
                for pattern in case_patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        # Get current and next sentence for better context
                        case_text = sentence
                        if i + 1 < len(sentences):
                            next_sentence = sentences[i+1].strip()
                            if len(next_sentence) > 10:
                                case_text += " " + next_sentence
                        
                        if 30 < len(case_text) < 400:
                            case_studies.append(case_text)
                        break
        
        return list(set(case_studies))[:12]
    
    def analyze_content(self):
        """
        Analyze all collected content for insights
        """
        print("\n🔍 Analyzing collected content...")
        
        all_texts = []
        
        # Collect all text content
        for category, items in self.research_data['sources'].items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        # Prioritize full_text if available, then summary
                        text = item.get('full_text') or item.get('summary')
                        if text:
                            all_texts.append(text)
                        
                        # Titles are also useful
                        if 'title' in item and item['title']:
                            all_texts.append(item['title'])
        
        if all_texts:
            combined_text = ' '.join(all_texts)
            
            # Extract definitions
            self.research_data['definitions'] = self.extract_definitions(all_texts)
            
            # Extract statistics
            self.research_data['statistics'] = self.extract_statistics(all_texts)
            
            # Extract quotes
            self.research_data['quotes'] = self.extract_quotes(all_texts)
            
            # Extract case studies
            self.research_data['case_studies'] = self.extract_case_studies(all_texts)
            
            # Extract key points (sentences with importance indicators)
            importance_indicators = [
                r'\bimportant\b', r'\bkey\b', r'\bcrucial\b', r'\bessential\b', r'\bsignificant\b',
                r'\bnotable\b', r'\bcritical\b', r'\bvital\b', r'\bfundamental\b', r'\bcore\b',
                r'\bprimary\b', r'\bmajor\b', r'\bmain\b', r'\bcentral\b', r'\bhighlight\b',
                r'\bconclusion\b', r'\bresult\b', r'\bfinding\b'
            ]
            
            sentences = re.split(r'(?<!\b[A-Z][a-z]\.)(?<!\b[A-Z]\.)(?<=[.!?]) +', combined_text)
            for sentence in sentences:
                sentence = sentence.strip()
                if 40 < len(sentence) < 400:
                    if any(re.search(indicator, sentence, re.IGNORECASE) for indicator in importance_indicators):
                        self.research_data['key_points'].append(sentence)
            
            self.research_data['key_points'] = list(set(self.research_data['key_points']))[:25]
            
            # Identify trends
            trend_indicators = [
                r'\btrend\b', r'\bincreasing\b', r'\bdecreasing\b', r'\bgrowing\b', r'\bemerging\b',
                r'\brising\b', r'\bdeclining\b', r'\bshifting\b', r'\bevolving\b', r'\bfuture\b',
                r'\bforecast\b', r'\bpredicted\b', r'\bexpected\b', r'\badoption\b', r'\btransformation\b'
            ]
            
            trends = []
            for sentence in sentences:
                sentence = sentence.strip()
                if 40 < len(sentence) < 400:
                    if any(re.search(indicator, sentence, re.IGNORECASE) for indicator in trend_indicators):
                        trends.append(sentence)
            self.research_data['trends'] = list(set(trends))[:15]
            
            print(f"  Found {len(self.research_data['definitions'])} definitions")
            print(f"  Found {len(self.research_data['statistics'])} statistics")
            print(f"  Found {len(self.research_data['quotes'])} quotes")
            print(f"  Found {len(self.research_data['key_points'])} key points")
            print(f"  Found {len(self.research_data['trends'])} trends")
    
    def research(self, topic: str, max_results_per_source: int = 20, tool_preference: str = None):
        """
        Main method to perform comprehensive research on ANY topic
        """
        print(f"\n{'='*60}")
        print(f"🔬 STARTING COMPREHENSIVE RESEARCH ON: {topic}")
        if tool_preference:
            print(f"🛠️  TOOL PREFERENCE: {tool_preference}")
        print(f"{'='*60}\n")
        
        if self.status_callback:
            self.status_callback(f"Starting research on: {topic}")
            
        # Setup research directory
        now = datetime.now()
        timestamp_str = now.strftime('%Y%m%d_%H%M%S')
        topic_slug = re.sub(r'[^\w\s-]', '', topic).strip().lower()
        topic_slug = re.sub(r'[-\s]+', '_', topic_slug)
        
        self.research_dir = os.path.join("researches", f"{topic_slug}_{timestamp_str}")
        if not os.path.exists(self.research_dir):
            os.makedirs(self.research_dir)
            
        self.research_data['query'] = topic
        self.research_data['timestamp'] = now.isoformat()
        
        # Generate search terms
        if self.status_callback: self.status_callback("Generating search terms...")
        search_terms = self.generate_search_terms(topic)
        
        # Search Wikipedia first (most comprehensive)
        if self.status_callback: self.status_callback(f"Searching Wikipedia for: {topic}...")
        wiki_info = self.search_wikipedia(topic)
        if wiki_info and wiki_info.get('summary'):
            self.research_data['sources']['wikipedia'].append(wiki_info)
            print(f"  ✓ Retrieved Wikipedia article: {wiki_info.get('title')}")
        
        # Search each source with relevant terms
        for i, term in enumerate(search_terms[:5]):  # Limit to 5 search terms
            print(f"\n--- Searching with term: {term} ---")
            if self.status_callback: self.status_callback(f"Phase {i+1}/5: Searching sources for '{term}'...")
            
            # Get web results
            web_results = self.search_web_results(term)
            self.research_data['sources']['web_results'].extend(web_results[:max_results_per_source])
            
            # Get news
            news_articles = self.search_news(term)
            self.research_data['sources']['news'].extend(news_articles[:max_results_per_source])
            
            # Get blog posts
            blog_posts = self.search_blog_posts(term)
            self.research_data['sources']['blogs'].extend(blog_posts[:max_results_per_source])
            
            # Deep dive into top results using smart scraper
            all_links = [r.get('url', r.get('link')) for r in web_results[:2] + news_articles[:1] if r.get('url') or r.get('link')]
            for link in all_links:
                if link:
                    if self.status_callback: self.status_callback(f"Deep diving into: {link[:50]}...")
                    scraped = self.smart_scraper.scrape_url(link, force_tool=tool_preference)
                    if scraped and scraped.get('text_content'):
                        self.research_data['sources']['deep_dive'].append({
                            'title': scraped.get('title', 'Unknown Article'),
                            'summary': scraped.get('text_content', '')[:1000],
                            'full_text': scraped.get('text_content', ''),
                            'url': link,
                            'source': scraped.get('tool', 'web_deep_dive')
                        })
            
            time.sleep(1)  # Be respectful to APIs
        
        # Remove duplicates across sources
        self._deduplicate_results()
        
        # Count total items
        total_items = sum(len(items) for items in self.research_data['sources'].values())
        print(f"\n📊 Collected {total_items} total items across all sources")
        
        # Analyze content
        if total_items > 0:
            self.analyze_content()
        else:
            print("\n⚠️  No results found. Try:")
            print("   - Using different search terms")
            print("   - Checking your internet connection")
            print("   - Trying a broader topic")
        
        print("\n✅ Research complete!")
        return self.research_data
    
    def _deduplicate_results(self):
        """Remove duplicate results based on title similarity"""
        for category in self.research_data['sources']:
            items = self.research_data['sources'][category]
            unique_items = {}
            
            for item in items:
                if isinstance(item, dict):
                    # Create a key from title (or summary if no title)
                    title = item.get('title', item.get('summary', ''))[:100]
                    title_lower = title.lower().strip()
                    
                    # Simple deduplication
                    if title_lower and title_lower not in unique_items:
                        unique_items[title_lower] = item
            
            self.research_data['sources'][category] = list(unique_items.values())
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive research report for ANY topic
        """
        print("\n📝 Generating comprehensive report...")
        
        report = []
        report.append("=" * 80)
        report.append(f"📚 COMPREHENSIVE RESEARCH REPORT")
        report.append(f"Topic: {self.research_data['query']}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        # Executive Summary
        report.append("📋 EXECUTIVE SUMMARY")
        report.append("-" * 40)
        
        total_sources = sum(len(items) for items in self.research_data['sources'].values())
        report.append(f"Total sources analyzed: {total_sources}")
        report.append(f"Key points identified: {len(self.research_data['key_points'])}")
        report.append(f"Statistics found: {len(self.research_data['statistics'])}")
        report.append(f"Definitions extracted: {len(self.research_data['definitions'])}")
        report.append("")
        
        # Definitions
        if self.research_data['definitions']:
            report.append("📖 KEY DEFINITIONS")
            report.append("-" * 40)
            for i, definition in enumerate(self.research_data['definitions'][:5], 1):
                report.append(f"{i}. {definition}")
            report.append("")
        
        # Key Points
        if self.research_data['key_points']:
            report.append("🔑 KEY POINTS")
            report.append("-" * 40)
            for i, point in enumerate(self.research_data['key_points'][:10], 1):
                report.append(f"{i}. {point}")
            report.append("")
        
        # Statistics
        if self.research_data['statistics']:
            report.append("📊 STATISTICS & DATA")
            report.append("-" * 40)
            for i, stat in enumerate(self.research_data['statistics'][:8], 1):
                report.append(f"{i}. {stat}")
            report.append("")
        
        # Trends
        if self.research_data['trends']:
            report.append("📈 TRENDS & PATTERNS")
            report.append("-" * 40)
            for i, trend in enumerate(self.research_data['trends'][:5], 1):
                report.append(f"{i}. {trend}")
            report.append("")
        
        # Case Studies
        if self.research_data['case_studies']:
            report.append("📋 CASE STUDIES & EXAMPLES")
            report.append("-" * 40)
            for i, case in enumerate(self.research_data['case_studies'][:5], 1):
                report.append(f"{i}. {case}")
            report.append("")
        
        # Quotes
        if self.research_data['quotes']:
            report.append("💬 NOTABLE QUOTES")
            report.append("-" * 40)
            for i, quote in enumerate(self.research_data['quotes'][:5], 1):
                report.append(f"{i}. \"{quote}\"")
            report.append("")
        
        # Wikipedia Summary
        if self.research_data['sources']['wikipedia']:
            wiki = self.research_data['sources']['wikipedia'][0]
            if wiki.get('summary'):
                report.append("📚 WIKIPEDIA SUMMARY")
                report.append("-" * 40)
                summary = wiki['summary'][:1000] + "..." if len(wiki['summary']) > 1000 else wiki['summary']
                report.append(summary)
                if wiki.get('url'):
                    report.append(f"\nFull article: {wiki['url']}")
                report.append("")
        
        # News Articles
        if self.research_data['sources']['news']:
            report.append("📰 RECENT NEWS")
            report.append("-" * 40)
            for i, article in enumerate(self.research_data['sources']['news'][:5], 1):
                report.append(f"{i}. {article.get('title', 'N/A')}")
                if article.get('source'):
                    report.append(f"   Source: {article['source']}")
                if article.get('link'):
                    report.append(f"   Link: {article['link']}")
                report.append("")
        
        # Blog Posts
        if self.research_data['sources']['blogs']:
            report.append("✍️ BLOG POSTS")
            report.append("-" * 40)
            for i, post in enumerate(self.research_data['sources']['blogs'][:5], 1):
                report.append(f"{i}. {post.get('title', 'N/A')}")
                if post.get('author'):
                    report.append(f"   Author: {post['author']}")
                if post.get('link'):
                    report.append(f"   Link: {post['link']}")
                report.append("")
        
        # Web Results
        if self.research_data['sources']['web_results']:
            report.append("🌐 WEB RESOURCES")
            report.append("-" * 40)
            for i, result in enumerate(self.research_data['sources']['web_results'][:5], 1):
                report.append(f"{i}. {result.get('title', 'N/A')}")
                if result.get('url'):
                    report.append(f"   URL: {result['url']}")
                report.append("")
        
        # Resources
        report.append("🔗 USEFUL RESOURCES")
        report.append("-" * 40)
        
        all_links = []
        for category in ['wikipedia', 'news', 'blogs', 'web_results']:
            for item in self.research_data['sources'].get(category, []):
                if isinstance(item, dict) and item.get('url'):
                    url = item.get('url')
                    title = item.get('title', 'Resource')[:50]
                    if url and url not in [l[1] for l in all_links]:
                        all_links.append((title, url))
        
        for i, (title, url) in enumerate(all_links[:15], 1):
            report.append(f"{i}. {title}")
            report.append(f"   {url}")
            report.append("")
        
        # Search Terms Used
        report.append("🔍 SEARCH TERMS USED")
        report.append("-" * 40)
        for term in self.research_data['expanded_terms'][:10]:
            report.append(f"• {term}")
        report.append("")
        
        report.append("=" * 80)
        report.append("📌 END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, filename: str = None):
        """Save report to file"""
        if not filename:
            filename = os.path.join(self.research_dir, "report.txt")
        elif not os.path.isabs(filename) and self.research_dir:
            filename = os.path.join(self.research_dir, filename)
        
        report = self.generate_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ Report saved to: {filename}")
        return filename
    
    def save_json_data(self, filename: str = None):
        """Save raw data as JSON"""
        if not filename:
            filename = os.path.join(self.research_dir, "data.json")
        elif not os.path.isabs(filename) and self.research_dir:
            filename = os.path.join(self.research_dir, filename)
        
        # Merge smart scraper data if any
        if self.smart_scraper.research_data:
            self.research_data['deep_dive_results'] = self.smart_scraper.research_data
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.research_data, f, indent=2, default=str)
        
        print(f"✅ Raw data saved to: {filename}")
        return filename
    
    def save_markdown_report(self, filename: str = None):
        """Save report as Markdown"""
        if not filename:
            filename = os.path.join(self.research_dir, "report.md")
        elif not os.path.isabs(filename) and self.research_dir:
            filename = os.path.join(self.research_dir, filename)
        
        report = self.generate_report()
        
        # Convert to markdown format
        md_report = report.replace("=" * 80, "---\n")
        md_report = md_report.replace("-" * 40, "###")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_report)
        
        print(f"✅ Markdown report saved to: {filename}")
        return filename

def main():
    """
    Main function to run the general research automator
    """
    import sys
    
    print("=" * 60)
    print("🎓 GENERAL RESEARCH AUTOMATION SCRIPT")
    print("=" * 60)
    print("Works for ANY topic - from science to pop culture!")
    print("=" * 60)
    
    # Create researcher
    researcher = GeneralResearchAutomator()
    
    # Get topic from arguments or user
    topic = ""
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
        print(f"\n🔍 Research topic (from arguments): {topic}")
    else:
        topic = input("\n🔍 Enter your research topic: ").strip()
    
    if not topic:
        print("No topic entered. Exiting.")
        return
    
    # Max results per source
    max_results = 15 # Default
    if len(sys.argv) <= 1:
        max_results_input = input("📊 Max items per source (default 15): ").strip()
        max_results = int(max_results_input) if max_results_input.isdigit() else 15
    
    # Confirm
    print(f"\n{'='*50}")
    print(f"Research Configuration:")
    print(f"  Topic: {topic}")
    print(f"  Max items per source: {max_results}")
    print(f"{'='*50}")
    
    proceed = 'y'
    if len(sys.argv) <= 1:
        proceed = input("\n✅ Proceed with research? (y/n): ").strip().lower()
    
    if proceed == 'y':
        import time
        start_time = time.time()
        
        # Perform research
        data = researcher.research(topic, max_results)
        
        # Save results
        if sum(len(items) for items in data['sources'].values()) > 0:
            txt_file = researcher.save_report()
            json_file = researcher.save_json_data()
            md_file = researcher.save_markdown_report()
            html_file = generate_html_report(json_file, researcher.research_dir)
            
            # Update central index and dashboard
            metadata = {
                "stats": {
                    "sources": sum(len(items) for items in data['sources'].values()),
                    "key_points": len(data.get('key_points', [])),
                    "trends": len(data.get('trends', []))
                },
                "files": [
                    {"name": "HTML Report", "path": html_file},
                    {"name": "Text Report", "path": txt_file},
                    {"name": "JSON Data", "path": json_file},
                    {"name": "Markdown Report", "path": md_file}
                ]
            }
            update_index(topic, researcher.research_dir, metadata)
            
            elapsed_time = time.time() - start_time
            print(f"\n⏱️  Research completed in {elapsed_time:.1f} seconds")
            
            # Summary
            total_items = sum(len(items) for items in data['sources'].values())
            print(f"\n📊 Research Summary:")
            print(f"  • Total sources: {total_items}")
            print(f"  • Key points: {len(data['key_points'])}")
            print(f"  • Statistics: {len(data['statistics'])}")
            print(f"  • Definitions: {len(data['definitions'])}")
            print(f"  • Trends: {len(data['trends'])}")
            
            print(f"\n📁 Check the generated files for your full report!")
        else:
            print("\n⚠️  No results to save. Try:")
            print("   - Using a broader topic")
            print("   - Checking your internet connection")
            print("   - Trying different search terms")
    else:
        print("Research cancelled.")

if __name__ == "__main__":
    main()