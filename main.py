import os
import logging
import argparse
import time
from datetime import datetime
from typing import Dict, List, Any

# Import configuration
import config

# Import modules
from src.job_boards.linkedin_scraper import LinkedInScraper
from src.job_boards.indeed_scraper import IndeedScraper
from src.job_boards.ziprecruiter_scraper import ZipRecruiterScraper
from src.filters.job_filter import JobFilter
from src.application.resume_customizer import ResumeCustomizer
from src.application.cover_letter_generator import CoverLetterGenerator
from src.application.job_applier import JobApplier
from src.utils.logger import setup_logger
from src.utils.h1b_sponsor_checker import H1BSponsorChecker
from src.utils.company_contact_finder import CompanyContactFinder

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='AI Job Application Assistant')
    parser.add_argument('--h1b-only', action='store_true',
                        help='Apply only to companies that sponsor H1B visas')
    parser.add_argument('--list-top-sponsors', action='store_true',
                        help='List top H1B sponsors and exit')
    parser.add_argument('--check-company', type=str,
                        help='Check if a specific company sponsors H1B visas')
    parser.add_argument('--find-contacts', type=str,
                        help='Find hiring manager contacts for a company')
    parser.add_argument('--job-titles', type=str, nargs='+',
                        help='Job titles to search for')
    parser.add_argument('--locations', type=str, nargs='+',
                        help='Locations to search in')
    parser.add_argument('--max-applications', type=int,
                        help='Maximum number of applications to submit')
    parser.add_argument('--supervised', action='store_true',
                        help='Run in supervised mode (asks for confirmation before submitting applications)')
    return parser.parse_args()

