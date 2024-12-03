import requests
import logging
import json
import os
from typing import Dict, List, Any
from datetime import datetime
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import re
from requests_oauthlib import OAuth1

logger = logging.getLogger(__name__)

class XFetcher:
    def __init__(self, save_files: bool = True):
        """
        Initialize the X (Twitter) fetcher.
        """
        # Get credentials from environment variables
        self.api_key = os.getenv('X_API_KEY')
        self.api_key_secret = os.getenv('X_API_KEY_SECRET')
        self.access_token = os.getenv('X_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')
        self.bearer_token = os.getenv('X_BEARER_TOKEN')

        if not all([self.api_key, self.api_key_secret, self.bearer_token]):
            raise ValueError("X API credentials are required. Please check your .env file.")

        self.base_url = "https://api.twitter.com/2"
        self.save_files = save_files
        self.data_dir = "data/x_downloads"
        
        # Set up OAuth 1.0a
        self.auth = OAuth1(
            self.api_key,
            self.api_key_secret,
            self.access_token,
            self.access_token_secret
        )
        
        # Headers with Bearer token for v2 API
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "GeoLensAI/1.0"
        }
        
        self.geocoder = Nominatim(user_agent="GeoLensAI")
        
        if self.save_files:
            os.makedirs(self.data_dir, exist_ok=True)
            logger.info(f"Files will be saved to: {os.path.abspath(self.data_dir)}")
            
        logger.info("X API credentials loaded successfully")

    def fetch_latest_posts(self, query: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent posts from X, focusing on those with location information.
        
        Args:
            query (str): Search query to filter posts
            max_results (int): Maximum number of results to return
            
        Returns:
            List of processed posts with location data
        """
        try:
            logger.info("="*50)
            logger.info("Starting X API fetch process")
            logger.info(f"Max results requested: {max_results}")
            
            # Default query focuses on news and events with location indicators
            default_query = 'lang:en (breaking OR news OR event) (in OR at OR near OR from) -is:retweet'
            query = query or default_query
            
            logger.info(f"Using query: {query}")
            logger.info("Preparing API request parameters...")
            
            url = f"{self.base_url}/tweets/search/recent"
            params = {
                'query': query,
                'max_results': max_results,
                'tweet.fields': 'created_at,geo,context_annotations,entities',
                'expansions': 'geo.place_id',
                'place.fields': 'contained_within,country,country_code,full_name,geo,id,name,place_type'
            }
            
            logger.info(f"Making API request to: {url}")
            logger.debug(f"Request parameters: {params}")
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            logger.info(f"API request successful - Status code: {response.status_code}")
            
            if self.save_files:
                self._save_raw_response(response.json())
            
            result = self._process_posts(response.json())
            logger.info("="*50)
            return result
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch posts: {str(e)}")
            logger.error(f"Response status code: {getattr(e.response, 'status_code', 'N/A')}")
            logger.error(f"Response text: {getattr(e.response, 'text', 'N/A')}")
            raise

    def _process_posts(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process raw X API response into structured format with location data.
        """
        processed_posts = []
        posts = raw_data.get('data', [])
        
        logger.info(f"Processing {len(posts)} posts")
        
        for post in posts:
            try:
                # Extract text and basic metadata
                text = post.get('text', '')
                created_at = post.get('created_at')
                
                # Try to extract location information
                location_info = self._extract_location(post, text)
                
                if location_info:
                    processed_post = {
                        "id": post.get('id'),
                        "text": text,
                        "created_at": created_at,
                        "location": location_info.get('name'),
                        "latitude": location_info.get('latitude'),
                        "longitude": location_info.get('longitude'),
                        "location_type": location_info.get('type'),
                        "country": location_info.get('country'),
                        "url": f"https://twitter.com/i/web/status/{post.get('id')}"
                    }
                    
                    processed_posts.append(processed_post)
                    logger.info(f"Processed post with location: {location_info['name']}")
                
            except Exception as e:
                logger.warning(f"Failed to process post {post.get('id')}: {str(e)}")
                continue
            
            # Be nice to the geocoding service
            time.sleep(1)
        
        logger.info(f"Successfully processed {len(processed_posts)} posts with location data")
        return processed_posts

    def _extract_location(self, post: Dict[str, Any], text: str) -> Dict[str, Any]:
        """
        Extract location information from post data and text.
        """
        # First try explicit geo data from the post
        if 'geo' in post:
            place_data = post['geo'].get('place_id')
            if place_data:
                # Process place data...
                return {
                    'name': place_data.get('full_name'),
                    'latitude': place_data.get('geo', {}).get('coordinates', [0, 0])[0],
                    'longitude': place_data.get('geo', {}).get('coordinates', [0, 0])[1],
                    'type': place_data.get('place_type'),
                    'country': place_data.get('country')
                }
        
        # Try to extract location from text
        location_patterns = [
            r'in ([A-Z][a-zA-Z\s]+(?:,\s*[A-Z][a-zA-Z\s]+)*)',
            r'at ([A-Z][a-zA-Z\s]+(?:,\s*[A-Z][a-zA-Z\s]+)*)',
            r'from ([A-Z][a-zA-Z\s]+(?:,\s*[A-Z][a-zA-Z\s]+)*)',
            r'near ([A-Z][a-zA-Z\s]+(?:,\s*[A-Z][a-zA-Z\s]+)*)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                location_name = match.group(1)
                try:
                    location = self.geocoder.geocode(location_name)
                    if location:
                        return {
                            'name': location_name,
                            'latitude': location.latitude,
                            'longitude': location.longitude,
                            'type': 'extracted_from_text',
                            'country': None  # Could be enhanced with reverse geocoding
                        }
                except GeocoderTimedOut:
                    logger.warning(f"Geocoding timed out for location: {location_name}")
                    continue
        
        return None

    def _save_raw_response(self, data: Dict[str, Any]):
        """Save raw API response for debugging."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(self.data_dir, f'x_response_{timestamp}.json')
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Saved raw API response to: {filepath}") 