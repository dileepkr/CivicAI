"""
Webset Management System for Policy Discovery

This module provides structured policy collection and monitoring using Exa's Webset API.
It creates organized containers for different policy domains and government levels.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from exa_py import Exa

from .config import DOMAIN_KEYWORDS, GOVERNMENT_DOMAINS
from .models import GovernmentLevel, PolicyDomain, PolicyResult, UserContext


class WebsetManager:
    """
    Manages Exa Websets for structured policy collection and monitoring
    """

    def __init__(self, exa_client: Exa):
        """
        Initialize the Webset Manager
        
        Args:
            exa_client: Configured Exa API client
        """
        self.exa = exa_client
        self.logger = logging.getLogger(__name__)
        
        # Cache for webset IDs to avoid repeated API calls
        self._webset_cache: Dict[str, str] = {}
        
        # Webset configuration
        self.webset_config = {
            "federal_housing": {
                "query": "Federal housing policies, rent control, affordable housing, HUD regulations, fair housing laws",
                "domains": GOVERNMENT_DOMAINS.get("federal", []),
                "entity": {"type": "custom", "description": "Federal housing policy documents and regulations"}
            },
            "state_housing": {
                "query": "California housing legislation, state rent control laws, tenant protection, housing development policies",
                "domains": ["calmatters.digitaldemocracy.org"],
                "entity": {"type": "custom", "description": "California state housing policy documents"}
            },
            "local_housing": {
                "query": "San Francisco housing ordinances, local rent control, zoning policies, affordable housing programs",
                "domains": GOVERNMENT_DOMAINS.get("local", []),
                "entity": {"type": "custom", "description": "San Francisco local housing policy documents"}
            },
            "federal_labor": {
                "query": "Federal labor laws, minimum wage, worker classification, employment regulations, NLRB policies",
                "domains": GOVERNMENT_DOMAINS.get("federal", []),
                "entity": {"type": "custom", "description": "Federal labor policy documents and regulations"}
            },
            "state_labor": {
                "query": "California labor legislation, worker protection laws, gig economy regulation, employment standards",
                "domains": ["calmatters.digitaldemocracy.org"],
                "entity": {"type": "custom", "description": "California state labor policy documents"}
            },
            "local_labor": {
                "query": "San Francisco labor ordinances, local minimum wage, worker protection, employment policies",
                "domains": GOVERNMENT_DOMAINS.get("local", []),
                "entity": {"type": "custom", "description": "San Francisco local labor policy documents"}
            },
            "state_general": {
                "query": "California legislation, state bills, government policies, public safety, environment, business regulation",
                "domains": ["calmatters.digitaldemocracy.org"],
                "entity": {"type": "custom", "description": "General California state policy documents"}
            }
        }

    async def initialize_websets(self) -> Dict[str, str]:
        """
        Initialize all policy websets for structured collection
        
        Returns:
            Dictionary mapping webset names to webset IDs
        """
        self.logger.info("Initializing policy websets...")
        
        webset_ids = {}
        
        for webset_name, config in self.webset_config.items():
            try:
                webset_id = await self._create_or_get_webset(webset_name, config)
                webset_ids[webset_name] = webset_id
                self._webset_cache[webset_name] = webset_id
                self.logger.info(f"Initialized webset '{webset_name}': {webset_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize webset '{webset_name}': {e}")
                continue
        
        return webset_ids

    async def _create_or_get_webset(self, webset_name: str, config: Dict[str, Any]) -> str:
        """
        Create a new webset or get existing one by external ID
        
        Args:
            webset_name: Name of the webset
            config: Webset configuration
            
        Returns:
            Webset ID
        """
        try:
            # Try to create webset with external ID
            webset_params = {
                "externalId": f"civicai_{webset_name}",
                "search": {
                    "query": config["query"],
                    "entity": config["entity"],
                    "count": 50,  # Start with moderate collection size
                    "criteria": self._generate_policy_criteria(webset_name),
                    "recall": True  # Get recall analysis
                },
                "enrichments": self._generate_enrichments(),
                "metadata": {
                    "domain": webset_name.split("_")[1] if "_" in webset_name else "general",
                    "government_level": webset_name.split("_")[0] if "_" in webset_name else "mixed",
                    "created_by": "civicai_policy_discovery",
                    "purpose": "automated_policy_collection"
                }
            }
            
            # Create the webset
            response = self.exa.websets.create(params=webset_params)
            return response.id
            
        except Exception as e:
            if "already exists" in str(e):
                # Webset with this external ID already exists, get it
                self.logger.info(f"Webset {webset_name} already exists, retrieving...")
                return await self._get_existing_webset(f"civicai_{webset_name}")
            else:
                raise e

    async def _get_existing_webset(self, external_id: str) -> str:
        """
        Get existing webset by external ID
        
        Args:
            external_id: External ID of the webset
            
        Returns:
            Webset ID
        """
        try:
            # List websets and find by external ID
            websets = self.exa.websets.list()
            for webset in websets.data:
                if webset.external_id == external_id:
                    return webset.id
            
            raise ValueError(f"Webset with external ID {external_id} not found")
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve existing webset: {e}")
            raise

    def _generate_policy_criteria(self, webset_name: str) -> List[Dict[str, str]]:
        """
        Generate evaluation criteria for policy websets
        
        Args:
            webset_name: Name of the webset
            
        Returns:
            List of criteria for policy evaluation
        """
        base_criteria = [
            {
                "description": "Document is an official government policy, law, regulation, or bill"
            },
            {
                "description": "Document contains actionable policy content, not just news or commentary"
            },
            {
                "description": "Document is from an official government source or legislative body"
            }
        ]
        
        # Add domain-specific criteria
        if "housing" in webset_name:
            base_criteria.append({
                "description": "Document relates to housing policy, rent control, zoning, tenant rights, or affordable housing"
            })
        elif "labor" in webset_name:
            base_criteria.append({
                "description": "Document relates to labor policy, employment law, worker rights, or workplace regulations"
            })
        
        # Add government level criteria
        if "federal" in webset_name:
            base_criteria.append({
                "description": "Document is from federal government agencies, Congress, or federal regulatory bodies"
            })
        elif "state" in webset_name:
            base_criteria.append({
                "description": "Document is from California state government, legislature, or state agencies"
            })
        elif "local" in webset_name:
            base_criteria.append({
                "description": "Document is from San Francisco city government, board of supervisors, or local agencies"
            })
        
        return base_criteria

    def _generate_enrichments(self) -> List[Dict[str, Any]]:
        """
        Generate enrichment configurations for policy extraction
        
        Returns:
            List of enrichment configurations
        """
        return [
            {
                "description": "Extract the effective date or implementation date of the policy",
                "format": "date"
            },
            {
                "description": "Extract the policy status: proposed, active, under review, expired, or superseded",
                "format": "options",
                "options": [
                    {"label": "proposed"},
                    {"label": "active"},
                    {"label": "under_review"},
                    {"label": "expired"},
                    {"label": "superseded"}
                ]
            },
            {
                "description": "Extract the primary stakeholder groups affected by this policy (e.g., renters, landlords, employees, employers, businesses)",
                "format": "text"
            },
            {
                "description": "Extract key deadlines or important dates mentioned in the policy",
                "format": "text"
            },
            {
                "description": "Extract the source agency or government body responsible for the policy",
                "format": "text"
            }
        ]

    async def query_websets(self, user_context: UserContext) -> List[PolicyResult]:
        """
        Query relevant websets based on user context
        
        Args:
            user_context: User context for determining relevant websets
            
        Returns:
            List of policy results from websets
        """
        relevant_websets = self._determine_relevant_websets(user_context)
        
        policy_results = []
        
        for webset_name in relevant_websets:
            try:
                webset_id = self._webset_cache.get(webset_name)
                if not webset_id:
                    continue
                
                # Get items from webset
                items = await self._get_webset_items(webset_id)
                
                # Convert to PolicyResult objects
                for item in items:
                    policy_result = self._convert_webset_item_to_policy_result(
                        item, webset_name, user_context
                    )
                    if policy_result:
                        policy_results.append(policy_result)
                        
            except Exception as e:
                self.logger.error(f"Failed to query webset {webset_name}: {e}")
                continue
        
        return policy_results

    def _determine_relevant_websets(self, user_context: UserContext) -> List[str]:
        """
        Determine which websets are relevant based on user context
        
        Args:
            user_context: User context
            
        Returns:
            List of relevant webset names
        """
        relevant_websets = []
        
        # Determine domains from interests and stakeholder roles
        relevant_domains = set()
        
        # Map interests to domains
        for interest in user_context.interests:
            interest_lower = interest.lower()
            if any(keyword in interest_lower for keyword in ["rent", "housing", "tenant", "landlord", "zoning"]):
                relevant_domains.add("housing")
            if any(keyword in interest_lower for keyword in ["labor", "worker", "employee", "wage", "employment"]):
                relevant_domains.add("labor")
        
        # Map stakeholder roles to domains
        for role in user_context.stakeholder_roles:
            role_lower = role.lower()
            if role_lower in ["renter", "homeowner", "landlord"]:
                relevant_domains.add("housing")
            if role_lower in ["employee", "employer", "business_owner"]:
                relevant_domains.add("labor")
        
        # If no specific domains, include general
        if not relevant_domains:
            relevant_domains.add("general")
        
        # Build webset names
        government_levels = ["federal", "state", "local"]
        
        for domain in relevant_domains:
            for level in government_levels:
                webset_name = f"{level}_{domain}"
                if webset_name in self.webset_config:
                    relevant_websets.append(webset_name)
        
        # Always include state general for broader coverage
        if "state_general" not in relevant_websets:
            relevant_websets.append("state_general")
        
        return relevant_websets

    async def _get_webset_items(self, webset_id: str) -> List[Dict[str, Any]]:
        """
        Get items from a webset
        
        Args:
            webset_id: ID of the webset
            
        Returns:
            List of webset items
        """
        try:
            response = self.exa.websets.items.list(webset_id=webset_id, limit=50)
            return response.data
        except Exception as e:
            self.logger.error(f"Failed to get items from webset {webset_id}: {e}")
            return []

    def _convert_webset_item_to_policy_result(
        self, 
        item: Dict[str, Any], 
        webset_name: str, 
        user_context: UserContext
    ) -> Optional[PolicyResult]:
        """
        Convert a webset item to a PolicyResult object
        
        Args:
            item: Webset item
            webset_name: Name of the source webset
            user_context: User context for relevance scoring
            
        Returns:
            PolicyResult object or None if conversion fails
        """
        try:
            from .utils import PolicyClassifier, StakeholderAnalyzer
            
            # Extract basic information
            title = item.get("title", "")
            url = item.get("url", "")
            content = item.get("text", "") or ""
            
            if not title or not url:
                return None
            
            # Determine government level from webset name
            government_level = GovernmentLevel.FEDERAL
            if "state" in webset_name:
                government_level = GovernmentLevel.STATE
            elif "local" in webset_name:
                government_level = GovernmentLevel.LOCAL
            
            # Determine domain from webset name
            domain = PolicyDomain.HOUSING  # Default
            if "labor" in webset_name:
                domain = PolicyDomain.LABOR
            elif "housing" in webset_name:
                domain = PolicyDomain.HOUSING
            else:
                # Use classifier for general websets
                classifier = PolicyClassifier()
                domain = classifier.classify_domain(title + " " + content)
            
            # Extract enriched data
            enrichment_data = item.get("enrichments", {})
            
            # Determine policy status from enrichment or classify
            status_enrichment = enrichment_data.get("policy_status")
            if status_enrichment:
                from .models import PolicyStatus
                status_mapping = {
                    "proposed": PolicyStatus.PROPOSED,
                    "active": PolicyStatus.ACTIVE,
                    "under_review": PolicyStatus.UNDER_REVIEW,
                    "expired": PolicyStatus.EXPIRED,
                    "superseded": PolicyStatus.SUPERSEDED
                }
                status = status_mapping.get(status_enrichment.lower(), PolicyStatus.PROPOSED)
            else:
                classifier = PolicyClassifier()
                status = classifier.classify_status(content)
            
            # Extract effective date
            effective_date = enrichment_data.get("effective_date")
            if effective_date:
                try:
                    last_updated = datetime.fromisoformat(effective_date.replace("Z", "+00:00"))
                except:
                    last_updated = datetime.now()
            else:
                last_updated = datetime.now()
            
            # Extract stakeholder impacts
            stakeholder_text = enrichment_data.get("stakeholder_groups", "")
            if stakeholder_text:
                stakeholder_analyzer = StakeholderAnalyzer()
                stakeholder_impacts = stakeholder_analyzer.analyze_impacts(content, title)
            else:
                stakeholder_impacts = []
            
            # Extract source agency
            source_agency = enrichment_data.get("source_agency", "")
            if not source_agency:
                source_agency = self._extract_agency_from_url(url, government_level)
            
            # Generate summary
            summary = self._generate_summary(content)
            
            # Calculate confidence score
            confidence_score = self._calculate_webset_confidence_score(item, user_context)
            
            return PolicyResult(
                title=title,
                summary=summary,
                url=url,
                government_level=government_level,
                domain=domain,
                status=status,
                stakeholder_impacts=stakeholder_impacts,
                last_updated=last_updated,
                source_agency=source_agency,
                document_type=self._classify_document_type(title, url),
                key_deadlines=[],
                related_policies=[],
                content_preview=content[:500] if content else None,
                confidence_score=confidence_score,
            )
            
        except Exception as e:
            self.logger.error(f"Failed to convert webset item to policy result: {e}")
            return None

    def _extract_agency_from_url(self, url: str, level: GovernmentLevel) -> str:
        """Extract source agency from URL"""
        if "congress.gov" in url:
            return "U.S. Congress"
        elif "regulations.gov" in url:
            return "Federal Agencies"
        elif "ca.gov" in url:
            return "State of California"
        elif "calmatters.digitaldemocracy.org" in url:
            return "California Legislature"
        elif "sf.gov" in url or "sfgov.org" in url:
            return "City and County of San Francisco"
        else:
            return f"{level.value.title()} Government"

    def _classify_document_type(self, title: str, url: str) -> str:
        """Classify the type of government document"""
        title_lower = title.lower()
        url_lower = url.lower()

        if "bill" in title_lower or "hr." in title_lower or "sb." in title_lower:
            return "Legislation"
        elif "regulation" in title_lower or "cfr" in url_lower:
            return "Regulation"
        elif "ordinance" in title_lower:
            return "Ordinance"
        elif "executive order" in title_lower:
            return "Executive Order"
        else:
            return "Policy Document"

    def _generate_summary(self, content: str) -> str:
        """Generate a concise summary of policy content"""
        if not content:
            return "No summary available"

        # Simple extractive summarization - take first few sentences
        sentences = content.split(". ")
        summary_sentences = sentences[:3]
        summary = ". ".join(summary_sentences)

        if len(summary) > 300:
            summary = summary[:300] + "..."

        return summary

    def _calculate_webset_confidence_score(self, item: Dict[str, Any], user_context: UserContext) -> float:
        """
        Calculate confidence score for webset items
        
        Args:
            item: Webset item
            user_context: User context
            
        Returns:
            Confidence score between 0 and 1
        """
        score = 0.5  # Base score for webset items (pre-filtered)
        
        # Boost for official government domains
        url = item.get("url", "")
        if any(domain in url for domain in ["gov", "legislature"]):
            score += 0.3
        
        # Boost for content length
        content = item.get("text", "")
        if content:
            content_length = len(content)
            if content_length > 2000:
                score += 0.2
            elif content_length > 500:
                score += 0.1
        
        # Boost for enrichment data availability
        enrichments = item.get("enrichments", {})
        if enrichments:
            score += 0.1 * min(len(enrichments), 3)  # Up to 0.3 boost
        
        # Boost for user interest relevance
        title = item.get("title", "").lower()
        content_lower = content.lower() if content else ""
        
        for interest in user_context.interests:
            if interest.lower() in title or interest.lower() in content_lower:
                score += 0.1
        
        return min(score, 1.0)

    async def setup_monitors(self) -> Dict[str, str]:
        """
        Set up monitoring for all websets to automatically collect new policies
        
        Returns:
            Dictionary mapping webset names to monitor IDs
        """
        self.logger.info("Setting up webset monitors...")
        
        monitor_ids = {}
        
        for webset_name, webset_id in self._webset_cache.items():
            try:
                monitor_id = await self._create_webset_monitor(webset_name, webset_id)
                monitor_ids[webset_name] = monitor_id
                self.logger.info(f"Created monitor for webset '{webset_name}': {monitor_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to create monitor for webset '{webset_name}': {e}")
                continue
        
        return monitor_ids

    async def _create_webset_monitor(self, webset_name: str, webset_id: str) -> str:
        """
        Create a monitor for a specific webset
        
        Args:
            webset_name: Name of the webset
            webset_id: ID of the webset
            
        Returns:
            Monitor ID
        """
        config = self.webset_config[webset_name]
        
        monitor_params = {
            "websetId": webset_id,
            "cadence": {
                "cron": "0 6 * * *",  # Daily at 6 AM UTC
                "timezone": "America/Los_Angeles"  # Pacific Time
            },
            "behavior": {
                "type": "search",
                "config": {
                    "query": config["query"],
                    "entity": config["entity"],
                    "count": 10,  # Find up to 10 new policies per day
                    "behavior": "append",  # Add to existing collection
                    "criteria": self._generate_policy_criteria(webset_name)
                }
            },
            "metadata": {
                "webset_name": webset_name,
                "purpose": "daily_policy_monitoring"
            }
        }
        
        response = self.exa.websets.monitors.create(params=monitor_params)
        return response.id

    async def get_webset_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all managed websets
        
        Returns:
            Dictionary with status information for each webset
        """
        status_info = {}
        
        for webset_name, webset_id in self._webset_cache.items():
            try:
                webset = self.exa.websets.get(webset_id=webset_id)
                
                # Get item count
                items_response = self.exa.websets.items.list(webset_id=webset_id, limit=1)
                item_count = getattr(items_response, 'total', 0)
                
                status_info[webset_name] = {
                    "id": webset_id,
                    "status": webset.status,
                    "item_count": item_count,
                    "created_at": webset.created_at,
                    "updated_at": webset.updated_at,
                    "searches": len(webset.searches),
                    "monitors": len(webset.monitors),
                    "enrichments": len(webset.enrichments)
                }
                
            except Exception as e:
                self.logger.error(f"Failed to get status for webset {webset_name}: {e}")
                status_info[webset_name] = {"error": str(e)}
        
        return status_info