import logging
import time
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os

logger = logging.getLogger(__name__)

class JobApplier:
    """
    Applies to jobs on various job boards.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the job applier.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.browser_config = config.get('BROWSER', {})
        self.user_info = config.get('USER_INFO', {})
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
    
    def apply(self, job: Dict[str, Any], resume_path: str, cover_letter_path: Optional[str] = None) -> bool:
        """
        Apply to a job.
        
        Args:
            job: Job listing dictionary
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file (optional)
            
        Returns:
            True if application was successful, False otherwise
        """
        if not resume_path or not os.path.exists(resume_path):
            logger.error(f"Resume file not found: {resume_path}")
            return False
        
        if cover_letter_path and not os.path.exists(cover_letter_path):
            logger.warning(f"Cover letter file not found: {cover_letter_path}")
            cover_letter_path = None
        
        job_url = job.get('url', '')
        job_source = job.get('source', '')
        
        if not job_url:
            logger.error("Job URL is missing")
            return False
        
        logger.info(f"Applying to job: {job.get('title', '')} at {job.get('company_name', '')}")
        
        driver = self._setup_driver()
        success = False
        
        try:
            # Apply based on job source
            if job_source == 'LinkedIn':
                success = self._apply_linkedin(driver, job, resume_path, cover_letter_path)
            elif job_source == 'Indeed':
                success = self._apply_indeed(driver, job, resume_path, cover_letter_path)
            elif job_source == 'ZipRecruiter':
                success = self._apply_ziprecruiter(driver, job, resume_path, cover_letter_path)
            else:
                logger.error(f"Unsupported job source: {job_source}")
                return False
            
            if success:
                # Record successful application
                self._record_application(job)
                
                # Schedule follow-up if enabled
                follow_up_days = self.config.get('APPLICATION', {}).get('follow_up_days', 0)
                if follow_up_days > 0:
                    self._schedule_follow_up(job, follow_up_days)
        
        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            success = False
        
        finally:
            driver.quit()
        
        return success
    
    def _apply_linkedin(self, driver, job: Dict[str, Any], resume_path: str, cover_letter_path: Optional[str]) -> bool:
        """
        Apply to a job on LinkedIn.
        
        Args:
            driver: Selenium WebDriver
            job: Job listing dictionary
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file
            
        Returns:
            True if application was successful, False otherwise
        """
        try:
            job_url = job.get('url', '')
            driver.get(job_url)
            
            # Wait for the apply button to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobs-apply-button"))
            )
            
            # Click the apply button
            apply_button = driver.find_element(By.CLASS_NAME, "jobs-apply-button")
            apply_button.click()
            
            # Wait for the application form to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobs-easy-apply-content"))
            )
            
            # Fill in the application form
            # Note: This is a simplified implementation. In reality, you'd need to handle
            # different form layouts and fields dynamically.
            
            # Upload resume
            resume_upload = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            resume_upload.send_keys(os.path.abspath(resume_path))
            
            # Upload cover letter if available
            if cover_letter_path:
                try:
                    cover_letter_upload = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")[1]
                    cover_letter_upload.send_keys(os.path.abspath(cover_letter_path))
                except:
                    logger.warning("Could not upload cover letter")
            
            # Click the submit button
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']")
            submit_button.click()
            
            # Wait for confirmation
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "artdeco-inline-feedback--success"))
            )
            
            logger.info("Successfully applied on LinkedIn")
            return True
        
        except Exception as e:
            logger.error(f"Error applying on LinkedIn: {e}")
            return False
    
    def _apply_indeed(self, driver, job: Dict[str, Any], resume_path: str, cover_letter_path: Optional[str]) -> bool:
        """
        Apply to a job on Indeed.
        
        Args:
            driver: Selenium WebDriver
            job: Job listing dictionary
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file
            
        Returns:
            True if application was successful, False otherwise
        """
        try:
            job_url = job.get('url', '')
            driver.get(job_url)
            
            # Wait for the apply button to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[id='indeedApplyButton']"))
            )
            
            # Click the apply button
            apply_button = driver.find_element(By.CSS_SELECTOR, "button[id='indeedApplyButton']")
            apply_button.click()
            
            # Wait for the application form to load in the iframe
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "indeed-apply-iframe"))
            )
            
            # Switch to the application iframe
            iframe = driver.find_element(By.ID, "indeed-apply-iframe")
            driver.switch_to.frame(iframe)
            
            # Fill in the application form
            # Note: This is a simplified implementation. In reality, you'd need to handle
            # different form layouts and fields dynamically.
            
            # Upload resume
            resume_upload = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            resume_upload.send_keys(os.path.abspath(resume_path))
            
            # Fill in contact information
            name_field = driver.find_element(By.ID, "input-applicant.name")
            name_field.send_keys(self.user_info.get('name', ''))
            
            email_field = driver.find_element(By.ID, "input-applicant.email")
            email_field.send_keys(self.user_info.get('email', ''))
            
            phone_field = driver.find_element(By.ID, "input-applicant.phone")
            phone_field.send_keys(self.user_info.get('phone', ''))
            
            # Click the continue button
            continue_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='continue-button']")
            continue_button.click()
            
            # Handle additional steps if needed
            # ...
            
            # Click the submit button
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='submit-button']")
            submit_button.click()
            
            # Wait for confirmation
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='success-message']"))
            )
            
            logger.info("Successfully applied on Indeed")
            return True
        
        except Exception as e:
            logger.error(f"Error applying on Indeed: {e}")
            return False
    
    def _apply_ziprecruiter(self, driver, job: Dict[str, Any], resume_path: str, cover_letter_path: Optional[str]) -> bool:
        """
        Apply to a job on ZipRecruiter.
        
        Args:
            driver: Selenium WebDriver
            job: Job listing dictionary
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file
            
        Returns:
            True if application was successful, False otherwise
        """
        try:
            job_url = job.get('url', '')
            driver.get(job_url)
            
            # Wait for the apply button to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.job_apply"))
            )
            
            # Click the apply button
            apply_button = driver.find_element(By.CSS_SELECTOR, "button.job_apply")
            apply_button.click()
            
            # Wait for the application form to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "resume_upload"))
            )
            
            # Upload resume
            resume_upload = driver.find_element(By.ID, "resume_upload")
            resume_upload.send_keys(os.path.abspath(resume_path))
            
            # Fill in contact information
            name_field = driver.find_element(By.ID, "applicant_name")
            name_field.send_keys(self.user_info.get('name', ''))
            
            email_field = driver.find_element(By.ID, "applicant_email")
            email_field.send_keys(self.user_info.get('email', ''))
            
            phone_field = driver.find_element(By.ID, "applicant_phone")
            phone_field.send_keys(self.user_info.get('phone', ''))
            
            # Upload cover letter if available
            if cover_letter_path:
                try:
                    cover_letter_upload = driver.find_element(By.ID, "cover_letter_upload")
                    cover_letter_upload.send_keys(os.path.abspath(cover_letter_path))
                except:
                    logger.warning("Could not upload cover letter")
            
            # Click the submit button
            submit_button = driver.find_element(By.ID, "submit_app")
            submit_button.click()
            
            # Wait for confirmation
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "application_success"))
            )
            
            logger.info("Successfully applied on ZipRecruiter")
            return True
        
        except Exception as e:
            logger.error(f"Error applying on ZipRecruiter: {e}")
            return False
    
    def _record_application(self, job: Dict[str, Any]):
        """
        Record a successful application.
        
        Args:
            job: Job listing dictionary
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = "data_folder/applications"
            os.makedirs(output_dir, exist_ok=True)
            
            # Record application details
            with open(os.path.join(output_dir, "applications.csv"), "a", encoding="utf-8") as f:
                # Write header if file is empty
                if os.path.getsize(os.path.join(output_dir, "applications.csv")) == 0:
                    f.write("Date,Company,Title,Location,URL,Source,H1B_Sponsor\n")
                
                # Write application details
                f.write(f"{time.strftime('%Y-%m-%d')},{job.get('company_name', '')},{job.get('title', '')},{job.get('location', '')},{job.get('url', '')},{job.get('source', '')},{job.get('sponsors_h1b', False)}\n")
        
        except Exception as e:
            logger.error(f"Error recording application: {e}")
    
    def _schedule_follow_up(self, job: Dict[str, Any], days: int):
        """
        Schedule a follow-up for a job application.
        
        Args:
            job: Job listing dictionary
            days: Number of days to wait before following up
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = "data_folder/follow_ups"
            os.makedirs(output_dir, exist_ok=True)
            
            # Calculate follow-up date
            follow_up_date = time.strftime('%Y-%m-%d', time.localtime(time.time() + days * 86400))
            
            # Record follow-up details
            with open(os.path.join(output_dir, "follow_ups.csv"), "a", encoding="utf-8") as f:
                # Write header if file is empty
                if os.path.getsize(os.path.join(output_dir, "follow_ups.csv")) == 0:
                    f.write("FollowUpDate,Company,Title,ContactEmail,URL,Applied\n")
                
                # Write follow-up details
                f.write(f"{follow_up_date},{job.get('company_name', '')},{job.get('title', '')},{job.get('contact_email', '')},{job.get('url', '')},{time.strftime('%Y-%m-%d')}\n")
        
        except Exception as e:
            logger.error(f"Error scheduling follow-up: {e}")
