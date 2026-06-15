import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmailPatternFinder:
    """
    Utility to find email patterns for companies without using external APIs.
    """
    
    def __init__(self):
        """Initialize the email pattern finder."""
        # Common email formats
        self.common_formats = [
            'first.last',    # john.doe@company.com
            'firstlast',     # johndoe@company.com
            'first_last',    # john_doe@company.com
            'flast',         # jdoe@company.com
            'lastf',         # doej@company.com
            'firstl',        # johnd@company.com
            'f.last',        # j.doe@company.com
            'last.first',    # doe.john@company.com
            'first',         # john@company.com
            'last'           # doe@company.com
        ]
        
        # Cache for company email formats
        self.company_formats = {}
    
    def find_email_pattern(self, company_name: str, domain: str) -> str:
        """
        Find the email pattern for a company.
        
        Args:
            company_name: Company name
            domain: Company domain
            
        Returns:
            Email format pattern
        """
        # Check cache first
        if domain in self.company_formats:
            return self.company_formats[domain]
        
        # Try to find email pattern from company website
        pattern = self._extract_pattern_from_website(domain)
        if pattern:
            self.company_formats[domain] = pattern
            return pattern
        
        # Try to find pattern from Google search
        pattern = self._extract_pattern_from_search(company_name, domain)
        if pattern:
            self.company_formats[domain] = pattern
            return pattern
        
        # Default to most common format
        return 'first.last'
    
    def _extract_pattern_from_website(self, domain: str) -> Optional[str]:
        """
        Extract email pattern from company website.
        
        Args:
            domain: Company domain
            
        Returns:
            Email format pattern or None
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Check common pages where emails might be found
            for page in ['contact', 'about', 'team', 'company', 'about-us', 'leadership', 'our-team']:
                url = f"https://{domain}/{page}"
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        # Look for email patterns
                        email_pattern = r'[a-zA-Z0-9._%+-]+@' + re.escape(domain)
                        emails = re.findall(email_pattern, response.text)
                        
                        if emails:
                            # Extract format from found email
                            return self._determine_format_from_email(emails[0])
                except:
                    continue
            
            return None
        
        except Exception as e:
            logger.error(f"Error extracting pattern from website: {e}")
            return None
    
    def _extract_pattern_from_search(self, company_name: str, domain: str) -> Optional[str]:
        """
        Extract email pattern from search results.
        
        Args:
            company_name: Company name
            domain: Company domain
            
        Returns:
            Email format pattern or None
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Search for company email format
            search_query = f"{company_name} email format {domain}"
            response = requests.get(f"https://www.google.com/search?q={search_query.replace(' ', '+')}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Look for email patterns in search results
                email_pattern = r'[a-zA-Z0-9._%+-]+@' + re.escape(domain)
                emails = re.findall(email_pattern, response.text)
                
                if emails:
                    # Extract format from found email
                    return self._determine_format_from_email(emails[0])
            
            return None
        
        except Exception as e:
            logger.error(f"Error extracting pattern from search: {e}")
            return None
    
    def _determine_format_from_email(self, email: str) -> str:
        """
        Determine email format from an email address.
        
        Args:
            email: Email address
            
        Returns:
            Email format pattern
        """
        try:
            # Extract username part
            username = email.split('@')[0].lower()
            
            # Check for common patterns
            if '.' in username:
                parts = username.split('.')
                if len(parts) == 2:
                    # Could be first.last or last.first
                    if len(parts[0]) == 1:
                        return 'f.last'
                    elif len(parts[1]) == 1:
                        return 'first.l'
                    else:
                        # Assume first.last as it's more common
                        return 'first.last'
            
            elif '_' in username:
                return 'first_last'
            
            elif len(username) <= 6:  # Likely firstl or flast
                return 'flast'
            
            else:
                return 'firstlast'
        
        except Exception as e:
            logger.error(f"Error determining format from email: {e}")
            return 'first.last'
    
    def generate_email(self, first_name: str, last_name: str, domain: str, format_type: str) -> str:
        """
        Generate email based on name, domain, and format.
        
        Args:
            first_name: First name
            last_name: Last name
            domain: Domain name
            format_type: Email format type
            
        Returns:
            Generated email address
        """
        try:
            # Clean names
            first_name = re.sub(r'[^\w]', '', first_name.lower())
            last_name = re.sub(r'[^\w]', '', last_name.lower())
            
            # Generate email based on format
            if format_type == 'first.last':
                return f"{first_name}.{last_name}@{domain}"
            elif format_type == 'firstlast':
                return f"{first_name}{last_name}@{domain}"
            elif format_type == 'first_last':
                return f"{first_name}_{last_name}@{domain}"
            elif format_type == 'flast':
                return f"{first_name[0]}{last_name}@{domain}"
            elif format_type == 'lastf':
                return f"{last_name}{first_name[0]}@{domain}"
            elif format_type == 'firstl':
                return f"{first_name}{last_name[0]}@{domain}"
            elif format_type == 'f.last':
                return f"{first_name[0]}.{last_name}@{domain}"
            elif format_type == 'last.first':
                return f"{last_name}.{first_name}@{domain}"
            elif format_type == 'first':
                return f"{first_name}@{domain}"
            elif format_type == 'last':
                return f"{last_name}@{domain}"
            else:
                # Default to first.last
                return f"{first_name}.{last_name}@{domain}"
        
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            return f"{first_name}.{last_name}@{domain}"

