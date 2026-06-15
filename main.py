#!/usr/bin/env python3
import os
import sys
import time
import logging
import argparse
import json
from datetime import datetime
from typing import Dict, Any, List
import random

# Import application modules
from src.application.job_applier import JobApplier
from src.job_boards.linkedin_scraper import LinkedInScraper
from src.job_boards.indeed_scraper import IndeedScraper
from src.job_boards.ziprecruiter_scraper import ZipRecruiterScraper
from src.utils.h1b_checker import H1BChecker
from src.utils.resume_matcher import ResumeMatcher
from src.utils.cover_letter_generator import CoverLetterGenerator

# Set up logging
def setup_logging(config: Dict[str, Any]):
    """Set up logging configuration."""
    log_level = getattr(logging, config.get('LOGGING', {}).get('level', 'INFO'))
    log_file = config.get('LOGGING', {}).get('log_file', 'data_folder/application_log.txt')
    
    # Create log directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

# Load configuration
def load_config(config_path: str = 'config.py') -> Dict[str, Any]:
    """Load configuration from config.py file."""
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    
    # Load config.py as a module
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    # Extract all uppercase variables as config
    config = {name: getattr(config_module, name) for name in dir(config_module) 
              if name.isupper() and not name.startswith('_')}
    
    return config

