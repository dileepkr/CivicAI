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
    key_deadlines: list[dict[str, Any]]
    related_policies: list[str]
    content_preview: str | None = None
    confidence_score: float = 0.0


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
    """Policy document with full text content"""
    
    title: str
    source_url: str
    text: str


@dataclass
class PolicyDiscoveryResponse:
    """Formatted response matching the specified output structure"""
    
    request_id: str
    user_profile: UserProfile
    policy_document: PolicyDocument


@dataclass
class PolicyDiscoveryResult:
    """Complete result set from policy discovery operation"""

    federal_policies: list[PolicyResult]
    state_policies: list[PolicyResult]
    local_policies: list[PolicyResult]
    stakeholder_impact_map: dict[str, list[PolicyResult]]
    priority_ranking: list[PolicyResult]
    related_policies: list[PolicyResult]
    search_metadata: dict[str, Any]
    total_found: int
    search_time: float


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
