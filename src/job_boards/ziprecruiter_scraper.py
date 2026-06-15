import logging
import time
import random
from typing import Dict, List, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.utils.human_behavior import HumanBehavior

logger = logging.getLogger(__name__)

class ZipRecruiterScraper:
    """
    Scrapes job listings from ZipRecruiter.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the ZipRecruiter scraper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.browser_config = config.get('BROWSER', {})
        self.job_search = config.get('JOB_SEARCH', {})
        self.timeout = self.browser_config.get('timeout', 30)
        self.user_agent = self.browser_config.get('user_agent', '')
        self.headless = self.browser_config.get('headless', False)
        
        # Initialize human behavior helper
        self.human = HumanBehavior()
    
    def _setup_driver(self):
        """Set up the Selenium WebDriver with randomized browser fingerprint."""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        
        # Randomize user agent if not explicitly set in config
        if not self.user_agent:
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
            ]
            self.user_agent = random.choice(user_agents)
        
        options.add_argument(f'user-agent={self.user_agent}')
        
        # Add randomized window dimensions to vary fingerprint
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Disable automation flags to avoid detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        
        # Execute CDP commands to prevent detection
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        driver.set_window_size(width, height)
        return driver
    
    def scrape_jobs(self) -> List[Dict[str, Any]]:
        """
        Scrape job listings from ZipRecruiter.
        
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        driver = self._setup_driver()
        
        try:
            # Get job search parameters
            job_titles = self.job_search.get('job_titles', [])
            locations = self.job_search.get('locations', [])
            
            # Search for jobs for each job title and location combination
            for job_title in job_titles:
                for location in locations:
                    logger.info(f"Searching for {job_title} jobs in {location}")
                    
                    # Search for jobs
                    jobs_for_search = self._search_jobs(driver, job_title, location)
                    
                    # Add jobs to the list
                    jobs.extend(jobs_for_search)
                    
                    # Add random delay between searches
                    HumanBehavior.random_delay(2.0, 5.0)
            
            logger.info(f"Scraped {len(jobs)} jobs from ZipRecruiter")
            
        except Exception as e:
            logger.error(f"Error scraping ZipRecruiter jobs: {e}")
        
        finally:
            driver.quit()
        
        return jobs
    
    def _search_jobs(self, driver, job_title: str, location: str) -> List[Dict[str, Any]]:
        """
        Search for jobs on ZipRecruiter.
        
        Args:
            driver: Selenium WebDriver
            job_title: Job title to search for
            location: Location to search in
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        try:
            # Navigate to ZipRecruiter
            driver.get("https://www.ziprecruiter.com/")
            logger.info("Navigated to ZipRecruiter")
            
            # Wait for the search form to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "keyword"))
            )
            
            # Enter job title with human-like typing
            job_title_field = driver.find_element(By.ID, "keyword")
            HumanBehavior.human_like_typing(job_title_field, job_title)
            
            # Pause briefly like a human would after entering job title
            HumanBehavior.random_delay(0.8, 1.5)
            
            # Enter location with human-like typing
            location_field = driver.find_element(By.ID, "location")
            location_field.clear()
            HumanBehavior.human_like_typing(location_field, location)
            
            # Random delay before clicking search to simulate human thinking
            HumanBehavior.random_delay(0.5, 1.5)
            
            # Find and click the search button with human-like movement
            search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            HumanBehavior.human_like_click(driver, search_button)
            
            # Wait for search results to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.job_result"))
            )
            
            # Apply filters
            self._apply_filters(driver)
            
            # Wait for filtered results to load
            HumanBehavior.random_delay(2.0, 4.0)
            
            # Scroll through results to load more jobs
            self._scroll_through_results(driver)
            
            # Extract job listings
            job_listings = driver.find_elements(By.CSS_SELECTOR, "article.job_result")
            logger.info(f"Found {len(job_listings)} job listings")
            
            # Process each job listing
            for job_listing in job_listings:
                try:
                    # Extract job information
                    job = self._extract_job_info(driver, job_listing)
                    
                    # Add source information
                    job['source'] = 'ZipRecruiter'
                    
                    # Add job to the list
                    jobs.append(job)
                    
                except Exception as e:
                    logger.error(f"Error extracting job info: {e}")
                    continue
            
            logger.info(f"Extracted {len(jobs)} jobs from search results")
            
        except Exception as e:
            logger.error(f"Error searching for jobs: {e}")
        
        return jobs
    
    def _apply_filters(self, driver):
        """
        Apply filters to the job search.
        
        Args:
            driver: Selenium WebDriver
        """
        try:
            # Apply date posted filter (Last 7 days)
            try:
                date_filter_button = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Date Posted')]"))
                )
                HumanBehavior.human_like_click(driver, date_filter_button)
                
                # Wait for dropdown to appear
                HumanBehavior.random_delay(0.5, 1.0)
                
                # Click on "Last 7 days" option
                last_7_days_option = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Last 7 days')]"))
                )
                HumanBehavior.human_like_click(driver, last_7_days_option)
                
                # Click on "Apply" button
                apply_button = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Apply')]"))
                )
                HumanBehavior.human_like_click(driver, apply_button)
                
                logger.info("Applied Date Posted filter")
                HumanBehavior.random_delay(1.0, 2.0)
            except Exception as e:
                logger.warning(f"Could not apply Date Posted filter: {e}")
            
            # Apply job type filter (Full-time)
            try:
                job_type_button = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Job Type')]"))
                )
                HumanBehavior.human_like_click(driver, job_type_button)
                
                # Wait for dropdown to appear
                HumanBehavior.random_delay(0.5, 1.0)
                
                # Click on "Full-time" option
                full_time_option = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Full-time')]"))
                )
                HumanBehavior.human_like_click(driver, full_time_option)
                
                # Click on "Apply" button
                apply_button = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Apply')]"))
                )
                HumanBehavior.human_like_click(driver, apply_button)
                
                logger.info("Applied Job Type filter")
                HumanBehavior.random_delay(1.0, 2.0)
            except Exception as e:
                logger.warning(f"Could not apply Job Type filter: {e}")
            
            # Apply salary filter ($60,000+)
            try:
                salary_button = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Salary')]"))
                )
                HumanBehavior.human_like_click(driver, salary_button)
                
                # Wait for dropdown to appear
                HumanBehavior.random_delay(0.5, 1.0)
                
                # Click on "$60,000+" option
                salary_option = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), '$60,000+')]"))
                )
                HumanBehavior.human_like_click(driver, salary_option)
                
                # Click on "Apply" button
                apply_button = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Apply')]"))
                )
                HumanBehavior.human_like_click(driver, apply_button)
                
                logger.info("Applied Salary filter")
                HumanBehavior.random_delay(1.0, 2.0)
            except Exception as e:
                logger.warning(f"Could not apply Salary filter: {e}")
            
            # Apply experience level filter (Entry level)
            try:
                experience_button = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Experience')]"))
                )
                HumanBehavior.human_like_click(driver, experience_button)
                
                # Wait for dropdown to appear
                HumanBehavior.random_delay(0.5, 1.0)
                
                # Click on "Entry level" option
                entry_level_option = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Entry level')]"))
                )
                HumanBehavior.human_like_click(driver, entry_level_option)
                
                # Click on "Apply" button
                apply_button = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Apply')]"))
                )
                HumanBehavior.human_like_click(driver, apply_button)
                
                logger.info("Applied Experience Level filter")
                HumanBehavior.random_delay(1.0, 2.0)
            except Exception as e:
                logger.warning(f"Could not apply Experience Level filter: {e}")
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
    
    def _scroll_through_results(self, driver):
        """
        Scroll through job search results to load more jobs.
        
        Args:
            driver: Selenium WebDriver
        """
        try:
            # Scroll down a few times to load more results
            for _ in range(5):
                # Scroll down with human-like behavior
                HumanBehavior.scroll_page(driver, "down")
                
                # Wait for new results to load
                HumanBehavior.random_delay(1.0, 2.0)
        
        except Exception as e:
            logger.error(f"Error scrolling through results: {e}")
    
    def _extract_job_info(self, driver, job_listing) -> Dict[str, Any]:
        """
        Extract job information from a job listing.
        
        Args:
            driver: Selenium WebDriver
            job_listing: Job listing element
            
        Returns:
            Job dictionary
        """
        job = {}
        
        try:
            # Extract job title
            try:
                job_title_element = job_listing.find_element(By.CSS_SELECTOR, "h2.job_title")
                job['title'] = job_title_element.text.strip()
            except NoSuchElementException:
                job['title'] = "Unknown Title"
            
            # Extract company name
            try:
                company_name_element = job_listing.find_element(By.CSS_SELECTOR, "a.company_name")
                job['company_name'] = company_name_element.text.strip()
            except NoSuchElementException:
                job['company_name'] = "Unknown Company"
            
            # Extract location
            try:
                location_element = job_listing.find_element(By.CSS_SELECTOR, "a.location")
                job['location'] = location_element.text.strip()
            except NoSuchElementException:
                job['location'] = "Unknown Location"
            
            # Extract job URL
            try:
                job_link = job_listing.find_element(By.CSS_SELECTOR, "a.job_link")
                job['url'] = job_link.get_attribute("href")
            except NoSuchElementException:
                job['url'] = ""
            
            # Extract salary if available
            try:
                salary_element = job_listing.find_element(By.CSS_SELECTOR, "span.salary")
                job['salary'] = salary_element.text.strip()
            except NoSuchElementException:
                job['salary'] = ""
            
            # Extract job posting date
            try:
                date_element = job_listing.find_element(By.CSS_SELECTOR, "span.date")
                job['date_posted'] = date_element.text.strip()
            except NoSuchElementException:
                job['date_posted'] = ""
            
            # Click on job listing to view details
            HumanBehavior.human_like_click(driver, job_listing)
            
            # Wait for job details to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_description"))
            )
            
            # Extract job description
            try:
                description_element = driver.find_element(By.CSS_SELECTOR, "div.job_description")
                job['description'] = description_element.text.strip()
            except NoSuchElementException:
                job['description'] = ""
            
            # Check if job has Easy Apply
            try:
                apply_button = driver.find_element(By.CSS_SELECTOR, "button.apply_now")
                job['easy_apply'] = "Apply Now" in apply_button.text
            except NoSuchElementException:
                job['easy_apply'] = False
            
            # Set default H1B sponsorship to False (will be checked later)
            job['sponsors_h1b'] = False
            
            logger.info(f"Extracted job info: {job['title']} at {job['company_name']}")
            
        except Exception as e:
            logger.error(f"Error extracting job info: {e}")
            
            # Set default values for required fields
            if 'title' not in job:
                job['title'] = "Unknown Title"
            if 'company_name' not in job:
                job['company_name'] = "Unknown Company"
            if 'location' not in job:
                job['location'] = "Unknown Location"
            if 'url' not in job:
                job['url'] = ""
            if 'description' not in job:
                job['description'] = ""
            if 'easy_apply' not in job:
                job['easy_apply'] = False
            if 'sponsors_h1b' not in job:
                job['sponsors_h1b'] = False
        
        return job

