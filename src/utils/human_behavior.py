import time
import random
import logging
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementNotInteractableException, StaleElementReferenceException

logger = logging.getLogger(__name__)

class HumanBehavior:
    """
    Utility class to simulate human-like behavior when interacting with web elements.
    """
    
    @staticmethod
    def random_delay(min_seconds=0.5, max_seconds=2.5):
        """
        Wait for a random amount of time within the given range.
        
        Args:
            min_seconds: Minimum wait time in seconds
            max_seconds: Maximum wait time in seconds
        """
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        return delay
    
    @staticmethod
    def human_like_typing(element, text, min_speed=0.05, max_speed=0.18, mistake_probability=0.03):
        """
        Type text into an element with human-like variations in typing speed and occasional mistakes.
        
        Args:
            element: Selenium WebElement to type into
            text: Text to type
            min_speed: Minimum time between keypresses in seconds
            max_speed: Maximum time between keypresses in seconds
            mistake_probability: Probability of making a typing mistake
        """
        try:
            element.click()
            HumanBehavior.random_delay(0.3, 1.0)
            
            # Type each character with variable speed and occasional mistakes
            for char in text:
                # Random chance of making a mistake
                if random.random() < mistake_probability:
                    # Type a wrong character
                    wrong_char = chr(ord(char) + random.randint(1, 5))
                    element.send_keys(wrong_char)
                    HumanBehavior.random_delay(0.1, 0.3)
                    
                    # Delete the wrong character
                    element.send_keys(Keys.BACKSPACE)
                    HumanBehavior.random_delay(0.2, 0.5)
                
                # Type the correct character
                element.send_keys(char)
                
                # Random delay between keypresses to simulate human typing
                HumanBehavior.random_delay(min_speed, max_speed)
            
            # Occasionally add a pause as if thinking
            if random.random() < 0.2:
                HumanBehavior.random_delay(0.8, 2.0)
        
        except (ElementNotInteractableException, StaleElementReferenceException) as e:
            logger.warning(f"Could not type into element: {e}")
            # Fall back to regular send_keys
            element.clear()
            element.send_keys(text)
    
    @staticmethod
    def human_like_click(driver, element, move_offset=True):
        """
        Click an element with human-like mouse movement.
        
        Args:
            driver: Selenium WebDriver
            element: Element to click
            move_offset: Whether to click with slight offset from center
        """
        try:
            # Create action chain
            actions = ActionChains(driver)
            
            # Move to a random position first, then to element with realistic mouse movement
            viewport_width = driver.execute_script("return window.innerWidth")
            viewport_height = driver.execute_script("return window.innerHeight")
            
            # Move to a random starting point
            random_x = random.randint(0, viewport_width)
            random_y = random.randint(0, viewport_height)
            actions.move_by_offset(random_x, random_y)
            
            # Move to element
            actions.move_to_element(element)
            
            # Add slight offset to click position to seem more human
            if move_offset:
                element_size = element.size
                offset_x = random.randint(-element_size['width']//4, element_size['width']//4)
                offset_y = random.randint(-element_size['height']//4, element_size['height']//4)
                actions.move_by_offset(offset_x, offset_y)
            
            # Slight pause before clicking
            actions.pause(random.uniform(0.1, 0.3))
            
            # Click
            actions.click()
            actions.perform()
            
            # Random delay after clicking
            HumanBehavior.random_delay()
            
        except Exception as e:
            logger.warning(f"Error in human-like click, falling back to regular click: {e}")
            element.click()
            HumanBehavior.random_delay()
    
    @staticmethod
    def scroll_page(driver, direction="down", amount=None):
        """
        Scroll the page in a human-like way.
        
        Args:
            driver: Selenium WebDriver
            direction: Direction to scroll ("up" or "down")
            amount: Amount to scroll in pixels, random if None
        """
        if amount is None:
            # Random scroll amount between 100 and 800 pixels
            amount = random.randint(100, 800)
        
        # Adjust amount based on direction
        if direction == "up":
            amount = -amount
        
        # Scroll in smaller increments to simulate human behavior
        remaining = amount
        while abs(remaining) > 0:
            # Determine increment for this step
            step = min(abs(remaining), random.randint(50, 200))
            if remaining < 0:
                step = -step
            
            # Execute scroll
            driver.execute_script(f"window.scrollBy(0, {step})")
            
            # Update remaining amount
            remaining -= step
            
            # Small pause between scroll steps
            time.sleep(random.uniform(0.05, 0.2))
        
        # Pause after scrolling
        HumanBehavior.random_delay(0.5, 1.5)
    
    @staticmethod
    def read_page_behavior(driver, duration_range=(3, 8)):
        """
        Simulate a human reading a page - scrolling, pausing, etc.
        
        Args:
            driver: Selenium WebDriver
            duration_range: Range of time to spend "reading" in seconds
        """
        # Determine reading duration
        read_duration = random.uniform(*duration_range)
        end_time = time.time() + read_duration
        
        # Get page height
        page_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # Continue reading behavior until time is up
        while time.time() < end_time:
            # Determine current scroll position
            current_position = driver.execute_script("return window.pageYOffset")
            
            # Either continue scrolling down or occasionally scroll back up
            if random.random() < 0.8 and current_position < page_height - viewport_height:
                # Scroll down
                scroll_amount = random.randint(100, 300)
                HumanBehavior.scroll_page(driver, "down", scroll_amount)
            elif current_position > 0:
                # Scroll up occasionally
                scroll_amount = random.randint(50, 200)
                HumanBehavior.scroll_page(driver, "up", scroll_amount)
            
            # Pause as if reading
            HumanBehavior.random_delay(0.5, 2.0)

