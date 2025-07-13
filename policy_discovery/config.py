"""
Configuration settings for the Policy Discovery module
"""

import os

# Exa API Configuration
EXA_API_KEY = os.getenv("EXA_API_KEY")

# Government website domains for targeted search
GOVERNMENT_DOMAINS = {
    "federal": [
        "congress.gov",
        "regulations.gov",
        "federalregister.gov",
        "whitehouse.gov",
        "usa.gov",
    ],
    "state": [
        # "ca.gov", 
        # "leginfo.legislature.ca.gov", 
        # "gov.ca.gov", 
        # "opr.ca.gov",
        "calmatters.digitaldemocracy.org"
    ],
    # "local": ["sfplanning.org", "sf.gov", "sfgov.org", "sfdph.org", "sfmta.com"],
    "local": ["sfplanning.org", "sfgov.org"],
}

# Search configuration
SEARCH_CONFIG = {
    "default_date_cutoff": "2023-01-01",
    "max_results_per_level": 20,
    "use_autoprompt": True,
    "include_text_content": True,
    "max_content_length": 5000,
}

# Policy domain keywords
DOMAIN_KEYWORDS = {
    "housing": [
        "rent control",
        "zoning",
        "tenant rights",
        "affordable housing",
        "housing policy",
        "residential development",
        "eviction protection",
    ],
    "labor": [
        "worker classification",
        "minimum wage",
        "benefits",
        "employment law",
        "workplace safety",
        "labor relations",
        "gig economy",
    ],
    "public_safety": [
        "policing",
        "community safety",
        "emergency services",
        "crime prevention",
        "public health",
        "disaster preparedness",
    ],
    "environment": [
        "climate policies",
        "pollution control",
        "environmental protection",
        "sustainability",
        "green energy",
        "carbon emissions",
    ],
    "transportation": [
        "transit",
        "parking",
        "infrastructure",
        "public transportation",
        "traffic management",
        "bike lanes",
        "pedestrian safety",
    ],
    "business": [
        "licensing",
        "business regulations",
        "taxation",
        "permits",
        "small business",
        "commercial development",
    ],
}

# Stakeholder role mappings
STAKEHOLDER_KEYWORDS = {
    "renter": ["tenant", "renter", "housing", "rent", "lease"],
    "homeowner": ["property owner", "homeowner", "property tax", "zoning"],
    "employee": ["worker", "employee", "labor", "wages", "benefits"],
    "business_owner": ["business", "entrepreneur", "commercial", "licensing"],
    "student": ["education", "student", "school", "university"],
    "parent": ["family", "children", "education", "childcare"],
    "senior": ["elderly", "senior", "retirement", "medicare", "social security"],
    "immigrant": ["immigration", "visa", "citizenship", "naturalization"],
}

# Cache configuration
CACHE_CONFIG = {
    "enabled": True,
    "ttl_hours": 24,
    "max_entries": 1000,
    "cache_directory": ".cache/policy_discovery",
}

# Rate limiting
RATE_LIMITS = {
    "exa_api_calls_per_minute": 60,
    "max_concurrent_searches": 5,
    "request_timeout_seconds": 30,
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "policy_discovery.log",
}
