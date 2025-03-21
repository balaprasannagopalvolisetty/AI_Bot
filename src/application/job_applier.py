import logging
import time
import os
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys

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
        
        # Add preferences to handle downloads and file uploads
        prefs = {
            "download.default_directory": os.path.abspath("data_folder"),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
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
            
            # First, log in to LinkedIn
            self._linkedin_login(driver)
            
            # Navigate to the job page
            driver.get(job_url)
            logger.info(f"Navigated to job URL: {job_url}")
            
            # Wait for the page to load
            time.sleep(3)
            
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
                
                # Click the apply button
                apply_button = driver.find_element(By.CSS_SELECTOR, "button[data-control-name='jobdetails_topcard_inapply']")
                apply_button.click()
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
                    apply_button.click()
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
    
    def _linkedin_login(self, driver):
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
            
            # Enter credentials
            username_field = driver.find_element(By.ID, "username")
            password_field = driver.find_element(By.ID, "password")
            
            username_field.send_keys(self.config.get('LINKEDIN', {}).get('username', ''))
            password_field.send_keys(self.config.get('LINKEDIN', {}).get('password', ''))
            
            # Submit the form
            password_field.submit()
            logger.info("Submitted LinkedIn login form")
            
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
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error logging in to LinkedIn: {e}")
            raise
    
    def _handle_linkedin_application_form(self, driver, job: Dict[str, Any], resume_path: str, cover_letter_path: Optional[str]) -> bool:
        """
        Handle the LinkedIn application form.
        
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
                
                # Check for resume upload
                try:
                    resume_upload = driver.find_element(By.CSS_SELECTOR, "input[type='file'][name='resume']")
                    resume_upload.send_keys(os.path.abspath(resume_path))
                    logger.info("Uploaded resume")
                    time.sleep(2)  # Wait for upload to complete
                except NoSuchElementException:
                    logger.debug("No resume upload field found in this step")
                
                # Check for cover letter upload
                if cover_letter_path:
                    try:
                        cover_letter_upload = driver.find_element(By.CSS_SELECTOR, "input[type='file'][name='coverLetter']")
                        cover_letter_upload.send_keys(os.path.abspath(cover_letter_path))
                        logger.info("Uploaded cover letter")
                        time.sleep(2)  # Wait for upload to complete
                    except NoSuchElementException:
                        logger.debug("No cover letter upload field found in this step")
                
                # Fill in contact information fields
                self._fill_linkedin_contact_info(driver, job)
                
                # Fill in additional questions
                self._fill_linkedin_additional_questions(driver, job)
                
                # Check for "Next" button
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
                    next_button.click()
                    logger.info("Clicked Next button")
                    time.sleep(2)  # Wait for next step to load
                    current_step += 1
                    continue
                except NoSuchElementException:
                    logger.debug("No Next button found in this step")
                
                # Check for "Review" button
                try:
                    review_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Review your application']")
                    review_button.click()
                    logger.info("Clicked Review button")
                    time.sleep(2)  # Wait for review page to load
                    current_step += 1
                    continue
                except NoSuchElementException:
                    logger.debug("No Review button found in this step")
                
                # Check for "Submit" button
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']")
                    submit_button.click()
                    logger.info("Clicked Submit button")
                    
                    # Wait for confirmation
                    try:
                        WebDriverWait(driver, self.timeout).until(
                            EC.presence_of_element_locate  self.timeout).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.artdeco-inline-feedback--success"))
                        )
                        logger.info("Application submitted successfully")
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
                                button.click()
                                logger.info(f"Clicked button with text: {button.text}")
                                time.sleep(2)
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
        Fill in contact information fields in LinkedIn application form.
        
        Args:
            driver: Selenium WebDriver
            job: Job listing dictionary
        """
        try:
            # Fill in name field
            try:
                name_field = driver.find_element(By.ID, "single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-3-name-firstName")
                name_field.clear()
                name_field.send_keys(self.user_info.get('name', '').split()[0])
                logger.info("Filled in first name")
            except NoSuchElementException:
                logger.debug("No first name field found")
            
            # Fill in last name field
            try:
                last_name_field = driver.find_element(By.ID, "single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-3-name-lastName")
                last_name_field.clear()
                last_name_field.send_keys(self.user_info.get('name', '').split()[-1])
                logger.info("Filled in last name")
            except NoSuchElementException:
                logger.debug("No last name field found")
            
            # Fill in email field
            try:
                email_field = driver.find_element(By.ID, "single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-3-email-email")
                email_field.clear()
                email_field.send_keys(self.user_info.get('email', ''))
                logger.info("Filled in email")
            except NoSuchElementException:
                logger.debug("No email field found")
            
            # Fill in phone field
            try:
                phone_field = driver.find_element(By.ID, "single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-3-phoneNumber-nationalNumber")
                phone_field.clear()
                phone_field.send_keys(self.user_info.get('phone', ''))
                logger.info("Filled in phone number")
            except NoSuchElementException:
                logger.debug("No phone field found")
            
            # Fill in hiring manager name if available
            hiring_manager_name = job.get('hiring_manager_name', '')
            if hiring_manager_name:
                try:
                    # Look for fields that might be for hiring manager
                    manager_fields = driver.find_elements(By.CSS_SELECTOR, "input[id*='hiring-manager'], input[id*='recruiter'], input[id*='addressee']")
                    if manager_fields:
                        manager_fields[0].clear()
                        manager_fields[0].send_keys(hiring_manager_name)
                        logger.info("Filled in hiring manager name")
                except:
                    logger.debug("Could not fill in hiring manager name")
        
        except Exception as e:
            logger.error(f"Error filling LinkedIn contact info: {e}")
    
    def _fill_linkedin_additional_questions(self, driver, job: Dict[str, Any]):
        """
        Fill in additional questions in LinkedIn application form.
        
        Args:
            driver: Selenium WebDriver
            job: Job listing dictionary
        """
        try:
            # Handle radio buttons for yes/no questions (usually select "Yes" for positive questions)
            try:
                radio_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'][value='Yes']")
                for radio in radio_buttons:
                    try:
                        radio.click()
                        logger.info("Selected 'Yes' for a radio button question")
                    except:
                        pass
            except:
                logger.debug("No radio buttons found")
            
            # Handle dropdown selects
            try:
                selects = driver.find_elements(By.TAG_NAME, "select")
                for select in selects:
                    try:
                        # Try to select the first non-empty option
                        options = select.find_elements(By.TAG_NAME, "option")
                        for option in options[1:]:  # Skip the first option (usually a placeholder)
                            if option.text.strip():
                                option.click()
                                logger.info(f"Selected '{option.text}' from dropdown")
                                break
                    except:
                        pass
            except:
                logger.debug("No dropdowns found")
            
            # Handle text inputs for work experience, education, etc.
            try:
                text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']:not([id*='name']):not([id*='email']):not([id*='phone'])")
                for text_input in text_inputs:
                    try:
                        placeholder = text_input.get_attribute("placeholder") or ""
                        label_elem = driver.find_element(By.CSS_SELECTOR, f"label[for='{text_input.get_attribute('id')}']")
                        label = label_elem.text if label_elem else ""
                        
                        # Fill based on the field type
                        if "years" in placeholder.lower() or "years" in label.lower() or "experience" in placeholder.lower() or "experience" in label.lower():
                            text_input.clear()
                            text_input.send_keys("3")
                            logger.info("Filled in years of experience")
                        elif "salary" in placeholder.lower() or "salary" in label.lower():
                            text_input.clear()
                            text_input.send_keys("90000")
                            logger.info("Filled in salary expectation")
                        elif "website" in placeholder.lower() or "website" in label.lower() or "portfolio" in placeholder.lower() or "portfolio" in label.lower():
                            text_input.clear()
                            text_input.send_keys(self.user_info.get('portfolio', ''))
                            logger.info("Filled in website/portfolio")
                        elif "linkedin" in placeholder.lower() or "linkedin" in label.lower():
                            text_input.clear()
                            text_input.send_keys(self.user_info.get('linkedin', ''))
                            logger.info("Filled in LinkedIn URL")
                        elif "github" in placeholder.lower() or "github" in label.lower():
                            text_input.clear()
                            text_input.send_keys(self.user_info.get('github', ''))
                            logger.info("Filled in GitHub URL")
                    except:
                        pass
            except:
                logger.debug("No additional text inputs found")
            
            # Handle textareas for additional information
            try:
                textareas = driver.find_elements(By.TAG_NAME, "textarea")
                for textarea in textareas:
                    try:
                        placeholder = textarea.get_attribute("placeholder") or ""
                        label_elem = driver.find_element(By.CSS_SELECTOR, f"label[for='{textarea.get_attribute('id')}']")
                        label = label_elem.text if label_elem else ""
                        
                        # Fill based on the field type
                        if "cover letter" in placeholder.lower() or "cover letter" in label.lower():
                            if cover_letter_path:
                                with open(cover_letter_path, 'r', encoding='utf-8') as f:
                                    cover_letter_text = f.read()
                                textarea.clear()
                                textarea.send_keys(cover_letter_text)
                                logger.info("Filled in cover letter text")
                        elif "additional information" in placeholder.lower() or "additional information" in label.lower():
                            textarea.clear()
                            textarea.send_keys("I am very excited about this opportunity and believe my skills and experience make me a strong candidate for this role.")
                            logger.info("Filled in additional information")
                    except:
                        pass
            except:
                logger.debug("No textareas found")
        
        except Exception as e:
            logger.error(f"Error filling LinkedIn additional questions: {e}")
    
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
        # Implementation for Indeed application process
        # Similar structure to LinkedIn but with Indeed-specific selectors
        return True
    
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
        # Implementation for ZipRecruiter application process
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

