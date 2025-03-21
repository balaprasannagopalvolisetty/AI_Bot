import logging
import time
from typing import Dict, List, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class IndeedScraper:
    """
    Scraper for Indeed job listings.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Indeed scraper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.browser_config = config.get('BROWSER', {})
        self.job_search = config.get('JOB_SEARCH', {})
        self.timeout = self.browser_config.get('timeout', 30)
        self.user_agent = self.browser_config.get('user_agent', '')
        self.headless = self.browser_config.get('headless', False)
        
    def _setup_driver(self):
        """Set up the Selenium WebDriver."""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        if self.user_agent:
            options.add_argument(f'user-agent={self.user_agent}')
        
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1920, 1080)
        return driver
    
    def scrape_jobs(self) -> List[Dict[str, Any]]:
        """
        Scrape job listings from Indeed.
        
        Returns:
            List of job listings
        """
        job_listings = []
        
        # Get search parameters
        job_titles = self.job_search.get('job_titles', [])
        locations = self.job_search.get('locations', [])
        
        if not job_titles or not locations:
            logger.error("Job titles or locations not specified in config")
            return job_listings
        
        driver = self._setup_driver()
        
        try:
            # Search for each job title in each location
            for job_title in job_titles:
                for location in locations:
                    logger.info(f"Searching Indeed for '{job_title}' in '{location}'")
                    jobs = self._search_jobs(driver, job_title, location)
                    job_listings.extend(jobs)
                    
                    # Pause between searches to avoid rate limiting
                    time.sleep(2)
        
        finally:
            driver.quit()
        
        logger.info(f"Scraped {len(job_listings)} job listings from Indeed")
        return job_listings
    
    def _search_jobs(self, driver, job_title: str, location: str) -> List[Dict[str, Any]]:
        """
        Search for jobs with the given title and location.
        
        Args:
            driver: Selenium WebDriver
            job_title: Job title to search for
            location: Location to search in
            
        Returns:
            List of job listings
        """
        job_listings = []
        
        # Format the search URL
        search_url = f"https://www.indeed.com/jobs?q={job_title.replace(' ', '+')}&l={location.replace(' ', '+')}"
        
        try:
            driver.get(search_url)
            
            # Wait for job listings to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobsearch-ResultsList"))
            )
            
            # Extract job listings
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in job_cards:
                try:
                    # Extract job details
                    title_elem = card.find('h2', class_='jobTitle')
                    company_elem = card.find('span', class_='companyName')
                    location_elem = card.find('div', class_='companyLocation')
                    
                    if title_elem and company_elem and location_elem:
                        # Get job URL
                        job_id = card.get('data-jk', '')
                        if not job_id:
                            continue
                            
                        job_url = f"https://www.indeed.com/viewjob?jk={job_id}"
                        
                        # Get detailed job description
                        job_description = self._get_job_description(driver, job_url)
                        
                        job = {
                            'title': title_elem.text.strip(),
                            'company_name': company_elem.text.strip(),
                            'location': location_elem.text.strip(),
                            'url': job_url,
                            'description': job_description,
                            'source': 'Indeed'
                        }
                        
                        job_listings.append(job)
                
                except Exception as e:
                    logger.error(f"Error extracting job details: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error searching Indeed jobs: {e}")
        
        return job_listings
    
    def _get_job_description(self, driver, job_url: str) -> str:
        """
        Get the detailed job description from the job page.
        
        Args:
            driver: Selenium WebDriver
            job_url: URL of the job listing
            
        Returns:
            Job description text
        """
        try:
            # Open the job page in a new tab
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(job_url)
            
            # Wait for job description to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "jobDescriptionText"))
            )
            
            # Extract job description
            description_elem = driver.find_element(By.ID, "jobDescriptionText")
            description = description_elem.text
            
            # Close the tab and switch back
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
            return description
        
        except Exception as e:
            logger.error(f"Error getting job description: {e}")
            
            # Make sure to close the tab and switch back in case of error
            try:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except:
                pass
                
            return ""
