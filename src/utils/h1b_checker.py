import logging
import os
import csv
import re
from typing import Dict, Set, Any

logger = logging.getLogger(__name__)

class H1BChecker:
    """
    Checks if a company sponsors H1B visas.
    """
    
    def __init__(self):
        """Initialize the H1B checker."""
        self.h1b_sponsors = self._load_h1b_sponsors()
    
    def _load_h1b_sponsors(self) -> Set[str]:
        """
        Load H1B sponsors from CSV file.
        
        Returns:
            Set of company names that sponsor H1B visas
        """
        sponsors = set()
        
        # Path to H1B sponsors CSV file
        h1b_file = os.path.join("data_folder", "h1b_sponsors.csv")
        
        # Create file with some known sponsors if it doesn't exist
        if not os.path.exists(h1b_file):
            self._create_default_h1b_file(h1b_file)
        
        try:
            with open(h1b_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                # Skip header
                next(reader, None)
                
                for row in reader:
                    if row and len(row) > 0:
                        # Add company name to set (lowercase for case-insensitive matching)
                        sponsors.add(row[0].lower())
            
            logger.info(f"Loaded {len(sponsors)} H1B sponsors")
            
        except Exception as e:
            logger.error(f"Error loading H1B sponsors: {e}")
        
        return sponsors
    
    def _create_default_h1b_file(self, file_path: str):
        """
        Create default H1B sponsors file with some known sponsors.
        
        Args:
            file_path: Path to H1B sponsors file
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # List of known H1B sponsors
            default_sponsors = [
                "Google",
                "Microsoft",
                "Amazon",
                "Apple",
                "Facebook",
                "IBM",
                "Intel",
                "Cisco",
                "Oracle",
                "Salesforce",
                "Adobe",
                "Twitter",
                "LinkedIn",
                "Uber",
                "Airbnb",
                "Netflix",
                "Tesla",
                "Nvidia",
                "Qualcomm",
                "Spotify",
                "Dropbox",
                "Slack",
                "Zoom",
                "Twilio",
                "Square",
                "Stripe",
                "Shopify",
                "Atlassian",
                "Workday",
                "ServiceNow",
                "Snowflake",
                "Palantir",
                "Databricks",
                "Coinbase",
                "Robinhood",
                "DoorDash",
                "Instacart",
                "Lyft",
                "Pinterest",
                "Snap",
                "Roblox",
                "Unity",
                "Epic Games",
                "Electronic Arts",
                "Activision Blizzard",
                "Zynga",
                "Take-Two Interactive",
                "Ubisoft",
                "Sony",
                "Samsung"
            ]
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Company Name", "Notes"])
                
                for sponsor in default_sponsors:
                    writer.writerow([sponsor, "Default entry"])
            
            logger.info(f"Created default H1B sponsors file with {len(default_sponsors)} entries")
            
        except Exception as e:
            logger.error(f"Error creating default H1B sponsors file: {e}")
    
    def is_h1b_sponsor(self, company_name: str, job_description: str = "") -> bool:
        """
        Check if a company sponsors H1B visas.
        
        Args:
            company_name: Company name to check
            job_description: Job description to check for H1B keywords
            
        Returns:
            True if the company sponsors H1B visas, False otherwise
        """
        if not company_name:
            return False
        
        # Clean company name
        clean_name = self._clean_company_name(company_name)
        
        # Check if company is in sponsors list
        for sponsor in self.h1b_sponsors:
            if clean_name in sponsor or sponsor in clean_name:
                logger.info(f"Company {company_name} is an H1B sponsor (found in database)")
                return True
        
        # Check job description for H1B keywords if provided
        if job_description:
            h1b_keywords = [
                "h1b", "h-1b", "h1-b", "h 1 b", "h1 b", "h-1 b",
                "visa sponsor", "visa sponsorship", "sponsorship available",
                "sponsor visa", "sponsor work visa", "sponsor h1b",
                "will sponsor", "can sponsor", "open to sponsor",
                "willing to sponsor", "eligible to work", "work authorization",
                "legally authorized", "work permit", "eligible for sponsorship",
                "international candidates", "international applicants"
            ]
            
            job_description_lower = job_description.lower()
            
            for keyword in h1b_keywords:
                if keyword in job_description_lower:
                    logger.info(f"Company {company_name} might sponsor H1B (keyword found in job description: {keyword})")
                    return True
        
        logger.info(f"Company {company_name} is not a known H1B sponsor")
        return False
    
    def _clean_company_name(self, company_name: str) -> str:
        """
        Clean company name for matching.
        
        Args:
            company_name: Company name to clean
            
        Returns:
            Cleaned company name
        """
        # Convert to lowercase
        name = company_name.lower()
        
        # Remove common suffixes
        suffixes = [
            "inc", "inc.", "incorporated", 
            "llc", "llc.", "limited liability company",
            "ltd", "ltd.", "limited",
            "corp", "corp.", "corporation",
            "co", "co.", "company"
        ]
        
        for suffix in suffixes:
            name = re.sub(r'\s+' + re.escape(suffix) + r'\s*$', '', name)
        
        # Remove special characters
        name = re.sub(r'[^\w\s]', '', name)
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def add_h1b_sponsor(self, company_name: str, notes: str = ""):
        """
        Add a company to the H1B sponsors list.
        
        Args:
            company_name: Company name to add
            notes: Notes about the company
        """
        if not company_name:
            return
        
        try:
            # Path to H1B sponsors CSV file
            h1b_file = os.path.join("data_folder", "h1b_sponsors.csv")
            
            # Add to in-memory set
            self.h1b_sponsors.add(company_name.lower())
            
            # Append to file
            with open(h1b_file, 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([company_name, notes])
            
            logger.info(f"Added {company_name} to H1B sponsors list")
            
        except Exception as e:
            logger.error(f"Error adding H1B sponsor: {e}")

    def check_job_for_h1b_keywords(self, job: Dict[str, Any]) -> bool:
        """
        Check if a job description contains H1B sponsorship keywords.
        
        Args:
            job: Job dictionary with description
            
        Returns:
            True if the job description contains H1B keywords, False otherwise
        """
        company_name = job.get('company_name', '')
        job_description = job.get('description', '')
        job_title = job.get('title', '')
        
        # First check if company is in known sponsors list
        if self.is_h1b_sponsor(company_name):
            return True
        
        # Check job description and title for H1B keywords
        combined_text = (job_description + " " + job_title).lower()
        
        h1b_keywords = [
            "h1b", "h-1b", "h1-b", "h 1 b", "h1 b", "h-1 b",
            "visa sponsor", "visa sponsorship", "sponsorship available",
            "sponsor visa", "sponsor work visa", "sponsor h1b",
            "will sponsor", "can sponsor", "open to sponsor",
            "willing to sponsor", "eligible to work", "work authorization",
            "legally authorized", "work permit", "eligible for sponsorship",
            "international candidates", "international applicants"
        ]
        
        for keyword in h1b_keywords:
            if keyword in combined_text:
                logger.info(f"Job at {company_name} might offer H1B sponsorship (keyword found: {keyword})")
                return True
        
        # Check for negative keywords that indicate no sponsorship
        negative_keywords = [
            "no visa sponsor", "no sponsorship", "not sponsor", 
            "will not sponsor", "cannot sponsor", "no h1b",
            "no visa", "no work visa", "no h1b visa",
            "not eligible for sponsorship", "sponsorship not available",
            "no sponsorship available", "citizens and permanent residents only",
            "authorized to work in the us", "must be authorized to work",
            "must be eligible to work", "must be legally authorized"
        ]
        
        for keyword in negative_keywords:
            if keyword in combined_text:
                logger.info(f"Job at {company_name} explicitly does NOT offer H1B sponsorship (negative keyword found: {keyword})")
            return False
        
        return False

