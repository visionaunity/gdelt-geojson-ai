import logging
import ollama
from typing import Dict, List, Any
from os import getenv

logger = logging.getLogger(__name__)

class EventSummarizer:
    def __init__(self, model_name: str = "llama3.1", model_options: Dict[str, Any] = None):
        """
        Initialize the event summarizer with Ollama model.
        """
        self.model_name = model_name
        self.model_options = model_options or {
            "num_predict": 100,
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.9,
        }
        
        try:
            logger.info("="*50)
            logger.info(f"Initializing AI Summarizer with model: {model_name}")
            logger.info(f"Model configuration:")
            for key, value in self.model_options.items():
                logger.info(f"  - {key}: {value}")
            logger.info("="*50)
            
            ollama.list()
            logger.info("Successfully connected to Ollama service")
        except ConnectionError as e:
            logger.error("Could not connect to Ollama service. Is it running?")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {str(e)}")
            raise

    def summarize_events(self, events_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Summarize events using Ollama.
        """
        total_events = len(events_data.get("events", []))
        logger.info("="*50)
        logger.info(f"Starting batch summarization of {total_events} events")
        logger.info(f"Using model: {self.model_name}")
        logger.info("="*50)
        
        summarized_events = []
        
        try:
            for idx, event in enumerate(events_data.get("events", []), 1):
                try:
                    logger.info(f"\nProcessing event {idx}/{total_events}")
                    logger.info(f"Event location: {event.get('location', 'Unknown')}")
                    logger.info(f"Event date: {event.get('date', 'Unknown')}")
                    
                    summary = self._generate_summary(event)
                    if summary:
                        summarized_events.append(summary)
                        logger.info(f"Summary generated ({len(summary['summary'])} chars)")
                        logger.info(f"Summary preview: {summary['summary'][:150]}...")
                    logger.info(f"Event {idx} processing complete")
                    logger.info("-"*30)
                    
                except KeyboardInterrupt:
                    logger.info("\nInterrupted during event summarization. Saving partial results...")
                    return summarized_events
                except Exception as e:
                    logger.error(f"Failed to summarize event {idx}: {str(e)}")
                    continue
            
            logger.info("="*50)
            logger.info(f"Batch summarization complete:")
            logger.info(f"  - Total events processed: {total_events}")
            logger.info(f"  - Successful summaries: {len(summarized_events)}")
            logger.info(f"  - Failed summaries: {total_events - len(summarized_events)}")
            logger.info("="*50)
            return summarized_events
            
        except KeyboardInterrupt:
            logger.info("\nInterrupted during event summarization. Saving partial results...")
            return summarized_events
        
    def _generate_summary(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary for a single event using Ollama.
        """
        try:
            location = f"{event.get('location', '')}"
            description = event.get('description', '')
            
            logger.info("Generating AI summary for event:")
            logger.info(f"  Description: {description}")
            logger.info(f"  Location: {location}")
            
            # Create a prompt for the model
            prompt = f"""
            Summarize the following event in a concise manner:
            Event: {description}
            Location: {location}
            Date: {event.get('date', '')}
            
            Provide a brief, factual summary focusing on the key details.
            """
            
            logger.info("Sending request to Ollama...")
            logger.debug(f"Full prompt: {prompt}")
            
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options=self.model_options
            )
            
            summary = response['response'].strip()
            logger.info("Received AI response:")
            logger.info(f"  Length: {len(summary)} characters")
            logger.info(f"  Preview: {summary[:100]}...")
            
            result = {
                "summary": summary,
                "location": {
                    "lat": event.get("latitude", 0.0),
                    "lon": event.get("longitude", 0.0)
                },
                "timestamp": event.get("date", ""),
                "tone": event.get("tone", 0.0)
            }
            
            logger.debug("Full processed result:")
            logger.debug(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            raise