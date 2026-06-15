import logging
import time
import random
import re
from typing import Dict, List, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from src.utils.human_behavior import HumanBehavior

logger = logging.getLogger(__name__)

class LinkedInScraper:
    """
    Scrapes job listings from LinkedIn.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LinkedIn scraper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.browser_config = config.get('BROWSER', {})
        self.job_search = config.get('JOB_SEARCH', {})
        self.timeout = self.browser_config.get('timeout', 30)
        self.user_agent = self.browser_config.get('user_agent', '')
        self.headless = self.browser_config.get('headless', False)
        
        # LinkedIn credentials
        self.linkedin_username = config.get('LINKEDIN', {}).get('username', '')
        self.linkedin_password = config.get('LINKEDIN', {}).get('password', '')
        
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
        
        # Add preferences to handle downloads and file uploads
        prefs = {
            "download.default_directory": "data_folder",
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            # Disable saving passwords
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        options.add_experimental_option("prefs", prefs)
        
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
        Scrape job listings from LinkedIn.
        
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        # Check if LinkedIn credentials are provided
        if not self.linkedin_username or not self.linkedin_password:
            logger.error("LinkedIn credentials not provided")
            return jobs
        
        driver = self._setup_driver()
        
        try:
            # Log in to LinkedIn
            self._login(driver)
            
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
            
            logger.info(f"Scraped {len(jobs)} jobs from LinkedIn")
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn jobs: {e}")
        
        finally:
            driver.quit()
        
        return jobs
    
    def _login(self, driver):
        """
        Log in to LinkedIn.
        
        Args:
            driver: Selenium WebDriver
        """
        try:
            # Navigate to LinkedIn login page
            driver.get("https://www.linkedin.com/login")
            logger.info("Navigated to LinkedIn login page")
            
            # Wait for the login form to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Enter credentials with human-like typing
            username_field = driver.find_element(By.ID, "username")
            password_field = driver.find_element(By.ID, "password")
            
            # Type username with human-like behavior
            HumanBehavior.human_like_typing(username_field, self.linkedin_username)
            
            # Pause briefly like a human would after entering username
            HumanBehavior.random_delay(0.8, 1.5)
            
            # Type password with human-like behavior
            HumanBehavior.human_like_typing(password_field, self.linkedin_password)
            
            # Random delay before clicking submit to simulate human thinking
            HumanBehavior.random_delay(0.5, 1.5)
            
            # Find and click the sign-in button with human-like movement
            sign_in_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            HumanBehavior.human_like_click(driver, sign_in_button)
            
            # Wait for login to complete
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            
            logger.info("Successfully logged in to LinkedIn")
            
            # Check for CAPTCHA or security verification
            if "checkpoint" in driver.current_url or "security-verification" in driver.current_url:
                logger.warning("LinkedIn security verification detected. Please complete it manually.")
                print("\n⚠️ LinkedIn security verification detected!")
                print("Please complete the verification in the browser window.")
                print("The application will continue once verification is complete.")
                
                # Wait for manual verification (up to 2 minutes)
                for _ in range(24):  # 24 * 5 seconds = 2 minutes
                    if "checkpoint" not in driver.current_url and "security-verification" not in driver.current_url:
                        break
                    time.sleep(5)
                
                if "checkpoint" in driver.current_url or "security-verification" in driver.current_url:
                    logger.error("LinkedIn security verification timed out")
                    raise Exception("LinkedIn security verification timed out")
                
                logger.info("LinkedIn security verification completed")
            
            # Wait a moment for the page to fully load
            HumanBehavior.random_delay(1.0, 2.0)
            
        except Exception as e:
            logger.error(f"Error logging in to LinkedIn: {e}")
            raise
    
    def _search_jobs(self, driver, job_title: str, location: str) -> List[Dict[str, Any]]:
        """
        Search for jobs on LinkedIn.
        
        Args:
            driver: Selenium WebDriver
            job_title: Job title to search for
            location: Location to search in
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        try:
            # Navigate to LinkedIn Jobs page
            driver.get("https://www.linkedin.com/jobs/")
            logger.info("Navigated to LinkedIn Jobs page")
            
            # Wait for the search form to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Search by title, skill, or company']"))
            )
            
            # Enter job title with human-like typing
            job_title_field = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Search by title, skill, or company']")
            HumanBehavior.human_like_typing(job_title_field, job_title)
            
            # Pause briefly like a human would after entering job title
            HumanBehavior.random_delay(0.8, 1.5)
            
            # Enter location with human-like typing
            location_field = driver.find_element(By.CSS_SELECTOR, "input[aria-label='City, state, or zip code']")
            location_field.clear()
            HumanBehavior.human_like_typing(location_field, location)
            
            # Random delay before clicking search to simulate human thinking
            HumanBehavior.random_delay(0.5, 1.5)
            
            # Find and click the search button with human-like movement
            search_button = driver.find_element(By.CSS_SELECTOR, "button[data-tracking-control-name='public_jobs_jobs-search-bar_base-search-button']")
            HumanBehavior.human_like_click(driver, search_button)
            
            # Wait for search results to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list"))
            )
            
            # Apply all the specified filters
            self._apply_advanced_filters(driver)
            
            # Wait for filtered results to load
            HumanBehavior.random_delay(2.0, 4.0)
            
            # Scroll through results to load more jobs
            self._scroll_through_results(driver)
            
            # Extract job listings
            job_listings = driver.find_elements(By.CSS_SELECTOR, "li.jobs-search-results__list-item")
            logger.info(f"Found {len(job_listings)} job listings")
            
            # Process each job listing
            for job_listing in job_listings:
                try:
                    # Extract job information
                    job = self._extract_job_info(driver, job_listing)
                    
                    # Add source information
                    job['source'] = 'LinkedIn'
                    
                    # Add job to the list
                    jobs.append(job)
                    
                except Exception as e:
                    logger.error(f"Error extracting job info: {e}")
                    continue
            
            logger.info(f"Extracted {len(jobs)} jobs from search results")
            
        except Exception as e:
            logger.error(f"Error searching for jobs: {e}")
        
        return jobs
    
    def _apply_advanced_filters(self, driver):
        """
        Apply advanced filters to the job search.
        
        Args:
            driver: Selenium WebDriver
        """
        try:
            logger.info("Applying advanced filters to job search")
            
            # 1. Sort by Most Recent
            try:
                # Click on the sort dropdown
                sort_button = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-dropdown__trigger--placement-bottom"))
                )
                HumanBehavior.human_like_click(driver, sort_button)
                
                # Wait for dropdown to appear
                HumanBehavior.random_delay(0.5, 1.0)
                
                # Click on "Most recent" option
                most_recent_option = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Most recent']"))
                )
                HumanBehavior.human_like_click(driver, most_recent_option)
                
                logger.info("Set sort to Most Recent")
                HumanBehavior.random_delay(1.0, 2.0)
            except Exception as e:
                logger.warning(f"Could not set sort to Most Recent: {e}")
            
            # 2. Click on "All filters" button to access more filters
            try:
                all_filters_button = WebDriverWait(driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'All filters')]"))
                )
                HumanBehavior.human_like_click(driver, all_filters_button)
                
                # Wait for filter modal to appear
                WebDriverWait(driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-search-box__advanced-filters"))
                )
                
                logger.info("Opened All Filters modal")
                HumanBehavior.random_delay(1.0, 2.0)
            except Exception as e:
                logger.warning(f"Could not open All Filters modal: {e}")
                # Try to find individual filter buttons instead
                self._apply_individual_filters(driver)
                return
            
            # 3. Set Date Posted to "Past Week"
            try:
                date_posted_section = driver.find_element(By.XPATH, "//h3[text()='Date posted']/ancestor::section")
                past_week_option = date_posted_section.find_element(By.XPATH, ".//label[contains(text(), 'Past week')]")
                HumanBehavior.human_like_click(driver, past_week_option)
                
                logger.info("Set Date Posted to Past Week")
                HumanBehavior.random_delay(0.5, 1.0)
            except Exception as e:
                logger.warning(f"Could not set Date Posted filter: {e}")
            
            # 4. Set Experience Level to "Entry Level, Associate, Internship"
            try:
                experience_section = driver.find_element(By.XPATH, "//h3[text()='Experience level']/ancestor::section")
                
                # Select Entry Level
                entry_level_option = experience_section.find_element(By.XPATH, ".//label[contains(text(), 'Entry level')]")
                HumanBehavior.human_like_click(driver, entry_level_option)
                
                # Select Associate
                associate_option = experience_section.find_element(By.XPATH, ".//label[contains(text(), 'Associate')]")
                HumanBehavior.human_like_click(driver, associate_option)
                
                # Select Internship
                internship_option = experience_section.find_element(By.XPATH, ".//label[contains(text(), 'Internship')]")
                HumanBehavior.human_like_click(driver, internship_option)
                
                logger.info("Set Experience Level filters")
                HumanBehavior.random_delay(0.5, 1.0)
            except Exception as e:
                logger.warning(f"Could not set Experience Level filters: {e}")
            
            # 5. Set Job Type to "Internship, Full Time"
            try:
                job_type_section = driver.find_element(By.XPATH, "//h3[text()='Job type']/ancestor::section")
                
                # Select Internship
                internship_option = job_type_section.find_element(By.XPATH, ".//label[contains(text(), 'Internship')]")
                HumanBehavior.human_like_click(driver, internship_option)
                
                # Select Full-time
                full_time_option = job_type_section.find_element(By.XPATH, ".//label[contains(text(), 'Full-time')]")
                HumanBehavior.human_like_click(driver, full_time_option)
                
                logger.info("Set Job Type filters")
                HumanBehavior.random_delay(0.5, 1.0)
            except Exception as e:
                logger.warning(f"Could not set Job Type filters: {e}")
            
            # 6. Set Remote options to "On-site, Remote, Hybrid"
            try:
                remote_section = driver.find_element(By.XPATH, "//h3[text()='On-site/remote']/ancestor::section")
                
                # Select On-site
                onsite_option = remote_section.find_element(By.XPATH, ".//label[contains(text(), 'On-site')]")
                HumanBehavior.human_like_click(driver, onsite_option)
                
                # Select Remote
                remote_option = remote_section.find_element(By.XPATH, ".//label[contains(text(), 'Remote')]")
                HumanBehavior.human_like_click(driver, remote_option)
                
                # Select Hybrid
                hybrid_option = remote_section.find_element(By.XPATH, ".//label[contains(text(), 'Hybrid')]")
                HumanBehavior.human_like_click(driver, hybrid_option)
                
                logger.info("Set Remote options filters")
                HumanBehavior.random_delay(0.5, 1.0)
            except Exception as e:
                logger.warning(f"Could not set Remote options filters: {e}")
            
            # 7. Set Easy Apply filter
            try:
                easy_apply_section = driver.find_element(By.XPATH, "//h3[text()='Easy Apply']/ancestor::section")
                easy_apply_option = easy_apply_section.find_element(By.XPATH, ".//label[contains(text(), 'Easy Apply')]")
                HumanBehavior.human_like_click(driver, easy_apply_option)
                
                logger.info("Set Easy Apply filter")
                HumanBehavior.random_delay(0.5, 1.0)
            except Exception as e:
                logger.warning(f"Could not set Easy Apply filter: {e}")
            
            # 8. Set Salary to $60,000+
            try:
                salary_section = driver.find_element(By.XPATH, "//h3[text()='Salary']/ancestor::section")
                
                # Find the salary input field
                salary_input = salary_section.find_element(By.CSS_SELECTOR, "input[aria-label='Minimum salary']")
                HumanBehavior.human_like_typing(salary_input, "60000")
                
                logger.info("Set Salary filter to $60,000+")
                HumanBehavior.random_delay(0.5, 1.0)
            except Exception as e:
                logger.warning(f"Could not set Salary filter: {e}")
            
            # 9. Set Has Verifications filter if available
            try:
                verifications_section = driver.find_element(By.XPATH, "//h3[text()='LinkedIn features']/ancestor::section")
                verifications_option = verifications_section.find_element(By.XPATH, ".//label[contains(text(), 'Has verifications')]")
                HumanBehavior.human_like_click(driver, verifications_option)
                
                logger.info("Set Has Verifications filter")
                HumanBehavior.random_delay(0.5, 1.0)
            except Exception as e:
                logger.warning(f"Could not set Has Verifications filter: {e}")
            
            # 10. Apply filters by clicking the Show Results button
            try:
                show_results_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Show results')]")
                HumanBehavior.human_like_click(driver, show_results_button)
                
                logger.info("Applied all filters")
                
                # Wait for filtered results to load
                WebDriverWait(driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list"))
                )
                
                HumanBehavior.random_delay(2.0, 4.0)
            except Exception as e:
                logger.warning(f"Could not apply filters: {e}")
        
        except Exception as e:
            logger.error(f"Error applying advanced filters: {e}")
    
    def _apply_individual_filters(self, driver):
        """
        Apply filters individually if the All Filters modal is not available.
        
        Args:
            driver: Selenium WebDriver
        """
        try:
            # Try to apply filters using individual filter buttons
            
            # 1. Easy Apply filter
            try:
                easy_apply_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Easy Apply')]")
                HumanBehavior.human_like_click(driver, easy_apply_button)
                logger.info("Applied Easy Apply filter")
                HumanBehavior.random_delay(1.0, 2.0)
            except Exception as e:
                logger.warning(f"Could not apply Easy Apply filter individually: {e}")
            
            # 2. Date Posted filter
            try:
                date_posted_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Date posted')]")
                HumanBehavior.human_like_click(driver, date_posted_button)
                
                # Wait for dropdown to appear
                HumanBehavior.random_delay(0.5, 1.0)
                
                # Select Past Week
                past_week_option = driver.find_element(By.XPATH, "//span[contains(text(), 'Past week')]")
                HumanBehavior.human_like_click(driver, past_week_option)
                
                logger.info("Applied Date Posted filter")
                HumanBehavior.random_delay(1.0, 2.0)
            except Exception as e:
                logger.warning(f"Could not apply Date Posted filter individually: {e}")
            
            # 3. Experience Level filter
            try:
                experience_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Experience level')]")
                HumanBehavior.human_like_click(driver, experience_button)
                
                # Wait for dropdown to appear
                HumanBehavior.random_delay(0.5, 1.0)
                
                # Select Entry level
                entry_level_option = driver.find_element(By.XPATH, "//span[contains(text(), 'Entry level')]")
                HumanBehavior.human_like_click(driver, entry_level_option)
                
                # Select Associate
                associate_option = driver.find_element(By.XPATH, "//span[contains(text(), 'Associate')]")
                HumanBehavior.human_like_click(driver, associate_option)
                
                # Select Internship
                internship_option = driver.find_element(By.XPATH, "//span[contains(text(), 'Internship')]")
                HumanBehavior.human_like_click(driver, internship_option)
                
                # Apply selections
                apply_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Show results')]")
                HumanBehavior.human_like_click(driver, apply_button)
                
                logger.info("Applied Experience Level filter")
                HumanBehavior.random_delay(1.0, 2.0)
            except Exception as e:
                logger.warning(f"Could not apply Experience Level filter individually: {e}")
            
            # Wait for filtered results to load
            HumanBehavior.random_delay(2.0, 4.0)
            
        except Exception as e:
            logger.error(f"Error applying individual filters: {e}")
    
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
            # Click on the job listing to view details
            HumanBehavior.human_like_click(driver, job_listing)
            
            # Wait for job details to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-details"))
            )
            
            # Extract job title
            try:
                job_title_element = driver.find_element(By.CSS_SELECTOR, "h2.jobs-details-top-card__job-title")
                job['title'] = job_title_element.text.strip()
            except NoSuchElementException:
                job['title'] = "Unknown Title"
            
            # Extract company name
            try:
                company_name_element = driver.find_element(By.CSS_SELECTOR, "a.jobs-details-top-card__company-url")
                job['company_name'] = company_name_element.text.strip()
            except NoSuchElementException:
                try:
                    company_name_element = driver.find_element(By.CSS_SELECTOR, "span.jobs-details-top-card__company-name")
                    job['company_name'] = company_name_element.text.strip()
                except NoSuchElementException:
                    job['company_name'] = "Unknown Company"
            
            # Extract location
            try:
                location_element = driver.find_element(By.CSS_SELECTOR, "span.jobs-details-top-card__bullet")
                job['location'] = location_element.text.strip()
            except NoSuchElementException:
                job['location'] = "Unknown Location"
            
            # Extract job URL
            job['url'] = driver.current_url
            
            # Extract job description
            try:
                description_element = driver.find_element(By.CSS_SELECTOR, "div.jobs-description-content__text")
                job['description'] = description_element.text.strip()
            except NoSuchElementException:
                job['description'] = ""
            
            # Check if job has Easy Apply
            try:
                easy_apply_button = driver.find_element(By.CSS_SELECTOR, "button[data-control-name='jobdetails_topcard_inapply']")
                job['easy_apply'] = True
            except NoSuchElementException:
                job['easy_apply'] = False
            
            # Extract salary information if available
            try:
                salary_element = driver.find_element(By.CSS_SELECTOR, "span.jobs-details-top-card__salary-info")
                job['salary'] = salary_element.text.strip()
            except NoSuchElementException:
                job['salary'] = ""
            
            # Extract job posting date
            try:
                date_element = driver.find_element(By.CSS_SELECTOR, "span.jobs-details-top-card__posted-date")
                job['date_posted'] = date_element.text.strip()
            except NoSuchElementException:
                job['date_posted'] = ""
            
            # Extract number of applicants if available
            try:
                applicants_element = driver.find_element(By.CSS_SELECTOR, "span.jobs-details-top-card__applicant-count")
                job['applicants'] = applicants_element.text.strip()
            except NoSuchElementException:
                job['applicants'] = ""
            
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

