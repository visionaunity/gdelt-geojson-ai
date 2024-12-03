import logging
from src.x_fetcher import XFetcher
from src.event_summarizer import EventSummarizer
from src.geojson_generator import GeoJSONGenerator
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("="*50)
        logger.info("=== Starting X (Twitter) GeoJSON Generator ===")
        logger.info("="*50)
        
        # Initialize components
        logger.info("Initializing components...")
        fetcher = XFetcher(save_files=True)
        summarizer = EventSummarizer()
        geojson_gen = GeoJSONGenerator()
        logger.info("Components initialized successfully")
        
        # Fetch latest posts
        logger.info("="*50)
        logger.info("Phase 1: Fetching posts from X")
        posts = fetcher.fetch_latest_posts(max_results=10)
        logger.info(f"Retrieved {len(posts)} posts with location data")
        
        # Convert posts to event format
        logger.info("="*50)
        logger.info("Phase 2: Converting posts to event format")
        events = {
            "events": [
                {
                    "id": post["id"],
                    "date": post["created_at"],
                    "description": post["text"],
                    "location": post["location"],
                    "latitude": post["latitude"],
                    "longitude": post["longitude"],
                    "metadata": {
                        "source_url": post["url"],
                        "location_type": post["location_type"],
                        "country": post["country"]
                    }
                }
                for post in posts
            ]
        }
        logger.info(f"Converted {len(events['events'])} posts to event format")
        
        # Summarize events
        logger.info("="*50)
        logger.info("Phase 3: Generating AI summaries")
        summarized_events = summarizer.summarize_events(events)
        logger.info(f"Generated summaries for {len(summarized_events)} events")
        
        # Generate GeoJSON
        logger.info("="*50)
        logger.info("Phase 4: Creating GeoJSON output")
        geojson_data = geojson_gen.generate(summarized_events)
        
        # Save to file
        output_file = f'x_events_{datetime.now().strftime("%Y%m%d_%H%M%S")}.geojson'
        geojson_gen.save(geojson_data, output_file)
        logger.info(f"Successfully saved GeoJSON to: {os.path.abspath(output_file)}")
        
        # Final summary
        logger.info("="*50)
        logger.info("Process Complete!")
        logger.info(f"Total posts processed: {len(posts)}")
        logger.info(f"Total events with summaries: {len(summarized_events)}")
        logger.info(f"Output file: {output_file}")
        logger.info("="*50)
        
    except Exception as e:
        logger.error("="*50)
        logger.error("Fatal error occurred!")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("="*50)
        raise

if __name__ == "__main__":
    main() 