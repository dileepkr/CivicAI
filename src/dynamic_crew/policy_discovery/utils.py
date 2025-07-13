"""
Utility classes for policy classification and stakeholder analysis
"""

import logging
import re
from datetime import datetime
from typing import Any

from .config import DOMAIN_KEYWORDS, STAKEHOLDER_KEYWORDS
from .models import ImpactSeverity, PolicyDomain, PolicyStatus, StakeholderImpact


class PolicyClassifier:
    """
    Classifier for policy domains and status
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Compile domain keyword patterns
        self.domain_patterns = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            pattern = "|".join(re.escape(keyword) for keyword in keywords)
            self.domain_patterns[domain] = re.compile(pattern, re.IGNORECASE)

        # Status keywords
        self.status_patterns = {
            PolicyStatus.PROPOSED: re.compile(
                r"\b(proposed|bill|draft|pending|under consideration|introduced)\b",
                re.IGNORECASE,
            ),
            PolicyStatus.ACTIVE: re.compile(
                r"\b(enacted|effective|active|law|regulation|in force|implemented)\b",
                re.IGNORECASE,
            ),
            PolicyStatus.UNDER_REVIEW: re.compile(
                r"\b(under review|reviewing|consideration|committee|hearing)\b",
                re.IGNORECASE,
            ),
            PolicyStatus.EXPIRED: re.compile(
                r"\b(expired|sunset|terminated|repealed|obsolete)\b", re.IGNORECASE
            ),
            PolicyStatus.SUPERSEDED: re.compile(
                r"\b(superseded|replaced|amended|updated|modified)\b", re.IGNORECASE
            ),
        }

    def classify_domain(self, text: str) -> PolicyDomain:
        """
        Classify the policy domain based on text content

        Args:
            text: Policy text to classify

        Returns:
            PolicyDomain enum value
        """
        if not text:
            return PolicyDomain.BUSINESS  # Default domain

        domain_scores = {}

        # Score each domain based on keyword matches
        for domain, pattern in self.domain_patterns.items():
            matches = pattern.findall(text)
            domain_scores[domain] = len(matches)

        # Return domain with highest score
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return PolicyDomain(best_domain)

        # Fallback classification based on common terms
        text_lower = text.lower()

        if any(term in text_lower for term in ["housing", "rent", "tenant", "zoning"]):
            return PolicyDomain.HOUSING
        elif any(
            term in text_lower for term in ["employment", "worker", "wage", "labor"]
        ):
            return PolicyDomain.LABOR
        elif any(
            term in text_lower for term in ["police", "safety", "crime", "emergency"]
        ):
            return PolicyDomain.PUBLIC_SAFETY
        elif any(
            term in text_lower for term in ["environment", "climate", "pollution"]
        ):
            return PolicyDomain.ENVIRONMENT
        elif any(term in text_lower for term in ["transport", "transit", "traffic"]):
            return PolicyDomain.TRANSPORTATION
        else:
            return PolicyDomain.BUSINESS

    def classify_status(self, text: str) -> PolicyStatus:
        """
        Classify the policy status based on text content

        Args:
            text: Policy text to analyze

        Returns:
            PolicyStatus enum value
        """
        if not text:
            return PolicyStatus.ACTIVE  # Default status

        # Check for status indicators
        for status, pattern in self.status_patterns.items():
            if pattern.search(text):
                return status

        # Default to active if no clear status indicators
        return PolicyStatus.ACTIVE

    def extract_key_dates(self, text: str) -> list[dict[str, Any]]:
        """
        Extract key dates and deadlines from policy text

        Args:
            text: Policy text to analyze

        Returns:
            List of date information dictionaries
        """
        dates = []

        # Common date patterns
        date_patterns = [
            r"effective\s+(\w+\s+\d{1,2},?\s+\d{4})",
            r"deadline\s+(\w+\s+\d{1,2},?\s+\d{4})",
            r"by\s+(\w+\s+\d{1,2},?\s+\d{4})",
            r"(\d{1,2}/\d{1,2}/\d{4})",
            r"(\w+\s+\d{1,2},?\s+\d{4})",
        ]

        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                context = text[max(0, match.start() - 50) : match.end() + 50]

                dates.append(
                    {
                        "date_string": date_str,
                        "context": context.strip(),
                        "type": self._classify_date_type(context),
                    }
                )

        return dates[:5]  # Limit to 5 most relevant dates

    def _classify_date_type(self, context: str) -> str:
        """Classify the type of date based on context"""
        context_lower = context.lower()

        if "effective" in context_lower:
            return "effective_date"
        elif "deadline" in context_lower:
            return "deadline"
        elif "expire" in context_lower:
            return "expiration_date"
        elif "hearing" in context_lower:
            return "hearing_date"
        else:
            return "other"


class StakeholderAnalyzer:
    """
    Analyzer for stakeholder impacts and relevance
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Compile stakeholder patterns
        self.stakeholder_patterns = {}
        for role, keywords in STAKEHOLDER_KEYWORDS.items():
            pattern = "|".join(re.escape(keyword) for keyword in keywords)
            self.stakeholder_patterns[role] = re.compile(pattern, re.IGNORECASE)

        # Impact severity indicators
        self.high_impact_terms = [
            "must",
            "required",
            "mandatory",
            "shall",
            "prohibited",
            "penalty",
            "fine",
            "violation",
            "enforcement",
        ]

        self.medium_impact_terms = [
            "should",
            "recommended",
            "encouraged",
            "may",
            "allowed",
            "guidelines",
            "standards",
            "procedures",
        ]

        self.low_impact_terms = [
            "voluntary",
            "optional",
            "advisory",
            "suggestion",
            "guidance",
        ]

    def analyze_impacts(
        self, policy_text: str, policy_title: str
    ) -> list[StakeholderImpact]:
        """
        Analyze stakeholder impacts from policy text

        Args:
            policy_text: Full policy text
            policy_title: Policy title

        Returns:
            List of StakeholderImpact objects
        """
        impacts = []
        combined_text = f"{policy_title} {policy_text}".lower()

        # Find stakeholder mentions
        for role, pattern in self.stakeholder_patterns.items():
            matches = pattern.findall(combined_text)

            if matches:
                # Determine impact severity
                severity = self._determine_impact_severity(combined_text, role)

                # Extract affected areas
                affected_areas = self._extract_affected_areas(combined_text, role)

                # Generate impact description
                description = self._generate_impact_description(
                    combined_text, role, severity
                )

                impact = StakeholderImpact(
                    stakeholder_group=role.replace("_", " ").title(),
                    impact_severity=severity,
                    description=description,
                    affected_areas=affected_areas,
                )

                impacts.append(impact)

        # If no specific stakeholders found, analyze for general groups
        if not impacts:
            impacts = self._analyze_general_impacts(combined_text)

        return impacts[:5]  # Limit to top 5 most relevant impacts

    def _determine_impact_severity(
        self, text: str, stakeholder_role: str
    ) -> ImpactSeverity:
        """Determine the severity of impact on a stakeholder"""

        # Count severity indicators
        high_count = sum(1 for term in self.high_impact_terms if term in text)
        medium_count = sum(1 for term in self.medium_impact_terms if term in text)
        sum(1 for term in self.low_impact_terms if term in text)

        # Check for role-specific high impact indicators
        role_high_impact = {
            "renter": ["eviction", "rent increase", "lease termination"],
            "employee": ["termination", "wage reduction", "layoff"],
            "business_owner": ["license revocation", "shutdown", "penalty"],
        }

        if stakeholder_role in role_high_impact:
            for term in role_high_impact[stakeholder_role]:
                if term in text:
                    high_count += 2

        # Determine severity based on counts
        if high_count >= 2:
            return ImpactSeverity.HIGH
        elif medium_count >= 2 or high_count >= 1:
            return ImpactSeverity.MEDIUM
        else:
            return ImpactSeverity.LOW

    def _extract_affected_areas(self, text: str, stakeholder_role: str) -> list[str]:
        """Extract areas affected by the policy for a stakeholder"""

        areas = []

        # Common affected areas by role
        role_areas = {
            "renter": [
                "housing costs",
                "tenant rights",
                "lease terms",
                "eviction protection",
            ],
            "employee": ["wages", "benefits", "working conditions", "job security"],
            "business_owner": ["licensing", "regulations", "taxes", "operations"],
            "student": ["education funding", "tuition", "transportation", "housing"],
            "parent": ["childcare", "education", "family benefits", "safety"],
            "senior": ["healthcare", "social security", "housing", "transportation"],
        }

        if stakeholder_role in role_areas:
            for area in role_areas[stakeholder_role]:
                if any(word in text for word in area.split()):
                    areas.append(area)

        return areas[:3]  # Limit to top 3 areas

    def _generate_impact_description(
        self, text: str, stakeholder_role: str, severity: ImpactSeverity
    ) -> str:
        """Generate a description of the impact"""

        role_display = stakeholder_role.replace("_", " ").title()

        if severity == ImpactSeverity.HIGH:
            return f"This policy has significant implications for {role_display}s with mandatory requirements or restrictions."
        elif severity == ImpactSeverity.MEDIUM:
            return f"This policy moderately affects {role_display}s with new guidelines or procedures."
        else:
            return f"This policy has minor relevance for {role_display}s with optional or advisory provisions."

    def _analyze_general_impacts(self, text: str) -> list[StakeholderImpact]:
        """Analyze general impacts when specific stakeholders aren't mentioned"""

        impacts = []

        # Look for general impact indicators
        if any(term in text for term in ["public", "citizen", "resident", "community"]):
            impacts.append(
                StakeholderImpact(
                    stakeholder_group="General Public",
                    impact_severity=ImpactSeverity.MEDIUM,
                    description="This policy affects the general public and community members.",
                    affected_areas=["public services", "community welfare"],
                )
            )

        return impacts


class PolicyCache:
    """
    Simple in-memory cache for policy results
    """

    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.cache = {}
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Any | None:
        """Get item from cache if not expired"""
        if key in self.cache:
            item, timestamp = self.cache[key]

            # Check if expired
            if (datetime.now() - timestamp).total_seconds() > self.ttl_hours * 3600:
                del self.cache[key]
                return None

            return item

        return None

    def set(self, key: str, value: Any) -> None:
        """Set item in cache with current timestamp"""
        # Remove oldest items if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        self.cache[key] = (value, datetime.now())

    def clear(self) -> None:
        """Clear the cache"""
        self.cache.clear()
        self.logger.info("Policy cache cleared") 