# Configuration for the Jobs Applier AI Agent

# User Information
USER_INFO = {
  "name": "Bala Prasanna Gopal Volisetty",
  "email": "bv1459@rit.edu",
  "phone": "+1 (585)-733-8040",
  "linkedin": "https://linkedin.com/bala-prasanna-gopal-volisetty-2001",
  "github": "https://github.com/balaprasannagopalvolisetty",
  "portfolio": "",
  "resume_path": "data_folder/resume.pdf",
}

# Job Search Parameters
JOB_SEARCH = {
  "job_titles": [
    "Cybersecurity Engineer", 
    "Cloud Security Engineer", 
    "Security Analyst", 
    "SOC Analyst", 
    "Security Operations Engineer", 
    "AWS Security Engineer", 
    "Cloud Security Analyst", 
    "Information Security Analyst",
    "Junior Security Engineer",
    "Associate Security Engineer",
    "Security Operations Specialist",
    "Cloud Security Specialist"
  ],
  "locations": [
    "Rochester, NY", 
    "Remote", 
    "New York, NY", 
    "Boston, MA"
  ],
  "experience_level": "Entry Level",  # Options: "Entry Level", "Mid Level", "Senior Level"
  "job_type": ["Full Time", "Internship"], # Options: "Full Time", "Part Time", "Contract", 
  "keywords": [
    "AWS Security", 
    "Cloud Security", 
    "SIEM", 
    "Incident Response", 
    "Python", 
    "Terraform", 
    "Security Automation", 
    "Splunk", 
    "Chronicle Security", 
    "IAM", 
    "GuardDuty", 
    "CloudTrail", 
    "Kubernetes", 
    "Docker",
    "Security Hub",
    "Threat Intelligence",
    "Anomaly Detection",
    "Palo Alto",
    "Fortinet",
    "IDS/IPS",
    "Zeek",
    "Sysmon",
    "Ansible",
    "Bash",
    "Serverless",
    "NIST 800-171",
    "NIST 800-53",
    "Cloud Security Audits",
    "eJPT",
    "CompTIA CySA+",
    "AWS Certified"
  ],
  "exclude_keywords": [
    "Senior", 
    "Lead", 
    "Principal", 
    "Director", 
    "Manager", 
    "5+ years",
    "7+ years",
    "10+ years",
    "15+ years",
    "CISSP required",
    "CISM required",
    "OSCP required"
  ],
  "min_salary": 70000,
  "max_applications_per_day": 20,
  "filter_h1b_sponsors": True,  # Always filter for companies that sponsor H1B visas
  "linkedin_filters": {
    "sort_by": "Most Recent",
    "date_posted": "Past Week",
    "experience_levels": ["Entry Level", "Associate", "Internship"],
    "job_types": ["Full Time"],
    "remote_options": ["On-site", "Remote", "Hybrid"],
    "easy_apply_only": True,
    "has_verifications": True,
    "min_salary": 70000
  }
}

# Job Boards to Search
JOB_BOARDS = {
  "linkedin": True,
  "indeed": True,
  "glassdoor": False,
  "monster": False,
  "ziprecruiter": True,
}

# Application Customization
APPLICATION = {
  "customize_resume": True,  # Automatically tailor resume to job description
  "customize_cover_letter": True,  # Generate custom cover letter for each application
  "follow_up_days": 7,  # Number of days to wait before sending follow-up email
  "personalize_to_hiring_manager": True,  # Personalize application to hiring manager if found
}

# AI Settings
AI_SETTINGS = {
  "model": "gpt-4",  # Options: "gpt-3.5-turbo", "gpt-4"
  "resume_match_threshold": 0.65,  # Minimum match score to apply (0.0 to 1.0)
  "api_key": "",  # Your OpenAI API key
}

# Browser Settings
BROWSER = {
  "headless": False,  # Run browser in headless mode (no UI)
  "timeout": 30,  # Seconds to wait for page elements
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}

# Logging Settings
LOGGING = {
  "level": "INFO",  # Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
  "log_file": "data_folder/application_log.txt",
}

# Email Settings (for follow-ups)
EMAIL = {
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "email_address": "",  # Your email address
  "email_password": "",  # Your email password or app password
}

# LinkedIn Settings (for finding hiring managers)
LINKEDIN = {
  "username": "",  # Your LinkedIn username/email
  "password": "",  # Your LinkedIn password
}