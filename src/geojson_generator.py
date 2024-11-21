import json
import logging
from typing import Dict, List, Any
from geojson import Feature, FeatureCollection, Point

logger = logging.getLogger(__name__)

class GeoJSONGenerator:
    def generate(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate GeoJSON from summarized events.
        
        Args:
            events (List[Dict]): List of summarized events
            
        Returns:
            Dict containing GeoJSON data
        """
        features = []
        
        for event in events:
            try:
                feature = self._create_feature(event)
                if feature:
                    features.append(feature)
            except Exception as e:
                logger.error(f"Failed to create feature for event: {str(e)}")
                continue
                
        return FeatureCollection(features)
        
    def save(self, geojson_data: Dict[str, Any], output_file: str):
        """
        Save GeoJSON data to a file.
        
        Args:
            geojson_data (Dict): GeoJSON data to save
            output_file (str): Path to output file
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(geojson_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save GeoJSON: {str(e)}")
            raise
            
    def _create_feature(self, event: Dict[str, Any]) -> Feature:
        """
        Create a GeoJSON feature from an event.
        
        Args:
            event (Dict): Single event data
            
        Returns:
            GeoJSON Feature object
        """
        point = Point((
            event["location"]["lon"],
            event["location"]["lat"]
        ))
        
        properties = {
            "summary": event["summary"],
            "timestamp": event["timestamp"],
            "tone": event["tone"]
        }
        
        return Feature(geometry=point, properties=properties) 