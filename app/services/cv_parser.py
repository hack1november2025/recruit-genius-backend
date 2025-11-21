"""CV parsing service for extracting information from PDF and DOCX files."""
import re
from pathlib import Path
from typing import Dict, List, Optional
from pypdf import PdfReader
from docx import Document
from app.core.errors import CVParsingError
from app.core.logging import cv_parser_logger


class CVParserService:
    """Service for parsing CV files and extracting structured information."""
    
    # Common skills to detect (can be expanded)
    TECH_SKILLS = {
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node.js", "express", "django", "flask", "fastapi", "spring", "springboot",
        "sql", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes",
        "aws", "azure", "gcp", "git", "ci/cd", "agile", "scrum", "rest", "graphql",
        "html", "css", "sass", "webpack", "npm", "yarn", "linux", "bash", "terraform"
    }
    
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
            
        Raises:
            CVParsingError: If extraction fails
        """
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            cv_parser_logger.info(f"Extracted {len(text)} characters from PDF")
            return text.strip()
        except Exception as e:
            cv_parser_logger.error(f"Failed to extract text from PDF: {str(e)}")
            raise CVParsingError(f"Failed to parse PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_path: Path) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
            
        Raises:
            CVParsingError: If extraction fails
        """
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            cv_parser_logger.info(f"Extracted {len(text)} characters from DOCX")
            return text.strip()
        except Exception as e:
            cv_parser_logger.error(f"Failed to extract text from DOCX: {str(e)}")
            raise CVParsingError(f"Failed to parse DOCX: {str(e)}")
    
    def extract_text(self, file_path: Path) -> str:
        """
        Extract text from PDF or DOCX file.
        
        Args:
            file_path: Path to CV file
            
        Returns:
            Extracted text
            
        Raises:
            CVParsingError: If file type not supported or extraction fails
        """
        suffix = file_path.suffix.lower()
        
        if suffix == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif suffix in [".docx", ".doc"]:
            return self.extract_text_from_docx(file_path)
        else:
            raise CVParsingError(f"Unsupported file type: {suffix}")
    
    def extract_name(self, text: str) -> Optional[str]:
        """
        Extract candidate name from CV text.
        Assumes name is in the first few lines.
        
        Args:
            text: CV text
            
        Returns:
            Extracted name or None
        """
        lines = text.split("\n")
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line.split()) <= 4 and len(line) < 50:
                # Simple heuristic: likely a name if 1-4 words and not too long
                if not any(char.isdigit() for char in line):
                    cv_parser_logger.debug(f"Extracted name: {line}")
                    return line
        return None
    
    def extract_email(self, text: str) -> Optional[str]:
        """
        Extract email address from CV text.
        
        Args:
            text: CV text
            
        Returns:
            Extracted email or None
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        if matches:
            cv_parser_logger.debug(f"Extracted email: {matches[0]}")
            return matches[0]
        return None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """
        Extract phone number from CV text.
        
        Args:
            text: CV text
            
        Returns:
            Extracted phone or None
        """
        # Common phone patterns
        phone_patterns = [
            r'\+?1?\d{9,15}',  # International format
            r'\(\d{3}\)\s*\d{3}-\d{4}',  # (123) 456-7890
            r'\d{3}-\d{3}-\d{4}',  # 123-456-7890
            r'\d{3}\.\d{3}\.\d{4}',  # 123.456.7890
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                phone = matches[0]
                # Clean up
                phone = re.sub(r'[^\d+]', '', phone)
                cv_parser_logger.debug(f"Extracted phone: {phone}")
                return phone
        return None
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract technical skills from CV text.
        
        Args:
            text: CV text
            
        Returns:
            List of detected skills
        """
        text_lower = text.lower()
        detected_skills = []
        
        for skill in self.TECH_SKILLS:
            if skill in text_lower:
                detected_skills.append(skill.title())
        
        cv_parser_logger.info(f"Detected {len(detected_skills)} skills")
        return detected_skills
    
    def extract_experience_years(self, text: str) -> Optional[int]:
        """
        Extract years of experience from CV text.
        
        Args:
            text: CV text
            
        Returns:
            Years of experience or None
        """
        # Look for patterns like "5 years", "5+ years", etc.
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience:\s*(\d+)\+?\s*years?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                years = int(matches[0])
                cv_parser_logger.debug(f"Extracted experience: {years} years")
                return years
        
        # Try to estimate from date ranges
        date_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(date_pattern, text)
        if len(years) >= 2:
            # Rough estimate: difference between first and last year mentioned
            years_int = [int(y) for y in years]
            experience = max(years_int) - min(years_int)
            if experience > 0 and experience < 50:  # Sanity check
                cv_parser_logger.debug(f"Estimated experience: {experience} years")
                return experience
        
        return None
    
    def parse_cv(self, file_path: Path) -> Dict:
        """
        Parse CV file and extract all available information.
        
        Args:
            file_path: Path to CV file
            
        Returns:
            Dictionary with extracted information
            
        Raises:
            CVParsingError: If parsing fails
        """
        try:
            # Extract text
            text = self.extract_text(file_path)
            
            # Extract fields
            result = {
                "resume_text": text,
                "name": self.extract_name(text),
                "email": self.extract_email(text),
                "phone": self.extract_phone(text),
                "skills": self.extract_skills(text),
                "experience_years": self.extract_experience_years(text),
            }
            
            cv_parser_logger.info("Successfully parsed CV")
            return result
            
        except Exception as e:
            cv_parser_logger.error(f"Failed to parse CV: {str(e)}")
            raise CVParsingError(f"Failed to parse CV: {str(e)}")
