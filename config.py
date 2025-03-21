# Configuration for the Jobs Applier AI Agent

# User Information
USER_INFO = {
    "name": "Bala Prasanna Gopal Volisetty",
    "email": "bv1459@rit.edu",
    "phone": "+1 (585)-733-8040",
    "linkedin": "https://linkedin.com/bala-prasanna-gopal-volisetty-2001",
    "github": "",  # Add your GitHub if you have one
    "portfolio": "",  # Add your portfolio website if you have one
    "resume_path": "data_folder/resume.pdf",  # Path to your resume
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
        "Information Security Analyst"
    ],
    "locations": ["Rochester, NY", "Remote", "New York, NY", "Boston, MA"],  # Add more locations if interested
    "experience_level": "Entry Level",  # Options: "Entry Level", "Mid Level", "Senior Level"
    "job_type": "Full Time",  # Options: "Full Time", "Part Time", "Contract", "Internship"
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
        "Docker"
    ],
    "exclude_keywords": [
        "Senior", 
        "Lead", 
        "2 years", 
        "Principal", 
        "Director", 
        "Manager",
        "15+ years"
    ],
    "min_salary": 65000,  # Minimum salary to consider
    "max_applications_per_day": 15,  # Maximum applications to submit per day
    "filter_h1b_sponsors": True,  # Filter for H1B visa sponsors
}

# Job Boards to Search
JOB_BOARDS = {
    "linkedin": True,
    "indeed": False,
    "glassdoor": False,
    "monster": False,
    "ziprecruiter": False,
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
    "resume_match_threshold": 0.7,  # Minimum match score to apply (0.0 to 1.0)
    "api_key": "your-openai-api-key",  # Your OpenAI API key
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
    "smtp_server": "smtp.gmail.com",  # Update if using a different email provider
    "smtp_port": 587,
    "email_address": "bv1459@rit.edu",  # Your email address
    "email_password": "",  # Your email password or app password
}

# LinkedIn Settings (for finding hiring managers)
LINKEDIN = {
    "username": "bv1459@rit.edu",  # Your LinkedIn email
    "password": "",  # Your LinkedIn password
}

# Resume Customization Emphasis
RESUME_EMPHASIS = {
    "highlight_skills": [
        "AWS Security",
        "Cloud Security",
        "SIEM",
        "Splunk",
        "Chronicle Security",
        "Python",
        "Terraform",
        "IAM",
        "CloudTrail",
        "GuardDuty",
        "Security Hub",
        "Kubernetes",
        "Docker",
        "NIST 800-171",
        "NIST 800-53"
    ],
    "highlight_certifications": [
        "eJPT",
        "CompTIA CySA+",
        "Microsoft Cybersecurity Analyst Professional Certificate",
        "API Security Fundamentals",
        "INE Certified Cloud Associate",
        "AWS Certified Cloud Practitioner"
    ],
    "highlight_projects": [
        "SOC Incident Detection & Threat Hunting",
        "Cloud Security Hardening & Threat Detection",
        "SIEM & Incident Response Optimization"
    ]
}

# Cover Letter Customization
COVER_LETTER_EMPHASIS = {
    "key_strengths": [
        "Cloud security expertise with AWS",
        "SIEM implementation and optimization",
        "Security automation with Python and Terraform",
        "Incident response and threat hunting",
        "Compliance knowledge (NIST frameworks)"
    ],
    "career_goals": "To leverage my cybersecurity and cloud security expertise in a challenging role that allows me to protect critical infrastructure while continuing to grow my skills in cloud security, automation, and threat detection.",
    "education_highlight": "MS in Cybersecurity from Rochester Institute of Technology with coursework in Advanced Network Security, Web Server Application Security Audits, and Cybersecurity Analytics."
}