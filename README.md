# GDELT GeoJSON Generator with LLM Summarization

This project retrieves daily event updates from the GDELT Event Database, summarizes significant events using Ollama (local LLM), and generates a GeoJSON file for visualization.

## Features
- **Daily PDF Retrieval**: Downloads the GDELT daily trend report based on the current date.
- **Event Summarization**: Uses Ollama to analyze and summarize key events.
- **GeoJSON Output**: Converts summarized events into a GeoJSON file for geospatial applications.

## Prerequisites
- **Python 3.9+**
- **Dependencies**:
  - `requests`
  - `pandas`
  - `geojson`
  - `ollama`
- **Ollama**: Must be installed and running locally
- **GDELT Daily Reports**: Ensure internet access for retrieving daily PDFs.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/gdelt-geojson-generator.git
   cd gdelt-geojson-generator
   ```

2. Install Ollama:
   ```bash
   # For macOS/Linux
   curl https://ollama.ai/install.sh | sh
   
   # For other systems, visit: https://ollama.ai/download
   ```

3. Pull the required model:
   ```bash
   ollama pull llama3.2
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Start the Ollama service:
   ```bash
   ollama serve
   ```

2. Run the GeoJSON Generator:
   ```bash
   python main.py
   ```

### Workflow:
1. Fetches the GDELT daily PDF using the current date.
2. Summarizes events using Ollama.
3. Outputs `events.geojson` in the project directory.

## Output Example
Sample GeoJSON Format:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-98.5795, 39.828175]
      },
      "properties": {
        "event": "Protest",
        "summary": "Protest in the United States over recent policy changes.",
        "timestamp": "2024-11-20",
        "tone": 6.5
      }
    }
  ]
}
```