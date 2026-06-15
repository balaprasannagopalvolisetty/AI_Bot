import logging
import os
import time
import random
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CoverLetterGenerator:
    """
    Generates custom cover letters for job applications.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the cover letter generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.user_info = config.get('USER_INFO', {})
        self.ai_settings = config.get('AI_SETTINGS', {})
        
        # Create cover letters directory if it doesn't exist
        os.makedirs("data_folder/cover_letters", exist_ok=True)
    
    def generate_cover_letter(self, job: Dict[str, Any]) -> Optional[str]:
        """
        Generate a custom cover letter for a job.
        
        Args:
            job: Job dictionary
            
        Returns:
            Path to generated cover letter file, or None if generation failed
        """
        try:
            # Get job information
            job_title = job.get('title', '')
            company_name = job.get('company_name', '')
            job_description = job.get('description', '')
            
            if not job_title or not company_name:
                logger.error("Job title or company name missing")
                return None
            
            # Check if we have a template cover letter
            template_path = self.user_info.get('cover_letter_template', '')
            
            if template_path and os.path.exists(template_path):
                # Use template to generate cover letter
                cover_letter_text = self._generate_from_template(template_path, job)
            else:
                # Generate cover letter from scratch
                cover_letter_text = self._generate_from_scratch(job)
            
            if not cover_letter_text:
                logger.error("Failed to generate cover letter text")
                return None
            
            # Save cover letter to file
            file_name = f"cover_letter_{company_name.replace(' ', '_')}_{int(time.time())}.txt"
            file_path = os.path.join("data_folder/cover_letters", file_name)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cover_letter_text)
            
            logger.info(f"Generated cover letter for {job_title} at {company_name}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return None
    
    def _generate_from_template(self, template_path: str, job: Dict[str, Any]) -> str:
        """
        Generate cover letter from template.
        
        Args:
            template_path: Path to template file
            job: Job dictionary
            
        Returns:
            Generated cover letter text
        """
        try:
            # Read template
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Get job information
            job_title = job.get('title', '')
            company_name = job.get('company_name', '')
            hiring_manager_name = job.get('hiring_manager_name', '')
            
            # Get user information
            user_name = self.user_info.get('name', '')
            user_email = self.user_info.get('email', '')
            user_phone = self.user_info.get('phone', '')
            
            # Get current date
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Replace placeholders
            template = template.replace("[DATE]", current_date)
            template = template.replace("[HIRING_MANAGER_NAME]", hiring_manager_name if hiring_manager_name else "Hiring Manager")
            template = template.replace("[COMPANY_NAME]", company_name)
            template = template.replace("[JOB_TITLE]", job_title)
            template = template.replace("[YOUR_NAME]", user_name)
            template = template.replace("[YOUR_EMAIL]", user_email)
            template = template.replace("[YOUR_PHONE]", user_phone)
            
            return template
            
        except Exception as e:
            logger.error(f"Error generating cover letter from template: {e}")
            return ""
    
    def _generate_from_scratch(self, job: Dict[str, Any]) -> str:
        """
        Generate cover letter from scratch.
        
        Args:
            job: Job dictionary
            
        Returns:
            Generated cover letter text
        """
        try:
            # Get job information
            job_title = job.get('title', '')
            company_name = job.get('company_name', '')
            job_description = job.get('description', '')
            hiring_manager_name = job.get('hiring_manager_name', '')
            
            # Get user information
            user_name = self.user_info.get('name', '')
            user_email = self.user_info.get('email', '')
            user_phone = self.user_info.get('phone', '')
            
            # Get current date
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Generate cover letter
            cover_letter = f"{current_date}\n\n"
            
            if hiring_manager_name:
                cover_letter += f"Dear {hiring_manager_name},\n\n"
            else:
                cover_letter += "Dear Hiring Manager,\n\n"
            
            # Introduction
            intro_options = [
                f"I am writing to express my interest in the {job_title} position at {company_name}. With my background and skills, I believe I would be a valuable addition to your team.",
                f"I am excited to apply for the {job_title} role at {company_name}. My experience and passion for this field make me a strong candidate for this position.",
                f"I was thrilled to see the opening for a {job_title} at {company_name}. My skills and experience align well with the requirements of this role."
            ]
            cover_letter += random.choice(intro_options) + "\n\n"
            
            # Body
            body_options = [
                f"Throughout my career, I have developed strong skills in [RELEVANT_SKILLS] that would be valuable in this role. I am particularly drawn to {company_name} because of your reputation for [COMPANY_STRENGTH].",
                f"My experience includes [RELEVANT_EXPERIENCE] which has prepared me well for the challenges of this position. I am impressed by {company_name}'s commitment to [COMPANY_VALUE].",
                f"I have a proven track record of [ACHIEVEMENT] that demonstrates my ability to excel as a {job_title}. I am particularly interested in joining {company_name} because of your innovative approach to [INDUSTRY_AREA]."
            ]
            cover_letter += random.choice(body_options) + "\n\n"
            
            # Closing
            closing_options = [
                f"I would welcome the opportunity to discuss how my background and skills would benefit {company_name}. Thank you for considering my application.",
                f"I am excited about the possibility of joining {company_name} and would appreciate the chance to further discuss my qualifications. Thank you for your time and consideration.",
                f"I look forward to the opportunity to further discuss how I can contribute to {company_name}'s continued success. Thank you for reviewing my application."
            ]
            cover_letter += random.choice(closing_options) + "\n\n"
            
            # Signature
            cover_letter += "Sincerely,\n\n"
            cover_letter += f"{user_name}\n"
            cover_letter += f"{user_email}\n"
            cover_letter += f"{user_phone}\n"
            
            return cover_letter
            
        except Exception as e:
            logger.error(f"Error generating cover letter from scratch: {e}")
            return ""