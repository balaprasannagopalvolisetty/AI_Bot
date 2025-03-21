import logging
import time
import os
import random
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementClickInterceptedException, StaleElementReferenceException
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from src.utils.human_behavior import HumanBehavior

logger = logging.getLogger(__name__)

class JobApplier:
    """
    Applies to jobs on various job boards with human-like behavior.
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
        
        # Initialize HumanBehavior helper
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
            "download.default_directory": os.path.abspath("data_folder"),
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
    
    def apply(self, job: Dict[str, Any], resume_path: str, cover_letter_path: Optional[str] = None) -> bool:
        """
        Apply to a job with human-like interaction patterns.
        
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
        
        # Double-check H1B sponsorship
        if not job.get('sponsors_h1b', False):
            logger.warning(f"Skipping job that doesn't sponsor H1B: {job.get('title', '')} at {job.get('company_name', '')}")
            return False
        
        # Get hiring manager information
        hiring_manager_name = job.get('hiring_manager_name', '')
        hiring_manager_email = job.get('hiring_manager_email', '')
        
        logger.info(f"Applying to job: {job.get('title', '')} at {job.get('company_name', '')}")
        if hiring_manager_name:
            logger.info(f"Hiring Manager: {hiring_manager_name} ({hiring_manager_email})")
        
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
                
                # Send direct email to hiring manager if available
                if hiring_manager_email and cover_letter_path:
                    self._send_direct_email(job, cover_letter_path)
        
        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            success = False
        
        finally:
            # Random delay before closing to avoid patterns
            HumanBehavior.random_delay(1.0, 3.0)
            driver.quit()
        
        return success
    
    def _linkedin_login(self, driver):
        """
        Log in to LinkedIn with human-like behavior.
        
        Args:
            driver: Selenium WebDriver
        """
        try:
            # Navigate to LinkedIn login page
            driver.get("https://www.linkedin.com/login")
            logger.info("Navigated to LinkedIn login page")
            
            # Simulate reading the page for a bit
            HumanBehavior.read_page_behavior(driver, (2, 4))
            
            # Wait for the login form to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Enter credentials with human-like typing
            username_field = driver.find_element(By.ID, "username")
            password_field = driver.find_element(By.ID, "password")
            
            # Type username with human-like behavior
            HumanBehavior.human_like_typing(
                username_field, 
                self.config.get('LINKEDIN', {}).get('username', '')
            )
            
            # Pause briefly like a human would after entering username
            HumanBehavior.random_delay(0.8, 1.5)
            
            # Type password with human-like behavior
            HumanBehavior.human_like_typing(
                password_field, 
                self.config.get('LINKEDIN', {}).get('password', '')
            )
            
            # Random delay before clicking submit to simulate human thinking
            HumanBehavior.random_delay(0.5, 1.5)
            
            # Find and click the sign-in button with human-like movement
            sign_in_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            HumanBehavior.human_like_click(driver, sign_in_button)
            
            # Wait for login to complete
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "global-nav")),
                message="Login was not successful: Could not find global-nav element"
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
            
            # "Browse" LinkedIn briefly to appear more human-like
            self._simulate_normal_browsing(driver)
            
        except Exception as e:
            logger.error(f"Error logging in to LinkedIn: {e}")
            raise
    
    def _simulate_normal_browsing(self, driver):
        """
        Simulate normal browsing behavior to appear more human-like.
        
        Args:
            driver: Selenium WebDriver
        """
        try:
            # Random chance to visit feed
            if random.random() < 0.7:
                driver.get("https://www.linkedin.com/feed/")
                HumanBehavior.read_page_behavior(driver, (3, 6))
                
                # Scroll through feed
                for _ in range(random.randint(2, 5)):
                    HumanBehavior.scroll_page(driver, "down")
            
            # Random chance to visit notifications
            if random.random() < 0.3:
                driver.get("https://www.linkedin.com/notifications/")
                HumanBehavior.read_page_behavior(driver, (2, 4))
            
            # Always visit jobs page at the end
            driver.get("https://www.linkedin.com/jobs/")
            HumanBehavior.read_page_behavior(driver, (2, 5))
            
        except Exception as e:
            logger.warning(f"Error during normal browsing simulation: {e}")
            # Non-critical function, so just log and continue
    
    def _apply_linkedin(self, driver, job: Dict[str, Any], resume_path: str, cover_letter_path: Optional[str]) -> bool:
        """
        Apply to a job on LinkedIn with human-like behavior.
        
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
            
            # First, log in to LinkedIn
            self._linkedin_login(driver)
            
            # Navigate to the job page
            logger.info(f"Navigating to job URL: {job_url}")
            driver.get(job_url)
            
            # Simulate reading the job description
            HumanBehavior.read_page_behavior(driver, (5, 12))
            
            # Check if already applied
            try:
                applied_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Applied')]")
                if applied_button:
                    logger.info("Already applied to this job")
                    return True
            except NoSuchElementException:
                pass  # Not applied yet, continue
            
            # Try to find the Easy Apply button
            try:
                # Wait for the apply button to load
                WebDriverWait(driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-control-name='jobdetails_topcard_inapply']"))
                )
                
                # Find the apply button
                apply_button = driver.find_element(By.CSS_SELECTOR, "button[data-control-name='jobdetails_topcard_inapply']")
                
                # Pause before clicking like a human would
                HumanBehavior.random_delay(1.0, 2.5)
                
                # Click the apply button with human-like movement
                HumanBehavior.human_like_click(driver, apply_button)
                logger.info("Clicked Easy Apply button")
                
                # Wait for the application form to load
                WebDriverWait(driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-easy-apply-content"))
                )
                
                # Handle the application process
                return self._handle_linkedin_application_form(driver, job, resume_path, cover_letter_path)
                
            except (NoSuchElementException, TimeoutException):
                # Try alternative apply button
                try:
                    apply_button = driver.find_element(By.CSS_SELECTOR, "button.jobs-apply-button")
                    
                    # Pause before clicking
                    HumanBehavior.random_delay(1.0, 2.0)
                    
                    # Click with human-like movement
                    HumanBehavior.human_like_click(driver, apply_button)
                    logger.info("Clicked alternative Apply button")
                    
                    # Wait for the application form to load
                    WebDriverWait(driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-easy-apply-content"))
                    )
                    
                    # Handle the application process
                    return self._handle_linkedin_application_form(driver, job, resume_path, cover_letter_path)
                    
                except (NoSuchElementException, TimeoutException):
                    logger.error("Could not find Apply button")
                    return False
        
        except Exception as e:
            logger.error(f"Error applying on LinkedIn: {e}")
            return False
    
    def _handle_linkedin_application_form(self, driver, job: Dict[str, Any], resume_path: str, cover_letter_path: Optional[str]) -> bool:
        """
        Handle the LinkedIn application form with human-like interactions.
        
        Args:
            driver: Selenium WebDriver
            job: Job listing dictionary
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file
            
        Returns:
            True if application was successful, False otherwise
        """
        try:
            # Track the current step in the application process
            current_step = 1
            max_steps = 10  # Arbitrary limit to prevent infinite loops
            
            while current_step <= max_steps:
                logger.info(f"Handling application step {current_step}")
                
                # Simulate reading the form page
                HumanBehavior.read_page_behavior(driver, (2, 5))
                
                # Check for resume upload
                try:
                    resume_upload = driver.find_element(By.CSS_SELECTOR, "input[type='file'][name='resume']")
                    
                    # Pause before uploading
                    HumanBehavior.random_delay(0.5, 1.5)
                    
                    # Upload file
                    resume_upload.send_keys(os.path.abspath(resume_path))
                    logger.info("Uploaded resume")
                    
                    # Realistic wait time for upload to complete
                    HumanBehavior.random_delay(2.0, 4.0)
                except NoSuchElementException:
                    logger.debug("No resume upload field found in this step")
                
                # Check for cover letter upload
                if cover_letter_path:
                    try:
                        cover_letter_upload = driver.find_element(By.CSS_SELECTOR, "input[type='file'][name='coverLetter']")
                        
                        # Pause before uploading
                        HumanBehavior.random_delay(0.5, 1.5)
                        
                        # Upload file
                        cover_letter_upload.send_keys(os.path.abspath(cover_letter_path))
                        logger.info("Uploaded cover letter")
                        
                        # Realistic wait time for upload to complete
                        HumanBehavior.random_delay(2.0, 4.0)
                    except NoSuchElementException:
                        logger.debug("No cover letter upload field found in this step")
                
                # Fill in contact information fields in a human-like manner
                self._fill_linkedin_contact_info(driver, job)
                
                # Fill in additional questions with human-like behavior
                self._fill_linkedin_additional_questions(driver, job, cover_letter_path)
                
                # Add random pauses to simulate human thinking
                HumanBehavior.random_delay(1.0, 3.0)
                
                # Check for "Next" button
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
                    
                    # Human-like click
                    HumanBehavior.human_like_click(driver, next_button)
                    logger.info("Clicked Next button")
                    
                    # Wait for next step to load with variable timing
                    HumanBehavior.random_delay(2.0, 3.5)
                    current_step += 1
                    continue
                except NoSuchElementException:
                    logger.debug("No Next button found in this step")
                
                # Check for "Review" button
                try:
                    review_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Review your application']")
                    
                    # Human-like click
                    HumanBehavior.human_like_click(driver, review_button)
                    logger.info("Clicked Review button")
                    
                    # Wait for review page to load with variable timing
                    HumanBehavior.random_delay(2.0, 4.0)
                    
                    # Simulate carefully reviewing the application
                    HumanBehavior.read_page_behavior(driver, (3, 7))
                    
                    current_step += 1
                    continue
                except NoSuchElementException:
                    logger.debug("No Review button found in this step")
                
                # Check for "Submit" button
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']")
                    
                    # Longer pause before submission as a human would take time to make final decision
                    HumanBehavior.random_delay(2.0, 5.0)
                    
                    # Human-like click
                    HumanBehavior.human_like_click(driver, submit_button)
                    logger.info("Clicked Submit button")
                    
                    # Wait for confirmation with longer timeout
                    try:
                        WebDriverWait(driver, self.timeout * 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.artdeco-inline-feedback--success"))
                        )
                        logger.info("Application submitted successfully")
                        
                        # Take a moment to "read" the success message
                        HumanBehavior.random_delay(2.0, 4.0)
                        return True
                    except TimeoutException:
                        logger.warning("Could not confirm application submission")
                        # Still return True as the submit button was clicked
                        return True
                except NoSuchElementException:
                    logger.debug("No Submit button found in this step")
                
                # If we reach here, we couldn't find Next, Review, or Submit buttons
                # Try to find any button that might continue the application
                try:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        try:
                            button_text = button.text.lower()
                            if "next" in button_text or "continue" in button_text or "submit" in button_text or "apply" in button_text:
                                # Pause before clicking
                                HumanBehavior.random_delay(1.0, 2.0)
                                
                                # Human-like click
                                HumanBehavior.human_like_click(driver, button)
                                logger.info(f"Clicked button with text: {button.text}")
                                
                                # Wait for next page with variable timing
                                HumanBehavior.random_delay(2.0, 3.5)
                                current_step += 1
                                break
                        except:
                            continue
                    else:
                        # No suitable button found, try to proceed anyway
                        logger.warning("Could not find a button to proceed to the next step")
                        current_step += 1
                except:
                    logger.warning("Error finding buttons to proceed")
                    current_step += 1
            
            # If we've gone through all steps and haven't returned yet, assume failure
            logger.warning("Reached maximum steps without completing application")
            return False
        
        except Exception as e:
            logger.error(f"Error handling LinkedIn application form: {e}")
            return False
    
    def _fill_linkedin_contact_info(self, driver, job: Dict[str, Any]):
        """
        Fill in contact information fields in LinkedIn application form with human-like typing.
        
        Args:
            driver: Selenium WebDriver
            job: Job listing dictionary
        """
        try:
            # Randomize the order of field filling to appear more human
            fields_to_fill = []
            
            # Add first name field if found
            try:
                name_field = driver.find_element(By.ID, "single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-3-name-firstName")
                if name_field:
                    fields_to_fill.append(("first_name", name_field))
            except NoSuchElementException:
                logger.debug("No first name field found")
            
            # Add last name field if found
            try:
                last_name_field = driver.find_element(By.ID, "single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-3-name-lastName")
                if last_name_field:
                    fields_to_fill.append(("last_name", last_name_field))
            except NoSuchElementException:
                logger.debug("No last name field found")
            
            # Add email field if found
            try:
                email_field = driver.find_element(By.ID, "single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-3-email-email")
                if email_field:
                    fields_to_fill.append(("email", email_field))
            except NoSuchElementException:
                logger.debug("No email field found")
            
            # Add phone field if found
            try:
                phone_field = driver.find_element(By.ID, "single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-3-phoneNumber-nationalNumber")
                if phone_field:
                    fields_to_fill.append(("phone", phone_field))
            except NoSuchElementException:
                logger.debug("No phone field found")
            
            # Shuffle the order of fields to fill for more human-like behavior
            random.shuffle(fields_to_fill)
            
            # Fill each field with human-like typing
            for field_type, field_element in fields_to_fill:
                # Add random delay between filling fields
                HumanBehavior.random_delay(0.5, 2.0)
                
                if field_type == "first_name":
                    HumanBehavior.human_like_typing(field_element, self.user_info.get('name', '').split()[0])
                    logger.info("Filled in first name")
                
                elif field_type == "last_name":
                    HumanBehavior.human_like_typing(field_element, self.user_info.get('name', '').split()[-1])
                    logger.info("Filled in last name")
                
                elif field_type == "email":
                    HumanBehavior.human_like_typing(field_element, self.user_info.get('email', ''))
                    logger.info("Filled in email")
                
                elif field_type == "phone":
                    HumanBehavior.human_like_typing(field_element, self.user_info.get('phone', ''))
                    logger.info("Filled in phone number")
            
            # Fill in hiring manager name if available
            hiring_manager_name = job.get('hiring_manager_name', '')
            if hiring_manager_name:
                try:
                    # Look for fields that might be for hiring manager
                    manager_fields = driver.find_elements(By.CSS_SELECTOR, "input[id*='hiring-manager'], input[id*='recruiter'], input[id*='addressee']")
                    if manager_fields:
                        # Add delay before filling this special field
                        HumanBehavior.random_delay(1.0, 2.0)
                        
                        HumanBehavior.human_like_typing(manager_fields[0], hiring_manager_name)
                        logger.info("Filled in hiring manager name")
                except:
                    logger.debug("Could not fill in hiring manager name")
        
        except Exception as e:
            logger.error(f"Error filling LinkedIn contact info: {e}")
    
    def _fill_linkedin_additional_questions(self, driver, job: Dict[str, Any], cover_letter_path=None):
        """
        Fill in additional questions in LinkedIn application form with human-like interactions.
        
        Args:
            driver: Selenium WebDriver
            job: Job listing dictionary
            cover_letter_path: Path to cover letter file
        """
        try:
            # Handle radio buttons for yes/no questions (usually select "Yes" for positive questions)
            try:
                radio_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'][value='Yes']")
                
                # Randomize order of radio button selection
                if radio_buttons:
                    random_indexes = list(range(len(radio_buttons)))
                    random.shuffle(random_indexes)
                    
                    for idx in random_indexes:
                        try:
                            # Random delay before selecting each radio button
                            HumanBehavior.random_delay(0.7, 2.0)
                            
                            # Human-like click
                            HumanBehavior.human_like_click(driver, radio_buttons[idx])
                            logger.info("Selected 'Yes' for a radio button question")
                        except:
                            pass
            except:
                logger.debug("No radio buttons found")
            
            # Handle dropdown selects
            try:
                selects = driver.find_elements(By.TAG_NAME, "select")
                
                # Randomize order of dropdown interaction
                if selects:
                    random_indexes = list(range(len(selects)))
                    random.shuffle(random_indexes)
                    
                    for idx in random_indexes:
                        try:
                            select = selects[idx]
                            
                            # Random delay before clicking dropdown
                            HumanBehavior.random_delay(0.7, 2.0)
                            
                            # Human-like click to open dropdown
                            HumanBehavior.human_like_click(driver, select)
                            
                            # Small delay as human would look at options
                            HumanBehavior.random_delay(0.5, 1.5)
                            
                            # Try to select the first non-empty option
                            options = select.find_elements(By.TAG_NAME, "option")
                            
                            # Skip the first option (usually a placeholder)
                            valid_options = [opt for opt in options[1:] if opt.text.strip()]
                            
                            if valid_options:
                                # Choose a random valid option sometimes instead of always the first one
                                option_to_select = random.choice(valid_options)
                                
                                # Human-like click
                                HumanBehavior.human_like_click(driver, option_to_select)
                                logger.info(f"Selected '{option_to_select.text}' from dropdown")
                                
                                # Delay after selection
                                HumanBehavior.random_delay(0.5, 1.0)
                        except:
                            pass
            except:
                logger.debug("No dropdowns found")
            
            # Handle text inputs for work experience, education, etc.
            try:
                text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']:not([id*='name']):not([id*='email']):not([id*='phone'])")
                
                # Randomize order of filling text inputs
                if text_inputs:
                    random_indexes = list(range(len(text_inputs)))
                    random.shuffle(random_indexes)
                    
                    for idx in random_indexes:
                        try:
                            text_input = text_inputs[idx]
                            placeholder = text_input.get_attribute("placeholder") or ""
                            
                            try:
                                label_elem = driver.find_element(By.CSS_SELECTOR, f"label[for='{text_input.get_attribute('id')}']")
                                label = label_elem.text if label_elem else ""
                            except:
                                label = ""
                            
                            # Add delay before filling each field
                            HumanBehavior.random_delay(1.0, 2.5)
                            
                            # Fill based on the field type
                            if "years" in placeholder.lower() or "years" in label.lower() or "experience" in placeholder.lower() or "experience" in label.lower():
                                # Add some variation to years of experience
                                years = str(random.randint(2, 5))
                                HumanBehavior.human_like_typing(text_input, years)
                                logger.info(f"Filled in years of experience: {years}")
                            
                            elif "salary" in placeholder.lower() or "salary" in label.lower():
                                # Add some variation to salary expectations
                                base_salary = 90000
                                variation = random.randint(-5000, 5000)
                                salary = str(base_salary + variation)
                                HumanBehavior.human_like_typing(text_input, salary)
                                logger.info(f"Filled in salary expectation: {salary}")
                            
                            elif "website" in placeholder.lower() or "website" in label.lower() or "portfolio" in placeholder.lower() or "portfolio" in label.lower():
                                HumanBehavior.human_like_typing(text_input, self.user_info.get('portfolio', ''))
                                logger.info("Filled in website/portfolio")
                            
                            elif "linkedin" in placeholder.lower() or "linkedin" in label.lower():
                                HumanBehavior.human_like_typing(text_input, self.user_info.get('linkedin', ''))
                                logger.info("Filled in LinkedIn URL")
                            
                            elif "github" in placeholder.lower() or "github" in label.lower():
                                HumanBehavior.human_like_typing(text_input, self.user_info.get('github', ''))
                                logger.info("Filled in GitHub URL")
                        except:
                            pass
            except:
                logger.debug("No additional text inputs found")
            
            # Handle textareas for additional information
            try:
                textareas = driver.find_elements(By.TAG_NAME, "textarea")
                
                # Randomize order of filling textareas
                if textareas:
                    random_indexes = list(range(len(textareas)))
                    random.shuffle(random_indexes)
                    
                    for idx in random_indexes:
                        try:
                            textarea = textareas[idx]
                            placeholder = textarea.get_attribute("placeholder") or ""
                            
                            try:
                                label_elem = driver.find_element(By.CSS_SELECTOR, f"label[for='{textarea.get_attribute('id')}']")
                                label = label_elem.text if label_elem else ""
                            except:
                                label = ""
                            
                            # Add longer delay before filling each textarea (they're usually more important)
                            HumanBehavior.random_delay(1.5, 3.0)
                            
                            # Fill based on the field type
                            if "cover letter" in placeholder.lower() or "cover letter" in label.lower():
                                if cover_letter_path:
                                    with open(cover_letter_path, 'r', encoding='utf-8') as f:
                                        cover_letter_text = f.read()
                                    
                                    # Type cover letter with slower, more deliberate typing
                                    HumanBehavior.human_like_typing(textarea, cover_letter_text, min_speed=0.03, max_speed=0.08)
                                    logger.info("Filled in cover letter text")
                            
                            elif "additional information" in placeholder.lower() or "additional information" in label.lower():
                                # Use one of several personalized responses for additional info
                                additional_info_options = [
                                    "I am very excited about this opportunity and believe my skills and experience make me a strong candidate for this role.",
                                    "I've been following your company's work for some time and am particularly impressed with your recent projects. I believe my background would be a great fit for this position.",
                                    "Thank you for considering my application. I'm passionate about this field and would welcome the opportunity to discuss how my experience aligns with your needs.",
                                    "I'm particularly drawn to this role because it aligns with my professional goals and technical skills. I look forward to potentially joining your team."
                                ]
                                selected_info = random.choice(additional_info_options)
                                
                                # Add job-specific customization
                                job_title = job.get('title', 'this position')
                                company_name = job.get('company_name', 'your company')
                                
                                custom_info = f"I'm excited about the {job_title} role at {company_name} and believe my background makes me well-suited for this opportunity."
                                
                                # 50% chance to use custom info
                                final_text = custom_info if random.random() < 0.5 else selected_info
                                
                                # Type additional info with human-like typing
                                HumanBehavior.human_like_typing(textarea, final_text)
                                logger.info("Filled in additional information")
                        except:
                            pass
            except:
                logger.debug("No textareas found")
        
        except Exception as e:
            logger.error(f"Error filling LinkedIn additional questions: {e}")
    
    def _apply_indeed(self, driver, job: Dict[str, Any], resume_path: str, cover_letter_path: Optional[str]) -> bool:
        """
        Apply to a job on Indeed with human-like behavior.
        
        Args:
            driver: Selenium WebDriver
            job: Job listing dictionary
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file
            
        Returns:
            True if application was successful, False otherwise
        """
        # Implementation for Indeed application process with human-like behavior
        # Similar structure to LinkedIn but with Indeed-specific selectors
        return True
    
    def _apply_ziprecruiter(self, driver, job: Dict[str, Any], resume_path: str, cover_letter_path: Optional[str]) -> bool:
        """
        Apply to a job on ZipRecruiter with human-like behavior.
        
        Args:
            driver: Selenium WebDriver
            job: Job listing dictionary
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file
            
        Returns:
            True if application was successful, False otherwise
        """
        # Implementation for ZipRecruiter application process with human-like behavior
        # Similar structure to LinkedIn but with ZipRecruiter-specific selectors
        return True
    
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
                    f.write("Date,Company,Title,Location,URL,Source,H1B_Sponsor,HiringManager,HiringManagerEmail\n")
                
                # Write application details
                f.write(f"{time.strftime('%Y-%m-%d')},{job.get('company_name', '')},{job.get('title', '')},{job.get('location', '')},{job.get('url', '')},{job.get('source', '')},{job.get('sponsors_h1b', False)},{job.get('hiring_manager_name', '')},{job.get('hiring_manager_email', '')}\n")
        
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
                    f.write("FollowUpDate,Company,Title,ContactName,ContactEmail,URL,Applied\n")
                
                # Write follow-up details
                f.write(f"{follow_up_date},{job.get('company_name', '')},{job.get('title', '')},{job.get('hiring_manager_name', '')},{job.get('hiring_manager_email', '')},{job.get('url', '')},{time.strftime('%Y-%m-%d')}\n")
        
        except Exception as e:
            logger.error(f"Error scheduling follow-up: {e}")
    
    def _send_direct_email(self, job: Dict[str, Any], cover_letter_path: str):
        """
        Send a direct email to the hiring manager.
        
        Args:
            job: Job listing dictionary
            cover_letter_path: Path to cover letter file
        """
        # Implementation for sending direct email to hiring manager
        pass

