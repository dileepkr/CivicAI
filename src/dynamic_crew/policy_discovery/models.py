"""
Data models for the Policy Discovery module
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class PolicyDomain(Enum):
    """Policy domain classifications"""

    HOUSING = "housing"
    LABOR = "labor"
    PUBLIC_SAFETY = "public_safety"
    ENVIRONMENT = "environment"
    TRANSPORTATION = "transportation"
    BUSINESS = "business"


class GovernmentLevel(Enum):
    """Government level classifications"""

    FEDERAL = "federal"
    STATE = "state"
    LOCAL = "local"


class PolicyStatus(Enum):
    """Policy status classifications"""

    PROPOSED = "proposed"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class RegulationTiming(Enum):
    """Regulation timing preferences"""
    
    CURRENT = "current"  # Already passed/active policies
    FUTURE = "future"    # Proposed/upcoming policies
    ALL = "all"          # Both current and future policies


class ImpactSeverity(Enum):
    """Impact severity levels"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class StakeholderImpact:
    """Represents the impact of a policy on a specific stakeholder group"""

    stakeholder_group: str
    impact_severity: ImpactSeverity
    description: str
    affected_areas: list[str]


@dataclass
class PolicyResult:
    """Represents a discovered policy document"""

    title: str
    summary: str
    url: str
    government_level: GovernmentLevel
    domain: PolicyDomain
    status: PolicyStatus
    stakeholder_impacts: list[StakeholderImpact]
    last_updated: datetime
    source_agency: str
    document_type: str
    confidence_score: float
    content_preview: str = ""


@dataclass
class SearchParameters:
    """Parameters for policy search operations"""

    user_location: str
    stakeholder_roles: list[str]
    domains: list[PolicyDomain]
    government_levels: list[GovernmentLevel]
    regulation_timing: RegulationTiming = RegulationTiming.ALL
    date_range: dict[str, datetime] | None = None
    max_results: int = 20
    include_expired: bool = False


@dataclass
class UserProfile:
    """User profile information"""
    
    persona: str
    location: str
    initial_stance: str = "Undecided"


@dataclass
class PolicyDocument:
    """Policy document with comprehensive metadata"""
    
    title: str
    summary: str
    url: str
    government_level: GovernmentLevel
    domain: PolicyDomain
    status: PolicyStatus
    source_agency: str
    last_updated: datetime
    stakeholder_impacts: list[StakeholderImpact]


@dataclass
class UserContext:
    """User context for personalized policy discovery"""

    location: str
    stakeholder_roles: list[str]
    interests: list[str]
    regulation_timing: RegulationTiming = RegulationTiming.ALL
    uploaded_documents: list[str] | None = None
    previous_searches: list[str] | None = None
    preferences: dict[str, Any] | None = None


@dataclass
class PolicyDiscoveryResponse:
    """Formatted response matching the specified output structure"""
    
    request_id: str
    user_context: UserContext
    policy_document: PolicyDocument
    relevance_score: float
    generated_at: datetime


@dataclass
class PolicyDiscoveryResult:
    """Complete result set from policy discovery operation"""

    total_found: int
    priority_ranking: list[PolicyResult]
    stakeholder_impact_map: dict[str, list[PolicyResult]]
    search_time: float
    search_metadata: dict[str, Any] 