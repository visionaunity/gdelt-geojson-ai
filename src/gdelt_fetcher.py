import requests
import logging
import pandas as pd
import io
import zipfile
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

logger = logging.getLogger(__name__)

class GDELTFetcher:
    # GDELT CSV column names
    COLUMNS = [
        'GLOBALEVENTID', 'SQLDATE', 'MonthYear', 'Year', 'FractionDate',
        'Actor1Code', 'Actor1Name', 'Actor1CountryCode', 'Actor1KnownGroupCode',
        'Actor1EthnicCode', 'Actor1Religion1Code', 'Actor1Religion2Code',
        'Actor1Type1Code', 'Actor1Type2Code', 'Actor1Type3Code',
        'Actor2Code', 'Actor2Name', 'Actor2CountryCode', 'Actor2KnownGroupCode',
        'Actor2EthnicCode', 'Actor2Religion1Code', 'Actor2Religion2Code',
        'Actor2Type1Code', 'Actor2Type2Code', 'Actor2Type3Code',
        'IsRootEvent', 'EventCode', 'EventBaseCode', 'EventRootCode',
        'QuadClass', 'GoldsteinScale', 'NumMentions', 'NumSources',
        'NumArticles', 'AvgTone',
        'Actor1Geo_Type', 'Actor1Geo_FullName', 'Actor1Geo_CountryCode',
        'Actor1Geo_ADM1Code', 'Actor1Geo_Lat', 'Actor1Geo_Long',
        'Actor2Geo_Type', 'Actor2Geo_FullName', 'Actor2Geo_CountryCode',
        'Actor2Geo_ADM1Code', 'Actor2Geo_Lat', 'Actor2Geo_Long',
        'ActionGeo_Type', 'ActionGeo_FullName', 'ActionGeo_CountryCode',
        'ActionGeo_ADM1Code', 'ActionGeo_Lat', 'ActionGeo_Long',
        'DATEADDED', 'SOURCEURL'
    ]

    def __init__(self, verify_ssl: bool = False, max_days_back: int = 7, save_files: bool = True):
        """
        Initialize the GDELT fetcher.
        
        Args:
            verify_ssl (bool): Whether to verify SSL certificates. Default False due to GDELT's cert issues.
            max_days_back (int): Maximum number of days to look back for reports
            save_files (bool): Whether to save downloaded files locally for debugging
        """
        self.base_url = "http://data.gdeltproject.org/events"
        self.verify_ssl = verify_ssl
        self.max_days_back = max_days_back
        self.save_files = save_files
        self.data_dir = "data/gdelt_downloads"
        
        if self.save_files:
            os.makedirs(self.data_dir, exist_ok=True)
            logger.info(f"Files will be saved to: {os.path.abspath(self.data_dir)}")
        
        if not verify_ssl:
            logger.warning("SSL certificate verification is disabled. Use with caution.")
        
    def fetch_daily_report(self, start_date: str) -> Dict[str, Any]:
        """
        Fetches the daily GDELT report, trying multiple dates if needed.
        
        Args:
            start_date (str): Starting date in YYYYMMDD format
            
        Returns:
            Dict containing the parsed GDELT data
            
        Raises:
            Exception: If no report is found within max_days_back
        """
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        
        for days_back in range(self.max_days_back):
            current_date = start_dt - timedelta(days=days_back)
            current_date_str = current_date.strftime('%Y%m%d')
            
            data = self._try_fetch_report(current_date_str)
            if data is not None:
                logger.info(f"Successfully found report for date: {current_date_str}")
                return data
                
            logger.info(f"No report found for {current_date_str}, trying previous day...")
            
        raise Exception(f"No GDELT report found within the last {self.max_days_back} days")
            
    def _try_fetch_report(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to fetch and parse a report for a specific date.
        
        Args:
            date (str): Date in YYYYMMDD format
            
        Returns:
            Dict containing parsed data if successful, None if report not found
        """
        try:
            url = f"{self.base_url}/{date}.export.CSV.zip"
            logger.info(f"Requesting URL: {url}")
            
            response = requests.get(url, verify=self.verify_ssl)
            response.raise_for_status()
            
            content_size_mb = len(response.content) / (1024 * 1024)
            logger.info(f"Successfully downloaded CSV report ({content_size_mb:.2f} MB)")
            
            if self.save_files:
                zip_path = os.path.join(self.data_dir, f"{date}.export.CSV.zip")
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Saved zip file to: {os.path.abspath(zip_path)}")
                
                # Also save the URL to a text file for reference
                url_file = os.path.join(self.data_dir, f"{date}_url.txt")
                with open(url_file, 'w') as f:
                    f.write(f"Download URL: {url}\n")
                    f.write(f"Download time: {datetime.now().isoformat()}\n")
                    f.write(f"File size: {content_size_mb:.2f} MB\n")
                logger.info(f"Saved URL info to: {os.path.abspath(url_file)}")
            
            # Parse CSV data
            logger.info("Beginning CSV parsing...")
            events_data = self._parse_csv(response.content)
            
            if self.save_files:
                # Save the parsed events data for debugging
                json_path = os.path.join(self.data_dir, f"{date}_parsed_events.json")
                import json
                with open(json_path, 'w') as f:
                    json.dump(events_data, f, indent=2)
                logger.info(f"Saved parsed events to: {os.path.abspath(json_path)}")
            
            return events_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
        except requests.exceptions.SSLError as e:
            logger.error("SSL Certificate verification failed. If you trust this source, "
                        "you can disable SSL verification by setting verify_ssl=False")
            raise
        except requests.RequestException as e:
            logger.error(f"Failed to fetch GDELT data: {str(e)}")
            raise
            
    def _parse_csv(self, content: bytes) -> Dict[str, Any]:
        """
        Parse the zipped CSV content into a structured format.
        Limited to the 10 most recent events.
        
        Args:
            content (bytes): Raw CSV content (zipped)
            
        Returns:
            Dict containing parsed event data
        """
        try:
            zip_buffer = io.BytesIO(content)
            
            with zipfile.ZipFile(zip_buffer) as zip_file:
                csv_filename = zip_file.namelist()[0]
                logger.info(f"Processing zip file, found CSV: {csv_filename}")
                
                if self.save_files:
                    # Extract the CSV file for inspection
                    csv_path = os.path.join(self.data_dir, f"latest_extract_{csv_filename}")
                    zip_file.extract(csv_filename, path=self.data_dir)
                    os.rename(os.path.join(self.data_dir, csv_filename), csv_path)
                    logger.info(f"Extracted CSV file to: {os.path.abspath(csv_path)}")
                
                with zip_file.open(csv_filename) as csv_file:
                    logger.info("Parsing CSV data with pandas...")
                    df = pd.read_csv(
                        csv_file,
                        sep='\t',  # GDELT uses tab-separated values
                        names=self.COLUMNS,  # Use predefined column names
                        dtype={'SQLDATE': str},  # Keep date as string
                        nrows=10  # Changed from 1000 to 10 rows
                    )
                    
            logger.info(f"Successfully parsed {len(df)} events from CSV (limited to 10 most recent)")
            
            # Sort by DATEADDED to ensure we get the most recent events
            df = df.sort_values('DATEADDED', ascending=False)
            
            # Convert DataFrame to list of events
            events = []
            for _, row in df.iterrows():
                event = {
                    "id": row['GLOBALEVENTID'],
                    "date": row['SQLDATE'],
                    "description": f"{row['Actor1Name'] or 'Unknown Actor'} - "
                                 f"{row['EventCode']} - "
                                 f"{row['Actor2Name'] or 'Unknown Target'}",
                    "location": row['ActionGeo_FullName'],
                    "latitude": row['ActionGeo_Lat'],
                    "longitude": row['ActionGeo_Long'],
                    "tone": row['AvgTone'],
                    "metadata": {
                        "event_code": row['EventCode'],
                        "goldstein_scale": row['GoldsteinScale'],
                        "num_mentions": row['NumMentions'],
                        "num_sources": row['NumSources'],
                        "num_articles": row['NumArticles'],
                        "source_url": row['SOURCEURL']
                    }
                }
                events.append(event)
            
            logger.info(f"Converted {len(events)} events to structured format")
            return {"events": events}
            
        except zipfile.BadZipFile:
            logger.error("Failed to extract ZIP file - content may be corrupted")
            raise
        except pd.errors.EmptyDataError:
            logger.error("CSV file is empty")
            return {"events": []}
        except Exception as e:
            logger.error(f"Error parsing CSV data: {str(e)}")
            raise 