def main():
    """Main function to run the job application process."""
    # Parse arguments
    args = parse_arguments()
    
    # Set up logging
    setup_logger(config.LOGGING['level'], config.LOGGING['log_file'])
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Jobs Applier AI Agent")
    
    # Display welcome message and limitations
    print("\n" + "="*80)
    print("Welcome to the AI Job Application Assistant!")
    print("="*80)
    print("\nIMPORTANT NOTES:")
    print("1. This tool works best with LinkedIn 'Easy Apply' jobs")
    print("2. Some applications may require manual intervention")
    print("3. LinkedIn may present CAPTCHA challenges")
    print("4. The tool cannot reliably answer custom screening questions")
    print("\nRecommendations:")
    print("- Start with supervision to see how it works")
    print("- Begin with a small number of applications (3-5)")
    print("- Keep max applications per day to a reasonable number (10-15)")
    print("- Be ready to intervene for complex applications")
    print("- Check your LinkedIn account to verify submissions")
    print("="*80 + "\n")
    
    # Handle special commands
    if args.list_top_sponsors:
        h1b_checker = H1BSponsorChecker()
        top_sponsors = h1b_checker.get_top_h1b_sponsors(limit=50)
        print("\nTop 50 H1B Visa Sponsors:")
        for i, sponsor in enumerate(top_sponsors, 1):
            print(f"{i}. {sponsor}")
        return
    
    if args.check_company:
        h1b_checker = H1BSponsorChecker()
        is_sponsor = h1b_checker.check_h1b_sponsorship(args.check_company)
        if is_sponsor:
            print(f"\n✅ {args.check_company} is known to sponsor H1B visas.")
        else:
            print(f"\n❌ {args.check_company} is not known to sponsor H1B visas or no data found.")
        return
    
    if args.find_contacts:
        contact_finder = CompanyContactFinder(config)
        mock_job = {
            'company_name': args.find_contacts,
            'title': 'Software Engineer',  # Default title
            'location': args.locations[0] if args.locations else 'Remote'
        }
        contacts = contact_finder.find_hiring_manager(mock_job)
        
        print(f"\nContacts for {args.find_contacts}:")
        print(f"Company Domain: {contacts.get('company_domain', 'Not found')}")
        print(f"Hiring Manager: {contacts.get('hiring_manager_name', 'Not found')}")
        print(f"Title: {contacts.get('hiring_manager_title', 'Not found')}")
        print(f"Email: {contacts.get('hiring_manager_email', 'Not found')}")
        print(f"LinkedIn: {contacts.get('hiring_manager_linkedin', 'Not found')}")
        
        if contacts.get('alternative_contacts'):
            print("\nAlternative Contacts:")
            for i, contact in enumerate(contacts['alternative_contacts'], 1):
                print(f"{i}. {contact.get('name', 'Unknown')} - {contact.get('title', 'Unknown')} - {contact.get('email', 'Unknown')}")
        
        return
    
    # Override config settings if specified in command line
    if args.h1b_only:
        config.JOB_SEARCH['filter_h1b_sponsors'] = True
        logger.info("H1B sponsorship filter enabled via command line")
    
    if args.job_titles:
        config.JOB_SEARCH['job_titles'] = args.job_titles
        logger.info(f"Job titles set to: {args.job_titles}")
    
    if args.locations:
        config.JOB_SEARCH['locations'] = args.locations
        logger.info(f"Locations set to: {args.locations}")
    
    if args.max_applications:
        config.JOB_SEARCH['max_applications_per_day'] = args.max_applications
        logger.info(f"Max applications set to: {args.max_applications}")
    
    # Initialize job filter
    job_filter = JobFilter(config.JOB_SEARCH)
    
    # Initialize job scrapers
    scrapers = []
    if config.JOB_BOARDS['linkedin']:
        scrapers.append(LinkedInScraper(config))
    if config.JOB_BOARDS['indeed']:
        scrapers.append(IndeedScraper(config))
    if config.JOB_BOARDS['ziprecruiter']:
        scrapers.append(ZipRecruiterScraper(config))
    
    # Initialize contact finder
    contact_finder = CompanyContactFinder(config)
    
    # Collect job listings
    all_jobs = []
    for scraper in scrapers:
        jobs = scraper.scrape_jobs()
        all_jobs.extend(jobs)
    
    logger.info(f"Collected {len(all_jobs)} job listings from all sources")
    
    # Filter jobs
    filtered_jobs = job_filter.filter_jobs(all_jobs)
    
    logger.info(f"Filtered down to {len(filtered_jobs)} matching jobs")
    
    # Initialize application tools
    resume_customizer = ResumeCustomizer(config)
    cover_letter_generator = CoverLetterGenerator(config)
    job_applier = JobApplier(config)
    
    # Set supervised mode if specified
    supervised_mode = args.supervised
    if supervised_mode:
        logger.info("Running in supervised mode - will ask for confirmation before submitting applications")
        print("\nRunning in SUPERVISED MODE - you will be asked to confirm each application before submission")
    
    # Apply to jobs
    applications_today = 0
    max_applications = config.JOB_SEARCH['max_applications_per_day']
    
    for job in filtered_jobs:
        if applications_today >= max_applications:
            logger.info(f"Reached maximum applications for today ({max_applications})")
            break
        
        # Find hiring manager contact information
        logger.info(f"Finding hiring manager contact for {job['company_name']}")
        contact_info = contact_finder.find_hiring_manager(job)
        
        # Add contact info to job
        job['hiring_manager_name'] = contact_info.get('hiring_manager_name', '')
        job['hiring_manager_email'] = contact_info.get('hiring_manager_email', '')
        job['hiring_manager_title'] = contact_info.get('hiring_manager_title', '')
        job['company_domain'] = contact_info.get('company_domain', '')
        
        # Display job information
        print("\n" + "-"*80)
        print(f"Job: {job.get('title', 'Unknown Title')}")
        print(f"Company: {job.get('company_name', 'Unknown Company')}")
        print(f"Location: {job.get('location', 'Unknown Location')}")
        print(f"H1B Sponsor: {'Yes' if job.get('sponsors_h1b', False) else 'Unknown'}")
        if job.get('hiring_manager_name'):
            print(f"Hiring Manager: {job.get('hiring_manager_name')} ({job.get('hiring_manager_title', 'Unknown Title')})")
            if job.get('hiring_manager_email'):
                print(f"Contact: {job.get('hiring_manager_email')}")
        print("-"*80)
        
        # Customize resume if enabled - only modifies skills and projects sections
        if config.APPLICATION['customize_resume']:
            logger.info(f"Customizing skills and projects in resume for {job['company_name']}")
            custom_resume_path = resume_customizer.customize(job)
        else:
            custom_resume_path = config.USER_INFO['resume_path']
        
        # Generate cover letter if enabled - now with enhanced AI-powered personalization
        if config.APPLICATION['customize_cover_letter']:
            logger.info(f"Generating AI-powered cover letter for {job['company_name']}")
            cover_letter_path = cover_letter_generator.generate(job)
        else:
            cover_letter_path = None
        
        # Ask for confirmation in supervised mode
        proceed = True
        if supervised_mode:
            response = input("\nDo you want to apply to this job? (y/n): ").strip().lower()
            proceed = response == 'y' or response == 'yes'
        
        if proceed:
            # Apply to job
            logger.info(f"Applying to {job.get('title', '')} at {job['company_name']}")
            success = job_applier.apply(job, custom_resume_path, cover_letter_path)
            
            if success:
                applications_today += 1
                h1b_status = "✅ Sponsors H1B" if job.get('sponsors_h1b', False) else ""
                contact_status = f"📧 Contact: {job.get('hiring_manager_name', 'Unknown')}" if job.get('hiring_manager_name') else ""
                logger.info(f"Successfully applied to job at {job['company_name']} {h1b_status} {contact_status} ({applications_today}/{max_applications})")
                print(f"\n✅ Successfully applied to {job.get('title', '')} at {job['company_name']}")
            else:
                logger.warning(f"Failed to apply to job at {job['company_name']}")
                print(f"\n❌ Failed to apply to {job.get('title', '')} at {job['company_name']}")
        else:
            logger.info(f"Skipped application to {job['company_name']} based on user input")
            print(f"\nSkipped application to {job.get('title', '')} at {job['company_name']}")
    
    logger.info(f"Applied to {applications_today} jobs today")
    logger.info("Jobs Applier AI Agent completed successfully")
    
    print("\n" + "="*80)
    print(f"Application process complete! Applied to {applications_today} jobs.")
    print("="*80)

if __name__ == "__main__":
    main()

