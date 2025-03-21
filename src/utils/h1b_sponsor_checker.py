import requests
import json
import os
import time
from typing import Dict, List, Optional, Tuple
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class H1BSponsorChecker:
    """
    Utility class to check if a company sponsors H1B visas.
    Uses real-time API calls to public H1B databases.
    """
    
    def __init__(self, cache_dir: str = "data_folder/h1b_cache"):
        """
        Initialize the H1B sponsor checker.
        
        Args:
            cache_dir: Directory to store temporary cache data
        """
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "h1b_cache.json")
        self.cache_expiry = 24  # Cache expires after 24 hours
        self.sponsors_cache = self._load_cache()
        
        # API endpoints
        self.h1b_grader_api = "https://www.h1bgrader.com/api/v1/search"
        self.h1b_data_api = "https://h1bdata.info/index.php"
        self.myvisajobs_url = "https://www.myvisajobs.com/Search_Visa_Sponsor.aspx"
        
    def _load_cache(self) -> Dict[str, Tuple[bool, float]]:
        """
        Load the cached H1B sponsor data if available.
        
        Returns:
            Dictionary mapping company names to (is_sponsor, timestamp) tuples
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                return cache_data
            except Exception as e:
                logger.error(f"Error loading H1B sponsors cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save the current cache to disk."""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.sponsors_cache, f)
        except Exception as e:
            logger.error(f"Error saving H1B sponsors cache: {e}")
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """
        Check if a cached entry is still valid.
        
        Args:
            timestamp: Unix timestamp of when the entry was cached
            
        Returns:
            True if the entry is still valid, False otherwise
        """
        current_time = time.time()
        return (current_time - timestamp) < (self.cache_expiry * 3600)
    
    def check_h1b_sponsorship(self, company_name: str) -> bool:
        """
        Check if a company sponsors H1B visas.
        
        Args:
            company_name: Name of the company to check
            
        Returns:
            True if the company sponsors H1B visas, False otherwise
        """
        company_name_lower = company_name.lower()
        
        # Check cache first
        if company_name_lower in self.sponsors_cache:
            is_sponsor, timestamp = self.sponsors_cache[company_name_lower]
            if self._is_cache_valid(timestamp):
                return is_sponsor
        
        # Check using multiple sources
        is_sponsor = self._check_multiple_sources(company_name)
        
        # Update cache
        self.sponsors_cache[company_name_lower] = (is_sponsor, time.time())
        self._save_cache()
        
        return is_sponsor
    
    def _check_multiple_sources(self, company_name: str) -> bool:
        """
        Check if a company sponsors H1B visas using multiple sources.
        
        Args:
            company_name: Name of the company to check
            
        Returns:
            True if the company sponsors H1B visas according to any source, False otherwise
        """
        # Try multiple sources and return True if any of them indicate sponsorship
        sources = [
            self._check_h1b_data,
            self._check_myvisajobs,
            self._check_h1b_grader
        ]
        
        for source_check in sources:
            try:
                if source_check(company_name):
                    return True
            except Exception as e:
                logger.debug(f"Error checking source for {company_name}: {e}")
                continue
        
        return False
    
    def _check_h1b_data(self, company_name: str) -> bool:
        """
        Check if a company is in H1BData.info database.
        
        Args:
            company_name: Name of the company to check
            
        Returns:
            True if found in database, False otherwise
        """
        try:
            # Query the H1B database
            params = {
                'employer': company_name,
                'year': 'all',  # Check all available years
                'top': '1'      # We just need to know if there are any results
            }
            response = requests.get(self.h1b_data_api, params=params, timeout=10)
            
            # If the company has sponsored H1B visas, the response will contain results
            return "No results found" not in response.text
        except Exception as e:
            logger.debug(f"Error checking H1BData for {company_name}: {e}")
            return False
    
    def _check_myvisajobs(self, company_name: str) -> bool:
        """
        Check if a company is in MyVisaJobs database.
        
        Args:
            company_name: Name of the company to check
            
        Returns:
            True if found in database, False otherwise
        """
        try:
            # Query MyVisaJobs
            params = {
                'searchtext': company_name,
                'searchtype': 'sponsor'
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.myvisajobs_url, params=params, headers=headers, timeout=10)
            
            # Parse the response
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if the company is in the results
            result_tables = soup.find_all('table', class_='tbl')
            if not result_tables:
                return False
                
            for table in result_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        result_company = cells[0].text.strip().lower()
                        if company_name.lower() in result_company or result_company in company_name.lower():
                            return True
            
            return False
        except Exception as e:
            logger.debug(f"Error checking MyVisaJobs for {company_name}: {e}")
            return False
    
    def _check_h1b_grader(self, company_name: str) -> bool:
        """
        Check if a company is in H1BGrader database.
        
        Args:
            company_name: Name of the company to check
            
        Returns:
            True if found in database, False otherwise
        """
        try:
            # Query H1BGrader API
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            data = {
                'query': company_name,
                'page': 1,
                'limit': 5
            }
            response = requests.post(self.h1b_grader_api, headers=headers, json=data, timeout=10)
            
            # Parse the response
            if response.status_code == 200:
                result = response.json()
                if 'companies' in result and len(result['companies']) > 0:
                    for company in result['companies']:
                        if company_name.lower() in company['name'].lower() or company['name'].lower() in company_name.lower():
                            return True
            
            return False
        except Exception as e:
            logger.debug(f"Error checking H1BGrader for {company_name}: {e}")
            return False
    
    def get_top_h1b_sponsors(self, limit: int = 100) -> List[str]:
        """
        Get a list of top H1B sponsors from MyVisaJobs.
        
        Args:
            limit: Maximum number of sponsors to return
            
        Returns:
            List of company names known to sponsor H1B visas
        """
        sponsors = []
        try:
            # Get the current year
            current_year = datetime.now().year
            
            # MyVisaJobs provides top H1B sponsors by year
            url = f"https://www.myvisajobs.com/Reports/{current_year}-H1B-Visa-Sponsor.aspx"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            # Parse the response
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract company names from the table
            tables = soup.find_all('table', class_='tbl')
            if tables:
                rows = tables[0].find_all('tr')
                for row in rows[1:limit+1]:  # Skip header row and limit results
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        company_name = cells[1].text.strip()
                        sponsors.append(company_name)
                        # Add to cache
                        self.sponsors_cache[company_name.lower()] = (True, time.time())
                
                # Save updated cache
                self._save_cache()
            
            logger.info(f"Collected {len(sponsors)} top H1B sponsors from MyVisaJobs")
        except Exception as e:
            logger.error(f"Error collecting top H1B sponsors: {e}")
        
        return sponsors
