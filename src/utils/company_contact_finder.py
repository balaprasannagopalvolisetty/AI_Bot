import logging
import re
import socket
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.utils.email_pattern_finder import EmailPatternFinder

logger = logging.getLogger(__name__)

class CompanyContactFinder:
    """
    A class to find contact information for companies.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the company contact finder.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.browser_config = config.get('BROWSER', {})
        self.user_info = config.get('USER_INFO', {})
        self.timeout = self.browser_config.get('timeout', 30)
        self.user_agent = self.browser_config.get('user_agent', '')
        self.headless = self.browser_config.get('headless', False)
        
        # LinkedIn credentials (if available)
        self.linkedin_username = config.get('LINKEDIN', {}).get('username', '')
        self.linkedin_password = config.get('LINKEDIN', {}).get('password', '')
        
        # Initialize email pattern finder
        self.email_pattern_finder = EmailPatternFinder()
        
        # Cache for company domains
        self.company_domains = {}

    def find_company_contacts(self, company_name: str, company_website: str = "") -> List[Dict[str, str]]:
        """
        Find contact information for a given company.
        
        Args:
            company_name: Name of the company
            company_website: Optional website of the company
            
        Returns:
            A list of dictionaries containing contact information.
        """
        contacts = []
        
        # 1. Find company domain
        domain = self._find_company_domain(company_name, company_website)
        if not domain:
            logger.warning(f"Could not find domain for {company_name}")
            return contacts
        
        # 2. Scrape company website for names and titles
        names_and_titles = self._scrape_company_website(domain)
        
        # 3. Generate email addresses
        for name, title in names_and_titles:
            email = self._generate_email(name, domain)
            if email:
                contacts.append({"name": name, "title": title, "email": email})
        
        return contacts

    def _find_company_domain(self, company_name: str, company_website: str = "") -> str:
        """
        Find the company domain name.
        
        Args:
            company_name: Name of the company
            company_website: Optional website of the company
            
        Returns:
            The company domain name.
        """
        if company_website:
            try:
                parsed_url = urlparse(company_website)
                domain = parsed_url.netloc
                if domain:
                    self.company_domains[company_name] = domain
                    return domain
            except Exception as e:
                logger.error(f"Error parsing company website: {e}")
        
        if company_name in self.company_domains:
            return self.company_domains[company_name]
        
        try:
            # Use a search engine to find the company website
            search_query = f"site:{company_name}.com {company_name}"
            search_url = f"https://www.google.com/search?q={search_query}"
            
            response = requests.get(search_url, headers={'User-Agent': self.user_agent}, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract the first result
            first_result = soup.find("a", href=True)
            if first_result:
                url = first_result["href"]
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                if domain:
                    self.company_domains[company_name] = domain
                    return domain
        
        except Exception as e:
            logger.error(f"Error finding company domain: {e}")
        
        return ""

    def _scrape_company_website(self, domain: str) -> List[tuple[str, str]]:
        """
        Scrape the company website for names and titles.
        
        Args:
            domain: Domain name of the company
            
        Returns:
            A list of tuples containing names and titles.
        """
        names_and_titles = []
        
        try:
            # Construct URLs for common "About Us" and "Contact Us" pages
            urls = [
                f"https://{domain}/about",
                f"https://{domain}/about-us",
                f"https://{domain}/contact",
                f"https://{domain}/contact-us",
                f"https://{domain}/team",
                f"https://{domain}/our-team",
            ]
            
            # Scrape each URL
            for url in urls:
                try:
                    response = requests.get(url, headers={'User-Agent': self.user_agent}, timeout=self.timeout)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, "html.parser")
                    
                    # Extract names and titles from the page
                    names_and_titles.extend(self._extract_names_and_titles(soup))
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Error scraping {url}: {e}")
        
        except Exception as e:
            logger.error(f"Error scraping company website: {e}")
        
        return names_and_titles

    def _extract_names_and_titles(self, soup: BeautifulSoup) -> List[tuple[str, str]]:
        """
        Extract names and titles from a BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            A list of tuples containing names and titles.
        """
        names_and_titles = []
        
        # Find common HTML elements containing names and titles
        name_elements = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"], class_=re.compile(r"(name|title)", re.IGNORECASE))
        
        for element in name_elements:
            try:
                name = element.text.strip()
                title = ""
                
                # Attempt to find the title in the next sibling element
                if element.next_sibling:
                    title_element = element.next_sibling
                    if title_element and hasattr(title_element, 'text'):
                        title = title_element.text.strip()
                
                # If no title is found, attempt to find it in the parent element
                if not title and element.parent:
                    title_element = element.parent.find(class_=re.compile(r"title", re.IGNORECASE))
                    if title_element and hasattr(title_element, 'text'):
                        title = title_element.text.strip()
                
                # Filter out common false positives
                if len(name) > 3 and not re.search(r"(email|phone|tel|fax|website)", name, re.IGNORECASE):
                    names_and_titles.append((name, title))
            
            except Exception as e:
                logger.error(f"Error extracting name and title: {e}")
        
        return names_and_titles

    def _generate_email(self, full_name: str, domain: str) -> str:
        """
        Generate email address based on name and domain.
        
        Args:
            full_name: Full name
            domain: Domain name
        
        Returns:
            Email address
        """
        try:
            # Parse name
            name_parts = full_name.strip().split()
            if len(name_parts) < 2:
                return ""
            
            first_name = name_parts[0].lower()
            last_name = name_parts[-1].lower()
            
            # Find email pattern for this domain
            format_type = self.email_pattern_finder.find_email_pattern(domain, domain)
            
            # Generate email based on pattern
            email = self.email_pattern_finder.generate_email(first_name, last_name, domain, format_type)
            
            # Verify domain has MX records
            if self._verify_email(email):
                return email
            
            # Try alternative formats if the first one doesn't work
            alternative_formats = ['first.last', 'firstlast', 'first_last', 'flast', 'firstl']
            for alt_format in alternative_formats:
                if alt_format == format_type:
                    continue
                
                alt_email = self.email_pattern_finder.generate_email(first_name, last_name, domain, alt_format)
                if self._verify_email(alt_email):
                    return alt_email
            
            # Return the original email if no alternatives work
            return email
        
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            return ""

    def _verify_email(self, email: str) -> bool:
        """
        Verify if the email address is valid by checking for MX records.
        
        Args:
            email: Email address to verify
            
        Returns:
            True if the email is valid, False otherwise.
        """
        try:
            domain = email.split('@')[1]
            socket.getaddrinfo(domain, 25)
            return True
        except socket.gaierror:
            return False
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return False

