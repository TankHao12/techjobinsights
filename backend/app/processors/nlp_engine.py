"""
NLP processing engine using spaCy for advanced text analysis
"""
import re
from typing import List, Dict, Set, Optional, Tuple
import logging
from datetime import datetime, date, timedelta

from ..core.logging import get_logger

logger = get_logger(__name__)

# Import spaCy - required dependency
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy loaded with en_core_web_sm model")
except OSError as e:
    logger.error("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
    raise RuntimeError("spaCy en_core_web_sm model is required. Please install it.") from e

class NLPEngine:
    """Advanced NLP processing for job descriptions"""

    def __init__(self):
        self.nlp = nlp

        # Comprehensive tech skills taxonomy
        # Updated: Removed non-tech business tools (Excel, PowerPoint, Visio)
        # Focus: Core programming & technology skills only
        self.tech_skills = {
            'programming_languages': {
                'python', 'javascript', 'java', 'c#', 'csharp', 'c++', 'cpp', 'php', 'ruby',
                'go', 'rust', 'scala', 'kotlin', 'swift', 'typescript', 'r', 'perl'
            },
            'web_frameworks': {
                'react', 'angular', 'vue', 'svelte', 'next.js', 'nuxt', 'gatsby',
                'django', 'flask', 'fastapi', 'spring', 'laravel', 'rails', 'express',
                'node.js', 'nodejs', 'asp.net', '.net', '.net core'
            },
            'databases': {
                'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 'elasticsearch',
                'cassandra', 'dynamodb', 'oracle', 'sqlite', 'neo4j', 'influxdb', 'sql server',
                'mariadb', 'db2', 'cosmos db'
            },
            'cloud_platforms': {
                'aws', 'azure', 'gcp', 'google cloud', 'digitalocean', 'heroku', 'vercel',
                'netlify', 'cloudflare', 'firebase'
            },
            'devops': {
                'docker', 'kubernetes', 'jenkins', 'gitlab', 'github', 'github actions', 'terraform',
                'ansible', 'chef', 'puppet', 'vagrant', 'helm', 'prometheus', 'grafana',
                'ci/cd', 'bitbucket'
            },
            'ai_ml': {
                'machine learning', 'artificial intelligence', 'deep learning', 'neural networks',
                'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn', 'sklearn',
                'opencv', 'nlp', 'computer vision', 'llm', 'data science', 'data engineering'
            },
            'mobile': {
                'ios', 'android', 'react native', 'flutter', 'xamarin', 'cordova', 'ionic',
                'swift', 'objective-c', 'kotlin'
            },
            'testing': {
                'selenium', 'cypress', 'jest', 'junit', 'pytest', 'mocha',
                'postman', 'swagger', 'api testing', 'test automation',
                'performance testing', 'load testing', 'jmeter', 'gatling',
                'testng', 'cucumber', 'appium'
            },
            'tools_and_methodologies': {
                'git', 'linux', 'bash', 'powershell', 'vim', 'vscode', 'intellij',
                'webpack', 'babel', 'npm', 'yarn', 'maven', 'gradle',
                'rest api', 'graphql', 'microservices', 'agile', 'scrum', 'kanban', 'jira'
            }
        }

        # Flatten all skills for quick lookup
        self.all_skills = set()
        for category_skills in self.tech_skills.values():
            self.all_skills.update(category_skills)

        # Display name mapping for proper capitalization and formatting
        self.skill_display_names = {
            # Programming Languages
            'r': 'R',
            'c#': 'C#',
            'csharp': 'C#',
            'c++': 'C++',
            'cpp': 'C++',
            
            # Acronyms & Short Forms
            'sql': 'SQL',
            'html': 'HTML',
            'css': 'CSS',
            'rest api': 'REST API',
            'aws': 'AWS',
            'gcp': 'GCP',
            'nlp': 'NLP',
            'ai': 'AI',
            'ml': 'ML',
            'ui': 'UI',
            'ux': 'UX',
            'llm': 'LLM',
            'npm': 'NPM',
            
            # Technologies
            'javascript': 'JavaScript',
            'typescript': 'TypeScript',
            'node.js': 'Node.js',
            'nodejs': 'Node.js',
            'next.js': 'Next.js',
            'nuxt': 'Nuxt.js',
            'vue': 'Vue.js',
            'react native': 'React Native',
            'asp.net': 'ASP.NET',
            '.net': '.NET',
            '.net core': '.NET Core',
            'graphql': 'GraphQL',
            
            # Cloud Platforms
            'azure': 'Azure',
            'google cloud': 'Google Cloud',
            'digitalocean': 'DigitalOcean',
            
            # Databases
            'mysql': 'MySQL',
            'postgresql': 'PostgreSQL',
            'postgres': 'PostgreSQL',
            'mongodb': 'MongoDB',
            'dynamodb': 'DynamoDB',
            'cosmos db': 'Cosmos DB',
            'sql server': 'SQL Server',
            'mariadb': 'MariaDB',
            'neo4j': 'Neo4j',
            'influxdb': 'InfluxDB',
            
            # Frameworks
            'django': 'Django',
            'flask': 'Flask',
            'fastapi': 'FastAPI',
            'spring': 'Spring',
            'laravel': 'Laravel',
            'express': 'Express.js',
            'rails': 'Rails',
            
            # DevOps & Tools
            'docker': 'Docker',
            'kubernetes': 'Kubernetes',
            'jenkins': 'Jenkins',
            'gitlab': 'GitLab',
            'github': 'GitHub',
            'github actions': 'GitHub Actions',
            'terraform': 'Terraform',
            'ansible': 'Ansible',
            'ci/cd': 'CI/CD',
            'git': 'Git',
            'linux': 'Linux',
            'bash': 'Bash',
            'powershell': 'PowerShell',
            
            # Testing
            'selenium': 'Selenium',
            'cypress': 'Cypress',
            'jest': 'Jest',
            'junit': 'JUnit',
            'pytest': 'Pytest',
            'mocha': 'Mocha',
            'postman': 'Postman',
            'cucumber': 'Cucumber',
            'api testing': 'API Testing',
            'test automation': 'Test Automation',
            
            # Mobile
            'ios': 'iOS',
            'android': 'Android',
            'swift': 'Swift',
            'kotlin': 'Kotlin',
            'react native': 'React Native',
            'flutter': 'Flutter',
            'xamarin': 'Xamarin',
            
            # AI/ML
            'tensorflow': 'TensorFlow',
            'pytorch': 'PyTorch',
            'pandas': 'Pandas',
            'numpy': 'NumPy',
            'scikit-learn': 'Scikit-learn',
            'sklearn': 'Scikit-learn',
            'opencv': 'OpenCV',
            'machine learning': 'Machine Learning',
            'artificial intelligence': 'Artificial Intelligence',
            'deep learning': 'Deep Learning',
            'computer vision': 'Computer Vision',
            'data science': 'Data Science',
            'data engineering': 'Data Engineering',
            
            # Methodologies
            'agile': 'Agile',
            'scrum': 'Scrum',
            'kanban': 'Kanban',
            'microservices': 'Microservices',
            'jira': 'Jira'
        }

        # Experience level patterns
        self.experience_patterns = {
            'senior': {'senior', 'sr', 'lead', 'principal', 'staff', 'expert'},
            'junior': {'junior', 'jr', 'graduate', 'entry', 'intern', 'trainee', 'associate'},
            'intermediate': {'intermediate', 'mid', 'mid-level', 'experienced'},
            'executive': {'director', 'head of', 'vp', 'chief', 'cto', 'ceo', 'manager'}
        }

        # Employment type patterns
        self.employment_patterns = {
            'full_time': {'full time', 'full-time', 'permanent', 'salary', 'salaried'},
            'part_time': {'part time', 'part-time', 'casual', 'flexible'},
            'contract': {'contract', 'contractor', 'freelance', 'temporary', 'temp', 'fixed term'},
            'internship': {'intern', 'internship', 'graduate program', 'co-op'}
        }

        # Work arrangement patterns
        self.work_arrangement_patterns = {
            'remote': {'remote', 'work from home', 'wfh', 'distributed', 'anywhere'},
            'hybrid': {'hybrid', 'flexible location', 'mix of office and remote'},
            'onsite': {'onsite', 'on-site', 'office based', 'in person'}
        }

        # New Zealand cities and regions for location extraction
        self.nz_locations = {
            # Major cities
            'auckland', 'wellington', 'christchurch', 'hamilton', 'tauranga',
            'dunedin', 'palmerston north', 'napier', 'hastings', 'new plymouth',
            'rotorua', 'whangarei', 'nelson', 'invercargill', 'queenstown',
            
            # Regions
            'northland', 'bay of plenty', 'gisborne', 'hawke\'s bay', 'taranaki',
            'manawatu-wanganui', 'wellington region', 'tasman', 'marlborough',
            'west coast', 'canterbury', 'otago', 'southland',
            
            # Suburbs and areas (commonly seen in tech jobs)
            'cbd', 'city centre', 'city center', 'north shore', 'central auckland',
            'lower hutt', 'upper hutt', 'porirua', 'kapiti coast'
        }

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract technical skills using spaCy NLP"""

        text_lower = text.lower()
        found_skills = {category: [] for category in self.tech_skills.keys()}

        # Process with spaCy
        try:
            doc = self.nlp(text)

            # Extract entities that might be technologies
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT", "PERSON","GPE"] and len(ent.text) > 2:
                    skill_lower = ent.text.lower()
                    if skill_lower in self.all_skills:
                        # FIXED: Use _skill_in_text() to prevent false positives
                        if self._skill_in_text(skill_lower, text):
                            # Find which category this skill belongs to
                            for category, skills in self.tech_skills.items():
                                if skill_lower in skills and skill_lower not in found_skills[category]:
                                    found_skills[category].append(skill_lower)

            # Extract technical compound nouns (HYBRID method: Uses NLP to find noun phrases, then does pattern matching within those phrases.)
            for chunk in doc.noun_chunks:
                chunk_text = chunk.text.lower()
                if any(tech_word in chunk_text for tech_word in ['software', 'web', 'data', 'cloud', 'system', 'application']):
                    for category, skills in self.tech_skills.items():
                        for skill in skills:
                            # FIXED: Use _skill_in_text() instead of simple substring matching
                            if self._skill_in_text(skill, chunk.text) and skill not in found_skills[category]:
                                found_skills[category].append(skill)

            # Also do pattern matching on tokens for better coverage (Direct pattern matching)
            for category, skills in self.tech_skills.items():
                for skill in skills:
                    if self._skill_in_text(skill, text_lower):
                        if skill not in found_skills[category]:
                            found_skills[category].append(skill)

        except Exception as e:
            logger.error(f"spaCy processing failed: {e}")
            raise

        # Remove empty categories and duplicates
        result = {}
        for category, skills in found_skills.items():
            if skills:
                result[category] = list(set(skills))

        return result

    def _skill_in_text(self, skill: str, text: str) -> bool:
        """Check if skill is mentioned in text with word boundary awareness"""
        import re
        
        # SPECIAL CASE: R programming language (CRITICAL FIX for false positives)
        if skill == 'r':
            # Only match when R appears in clear programming/statistical context
            # This prevents matching "r" in "requirements", "your", "for", etc.
            r_patterns = [
                r'\bR\s+(?:programming|language|studio|statistical|project)',
                r'(?:programming|statistical)\s+(?:language\s+)?R\b',
                r'\bR\s+(?:packages?|scripts?|tidyverse|ggplot2?|dplyr|shiny)',
                r'(?:proficient|experience|skilled|expert)\s+in\s+R\b',
                r'\bRStudio\b',
                r'statistical\s+computing.*\bR\b',
                r'\bR\b.*(?:data analysis|statistical analysis)',
                r'(?:data analysis|statistical analysis).*\bR\b',
                r'\bR\b\s+and\s+(?:Python|SPSS|SAS)',
                r'(?:Python|SPSS|SAS)\s+and\s+R\b'
            ]
            return any(re.search(p, text, re.IGNORECASE) for p in r_patterns)
        
        # SPECIAL CASE: AI (prevent matching in "email", "paid", "wait")  
        if skill == 'ai':
            ai_patterns = [
                r'\bAI\b',  # Must be uppercase
                r'artificial\s+intelligence',
                r'\bA\.I\.\b',
                r'machine\s+learning.*\bAI\b',
                r'\bAI\b.*machine\s+learning'
            ]
            return any(re.search(p, text, re.IGNORECASE) for p in ai_patterns)
        
        # Handle variations first
        variations = {
            'javascript': ['js', 'ecmascript'],
            'typescript': ['ts'],
            'c++': ['cpp', 'c plus plus'],
            'c#': ['csharp', 'c sharp'],
            'node.js': ['nodejs', 'node js'],
            'react native': ['reactnative'],
            'rest api': ['restful api', 'restful', 'rest'],  # FIXED: "rest" → "REST API"
            'machine learning': ['ml', 'machinelearning'],
            'artificial intelligence': ['ai'],
            'google cloud': ['gcp', 'google cloud platform']
        }

        # Check variations with word boundaries
        if skill in variations:
            for var in variations[skill]:
                if len(var) <= 3:
                    # Use word boundaries for short variations
                    pattern = r'\b' + re.escape(var) + r'\b'
                    if re.search(pattern, text, re.IGNORECASE):
                        return True
                else:
                    # Use substring for longer variations
                    if var in text.lower():
                        return True
        
        # IMPROVED: Use word boundaries for ALL skills to prevent false positives
        # Special handling for skills that are commonly part of other words
        problematic_skills = {
            'scala': [r'\bScala\b', r'Scala programming', r'Scala language', r'Scala developer'],
            'rust': [r'\bRust\b(?!\s*(?:protection|resistant|proof))', r'Rust programming', r'Rust language', r'Rust developer'],
            'go': [r'\bGo\b(?!\s*(?:to|through|over|with|on|in|out|up|down))', r'Golang', r'Go programming', r'Go language'],
            'sql': [r'\bSQL\b', r'SQL database', r'SQL server', r'SQL query', r'SQL development', r'SQL programming'],
            'r': []  # Already handled above
        }
        
        skill_lower = skill.lower()
        
        # Check if this skill has special patterns
        if skill_lower in problematic_skills:
            if not problematic_skills[skill_lower]:  # Empty list (like 'r') means already handled
                return False
            return any(re.search(pattern, text, re.IGNORECASE) for pattern in problematic_skills[skill_lower])
        
        # For all other skills, use word boundaries
        pattern = r'\b' + re.escape(skill) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    def extract_salary_info(self, text: str) -> Dict[str, any]:
        """Extract salary information with confidence scoring"""

        salary_info = {
            'raw_text': '',
            'min_salary': None,
            'max_salary': None,
            'currency': 'NZD',
            'period': None,
            'confidence_score': 0.0
        }

        if not text:
            return salary_info

        text_lower = text.lower()

        # Salary patterns for NZ
        patterns = [
            # Range patterns
            r'\$([0-9]{2,3}),?([0-9]{3})\s*-\s*\$([0-9]{2,3}),?([0-9]{3})',  # $80,000 - $120,000
            r'\$([0-9]{2,3})k\s*-\s*\$([0-9]{2,3})k',  # $80k - $120k
            r'([0-9]{2,3}),?([0-9]{3})\s*-\s*([0-9]{2,3}),?([0-9]{3})',  # 80,000 - 120,000
            r'([0-9]{2,3})k\s*-\s*([0-9]{2,3})k',  # 80k - 120k

            # Single salary patterns
            r'\$([0-9]{2,3}),?([0-9]{3})',  # $100,000
            r'\$([0-9]{2,3})k',  # $100k
            r'([0-9]{2,3}),?([0-9]{3})\s*(?:dollars?|nzd)',  # 100,000 dollars

            # Hourly rate patterns
            r'\$([0-9]{2,3})\s*-\s*\$([0-9]{2,3})\s*(?:per\s*hour|hourly|/hr)',  # $45 - $65 per hour
            r'\$([0-9]{2,3})\s*(?:per\s*hour|hourly|/hr)',  # $50 per hour
        ]

        best_match = None
        best_confidence = 0.0

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                confidence = self._calculate_salary_confidence(match.group(0), text_lower)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = match

        if best_match:
            salary_info['raw_text'] = best_match.group(0)
            salary_info['confidence_score'] = best_confidence

            # Parse the numbers
            groups = best_match.groups()
            if len(groups) >= 4:  # Range
                try:
                    min_sal = int(groups[0]) * 1000 + int(groups[1])
                    max_sal = int(groups[2]) * 1000 + int(groups[3])
                    salary_info['min_salary'] = min_sal
                    salary_info['max_salary'] = max_sal
                except:
                    pass
            elif len(groups) >= 2:  # Single salary
                try:
                    salary = int(groups[0]) * 1000 + int(groups[1])
                    salary_info['min_salary'] = salary
                    salary_info['max_salary'] = salary
                except:
                    pass

            # Determine period using spaCy for better context understanding
            doc = self.nlp(text)
            period_found = False

            for token in doc:
                token_lower = token.text.lower()
                if token_lower in ['hour', 'hourly', '/hr', 'hr']:
                    salary_info['period'] = 'hourly'
                    period_found = True
                    break
                elif token_lower in ['month', 'monthly', '/month', 'pm', 'pcm']:
                    salary_info['period'] = 'monthly'
                    period_found = True
                    break
                elif token_lower in ['annual', 'yearly', 'pa', 'per annum', 'p.a.']:
                    salary_info['period'] = 'yearly'
                    period_found = True
                    break

            if not period_found:
                # Check for contextual clues
                if any(phrase in text_lower for phrase in ['per hour', 'hourly rate', 'contract rate']):
                    salary_info['period'] = 'hourly'
                elif any(phrase in text_lower for phrase in ['per month', 'monthly salary']):
                    salary_info['period'] = 'monthly'
                else:
                    salary_info['period'] = 'yearly'  # Default assumption for NZ jobs

        return salary_info

    def _calculate_salary_confidence(self, salary_text: str, full_text: str) -> float:
        """Calculate confidence in salary extraction"""

        confidence = 0.0

        # Has explicit range
        if '-' in salary_text:
            confidence += 0.4

        # Has currency symbol
        if '$' in salary_text:
            confidence += 0.3

        # Context indicators
        context_words = ['salary', 'pay', 'package', 'compensation', 'remuneration']
        if any(word in full_text for word in context_words):
            confidence += 0.2

        # Reasonable range for NZ
        numbers = re.findall(r'\\d+', salary_text.replace(',', '').replace('k', '000'))
        if numbers:
            try:
                amounts = [int(n) for n in numbers]
                if any(30000 <= amount <= 300000 for amount in amounts):
                    confidence += 0.1
            except:
                pass

        return min(confidence, 1.0)

    def extract_experience_level(self, title: str, description: str) -> Optional[str]:
        """
        Extract experience level from job title and description.
        
        Returns database enum values (UPPERCASE):
        ENTRY, JUNIOR, MID, SENIOR, LEAD, PRINCIPAL, EXECUTIVE
        
        Returns None if not specified (database allows NULL for this column)
        Note: Maps 'intermediate' → 'MID', 'executive' → 'EXECUTIVE'
        """
        text = f"{title} {description}".lower()

        # Mapping from pattern keys to database enum values
        level_mapping = {
            'senior': 'SENIOR',
            'junior': 'JUNIOR', 
            'intermediate': 'MID',
            'executive': 'EXECUTIVE'
        }

        # Check for explicit patterns
        for level, patterns in self.experience_patterns.items():
            if any(pattern in text for pattern in patterns):
                # Map to database enum value
                return level_mapping.get(level, None)

        # Contextual analysis
        if any(word in text for word in ['5+ years', '10+ years', 'extensive experience']):
            return 'SENIOR'
        elif any(word in text for word in ['recent graduate', 'new to', 'learning']):
            return 'JUNIOR'

        return None  # Return None instead of 'NOT_SPECIFIED' - database allows NULL

    def extract_employment_type(self, text: str) -> str:
        """
        Extract employment type from job description.
        
        Returns database enum values (UPPERCASE):
        FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP, NOT_SPECIFIED
        """
        text_lower = text.lower()

        # Mapping from pattern keys to database enum values
        type_mapping = {
            'full_time': 'FULL_TIME',
            'part_time': 'PART_TIME',
            'contract': 'CONTRACT',
            'internship': 'INTERNSHIP'
        }

        for emp_type, patterns in self.employment_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return type_mapping.get(emp_type, 'NOT_SPECIFIED')

        return 'NOT_SPECIFIED'

    def extract_work_arrangement(self, text: str) -> str:
        """
        Extract work arrangement (remote/hybrid/onsite).
        
        Returns database enum values (UPPERCASE):
        REMOTE, HYBRID, ONSITE, FLEXIBLE, NOT_SPECIFIED
        """
        text_lower = text.lower()

        # Mapping from pattern keys to database enum values
        arrangement_mapping = {
            'remote': 'REMOTE',
            'hybrid': 'HYBRID',
            'onsite': 'ONSITE',
            'flexible': 'FLEXIBLE'
        }

        for arrangement, patterns in self.work_arrangement_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return arrangement_mapping.get(arrangement, 'NOT_SPECIFIED')

        return 'NOT_SPECIFIED'

    def parse_posted_date(self, date_text: str) -> Optional[date]:
        """Parse posted date from various text formats"""

        if not date_text:
            return None

        date_text = date_text.lower().strip()
        today = date.today()

        try:
            # Relative dates
            if 'today' in date_text or 'just posted' in date_text:
                return today
            elif 'yesterday' in date_text:
                return today - timedelta(days=1)
            elif 'days ago' in date_text:
                days_match = re.search(r'(\\d+)\\s*days?\\s*ago', date_text)
                if days_match:
                    return today - timedelta(days=int(days_match.group(1)))
            elif 'week ago' in date_text or 'weeks ago' in date_text:
                weeks_match = re.search(r'(\\d+)\\s*weeks?\\s*ago', date_text)
                if weeks_match:
                    return today - timedelta(weeks=int(weeks_match.group(1)))
                else:
                    return today - timedelta(weeks=1)

            # Absolute dates
            date_patterns = [
                r'(\\d{1,2})\\s*[/-]\\s*(\\d{1,2})\\s*[/-]\\s*(\\d{4})',  # dd/mm/yyyy
                r'(\\d{4})\\s*[/-]\\s*(\\d{1,2})\\s*[/-]\\s*(\\d{1,2})',  # yyyy/mm/dd
            ]

            for pattern in date_patterns:
                match = re.search(pattern, date_text)
                if match:
                    groups = match.groups()
                    try:
                        # Assume dd/mm/yyyy for first pattern
                        if len(groups[2]) == 4:  # First pattern
                            day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        else:  # Second pattern
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])

                        return date(year, month, day)
                    except ValueError:
                        continue

        except Exception as e:
            logger.warning(f"Date parsing failed for '{date_text}': {e}")

        return None

    def extract_location(self, location_text: str = None, description: str = None) -> Dict[str, Optional[str]]:
        """
        Extract location information using spaCy NLP and pattern matching.
        
        Prioritizes scraped location_text, falls back to extracting from description.
        
        Args:
            location_text: Raw location string from scraper (e.g., "Auckland CBD, Auckland")
            description: Job description text to extract location from if location_text is None
            
        Returns:
            Dict with keys: city, region, country, raw_location
            Example: {"city": "Auckland", "region": "Auckland", "country": "New Zealand", "raw_location": "Auckland CBD"}
        """
        location_info = {
            'city': None,
            'region': None,
            'country': 'New Zealand',  # Default for NZ job board
            'raw_location': None
        }

        # Priority 1: Use scraped location_text if available
        if location_text and location_text.strip():
            location_info['raw_location'] = location_text.strip()
            location_lower = location_text.lower()
            
            # Try to extract city from location_text
            city = self._extract_city_from_text(location_lower)
            if city:
                location_info['city'] = city
                location_info['region'] = self._get_region_for_city(city)
                return location_info

        # Priority 2: Extract from description using spaCy NER
        if description:
            try:
                doc = self.nlp(description)
                
                # Extract GPE (Geo-Political Entity) and LOC (Location) entities
                location_entities = []
                for ent in doc.ents:
                    if ent.label_ in ['GPE', 'LOC']:
                        location_entities.append(ent.text)
                
                # Check if any extracted entities match NZ locations
                for entity in location_entities:
                    entity_lower = entity.lower()
                    city = self._extract_city_from_text(entity_lower)
                    if city:
                        location_info['city'] = city
                        location_info['region'] = self._get_region_for_city(city)
                        location_info['raw_location'] = entity
                        return location_info
                
                # Fallback: Pattern matching for common location phrases
                location_patterns = [
                    r'(?:located in|based in|office in|position in|role in)\s+([A-Za-z\s]+?)(?:\s+(?:CBD|city|region))?(?:\.|,|$)',
                    r'([A-Za-z\s]+?)\s+(?:CBD|city centre|city center)',
                    r'(?:Auckland|Wellington|Christchurch|Hamilton|Tauranga|Dunedin)(?:\s+CBD|\s+city)?'
                ]
                
                for pattern in location_patterns:
                    matches = re.finditer(pattern, description, re.IGNORECASE)
                    for match in matches:
                        location_text = match.group(0) if match.lastindex is None else match.group(1)
                        city = self._extract_city_from_text(location_text.lower())
                        if city:
                            location_info['city'] = city
                            location_info['region'] = self._get_region_for_city(city)
                            location_info['raw_location'] = location_text.strip()
                            return location_info
                            
            except Exception as e:
                logger.warning(f"spaCy location extraction failed: {e}")

        return location_info

    def _extract_city_from_text(self, text: str) -> Optional[str]:
        """Extract city name from text by matching against known NZ locations"""
        text_lower = text.lower().strip()
        
        # Direct match
        if text_lower in self.nz_locations:
            return self._normalize_city_name(text_lower)
        
        # Partial match (e.g., "Auckland CBD" contains "Auckland")
        for location in self.nz_locations:
            if location in text_lower:
                return self._normalize_city_name(location)
        
        return None

    def _normalize_city_name(self, city: str) -> str:
        """Normalize city name to proper case"""
        # Special cases
        special_cases = {
            'cbd': 'CBD',
            'new plymouth': 'New Plymouth',
            'palmerston north': 'Palmerston North',
            'upper hutt': 'Upper Hutt',
            'lower hutt': 'Lower Hutt',
            'north shore': 'North Shore',
            'bay of plenty': 'Bay of Plenty',
            'hawke\'s bay': 'Hawke\'s Bay',
            'manawatu-wanganui': 'Manawatu-Wanganui',
            'west coast': 'West Coast'
        }
        
        if city in special_cases:
            return special_cases[city]
        
        # Default to title case
        return city.title()

    def _get_region_for_city(self, city: str) -> Optional[str]:
        """Map city to its region"""
        city_region_map = {
            'Auckland': 'Auckland',
            'Wellington': 'Wellington',
            'Christchurch': 'Canterbury',
            'Hamilton': 'Waikato',
            'Tauranga': 'Bay of Plenty',
            'Dunedin': 'Otago',
            'Palmerston North': 'Manawatu-Wanganui',
            'Napier': 'Hawke\'s Bay',
            'Hastings': 'Hawke\'s Bay',
            'New Plymouth': 'Taranaki',
            'Rotorua': 'Bay of Plenty',
            'Whangarei': 'Northland',
            'Nelson': 'Nelson',
            'Invercargill': 'Southland',
            'Queenstown': 'Otago',
            'Lower Hutt': 'Wellington',
            'Upper Hutt': 'Wellington',
            'Porirua': 'Wellington',
            'North Shore': 'Auckland'
        }
        
        return city_region_map.get(city, None)

    def get_display_name(self, skill: str) -> str:
        """
        Get proper display name for a skill.
        
        Args:
            skill: Skill name in lowercase (e.g., "r", "javascript", "rest")
            
        Returns:
            Properly formatted display name (e.g., "R", "JavaScript", "REST API")
        """
        return self.skill_display_names.get(skill.lower(), skill.title())
    
    def get_skill_category(self, skill: str) -> str:
        """
        Get the category for a given skill.
        
        Args:
            skill: Internal skill name (lowercase)
            
        Returns:
            Category name or 'other' if not found
            
        Example:
            get_skill_category('python') → 'programming_languages'
            get_skill_category('docker') → 'devops'
        """
        skill_lower = skill.lower()
        for category, skills in self.tech_skills.items():
            if skill_lower in skills:
                return category
        return 'other'

    def is_tech_job(self, title: str, description: str) -> Tuple[bool, float]:
        """
        Determine if job is tech-related with confidence score.
        
        Improved to reduce false negatives for tech-adjacent roles like:
        - Business Analysts in tech companies
        - Product Managers
        - Scrum Masters / Agile Coaches
        - Project Managers (tech projects)
        - QA / Test Analysts
        
        Args:
            title: Job title
            description: Full job description
            
        Returns:
            Tuple of (is_tech, confidence_score)
        """

        text = f"{title} {description}".lower()
        title_lower = title.lower()

        # Extract skills
        skills = self.extract_skills(text)
        total_skills = sum(len(skill_list) for skill_list in skills.values())

        # Expanded title indicators (more inclusive)
        # Core technical roles
        core_tech_indicators = {
            'developer', 'engineer', 'programmer', 'software', 'web', 
            'mobile', 'devops', 'data scientist', 'data engineer',
            'machine learning', 'ai engineer', 'cloud', 'database administrator',
            'security engineer', 'network engineer', 'systems administrator'
        }
        
        # Tech-adjacent roles (still tech jobs!)
        tech_adjacent_indicators = {
            'analyst', 'product manager', 'product owner', 'scrum master',
            'project manager', 'agile coach', 'qa', 'test', 'tester',
            'business analyst', 'technical writer', 'designer', 'ux', 'ui',
            'architect', 'solution architect', 'technical lead', 'tech lead',
            'implementation consultant', 'technical consultant'
        }
        
        # Technology-specific keywords
        tech_domain_words = {
            'software', 'digital', 'technology', 'it ', 'i.t.', 'tech ',
            'computer', 'system', 'application', 'platform', 'infrastructure'
        }

        # Calculate title scores
        core_tech_in_title = sum(1 for indicator in core_tech_indicators if indicator in title_lower)
        tech_adjacent_in_title = sum(1 for indicator in tech_adjacent_indicators if indicator in title_lower)
        domain_in_title = sum(1 for word in tech_domain_words if word in title_lower)
        
        # Calculate confidence
        confidence = 0.0

        # 1. Skills weight (50% - reduced from 60% to be less skill-heavy)
        if total_skills >= 5:
            confidence += 0.5
        elif total_skills >= 3:
            confidence += 0.4
        elif total_skills >= 2:
            confidence += 0.3
        elif total_skills >= 1:
            confidence += 0.2

        # 2. Title weight (35% - increased from 30%)
        if core_tech_in_title >= 1:
            # Strong indicator: developer, engineer, programmer
            confidence += 0.35
        elif tech_adjacent_in_title >= 1:
            # Moderate indicator: analyst, product manager, scrum master
            # But only if there's tech context
            if domain_in_title >= 1 or total_skills >= 1:
                confidence += 0.30  # Full credit with context
            else:
                confidence += 0.15  # Reduced credit without context

        # 3. Content weight (15% - increased from 10%)
        # Expanded to include business/product/project tech terms
        tech_content_words = [
            # Development
            'code', 'coding', 'programming', 'algorithm', 'api', 'database',
            'software development', 'application development', 'web development',
            # Tech processes
            'agile', 'scrum', 'sprint', 'jira', 'confluence', 'git', 'ci/cd',
            'devops', 'automation', 'testing', 'deployment',
            # Business/Product in tech
            'technical requirements', 'user stories', 'product backlog',
            'stakeholder', 'roadmap', 'technical documentation',
            # Data/Analytics
            'data analysis', 'sql', 'reporting', 'dashboard', 'analytics',
            'business intelligence', 'data warehouse'
        ]
        
        content_matches = sum(1 for word in tech_content_words if word in text)
        confidence += min(content_matches * 0.015, 0.15)

        # 4. Company/Context indicators (bonus weight, up to 10%)
        context_indicators = [
            'tech company', 'software company', 'saas', 'startup',
            'digital transformation', 'it department', 'technology team',
            'engineering team', 'development team', 'product team'
        ]
        context_matches = sum(1 for indicator in context_indicators if indicator in text)
        confidence += min(context_matches * 0.05, 0.10)

        # Determine if tech job (threshold 0.4 - lowered from 0.5 to reduce false negatives)
        is_tech = confidence >= 0.4

        return is_tech, confidence