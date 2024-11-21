import logging
import ollama
from typing import Dict, List, Any
from os import getenv

logger = logging.getLogger(__name__)

class EventSummarizer:
    def __init__(self, model_name: str = "llama2"):
        """
        Initialize the event summarizer with Ollama model.
        
        Args:
            model_name (str): Name of the Ollama model to use
        """
        self.model_name = model_name
        try:
            # Test connection to Ollama
            ollama.pull(self.model_name)
        except Exception as e:
            logger.error(f"Failed to initialize Ollama model: {str(e)}")
            raise
            
    def summarize_events(self, events_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Summarize events using Ollama.
        
        Args:
            events_data (Dict): Raw event data from GDELT
            
        Returns:
            List of summarized events with locations and metadata
        """
        summarized_events = []
        
        for event in events_data.get("events", []):
            try:
                summary = self._generate_summary(event)
                if summary:
                    summarized_events.append(summary)
            except Exception as e:
                logger.error(f"Failed to summarize event: {str(e)}")
                continue
                
        return summarized_events
        
    def _generate_summary(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary for a single event using Ollama.
        
        Args:
            event (Dict): Single event data
            
        Returns:
            Dict containing the summarized event with metadata
        """
        try:
            # Create a prompt for the model
            prompt = f"""
            Summarize the following event in a concise manner:
            Event: {event.get('description', '')}
            Location: {event.get('location', '')}
            Date: {event.get('date', '')}
            
            Provide a brief, factual summary focusing on the key details.
            """
            
            # Get response from Ollama
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                temperature=0.7,
                max_tokens=100
            )
            
            summary = response['response'].strip()
            
            return {
                "summary": summary,
                "location": {
                    "lat": event.get("latitude", 0.0),
                    "lon": event.get("longitude", 0.0)
                },
                "timestamp": event.get("date", ""),
                "tone": event.get("tone", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            raise 