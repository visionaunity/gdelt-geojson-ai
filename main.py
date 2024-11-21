import logging
from datetime import datetime
from src.gdelt_fetcher import GDELTFetcher
from src.event_summarizer import EventSummarizer
from src.geojson_generator import GeoJSONGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize components
        fetcher = GDELTFetcher()
        summarizer = EventSummarizer()
        geojson_gen = GeoJSONGenerator()

        # Get today's date
        today = datetime.now().strftime('%Y%m%d')
        
        # Fetch GDELT data
        logger.info("Fetching GDELT data...")
        events_data = fetcher.fetch_daily_report(today)
        
        # Summarize events
        logger.info("Summarizing events...")
        summarized_events = summarizer.summarize_events(events_data)
        
        # Generate GeoJSON
        logger.info("Generating GeoJSON...")
        geojson_data = geojson_gen.generate(summarized_events)
        
        # Save to file
        output_file = 'events.geojson'
        geojson_gen.save(geojson_data, output_file)
        logger.info(f"GeoJSON saved to {output_file}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 