# Update config with command line arguments
def update_config_with_args(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """Update configuration with command line arguments."""
    # Update job search parameters
    if args.job_titles:
        config['JOB_SEARCH']['job_titles'] = args.job_titles
    
    if args.locations:
        config['JOB_SEARCH']['locations'] = args.locations
    
    if args.keywords:
        config['JOB_SEARCH']['keywords'] = args.keywords
    
    if args.exclude_keywords:
        config['JOB_SEARCH']['exclude_keywords'] = args.exclude_keywords
    
    if args.max_applications is not None:
        config['JOB_SEARCH']['max_applications_per_day'] = args.max_applications
    
    if args.h1b_only is not None:
        config['JOB_SEARCH']['filter_h1b_sponsors'] = args.h1b_only
    
    # Update job boards
    if args.linkedin is not None:
        config['JOB_BOARDS']['linkedin'] = args.linkedin
    
    if args.indeed is not None:
        config['JOB_BOARDS']['indeed'] = args.indeed
    
    if args.ziprecruiter is not None:
        config['JOB_BOARDS']['ziprecruiter'] = args.ziprecruiter
    
    # Update browser settings
    if args.headless is not None:
        config['BROWSER']['headless'] = args.headless
    
    return config

# Create necessary directories
def create_directories():
    """Create necessary directories for the application."""
    directories = [
        'data_folder',
        'data_folder/resumes',
        'data_folder/cover_letters',
        'data_folder/applications',
        'data_folder/follow_ups'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Print welcome message
def print_welcome_message():
    """Print welcome message with ASCII art."""
    welcome_message = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   🤖 AI Job Application Assistant 🤖                          ║
    ║                                                               ║
    ║   Automate your job search and application process            ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(welcome_message)

# Print configuration summary
def print_config_summary(config: Dict[str, Any]):
    """Print a summary of the configuration."""
    print("\n📋 Configuration Summary:")
    print("------------------------")
    
    # Job Search Parameters
    print("\n🔍 Job Search Parameters:")
    print(f"  - Job Titles: {', '.join(config['JOB_SEARCH']['job_titles'])}")
    print(f"  - Locations: {', '.join(config['JOB_SEARCH']['locations'])}")
    print(f"  - Keywords: {', '.join(config['JOB_SEARCH']['keywords'])}")
    print(f"  - Exclude Keywords: {', '.join(config['JOB_SEARCH']['exclude_keywords'])}")
    print(f"  - Max Applications Per Day: {config['JOB_SEARCH']['max_applications_per_day']}")
    print(f"  - Filter H1B Sponsors: {config['JOB_SEARCH']['filter_h1b_sponsors']}")
    
    # Job Boards
    print("\n🌐 Job Boards:")
    print(f"  - LinkedIn: {'✅' if config['JOB_BOARDS']['linkedin'] else '❌'}")
    print(f"  - Indeed: {'✅' if config['JOB_BOARDS']['indeed'] else '❌'}")
    print(f"  - ZipRecruiter: {'✅' if config['JOB_BOARDS']['ziprecruiter'] else '❌'}")
    
    # LinkedIn Filters
    if config['JOB_BOARDS']['linkedin']:
        print("\n🔍 LinkedIn Filters:")
        linkedin_filters = config['JOB_SEARCH'].get('linkedin_filters', {})
        print(f"  - Sort By: {linkedin_filters.get('sort_by', 'Most Recent')}")
        print(f"  - Date Posted: {linkedin_filters.get('date_posted', 'Past Week')}")
        print(f"  - Experience Levels: {', '.join(linkedin_filters.get('experience_levels', ['Entry Level', 'Associate', 'Internship']))}")
        print(f"  - Job Types: {', '.join(linkedin_filters.get('job_types', ['Internship', 'Full Time']))}")
        print(f"  - Remote Options: {', '.join(linkedin_filters.get('remote_options', ['On-site', 'Remote', 'Hybrid']))}")
        print(f"  - Easy Apply Only: {'✅' if linkedin_filters.get('easy_apply_only', True) else '❌'}")
        print(f"  - Has Verifications: {'✅' if linkedin_filters.get('has_verifications', True) else '❌'}")
        print(f"  - Min Salary: ${linkedin_filters.get('min_salary', 60000)}+")
    
    # Application Settings
    print("\n📝 Application Settings:")
    print(f"  - Customize Resume: {'✅' if config['APPLICATION']['customize_resume'] else '❌'}")
    print(f"  - Customize Cover Letter: {'✅' if config['APPLICATION']['customize_cover_letter'] else '❌'}")
    print(f"  - Follow Up Days: {config['APPLICATION']['follow_up_days']}")
    print(f"  - Personalize to Hiring Manager: {'✅' if config['APPLICATION']['personalize_to_hiring_manager'] else '❌'}")
    
    # Browser Settings
    print("\n🌐 Browser Settings:")
    print(f"  - Headless Mode: {'✅' if config['BROWSER']['headless'] else '❌'}")
    print(f"  - Timeout: {config['BROWSER']['timeout']} seconds")
    
    print("\n- Human-like behavior is enabled to improve application success rates")
    print("- System will simulate natural typing, scrolling, and interaction patterns")
    print("- Random pauses and variations are added to mimic human decision making")
    
    print("\n📂 Data Folder: data_folder/")
    print(f"📄 Log File: {config['LOGGING']['log_file']}")
    print("\n")

# Main function
def main():
    """Main function to run the job application process."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='AI Job Application Assistant')
    
    # Job search parameters
    parser.add_argument('--job-titles', nargs='+', help='Job titles to search for')
    parser.add_argument('--locations', nargs='+', help='Locations to search in')
    parser.add_argument('--keywords', nargs='+', help='Keywords to include in job search')
    parser.add_argument('--exclude-keywords', nargs='+', help='Keywords to exclude from job search')
    parser.add_argument('--max-applications', type=int, help='Maximum number of applications per day')
    parser.add_argument('--h1b-only', action='store_true', help='Only apply to jobs from companies that sponsor H1B visas')
    
    # Job boards
    parser.add_argument('--linkedin', action='store_true', help='Search for jobs on LinkedIn')
    parser.add_argument('--indeed', action='store_true', help='Search for jobs on Indeed')
    parser.add_argument('--ziprecruiter', action='store_true', help='Search for jobs on ZipRecruiter')
    
    # Browser settings
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    
    # Config file
    parser.add_argument('--config', default='config.py', help='Path to configuration file')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Print welcome message
    print_welcome_message()
    
    # Create necessary directories
    create_directories()
    
    # Load configuration
    config = load_config(args.config)
    
    # Update configuration with command line arguments
    config = update_config_with_args(config, args)
    
    # Set up logging
    setup_logging(config)
    
    # Get logger
    logger = logging.getLogger(__name__)
    
    # Print configuration summary
    print_config_summary(config)
    
    # Check if required directories and files exist
    resume_path = config['USER_INFO'].get('resume_path', '')
    if not resume_path or not os.path.exists(resume_path):
        logger.error(f"Resume file not found: {resume_path}")
        print(f"\n❌ Error: Resume file not found: {resume_path}")
        print("Please update the 'resume_path' in config.py with the path to your resume file.")
        sys.exit(1)
    
    # Check LinkedIn credentials if LinkedIn is enabled
    if config['JOB_BOARDS']['linkedin']:
        linkedin_username = config.get('LINKEDIN', {}).get('username', '')
        linkedin_password = config.get('LINKEDIN', {}).get('password', '')
        
        if not linkedin_username or not linkedin_password:
            logger.error("LinkedIn credentials not provided")
            print("\n❌ Error: LinkedIn credentials not provided")
            print("Please update the 'LINKEDIN' section in config.py with your LinkedIn username and password.")
            sys.exit(1)
    
    # Initialize job scrapers
    job_listings = []
    
    # Scrape LinkedIn jobs
    if config['JOB_BOARDS']['linkedin']:
        print("\n🔍 Scraping LinkedIn jobs...")
        linkedin_scraper = LinkedInScraper(config)
        linkedin_jobs = linkedin_scraper.scrape_jobs()
        job_listings.extend(linkedin_jobs)
        print(f"✅ Found {len(linkedin_jobs)} jobs on LinkedIn")
    
    # Scrape Indeed jobs
    if config['JOB_BOARDS']['indeed']:
        print("\n🔍 Scraping Indeed jobs...")
        indeed_scraper = IndeedScraper(config)
        indeed_jobs = indeed_scraper.scrape_jobs()
        job_listings.extend(indeed_jobs)
        print(f"✅ Found {len(indeed_jobs)} jobs on Indeed")
    
    # Scrape ZipRecruiter jobs
    if config['JOB_BOARDS']['ziprecruiter']:
        print("\n🔍 Scraping ZipRecruiter jobs...")
        ziprecruiter_scraper = ZipRecruiterScraper(config)
        ziprecruiter_jobs = ziprecruiter_scraper.scrape_jobs()
        job_listings.extend(ziprecruiter_jobs)
        print(f"✅ Found {len(ziprecruiter_jobs)} jobs on ZipRecruiter")
    
    # Check if any jobs were found
    if not job_listings:
        logger.error("No jobs found")
        print("\n❌ Error: No jobs found")
        print("Please check your job search parameters and try again.")
        sys.exit(1)
    
    print(f"\n✅ Found a total of {len(job_listings)} jobs")
    
    # Always filter jobs for H1B sponsors
    print("\n🔍 Filtering jobs for H1B sponsors...")
    h1b_checker = H1BChecker()
    h1b_jobs = []

    for job in job_listings:
        company_name = job.get('company_name', '')
        job_description = job.get('description', '')
        
        # Check both company name and job description for H1B sponsorship
        if h1b_checker.is_h1b_sponsor(company_name, job_description) or h1b_checker.check_job_for_h1b_keywords(job):
            job['sponsors_h1b'] = True
            h1b_jobs.append(job)

    job_listings = h1b_jobs
    print(f"✅ Found {len(job_listings)} jobs from H1B sponsors")

    # If no H1B sponsors found, exit
    if not job_listings:
        logger.error("No H1B sponsoring jobs found")
        print("\n❌ Error: No H1B sponsoring jobs found")
        print("Please check your job search parameters or try again later.")
        sys.exit(1)
    
    # Filter jobs for Easy Apply if using LinkedIn
    if config['JOB_BOARDS']['linkedin']:
        easy_apply_jobs = [job for job in job_listings if job.get('easy_apply', False)]
        
        if easy_apply_jobs:
            job_listings = easy_apply_jobs
            print(f"\n✅ Found {len(job_listings)} Easy Apply jobs")
        else:
            logger.warning("No Easy Apply jobs found")
            print("\n⚠️ Warning: No Easy Apply jobs found")
            print("Proceeding with all jobs...")
    
    # Sort jobs by match score if resume matcher is enabled
    if config['APPLICATION']['customize_resume']:
        print("\n🔍 Matching jobs to your resume...")
        resume_matcher = ResumeMatcher(config)
        
        for job in job_listings:
            match_score = resume_matcher.calculate_match_score(job)
            job['match_score'] = match_score
        
        # Sort jobs by match score (highest first)
        job_listings = sorted(job_listings, key=lambda x: x.get('match_score', 0), reverse=True)
        
        # Filter jobs by match score threshold
        match_threshold = config['AI_SETTINGS'].get('resume_match_threshold', 0.7)
        matching_jobs = [job for job in job_listings if job.get('match_score', 0) >= match_threshold]
        
        if matching_jobs:
            job_listings = matching_jobs
            print(f"✅ Found {len(job_listings)} jobs matching your resume (score >= {match_threshold})")
        else:
            logger.warning(f"No jobs found with match score >= {match_threshold}")
            print(f"\n⚠️ Warning: No jobs found with match score >= {match_threshold}")
            print("Proceeding with all jobs...")
    
    # Limit the number of applications
    max_applications = config['JOB_SEARCH']['max_applications_per_day']
    if len(job_listings) > max_applications:
        job_listings = job_listings[:max_applications]
        print(f"\n⚠️ Limiting to {max_applications} applications per day")
    
    # Save job listings to file
    jobs_file = f"data_folder/jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(jobs_file, 'w', encoding='utf-8') as f:
        json.dump(job_listings, f, indent=2)
    
    print(f"\n✅ Saved job listings to {jobs_file}")
    
    # Ask for confirmation before applying
    print(f"\n🚀 Ready to apply to {len(job_listings)} jobs")
    confirmation = input("Do you want to proceed with applying to these jobs? (y/n): ")
    
    if confirmation.lower() != 'y':
        print("\n❌ Application process cancelled")
        sys.exit(0)
    
    # Initialize job applier
    job_applier = JobApplier(config)
    
    # Initialize cover letter generator if enabled
    if config['APPLICATION']['customize_cover_letter']:
        cover_letter_generator = CoverLetterGenerator(config)
    
    # Apply to jobs
    print("\n🚀 Starting job application process...")
    successful_applications = 0
    
    for i, job in enumerate(job_listings, 1):
        print(f"\n[{i}/{len(job_listings)}] Applying to: {job.get('title', '')} at {job.get('company_name', '')}")
        
        # Generate custom cover letter if enabled
        cover_letter_path = None
        if config['APPLICATION']['customize_cover_letter']:
            print("  Generating custom cover letter...")
            cover_letter_path = cover_letter_generator.generate_cover_letter(job)
        
        # Apply to job
        success = job_applier.apply(job, config['USER_INFO']['resume_path'], cover_letter_path)
        
        if success:
            successful_applications += 1
            print(f"  ✅ Successfully applied!")
        else:
            print(f"  ❌ Failed to apply")
        
        # Add random delay between applications
        if i < len(job_listings):
            delay = random.randint(30, 60)
            print(f"  Waiting {delay} seconds before next application...")
            time.sleep(delay)
    
    # Print summary
    print("\n📊 Application Summary:")
    print(f"  - Total Jobs Found: {len(job_listings)}")
    print(f"  - Successfully Applied: {successful_applications}")
    print(f"  - Failed Applications: {len(job_listings) - successful_applications}")
    
    print("\n✅ Job application process completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        logging.exception("Unhandled exception")
        sys.exit(1)

