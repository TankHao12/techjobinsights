"""
Enums for the tech jobs insights application
"""

import enum

# =============================================================================
# ENUMS
# =============================================================================

class EmploymentType(enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    NOT_SPECIFIED = "not_specified"

class ExperienceLevel(enum.Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"
    NOT_SPECIFIED = "not_specified"

class WorkArrangement(enum.Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    FLEXIBLE = "flexible"
    NOT_SPECIFIED = "not_specified"

class SkillCategory(enum.Enum):
    PROGRAMMING = "programming"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    TOOLS = "tools"
    DEVOPS = "devops"
    INFRASTRUCTURE = "infrastructure"
    CLOUD = "cloud"
    NOT_SPECIFIED = "not_specified"

class SkillType(enum.Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    CERTIFICATION = "certification"
    METHODOLOGY = "methodology"
    NOT_SPECIFIED = "not_specified"

class ProficiencyLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    NOT_SPECIFIED = "not_specified"
