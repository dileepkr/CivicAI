"""
Core PolicyDiscoveryAgent implementation using CrewAI framework
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from crewai import Agent
from exa_py import Exa

from .config import (
    DOMAIN_KEYWORDS,
    EXA_API_KEY,
    GOVERNMENT_DOMAINS,
    SEARCH_CONFIG,
    STAKEHOLDER_KEYWORDS,
)
from .models import (
    GovernmentLevel,
    ImpactSeverity,
    PolicyDiscoveryResult,
    PolicyDiscoveryResponse,
    PolicyDocument,
    PolicyDomain,
    PolicyResult,
    PolicyStatus,
    RegulationTiming,
    SearchParameters,
    UserContext,
    UserProfile,
)
from .search import PolicySearchEngine
from .utils import PolicyClassifier, StakeholderAnalyzer
from .webset_manager import WebsetManager


class PolicyDiscoveryAgent:
    """
    CrewAI agent for discovering policies across multiple government levels
    """

    def __init__(self, exa_api_key: str | None = None):
        """
        Initialize the Policy Discovery Agent

        Args:
            exa_api_key: API key for Exa search service
        """
        self.exa_api_key = exa_api_key or EXA_API_KEY
        if not self.exa_api_key:
            raise ValueError("Exa API key is required")

        self.exa = Exa(api_key=self.exa_api_key)
        self.search_engine = PolicySearchEngine(self.exa)
        self.webset_manager = WebsetManager(self.exa)
        self.classifier = PolicyClassifier()
        self.stakeholder_analyzer = StakeholderAnalyzer()
        
        # Track initialization status
        self._websets_initialized = False

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Create the CrewAI agent
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create and configure the CrewAI agent"""
        return Agent(
            role="Universal Policy Discovery Specialist",
            goal="""Discover and categorize relevant policies across all government levels
                    (Federal, State of California, City of San Francisco) based on user context
                    and stakeholder roles. Provide comprehensive policy intelligence that enables
                    informed civic engagement and multi-stakeholder debate.""",
            backstory="""You are an expert in navigating complex government policy landscapes
                        with deep knowledge of Federal, California State, and San Francisco local
                        governance structures. You excel at identifying policies that impact specific
                        stakeholder groups and understanding the interconnections between different
                        levels of government regulation. Your expertise includes policy analysis,
                        stakeholder impact assessment, and translating complex governmental processes
                        into actionable insights for civic engagement.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3,
        )

    async def discover_policies(
        self,
        user_context: UserContext,
        domains: list[PolicyDomain] | None = None,
        government_levels: list[GovernmentLevel] | None = None,
        use_websets: bool = True,
    ) -> PolicyDiscoveryResult:
        """
        Main policy discovery method using hybrid Webset + Search approach

        Args:
            user_context: User context for personalized search
            domains: Specific policy domains to search (optional)
            government_levels: Specific government levels to search (optional)
            use_websets: Whether to include webset results (default: True)

        Returns:
            PolicyDiscoveryResult with discovered policies
        """
        start_time = datetime.now()

        # Initialize websets if not already done and websets are enabled
        if use_websets and not self._websets_initialized:
            try:
                await self.initialize_websets()
            except Exception as e:
                self.logger.warning(f"Failed to initialize websets, continuing with search only: {e}")
                use_websets = False

        # 1. Get policies from websets (structured collection)
        webset_policies = []
        if use_websets:
            try:
                webset_policies = await self.webset_manager.query_websets(user_context)
                self.logger.info(f"Retrieved {len(webset_policies)} policies from websets")
            except Exception as e:
                self.logger.warning(f"Failed to query websets: {e}")

        # 2. Get real-time policies from search API
        search_policies = await self._execute_live_search(
            user_context, domains, government_levels
        )
        self.logger.info(f"Retrieved {len(search_policies)} policies from live search")

        # 3. Combine and deduplicate results
        all_policies = self._combine_webset_and_search_results(webset_policies, search_policies)
        
        # Organize policies by government level
        federal_policies = [p for p in all_policies if p.government_level == GovernmentLevel.FEDERAL]
        state_policies = [p for p in all_policies if p.government_level == GovernmentLevel.STATE]
        local_policies = [p for p in all_policies if p.government_level == GovernmentLevel.LOCAL]
        
        # Generate stakeholder impact mapping
        stakeholder_impact_map = self._create_stakeholder_impact_map(
            all_policies, user_context.stakeholder_roles
        )

        # Rank policies by relevance
        priority_ranking = self._rank_policies_by_relevance(all_policies, user_context)

        # Find related policies
        related_policies = await self._find_related_policies(all_policies)
        
        # Generate AI-powered policy analysis if user has specific interests
        policy_analysis = None
        if user_context.interests:
            analysis_question = f"What are the key policy implications for {', '.join(user_context.interests)} in {user_context.location}?"
            policy_analysis = await self.search_engine.analyze_policy_question(analysis_question)

        search_time = (datetime.now() - start_time).total_seconds()

        return PolicyDiscoveryResult(
            federal_policies=federal_policies,
            state_policies=state_policies,
            local_policies=local_policies,
            stakeholder_impact_map=stakeholder_impact_map,
            priority_ranking=priority_ranking,
            related_policies=related_policies,
            search_metadata={
                "search_time": search_time,
                "user_context": user_context,
                "webset_policies_count": len(webset_policies),
                "search_policies_count": len(search_policies),
                "policy_analysis": policy_analysis,
                "hybrid_mode": use_websets,
            },
            total_found=len(all_policies),
            search_time=search_time,
        )

    def _generate_search_parameters(
        self,
        user_context: UserContext,
        domains: list[PolicyDomain] | None,
        government_levels: list[GovernmentLevel] | None,
    ) -> SearchParameters:
        """Generate search parameters from user context"""

        # Determine domains from user context if not specified
        if not domains:
            domains = self._infer_domains_from_context(user_context)

        # Set default government levels if not specified
        if not government_levels:
            government_levels = list(GovernmentLevel)

        return SearchParameters(
            user_location=user_context.location,
            stakeholder_roles=user_context.stakeholder_roles,
            domains=domains,
            government_levels=government_levels,
            regulation_timing=user_context.regulation_timing,
            max_results=SEARCH_CONFIG["max_results_per_level"],
        )

    def _infer_domains_from_context(
        self, user_context: UserContext
    ) -> list[PolicyDomain]:
        """Infer relevant policy domains from user context"""
        domains = []

        # Map stakeholder roles to domains
        role_domain_map = {
            "renter": [PolicyDomain.HOUSING],
            "homeowner": [PolicyDomain.HOUSING],
            "employee": [PolicyDomain.LABOR],
            "business_owner": [PolicyDomain.BUSINESS, PolicyDomain.LABOR],
            "student": [PolicyDomain.TRANSPORTATION],
            "parent": [PolicyDomain.PUBLIC_SAFETY],
        }

        for role in user_context.stakeholder_roles:
            if role in role_domain_map:
                domains.extend(role_domain_map[role])

        # If no specific domains found, include all
        if not domains:
            domains = list(PolicyDomain)

        return list(set(domains))  # Remove duplicates

    async def _search_government_level(
        self, level: GovernmentLevel, search_params: SearchParameters
    ) -> list[PolicyResult]:
        """Search specific government level for policies"""

        queries = self._generate_search_queries(level, search_params)
        domains = GOVERNMENT_DOMAINS.get(level.value, [])

        results = []
        seen_urls = set()  # Track URLs within this government level search

        for query in queries:
            try:
                # Execute Exa search
                search_response = await self.search_engine.search_policies(
                    query=query,
                    domains=domains,
                    max_results=search_params.max_results // len(queries),
                )

                # Process and classify results
                for item in search_response:
                    # Skip if we've already seen this URL in this government level
                    url = item.get("url", "")
                    if url in seen_urls:
                        continue
                    
                    policy = self._create_policy_result(item, level)
                    if policy and self._matches_regulation_timing(policy, search_params.regulation_timing):
                        seen_urls.add(url)
                        results.append(policy)

            except Exception as e:
                self.logger.error(f"Search failed for query '{query}': {e}")
                continue

        return results

    def _generate_search_queries(
        self, level: GovernmentLevel, search_params: SearchParameters
    ) -> list[str]:
        """Generate intelligent search queries based on government level and context"""

        queries = []

        # Base queries for each domain
        for domain in search_params.domains:
            domain_keywords = DOMAIN_KEYWORDS.get(domain.value, [])

            for keyword in domain_keywords[:3]:  # Limit to top 3 keywords
                base_query = ""
                if level == GovernmentLevel.FEDERAL:
                    base_query = f"federal {keyword} policy regulation law"
                elif level == GovernmentLevel.STATE:
                    base_query = f"California {keyword} state law bill regulation"
                elif level == GovernmentLevel.LOCAL:
                    base_query = f"San Francisco {keyword} ordinance local policy"

                # Add timing-specific terms
                if search_params.regulation_timing == RegulationTiming.FUTURE:
                    if level == GovernmentLevel.FEDERAL:
                        query = f"{base_query} proposed bill congress introduced"
                    elif level == GovernmentLevel.STATE:
                        query = f"{base_query} proposed bill introduced assembly senate"
                    else:
                        query = f"{base_query} proposed ordinance introduction"
                elif search_params.regulation_timing == RegulationTiming.CURRENT:
                    if level == GovernmentLevel.FEDERAL:
                        query = f"{base_query} enacted signed passed law"
                    elif level == GovernmentLevel.STATE:
                        query = f"{base_query} enacted chaptered signed law"
                    else:
                        query = f"{base_query} enacted passed ordinance"
                else:
                    query = base_query

                queries.append(query)

        # Add stakeholder-specific queries
        for role in search_params.stakeholder_roles:
            if role in STAKEHOLDER_KEYWORDS:
                role_keywords = STAKEHOLDER_KEYWORDS[role]

                for keyword in role_keywords[:2]:  # Limit to top 2 keywords
                    base_query = ""
                    if level == GovernmentLevel.FEDERAL:
                        base_query = f"federal {keyword} policy law"
                    elif level == GovernmentLevel.STATE:
                        base_query = f"California {keyword} legislation"
                    elif level == GovernmentLevel.LOCAL:
                        base_query = f"San Francisco {keyword} ordinance"

                    # Add timing-specific terms to stakeholder queries
                    if search_params.regulation_timing == RegulationTiming.FUTURE:
                        query = f"{base_query} proposed introduced"
                    elif search_params.regulation_timing == RegulationTiming.CURRENT:
                        query = f"{base_query} enacted passed"
                    else:
                        query = base_query

                    queries.append(query)

        # Add generic searches for broader coverage
        if level == GovernmentLevel.STATE and search_params.regulation_timing == RegulationTiming.FUTURE:
            # Add broader searches that might catch bills not found by specific terms
            from datetime import datetime
            current_year = datetime.now().year
            
            additional_searches = []
            for domain in search_params.domains:
                if domain == PolicyDomain.HOUSING:
                    additional_searches.extend([
                        f"California housing legislation {current_year} proposed",
                        "California tenant protection bills introduced",
                        "California housing policy reform proposed"
                    ])
                elif domain == PolicyDomain.LABOR:
                    additional_searches.extend([
                        f"California labor legislation {current_year} proposed",
                        "California worker protection bills introduced"
                    ])
                elif domain == PolicyDomain.BUSINESS:
                    additional_searches.extend([
                        f"California business legislation {current_year} proposed",
                        "California business regulation bills introduced"
                    ])
            queries.extend(additional_searches[:3])  # Limit additional searches

        self.logger.info(f"Generated {len(queries)} queries for {level.value}: {queries[:5]}...")  # Log first 5 queries
        return queries[:10]  # Keep reasonable limit

    def _create_policy_result(
        self, search_item: dict[str, Any], level: GovernmentLevel
    ) -> PolicyResult | None:
        """Create PolicyResult from search item"""

        try:
            # Extract basic information
            title = search_item.get("title", "")
            url = search_item.get("url", "")
            content = search_item.get("text", "") or ""

            if not title or not url:
                return None

            # Classify policy domain
            domain = self.classifier.classify_domain(title + " " + content)

            # Determine policy status
            status = self.classifier.classify_status(content)

            # Generate summary
            summary = self._generate_summary(content)

            # Analyze stakeholder impacts
            stakeholder_impacts = self.stakeholder_analyzer.analyze_impacts(
                content, title
            )

            # Extract metadata
            last_updated = self._extract_date(search_item)
            source_agency = self._extract_agency(url, level)

            return PolicyResult(
                title=title,
                summary=summary,
                url=url,
                government_level=level,
                domain=domain,
                status=status,
                stakeholder_impacts=stakeholder_impacts,
                last_updated=last_updated,
                source_agency=source_agency,
                document_type=self._classify_document_type(title, url),
                key_deadlines=[],
                related_policies=[],
                content_preview=content[:500] if content else None,
                confidence_score=self._calculate_confidence(search_item),
            )

        except Exception as e:
            self.logger.error(f"Failed to create PolicyResult: {e}")
            return None

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

    def _extract_date(self, search_item: dict[str, Any]) -> datetime:
        """Extract date from search item"""
        # Try to find date in published_date or similar fields
        date_str = search_item.get("published_date") or search_item.get("date")

        if date_str:
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Default to current date
        return datetime.now()

    def _extract_agency(self, url: str, level: GovernmentLevel) -> str:
        """Extract source agency from URL"""
        if "congress.gov" in url:
            return "U.S. Congress"
        elif "regulations.gov" in url:
            return "Federal Agencies"
        elif "ca.gov" in url:
            return "State of California"
        elif "sf.gov" in url:
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

    def _calculate_confidence(self, search_item: dict[str, Any]) -> float:
        """Calculate confidence score for search result"""
        score = 0.3  # Lower base score

        # Boost score for government domains (higher weights for official sources)
        url = search_item.get("url", "")
        if any(domain in url for domain in GOVERNMENT_DOMAINS["federal"]):
            score += 0.4
        elif any(domain in url for domain in GOVERNMENT_DOMAINS["state"]):
            score += 0.35
        elif any(domain in url for domain in GOVERNMENT_DOMAINS["local"]):
            score += 0.3

        # Boost for recent content with date parsing
        published_date = search_item.get("published_date")
        if published_date:
            try:
                # Parse the date and check recency
                if published_date != "2000-01-01":  # Filter out default dates
                    date_obj = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
                    days_ago = (datetime.now(date_obj.tzinfo) - date_obj).days
                    if days_ago <= 90:  # Within 3 months
                        score += 0.3
                    elif days_ago <= 365:  # Within a year
                        score += 0.2
                    else:
                        score += 0.1
            except (ValueError, TypeError):
                score += 0.05  # Small boost for having any date

        # Boost for Exa search score if available
        exa_score = search_item.get("score", 0.0)
        if exa_score > 0:
            score += min(exa_score * 0.3, 0.3)  # Use Exa's relevance score

        # Boost for content length (more comprehensive content)
        content = search_item.get("text", "")
        if content:
            content_length = len(content)
            if content_length > 2000:
                score += 0.2
            elif content_length > 500:
                score += 0.1

        # Boost for highlight relevance (if available)
        highlights = search_item.get("highlights", [])
        highlight_scores = search_item.get("highlight_scores", [])
        if highlights and highlight_scores:
            # Use average highlight score as relevance boost
            avg_highlight_score = sum(highlight_scores) / len(highlight_scores)
            score += min(avg_highlight_score * 0.2, 0.2)

        return min(score, 1.0)

    def _create_stakeholder_impact_map(
        self, policies: list[PolicyResult], stakeholder_roles: list[str]
    ) -> dict[str, list[PolicyResult]]:
        """Create mapping of stakeholder groups to relevant policies"""

        impact_map = {role: [] for role in stakeholder_roles}

        for policy in policies:
            for impact in policy.stakeholder_impacts:
                for role in stakeholder_roles:
                    if role in impact.stakeholder_group.lower():
                        impact_map[role].append(policy)

        return impact_map

    def _rank_policies_by_relevance(
        self, policies: list[PolicyResult], user_context: UserContext
    ) -> list[PolicyResult]:
        """Rank policies by relevance to user context"""

        def relevance_score(policy: PolicyResult) -> float:
            score = policy.confidence_score

            # 1. Recency scoring (higher weight for recent policies)
            if policy.last_updated:
                try:
                    # Ensure both dates are timezone-aware or naive
                    now = datetime.now()
                    last_updated = policy.last_updated
                    
                    # Make both timezone-naive for comparison
                    if last_updated.tzinfo is not None:
                        last_updated = last_updated.replace(tzinfo=None)
                    
                    days_ago = (now - last_updated).days
                    if days_ago <= 30:  # Very recent
                        score += 0.4
                    elif days_ago <= 90:  # Recent
                        score += 0.3
                    elif days_ago <= 365:  # Within a year
                        score += 0.2
                    else:  # Older
                        score += 0.1
                except (TypeError, AttributeError):
                    score += 0.05  # Small boost for having any date

            # 2. Interest relevance scoring (check title, summary, and highlights against user interests)
            interest_relevance = 0.0
            policy_text = f"{policy.title} {policy.summary}".lower()
            
            # Check highlights if available (they contain the most relevant excerpts)
            highlights_text = ""
            if hasattr(policy, 'content_preview') and policy.content_preview:
                # Assume highlights might be in the content preview metadata
                highlights_text = policy.content_preview.lower()
            
            # Combined text for comprehensive interest matching
            combined_text = f"{policy_text} {highlights_text}"
            
            for interest in user_context.interests:
                interest_words = interest.lower().split()
                for word in interest_words:
                    if len(word) > 2:  # Skip very short words
                        if word in policy_text:
                            interest_relevance += 0.15  # Higher weight for title/summary
                        elif word in highlights_text:
                            interest_relevance += 0.1   # Medium weight for highlights
                        elif word in combined_text:
                            interest_relevance += 0.05  # Lower weight for general content
            score += min(interest_relevance, 0.6)  # Cap at 0.6

            # 3. Stakeholder role relevance
            for role in user_context.stakeholder_roles:
                # Direct role mention in title/summary
                if role.lower() in policy_text:
                    score += 0.3
                
                # Stakeholder impact analysis
                for impact in policy.stakeholder_impacts:
                    if role in impact.stakeholder_group.lower():
                        if impact.impact_severity == ImpactSeverity.HIGH:
                            score += 0.3
                        elif impact.impact_severity == ImpactSeverity.MEDIUM:
                            score += 0.2
                        else:
                            score += 0.1

            # 4. Government level relevance (prioritize based on directness)
            if policy.government_level == GovernmentLevel.LOCAL:
                score += 0.3  # Most direct impact
            elif policy.government_level == GovernmentLevel.STATE:
                score += 0.2
            elif policy.government_level == GovernmentLevel.FEDERAL:
                score += 0.1

            # 5. Policy status relevance (based on user timing preference)
            if user_context.regulation_timing == RegulationTiming.FUTURE:
                if policy.status == PolicyStatus.PROPOSED:
                    # Check if policy has already taken effect (should penalize)
                    if self._has_policy_taken_effect(policy):
                        score -= 0.5  # Heavy penalty for outdated "future" policies
                    else:
                        score += 0.4
                elif policy.status == PolicyStatus.UNDER_REVIEW:
                    score += 0.3
            elif user_context.regulation_timing == RegulationTiming.CURRENT:
                if policy.status == PolicyStatus.ACTIVE:
                    score += 0.4
                elif policy.status == PolicyStatus.PROPOSED and self._has_policy_taken_effect(policy):
                    score += 0.3  # Treat as current if already in effect
                elif policy.status == PolicyStatus.UNDER_REVIEW:
                    score += 0.2
            else:  # ALL
                if policy.status == PolicyStatus.ACTIVE:
                    score += 0.3
                elif policy.status == PolicyStatus.PROPOSED:
                    if self._has_policy_taken_effect(policy):
                        score += 0.2  # Treat as current
                    else:
                        score += 0.1  # True future policy

            # 6. Source credibility (boost official government sources)
            if any(domain in policy.url for domain in ["gov", "legislature", "sfplanning"]):
                score += 0.2

            return min(score, 3.0)  # Cap total score

        return sorted(policies, key=relevance_score, reverse=True)

    async def _find_related_policies(
        self, policies: list[PolicyResult]
    ) -> list[PolicyResult]:
        """Find policies related to the discovered set"""

        related = []
        seen_urls = set()
        
        # Track URLs from original policies to avoid duplicating them
        original_urls = {policy.url for policy in policies}

        # Use Exa's find_similar functionality for top policies
        for policy in policies[:5]:  # Limit to top 5 to avoid rate limits
            try:
                similar_results = await self.search_engine.find_similar_policies(
                    policy.url, max_results=3
                )

                for item in similar_results:
                    url = item.get("url", "")
                    # Skip if this URL is already in original policies or already seen in related
                    if url in original_urls or url in seen_urls:
                        continue
                        
                    related_policy = self._create_policy_result(
                        item, policy.government_level
                    )
                    if related_policy:
                        seen_urls.add(url)
                        related.append(related_policy)

            except Exception as e:
                self.logger.error(f"Failed to find similar policies: {e}")
                continue

        return related

    def _matches_regulation_timing(
        self, policy: PolicyResult, timing: RegulationTiming
    ) -> bool:
        """Check if policy matches the desired regulation timing"""
        
        if timing == RegulationTiming.ALL:
            return True
        elif timing == RegulationTiming.CURRENT:
            # Only include active, under_review, expired, or superseded policies (already passed)
            if policy.status in [
                PolicyStatus.ACTIVE,
                PolicyStatus.UNDER_REVIEW,
                PolicyStatus.EXPIRED,
                PolicyStatus.SUPERSEDED
            ]:
                return True
            # Also include "proposed" policies that have already taken effect based on dates
            if policy.status == PolicyStatus.PROPOSED:
                return self._has_policy_taken_effect(policy)
            return False
        elif timing == RegulationTiming.FUTURE:
            # Only include proposed policies that haven't taken effect yet
            if policy.status == PolicyStatus.PROPOSED:
                return not self._has_policy_taken_effect(policy)
            return False
        
        return True

    def _has_policy_taken_effect(self, policy: PolicyResult) -> bool:
        """Check if a policy has already taken effect based on content analysis"""
        now = datetime.now()
        
        # Check the title and summary for effective dates
        content = f"{policy.title} {policy.summary}".lower()
        
        # Look for patterns like "effective April 1, 2025", "starting January 1", etc.
        import re
        
        # More comprehensive date parsing
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 
            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Pattern for dates - generic for any year
        current_year = now.year
        future_years = [str(current_year), str(current_year + 1), str(current_year + 2)]
        
        date_patterns = [
            r'effective\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})',
            r'starting\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})',
            r'beginning\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})',
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY format
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD format
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    if len(match) == 3:
                        if match[0].lower() in month_map:  # Month name format
                            month = month_map[match[0].lower()]
                            day = int(match[1])
                            year = int(match[2])
                        elif match[2] in future_years and match[0].isdigit():  # MM/DD/YYYY
                            month = int(match[0])
                            day = int(match[1])
                            year = int(match[2])
                        elif len(match[0]) == 4:  # YYYY-MM-DD
                            year = int(match[0])
                            month = int(match[1])
                            day = int(match[2])
                        else:
                            continue
                            
                        # Only consider dates in current or future years
                        if year >= current_year:
                            effective_date = datetime(year, month, day)
                            if now >= effective_date:
                                return True
                except (ValueError, KeyError):
                    continue
        
        # If no specific date found but contains "upcoming" or "will" and we're past recent dates
        if "upcoming" in content and policy.last_updated:
            try:
                # If policy was last updated more than 6 months ago, it's likely no longer "upcoming"
                update_date = policy.last_updated
                if update_date.tzinfo is not None:
                    update_date = update_date.replace(tzinfo=None)
                months_ago = (now - update_date).days // 30
                if months_ago > 6:
                    return True
            except:
                pass
        
        return False

    def _deduplicate_policies(self, policies: list[PolicyResult]) -> list[PolicyResult]:
        """Remove duplicate policies based on URL and title similarity"""
        seen_urls = set()
        seen_titles = set()
        deduplicated = []
        
        for policy in policies:
            # Primary deduplication by URL (exact match)
            if policy.url in seen_urls:
                continue
            
            # Secondary deduplication by title (exact match)
            if policy.title in seen_titles:
                continue
            
            # Tertiary deduplication by similar titles (fuzzy match)
            title_words = set(policy.title.lower().split())
            is_similar = False
            
            for existing_title in seen_titles:
                existing_words = set(existing_title.lower().split())
                # If 80% or more words match, consider it a duplicate
                if len(title_words) > 0 and len(existing_words) > 0:
                    intersection = title_words.intersection(existing_words)
                    similarity = len(intersection) / max(len(title_words), len(existing_words))
                    if similarity >= 0.8:
                        is_similar = True
                        break
            
            if not is_similar:
                seen_urls.add(policy.url)
                seen_titles.add(policy.title)
                deduplicated.append(policy)
        
        self.logger.info(f"Deduplicated {len(policies)} policies down to {len(deduplicated)}")
        return deduplicated

    async def format_policy_response(
        self, 
        user_context: UserContext, 
        policy_result: PolicyResult,
        request_id: str = None
    ) -> PolicyDiscoveryResponse:
        """
        Format a policy result into the specified output structure
        
        Args:
            user_context: User context information
            policy_result: The policy to format
            request_id: Optional request ID, will generate one if not provided
            
        Returns:
            PolicyDiscoveryResponse in the specified format
        """
        import uuid
        
        if not request_id:
            request_id = f"user{uuid.uuid4().hex[:6]}-policy{uuid.uuid4().hex[:3]}"
        
        # Determine persona from stakeholder roles
        persona = "Citizen"
        if "renter" in user_context.stakeholder_roles:
            persona = "Renter"
        elif "homeowner" in user_context.stakeholder_roles:
            persona = "Homeowner"
        elif "business_owner" in user_context.stakeholder_roles:
            persona = "Business Owner"
        elif "employee" in user_context.stakeholder_roles:
            persona = "Employee"
        elif "employer" in user_context.stakeholder_roles:
            persona = "Employer"
        
        # Get full text content if available
        full_text = ""
        try:
            if policy_result.content_preview:
                # If we have preview content, try to get the full content
                content_result = await self.search_engine.get_policy_content([policy_result.url])
                if policy_result.url in content_result:
                    full_text = content_result[policy_result.url].get("text", "")
            
            # If still no full text, use what we have
            if not full_text and policy_result.content_preview:
                full_text = policy_result.content_preview
                
        except Exception as e:
            self.logger.error(f"Failed to get full text content: {e}")
            full_text = policy_result.summary
        
        # Create the formatted response
        user_profile = UserProfile(
            persona=persona,
            location=user_context.location,
            initial_stance="Undecided"
        )
        
        policy_document = PolicyDocument(
            title=policy_result.title,
            source_url=policy_result.url,
            text=full_text or policy_result.summary
        )
        
        return PolicyDiscoveryResponse(
            request_id=request_id,
            user_profile=user_profile,
            policy_document=policy_document
        )
    
    def format_response_as_json(self, response: PolicyDiscoveryResponse) -> dict:
        """
        Convert PolicyDiscoveryResponse to JSON-serializable dictionary
        
        Args:
            response: PolicyDiscoveryResponse object
            
        Returns:
            Dictionary that can be serialized to JSON
        """
        from dataclasses import asdict
        return asdict(response)

    # Hybrid Webset + Search Methods

    async def initialize_websets(self) -> Dict[str, str]:
        """
        Initialize all policy websets for structured collection
        
        Returns:
            Dictionary mapping webset names to webset IDs
        """
        self.logger.info("Initializing policy websets...")
        webset_ids = await self.webset_manager.initialize_websets()
        self._websets_initialized = True
        return webset_ids

    async def setup_policy_monitoring(self) -> Dict[str, str]:
        """
        Set up automated monitoring for policy updates
        
        Returns:
            Dictionary mapping webset names to monitor IDs
        """
        if not self._websets_initialized:
            await self.initialize_websets()
        
        return await self.webset_manager.setup_monitors()

    async def get_webset_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all managed websets
        
        Returns:
            Dictionary with status information for each webset
        """
        return await self.webset_manager.get_webset_status()

    async def _execute_live_search(
        self,
        user_context: UserContext,
        domains: list[PolicyDomain] | None,
        government_levels: list[GovernmentLevel] | None,
    ) -> list[PolicyResult]:
        """
        Execute live search using the existing search engine
        
        Args:
            user_context: User context for search
            domains: Specific domains to search
            government_levels: Specific government levels to search
            
        Returns:
            List of policy results from live search
        """
        # Generate search parameters
        search_params = self._generate_search_parameters(
            user_context, domains, government_levels
        )

        # Execute searches across government levels
        search_tasks = []
        levels_to_search = government_levels or list(GovernmentLevel)

        for level in levels_to_search:
            task = self._search_government_level(level, search_params)
            search_tasks.append(task)

        # Execute searches concurrently
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Process and organize results
        all_search_policies = []

        for i, result in enumerate(search_results):
            if isinstance(result, Exception):
                self.logger.error(f"Search failed for {levels_to_search[i]}: {result}")
                continue

            if isinstance(result, list):
                all_search_policies.extend(result)

        return all_search_policies

    def _combine_webset_and_search_results(
        self, 
        webset_policies: list[PolicyResult], 
        search_policies: list[PolicyResult]
    ) -> list[PolicyResult]:
        """
        Combine and deduplicate webset and search results
        
        Args:
            webset_policies: Policies from websets
            search_policies: Policies from live search
            
        Returns:
            Combined and deduplicated list of policies
        """
        # Combine all policies
        all_policies = webset_policies + search_policies
        
        # Deduplicate using existing method
        deduplicated_policies = self._deduplicate_policies(all_policies)
        
        # Boost confidence scores for webset policies (they're pre-filtered)
        for policy in deduplicated_policies:
            # Check if this policy came from websets
            if any(wp.url == policy.url for wp in webset_policies):
                policy.confidence_score = min(policy.confidence_score + 0.1, 1.0)
        
        return deduplicated_policies
