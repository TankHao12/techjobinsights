"""
TechInsights  - Technology Stack Detection
ML-enhanced technology detection in job descriptions
"""

import re
from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class TechMatch:
    """Represents a detected technology match."""
    
    tech_id: int
    tech_name: str
    normalized_name: str
    confidence: float
    requirement_type: str  # 'required', 'preferred', 'nice-to-have', 'mentioned'
    context: str
    position: int
    years_experience: Optional[int] = None
    proficiency_level: Optional[str] = None


@dataclass
class DetectionResult:
    """Results from technology detection."""
    
    matches: List[TechMatch]
    total_techs_found: int
    confidence_scores: Dict[str, float]
    processing_time: float
    detection_method: str


class TechStackDetector:
    """
    Technology stack detection engine with multiple detection methods.
    
    Combines keyword matching, pattern recognition, and contextual analysis
    to identify technology requirements in job descriptions.
    """
    
    def __init__(self):
        """Initialize the tech detection engine."""
        
        # Technology patterns and keywords
        self.tech_patterns = self._build_tech_patterns()
        
        # Context patterns for requirement classification
        self.requirement_patterns = {
            'required': [
                r'(?:must\s+have|required|essential|mandatory|critical)',
                r'(?:experience\s+(?:in|with)|proficient\s+(?:in|with)|skilled\s+(?:in|with))',
                r'(?:minimum|at\s+least)\s+\d+\s+years?',
                r'(?:strong|solid|extensive)\s+(?:knowledge|experience|background)'
            ],
            'preferred': [
                r'(?:preferred|desirable|ideal|advantageous|beneficial)',
                r'(?:nice\s+to\s+have|bonus|plus|additional)',
                r'(?:would\s+be\s+(?:great|nice|good))',
                r'(?:familiarity\s+with|exposure\s+to)'
            ],
            'nice-to-have': [
                r'(?:nice\s+to\s+have|bonus|plus|additional)',
                r'(?:would\s+be\s+(?:great|nice|good|beneficial))',
                r'(?:familiarity\s+with|exposure\s+to|some\s+knowledge)'
            ]
        }
        
        # Experience level patterns
        self.experience_patterns = {
            r'(\d+)(?:\+)?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)': 'years',
            r'(?:senior|lead|principal|expert)': 'senior',
            r'(?:junior|entry|graduate|trainee|intern)': 'junior',
            r'(?:mid|intermediate|standard)': 'mid',
            r'(?:beginner|basic|introductory)': 'beginner',
            r'(?:advanced|expert|proficient|skilled)': 'advanced'
        }
        
        # Common false positives to filter out
        self.false_positives = {
            'go', 'r', 'c', 'dart', 'scala', 'rust'  # Single letter techs need context
        }
    
    def detect_technologies(
        self,
        job_description: str,
        available_techs: List[Dict[str, Any]],
        confidence_threshold: float = 0.3
    ) -> DetectionResult:
        """
        Detect technologies in a job description.
        
        Args:
            job_description: Job description text
            available_techs: List of available technologies from database
            confidence_threshold: Minimum confidence score to include
            
        Returns:
            DetectionResult: Detection results with matches and metadata
        """
        import time
        start_time = time.time()
        
        if not job_description or not available_techs:
            return DetectionResult(
                matches=[],
                total_techs_found=0,
                confidence_scores={},
                processing_time=0.0,
                detection_method="none"
            )
        
        # Normalize text for processing
        normalized_text = self._normalize_text(job_description)
        
        # Build tech lookup dictionary
        tech_lookup = self._build_tech_lookup(available_techs)
        
        # Detect technologies using multiple methods
        matches = []
        confidence_scores = {}
        
        # 1. Keyword matching
        keyword_matches = self._detect_via_keywords(
            normalized_text, tech_lookup, job_description
        )
        matches.extend(keyword_matches)
        
        # 2. Pattern matching
        pattern_matches = self._detect_via_patterns(
            normalized_text, tech_lookup, job_description
        )
        matches.extend(pattern_matches)
        
        # 3. Context analysis
        matches = self._analyze_context(matches, job_description)
        
        # 4. Filter and deduplicate
        matches = self._filter_matches(matches, confidence_threshold)
        
        # Calculate confidence scores
        for match in matches:
            confidence_scores[match.normalized_name] = match.confidence
        
        processing_time = time.time() - start_time
        
        result = DetectionResult(
            matches=matches,
            total_techs_found=len(matches),
            confidence_scores=confidence_scores,
            processing_time=processing_time,
            detection_method="hybrid"
        )
        
        logger.debug(f"Detected {len(matches)} technologies in {processing_time:.3f}s")
        return result
    
    def _build_tech_lookup(self, available_techs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Build lookup dictionary for fast technology matching."""
        lookup = {}
        
        for tech in available_techs:
            tech_id = tech.get('tech_id')
            tech_name = tech.get('technology_name', '').lower()
            normalized_name = tech.get('normalized_name', '').lower()
            aliases = tech.get('aliases', []) or []
            
            if not tech_id or not tech_name:
                continue
            
            # Add main name
            lookup[tech_name] = tech
            lookup[normalized_name] = tech
            
            # Add aliases
            for alias in aliases:
                if alias:
                    lookup[alias.lower()] = tech
        
        return lookup
    
    def _detect_via_keywords(
        self,
        normalized_text: str,
        tech_lookup: Dict[str, Dict[str, Any]],
        original_text: str
    ) -> List[TechMatch]:
        """Detect technologies using keyword matching."""
        matches = []
        
        for tech_term, tech_data in tech_lookup.items():
            if len(tech_term) < 2:  # Skip single character terms
                continue
            
            # Build regex pattern for the technology
            pattern = self._build_tech_pattern(tech_term)
            
            # Find all matches
            for match in re.finditer(pattern, normalized_text, re.IGNORECASE):
                start_pos = match.start()
                end_pos = match.end()
                matched_text = match.group()
                
                # Extract context around the match
                context = self._extract_context(original_text, start_pos, end_pos)
                
                # Calculate confidence based on match quality
                confidence = self._calculate_keyword_confidence(
                    tech_term, matched_text, context
                )
                
                # Determine requirement type from context
                req_type = self._classify_requirement_type(context)
                
                tech_match = TechMatch(
                    tech_id=tech_data['tech_id'],
                    tech_name=tech_data['technology_name'],
                    normalized_name=tech_data['normalized_name'],
                    confidence=confidence,
                    requirement_type=req_type,
                    context=context,
                    position=start_pos
                )
                
                matches.append(tech_match)
        
        return matches
    
    def _detect_via_patterns(
        self,
        normalized_text: str,
        tech_lookup: Dict[str, Dict[str, Any]],
        original_text: str
    ) -> List[TechMatch]:
        """Detect technologies using pattern matching."""
        matches = []
        
        # Technology stack patterns
        patterns = [
            r'(?:stack|technologies?):\s*([^.!?]+)',
            r'(?:experience\s+(?:in|with)|knowledge\s+of|familiar\s+with|proficient\s+in):\s*([^.!?]+)',
            r'(?:skills|requirements):\s*([^.!?]+)',
            r'(?:using|with|including):\s*([^.!?]+)'
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, normalized_text, re.IGNORECASE):
                tech_list_text = match.group(1)
                
                # Extract individual technologies from the list
                tech_matches = self._extract_techs_from_list(
                    tech_list_text, tech_lookup, original_text
                )
                matches.extend(tech_matches)
        
        return matches
    
    def _extract_techs_from_list(
        self,
        tech_list_text: str,
        tech_lookup: Dict[str, Dict[str, Any]],
        original_text: str
    ) -> List[TechMatch]:
        """Extract technologies from a comma/delimiter separated list."""
        matches = []
        
        # Split on common delimiters
        items = re.split(r'[,;/&+\n]', tech_list_text)
        
        for item in items:
            item = item.strip()
            if not item or len(item) < 2:
                continue
            
            # Clean up the item
            cleaned_item = re.sub(r'[^\w\s.-]', '', item).strip()
            
            # Check if it matches any known technology
            if cleaned_item.lower() in tech_lookup:
                tech_data = tech_lookup[cleaned_item.lower()]
                
                tech_match = TechMatch(
                    tech_id=tech_data['tech_id'],
                    tech_name=tech_data['technology_name'],
                    normalized_name=tech_data['normalized_name'],
                    confidence=0.8,  # High confidence for pattern-based detection
                    requirement_type='mentioned',
                    context=tech_list_text,
                    position=0
                )
                
                matches.append(tech_match)
        
        return matches
    
    def _analyze_context(
        self,
        matches: List[TechMatch],
        job_description: str
    ) -> List[TechMatch]:
        """Analyze context to enhance matches with additional information."""
        enhanced_matches = []
        
        for match in matches:
            # Extract years of experience
            match.years_experience = self._extract_years_experience(match.context)
            
            # Extract proficiency level
            match.proficiency_level = self._extract_proficiency_level(match.context)
            
            # Refine requirement type based on full context
            refined_req_type = self._classify_requirement_type(match.context)
            if refined_req_type != 'mentioned':
                match.requirement_type = refined_req_type
            
            # Adjust confidence based on context quality
            match.confidence = self._adjust_confidence_by_context(match)
            
            enhanced_matches.append(match)
        
        return enhanced_matches
    
    def _filter_matches(
        self,
        matches: List[TechMatch],
        confidence_threshold: float
    ) -> List[TechMatch]:
        """Filter and deduplicate matches."""
        # Group by technology ID
        tech_groups = defaultdict(list)
        for match in matches:
            tech_groups[match.tech_id].append(match)
        
        filtered_matches = []
        
        for tech_id, tech_matches in tech_groups.items():
            if not tech_matches:
                continue
            
            # Find the best match for this technology
            best_match = max(tech_matches, key=lambda m: m.confidence)
            
            # Only include if above threshold
            if best_match.confidence >= confidence_threshold:
                filtered_matches.append(best_match)
        
        # Sort by confidence descending
        filtered_matches.sort(key=lambda m: m.confidence, reverse=True)
        
        return filtered_matches
    
    def _build_tech_pattern(self, tech_term: str) -> str:
        """Build regex pattern for technology term."""
        # Escape special regex characters
        escaped_term = re.escape(tech_term)
        
        # Handle special cases
        if '.' in tech_term:
            # For terms like "vue.js", make the dot optional
            escaped_term = escaped_term.replace(r'\.', r'\.?')
        
        # Word boundary pattern
        pattern = rf'\b{escaped_term}\b'
        
        return pattern
    
    def _extract_context(self, text: str, start_pos: int, end_pos: int, window: int = 100) -> str:
        """Extract context around a match."""
        context_start = max(0, start_pos - window)
        context_end = min(len(text), end_pos + window)
        
        context = text[context_start:context_end]
        return context.strip()
    
    def _calculate_keyword_confidence(
        self,
        tech_term: str,
        matched_text: str,
        context: str
    ) -> float:
        """Calculate confidence score for keyword match."""
        confidence = 0.5  # Base confidence
        
        # Exact match bonus
        if tech_term.lower() == matched_text.lower():
            confidence += 0.2
        
        # Length bonus (longer terms are more specific)
        if len(tech_term) > 4:
            confidence += 0.1
        
        # Context quality bonus
        if any(keyword in context.lower() for keyword in [
            'experience', 'skill', 'knowledge', 'proficient', 'familiar'
        ]):
            confidence += 0.2
        
        # Technology-specific context bonus
        if any(keyword in context.lower() for keyword in [
            'framework', 'library', 'language', 'database', 'tool', 'platform'
        ]):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _classify_requirement_type(self, context: str) -> str:
        """Classify requirement type based on context."""
        context_lower = context.lower()
        
        # Check required patterns
        for pattern in self.requirement_patterns['required']:
            if re.search(pattern, context_lower):
                return 'required'
        
        # Check preferred patterns
        for pattern in self.requirement_patterns['preferred']:
            if re.search(pattern, context_lower):
                return 'preferred'
        
        # Check nice-to-have patterns
        for pattern in self.requirement_patterns['nice-to-have']:
            if re.search(pattern, context_lower):
                return 'nice-to-have'
        
        return 'mentioned'
    
    def _extract_years_experience(self, context: str) -> Optional[int]:
        """Extract years of experience from context."""
        patterns = [
            r'(\d+)(?:\+)?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)',
            r'(?:minimum|min|at\s+least)\s*(\d+)\s*(?:years?|yrs?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_proficiency_level(self, context: str) -> Optional[str]:
        """Extract proficiency level from context."""
        context_lower = context.lower()
        
        if any(term in context_lower for term in ['expert', 'advanced', 'senior', 'lead']):
            return 'Expert'
        elif any(term in context_lower for term in ['proficient', 'skilled', 'experienced']):
            return 'Advanced'
        elif any(term in context_lower for term in ['intermediate', 'mid', 'moderate']):
            return 'Intermediate'
        elif any(term in context_lower for term in ['basic', 'beginner', 'entry', 'junior']):
            return 'Beginner'
        
        return None
    
    def _adjust_confidence_by_context(self, match: TechMatch) -> float:
        """Adjust confidence based on context quality."""
        confidence = match.confidence
        
        # Bonus for having years of experience
        if match.years_experience:
            confidence += 0.1
        
        # Bonus for having proficiency level
        if match.proficiency_level:
            confidence += 0.1
        
        # Bonus for required/preferred classification
        if match.requirement_type in ['required', 'preferred']:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for processing."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _build_tech_patterns(self) -> Dict[str, str]:
        """Build common technology patterns."""
        patterns = {
            # Programming languages
            'javascript': r'\b(?:javascript|js|ecmascript)\b',
            'typescript': r'\b(?:typescript|ts)\b',
            'python': r'\bpython\b',
            'java': r'\bjava\b(?!\s*script)',  # Exclude javascript
            'csharp': r'\b(?:c#|c-sharp|csharp)\b',
            'cpp': r'\b(?:c\+\+|cpp)\b',
            'go': r'\bgolang\b|\bgo\b(?:\s+lang)',
            'rust': r'\brust\b(?:\s+lang)',
            'php': r'\bphp\b',
            'ruby': r'\bruby\b',
            'swift': r'\bswift\b',
            'kotlin': r'\bkotlin\b',
            
            # Frameworks
            'react': r'\b(?:react|reactjs|react\.js)\b',
            'angular': r'\b(?:angular|angularjs|angular\.js)\b',
            'vue': r'\b(?:vue|vuejs|vue\.js)\b',
            'django': r'\bdjango\b',
            'flask': r'\bflask\b',
            'spring': r'\bspring\b(?:\s+boot)?',
            'express': r'\bexpress\b(?:\.js)?',
            'laravel': r'\blaravel\b',
            
            # Databases
            'postgresql': r'\b(?:postgresql|postgres|psql)\b',
            'mysql': r'\bmysql\b',
            'mongodb': r'\b(?:mongodb|mongo)\b',
            'redis': r'\bredis\b',
            'sqlite': r'\bsqlite\b',
            
            # Cloud and DevOps
            'aws': r'\b(?:aws|amazon\s+web\s+services)\b',
            'azure': r'\b(?:azure|microsoft\s+azure)\b',
            'gcp': r'\b(?:gcp|google\s+cloud\s+platform|google\s+cloud)\b',
            'docker': r'\bdocker\b',
            'kubernetes': r'\b(?:kubernetes|k8s)\b',
            'terraform': r'\bterraform\b'
        }
        
        return patterns

