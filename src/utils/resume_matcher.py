import logging
import os
import re
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class ResumeMatcher:
    """
    Matches job descriptions to resumes.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the resume matcher.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.resume_text = self._load_resume()
        self.resume_keywords = self._extract_keywords(self.resume_text)
    
    def _load_resume(self) -> str:
        """
        Load resume text from file.
        
        Returns:
            Resume text
        """
        resume_path = self.config['USER_INFO'].get('resume_path', '')
        
        if not resume_path or not os.path.exists(resume_path):
            logger.error(f"Resume file not found: {resume_path}")
            return ""
        
        try:
            # Determine file type
            file_extension = os.path.splitext(resume_path)[1].lower()
            
            if file_extension == '.pdf':
                return self._extract_text_from_pdf(resume_path)
            elif file_extension == '.docx':
                return self._extract_text_from_docx(resume_path)
            elif file_extension == '.txt':
                with open(resume_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.error(f"Unsupported resume file format: {file_extension}")
                return ""
            
        except Exception as e:
            logger.error(f"Error loading resume: {e}")
            return ""
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(file_path)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        try:
            import docx2txt
            
            text = docx2txt.process(file_path)
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of keywords
        """
        if not text:
            return []
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split into words
        words = text.split()
        
        # Remove common words
        stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
            'when', 'where', 'how', 'from', 'to', 'by', 'for', 'with', 'about',
            'against', 'between', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
            'again', 'further', 'then', 'once', 'here', 'there', 'all', 'any', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
            'just', 'don', 'should', 'now', 'of', 'at', 'be', 'is', 'am', 'are', 'was',
            'were', 'has', 'have', 'had', 'do', 'does', 'did', 'doing', 'this', 'that',
            'these', 'those', 'i', 'me', 'my', 'mine', 'myself', 'you', 'your', 'yours',
            'yourself', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
            'it', 'its', 'itself', 'we', 'us', 'our', 'ours', 'ourselves', 'they', 'them',
            'their', 'theirs', 'themselves', 'who', 'whom', 'whose', 'which', 'what'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Add user-defined keywords
        user_keywords = self.config['JOB_SEARCH'].get('keywords', [])
        keywords.extend([keyword.lower() for keyword in user_keywords])
        
        # Remove duplicates
        keywords = list(set(keywords))
        
        return keywords
    
    def calculate_match_score(self, job: Dict[str, Any]) -> float:
        """
        Calculate match score between job and resume.
        
        Args:
            job: Job dictionary
            
        Returns:
            Match score (0.0 to 1.0)
        """
        if not job or not self.resume_keywords:
            return 0.0
        
        # Get job description
        job_description = job.get('description', '').lower()
        
        if not job_description:
            return 0.0
        
        # Count matching keywords
        matching_keywords = []
        
        for keyword in self.resume_keywords:
            if keyword in job_description:
                matching_keywords.append(keyword)
        
        # Calculate match score
        match_score = len(matching_keywords) / max(len(self.resume_keywords), 1)
        
        # Adjust score based on job title match
        job_title = job.get('title', '').lower()
        user_job_titles = [title.lower() for title in self.config['JOB_SEARCH'].get('job_titles', [])]
        
        title_match = False
        for user_title in user_job_titles:
            if user_title in job_title:
                title_match = True
                break
        
        if title_match:
            match_score += 0.1
        
        # Adjust score based on location match
        job_location = job.get('location', '').lower()
        user_locations = [location.lower() for location in self.config['JOB_SEARCH'].get('locations', [])]
        
        location_match = False
        for user_location in user_locations:
            if user_location in job_location:
                location_match = True
                break
        
        if location_match:
            match_score += 0.1
        
        # Adjust score based on excluded keywords
        excluded_keywords = [keyword.lower() for keyword in self.config['JOB_SEARCH'].get('exclude_keywords', [])]
        
        for keyword in excluded_keywords:
            if keyword in job_description or keyword in job_title:
                match_score -= 0.2
        
        # Ensure score is between 0.0 and 1.0
        match_score = max(0.0, min(1.0, match_score))
        
        logger.info(f"Match score for {job.get('title', '')} at {job.get('company_name', '')}: {match_score:.2f}")
        
        return match_score