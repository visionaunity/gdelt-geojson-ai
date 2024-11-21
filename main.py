import logging
import signal
import sys
from datetime import datetime
from src.gdelt_fetcher import GDELTFetcher
from src.event_summarizer import EventSummarizer
from src.geojson_generator import GeoJSONGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    logger.info("\n=== Received interrupt signal. Cleaning up... ===")
    sys.exit(0)

def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination requests
    
    # LLM Configuration
    MODEL_CONFIG = {
        "model_name": "llama3.1",  # or "mistral", "llama2-uncensored", etc.
        "options": {
            "num_predict": 200,  # Increased from 100 for longer summaries
            "temperature": 0.3,  # Lower temperature for more focused outputs
            "top_k": 10,         # Limit token selection to top 10
            "top_p": 0.9,        # Nucleus sampling threshold
        }
    }
    
    try:
        logger.info("=== Starting GDELT GeoJSON Generator ===")
        logger.info("Press Ctrl+C at any time to safely exit")
        
        # Initialize components
        logger.info("Initializing components...")
        fetcher = GDELTFetcher(
            verify_ssl=False, 
            max_days_back=3,
            save_files=True  # Set to False in production
        )
        summarizer = EventSummarizer(
            model_name=MODEL_CONFIG["model_name"],
            model_options=MODEL_CONFIG["options"]
        )
        geojson_gen = GeoJSONGenerator()
        logger.info(f"Components initialized successfully with model: {MODEL_CONFIG['model_name']}")

        # Get today's date
        today = datetime.now().strftime('%Y%m%d')
        logger.info(f"Starting search from date: {today}")
        
        # Fetch GDELT data
        logger.info("=== Phase 1: Fetching GDELT Data ===")
        events_data = fetcher.fetch_daily_report(today)
        logger.info(f"Successfully fetched {len(events_data.get('events', []))} events")
        
        # Summarize events
        logger.info("=== Phase 2: Summarizing Events ===")
        summarized_events = summarizer.summarize_events(events_data)
        logger.info(f"Successfully summarized {len(summarized_events)} events")
        
        # Generate GeoJSON
        logger.info("=== Phase 3: Generating GeoJSON ===")
        geojson_data = geojson_gen.generate(summarized_events)
        
        # Save to file
        output_file = 'events.geojson'
        geojson_gen.save(geojson_data, output_file)
        logger.info(f"Successfully saved GeoJSON to {output_file}")
        logger.info("=== Process Complete ===")

    except KeyboardInterrupt:
        logger.info("\n=== Process interrupted by user ===")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 