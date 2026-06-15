import logging
from typing import Dict, List, Any, Optional
from src.utils.h1b_sponsor_checker import H1BSponsorChecker

logger = logging.getLogger(__name__)

class JobFilter:
    """
    Filter job listings based on various criteria including H1B sponsorship.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the job filter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.h1b_filter_enabled = config.get('filter_h1b_sponsors', False)
        self.h1b_checker = H1BSponsorChecker() if self.h1b_filter_enabled else None
        
        # Pre-load top sponsors if H1B filter is enabled
        if self.h1b_filter_enabled:
            logger.info("Initializing H1B sponsor filter and pre-loading top sponsors...")
            self.h1b_checker.get_top_h1b_sponsors()
        
        # Other filter settings
        self.keywords = config.get('keywords', [])
        self.exclude_keywords = config.get('exclude_keywords', [])
        self.min_salary = config.get('min_salary', 0)
        self.experience_level = config.get('experience_level', '')
        self.job_type = config.get('job_type', '')
        
    def filter_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter job listings based on configured criteria.
        
        Args:
            jobs: List of job listings to filter
            
        Returns:
            Filtered list of job listings
        """
        filtered_jobs = []
        h1b_sponsor_count = 0
        
        for job in jobs:
            if self._passes_filters(job):
                filtered_jobs.append(job)
                if self.h1b_filter_enabled and job.get('sponsors_h1b', False):
                    h1b_sponsor_count += 1
        
        logger.info(f"Filtered {len(jobs)} jobs down to {len(filtered_jobs)} jobs")
        if self.h1b_filter_enabled:
            logger.info(f"Found {h1b_sponsor_count} jobs at companies that sponsor H1B visas")
        
        return filtered_jobs
    
    def _passes_filters(self, job: Dict[str, Any]) -> bool:
        """
        Check if a job passes all configured filters.
        
        Args:
            job: Job listing to check
            
        Returns:
            True if the job passes all filters, False otherwise
        """
        # Apply H1B sponsorship filter if enabled
        if self.h1b_filter_enabled:
            company_name = job.get('company_name', '')
            if not company_name:
                return False
                
            sponsors_h1b = self.h1b_checker.check_h1b_sponsorship(company_name)
            job['sponsors_h1b'] = sponsors_h1b  # Add this info to the job dict for later use
            
            if not sponsors_h1b:
                logger.debug(f"Filtered out job at {company_name} - does not sponsor H1B")
                return False
        
        # Apply keyword filters
        job_description = job.get('description', '').lower()
        job_title = job.get('title', '').lower()
        
        # Check for required keywords
        for keyword in self.keywords:
            if keyword.lower() not in job_description and keyword.lower() not in job_title:
                logger.debug(f"Filtered out job: missing keyword '{keyword}'")
                return False
        
        # Check for excluded keywords
        for keyword in self.exclude_keywords:
            if keyword.lower() in job_description or keyword.lower() in job_title:
                logger.debug(f"Filtered out job: contains excluded keyword '{keyword}'")
                return False
        
        # Apply salary filter if available
        if 'salary' in job and self.min_salary > 0:
            salary = job.get('salary', 0)
            if salary < self.min_salary:
                logger.debug(f"Filtered out job: salary {salary} below minimum {self.min_salary}")
                return False
        
        # Apply experience level filter if specified
        if self.experience_level and 'experience_level' in job:
            if job['experience_level'].lower() != self.experience_level.lower():
                logger.debug(f"Filtered out job: experience level mismatch")
                return False
        
        # Apply job type filter if specified
        if self.job_type and 'job_type' in job:
            if job['job_type'].lower() != self.job_type.lower():
                logger.debug(f"Filtered out job: job type mismatch")
                return False
        
        return True
