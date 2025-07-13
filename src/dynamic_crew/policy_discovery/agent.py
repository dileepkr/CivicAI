"""
Core PolicyDiscoveryAgent implementation using CrewAI framework
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Any

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
        self.classifier = PolicyClassifier()
        self.stakeholder_analyzer = StakeholderAnalyzer()

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
    ) -> PolicyDiscoveryResult:
        """
        Main policy discovery method

        Args:
            user_context: User context for personalized search
            domains: Specific policy domains to search (optional)
            government_levels: Specific government levels to search (optional)

        Returns:
            PolicyDiscoveryResult with discovered policies
        """
        start_time = datetime.now()

        # Generate search parameters
        search_params = self._generate_search_parameters(
            user_context, domains, government_levels
        )

        # Search across government levels
        all_policies = []
        for level in search_params.government_levels:
            policies = await self._search_government_level(level, search_params)
            all_policies.extend(policies)

        # Post-process results
        all_policies = self._deduplicate_policies(all_policies)
        related_policies = await self._find_related_policies(all_policies)
        all_policies.extend(related_policies)
        all_policies = self._deduplicate_policies(all_policies)

        # Rank and organize results
        priority_ranking = self._rank_policies_by_relevance(all_policies, user_context)
        stakeholder_impact_map = self._create_stakeholder_impact_map(
            all_policies, user_context.stakeholder_roles
        )

        # Calculate search time
        search_time = (datetime.now() - start_time).total_seconds()

        # Create result
        from dataclasses import asdict
        result = PolicyDiscoveryResult(
            total_found=len(all_policies),
            priority_ranking=priority_ranking,
            stakeholder_impact_map=stakeholder_impact_map,
            search_time=search_time,
            search_metadata={
                "search_params": asdict(search_params),
                "domains_searched": [d.value for d in search_params.domains],
                "levels_searched": [l.value for l in search_params.government_levels],
                "user_context": asdict(user_context),
            },
        )

        self.logger.info(
            f"Discovery complete: {len(all_policies)} total policies, "
            f"{len(priority_ranking)} in priority ranking, "
            f"search time: {search_time:.2f}s"
        )

        return result

    def _generate_search_parameters(
        self,
        user_context: UserContext,
        domains: list[PolicyDomain] | None,
        government_levels: list[GovernmentLevel] | None,
    ) -> SearchParameters:
        """Generate search parameters from user context"""
        if not domains:
            domains = self._infer_domains_from_context(user_context)

        if not government_levels:
            government_levels = [
                GovernmentLevel.FEDERAL,
                GovernmentLevel.STATE,
                GovernmentLevel.LOCAL,
            ]

        return SearchParameters(
            domains=domains,
            government_levels=government_levels,
            stakeholder_roles=user_context.stakeholder_roles,
            user_location=user_context.location,
            regulation_timing=user_context.regulation_timing,
        )

    def _infer_domains_from_context(
        self, user_context: UserContext
    ) -> list[PolicyDomain]:
        """Infer policy domains from user context"""
        domains = []

        # Check interests for domain keywords
        for interest in user_context.interests:
            for domain in PolicyDomain:
                domain_keywords = DOMAIN_KEYWORDS.get(domain.value, [])
                if any(keyword in interest.lower() for keyword in domain_keywords):
                    if domain not in domains:
                        domains.append(domain)

        # Check stakeholder roles for domain implications
        for role in user_context.stakeholder_roles:
            if role in ["renter", "tenant", "landlord", "homeowner"]:
                if PolicyDomain.HOUSING not in domains:
                    domains.append(PolicyDomain.HOUSING)
            elif role in ["employee", "worker", "employer"]:
                if PolicyDomain.LABOR not in domains:
                    domains.append(PolicyDomain.LABOR)
            elif role in ["business_owner", "entrepreneur"]:
                if PolicyDomain.BUSINESS not in domains:
                    domains.append(PolicyDomain.BUSINESS)

        # Default to all domains if none inferred
        if not domains:
            domains = list(PolicyDomain)

        return domains

    async def _search_government_level(
        self, level: GovernmentLevel, search_params: SearchParameters
    ) -> list[PolicyResult]:
        """Search for policies at a specific government level"""
        queries = self._generate_search_queries(level, search_params)
        all_results = []

        for query in queries:
            try:
                # Use government domains for search
                domains = ["gov", "legislature.ca.gov", "sfgov.org"] if level == GovernmentLevel.LOCAL else \
                         ["ca.gov", "legislature.ca.gov"] if level == GovernmentLevel.STATE else \
                         ["gov", "congress.gov", "regulations.gov"]
                
                results = await self.search_engine.search_policies(
                    query=query,
                    domains=domains,
                    max_results=10,
                    include_text=True
                )
                all_results.extend(results)
            except Exception as e:
                self.logger.error(f"Search failed for query '{query}': {e}")
                continue

        # Convert to PolicyResult objects
        policies = []
        for result in all_results:
            policy = self._create_policy_result(result, level)
            if policy:
                policies.append(policy)

        self.logger.info(f"Found {len(policies)} policies for {level.value}")
        return policies

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
        """Create a PolicyResult from search data"""
        try:
            title = search_item.get("title", "")
            url = search_item.get("url", "")
            text = search_item.get("text", "")
            
            if not title or not url:
                return None

            # Filter out non-policy content first
            if not self._is_actual_policy(title, url, text):
                return None

            # Clean the title and text
            title = self._clean_text(title)
            text = self._clean_text(text)

            # Extract basic information
            summary = self._generate_summary(text)
            last_updated = self._extract_date(search_item)
            source_agency = self._extract_agency(url, level)
            document_type = self._classify_document_type(title, url)
            confidence_score = self._calculate_confidence(search_item)

            # Determine policy status and domain
            status = self.classifier.classify_status(f"{title} {summary}")
            domain = self.classifier.classify_domain(f"{title} {summary}")

            # Generate stakeholder impacts
            stakeholder_impacts = self.stakeholder_analyzer.analyze_impacts(
                f"{title} {summary}", title
            )

            return PolicyResult(
                title=title,
                url=url,
                summary=summary,
                government_level=level,
                domain=domain,
                status=status,
                source_agency=source_agency,
                document_type=document_type,
                last_updated=last_updated,
                confidence_score=confidence_score,
                stakeholder_impacts=stakeholder_impacts,
                content_preview=text[:500] if text else "",
            )

        except Exception as e:
            self.logger.error(f"Error creating policy result: {e}")
            return None
    
    def _is_actual_policy(self, title: str, url: str, text: str) -> bool:
        """Filter to include only actual policies, bills, and regulations"""
        import re
        
        # Check if URL is from a government domain
        government_domains = [
            'gov', 'legislature.ca.gov', 'leginfo.legislature.ca.gov', 
            'congress.gov', 'regulations.gov', 'sfgov.org', 'ca.gov',
            'sfplanning.org', 'whitehouse.gov', 'federalregister.gov'
        ]
        
        is_gov_domain = any(domain in url.lower() for domain in government_domains)
        
        # Policy/bill indicators in title
        policy_indicators = [
            r'\b(bill|act|law|regulation|ordinance|resolution|statute|code|policy|rule)\b',
            r'\b(ab|sb|hr|s\.)\s*\d+',  # Bill numbers like AB 123, SB 456, HR 789
            r'\b(chapter|section|title)\s*\d+',
            r'\b(executive order|eo)\s*\d+',
            r'\b(proposition|prop)\s*\d+',
            r'\b(measure|initiative)\b'
        ]
        
        has_policy_indicator = any(re.search(pattern, title.lower()) for pattern in policy_indicators)
        
        # Exclude non-policy content
        exclude_patterns = [
            r'\b(about|contact|home|news|press|blog|events|calendar)\b',
            r'\b(directory|staff|organization|department)\b',
            r'\b(faq|help|support|tutorial|guide)\b',
            r'\b(login|register|account|profile)\b',
            r'\b(search|results|page|site|website)\b',
            r'\b(poster|flyer|brochure|form|application)\b',
            r'\b(meeting|agenda|minutes|schedule)\b'
        ]
        
        is_excluded = any(re.search(pattern, title.lower()) for pattern in exclude_patterns)
        
        # Check content for policy-related terms
        policy_content_terms = [
            'enacted', 'legislation', 'amendment', 'compliance', 'enforcement',
            'effective date', 'implementation', 'regulatory', 'statutory',
            'municipal code', 'administrative code', 'public law'
        ]
        
        has_policy_content = any(term in text.lower() for term in policy_content_terms)
        
        # Final decision logic
        if is_gov_domain and (has_policy_indicator or has_policy_content) and not is_excluded:
            return True
        
        # Special case for very clear policy titles even from non-gov domains
        if has_policy_indicator and not is_excluded:
            clear_policy_terms = [
                r'\b(federal|state|california|san francisco)\s+(law|act|bill|regulation|ordinance)\b',
                r'\b(housing|labor|employment|minimum wage|rent control)\s+(law|act|bill|regulation|ordinance)\b'
            ]
            if any(re.search(pattern, title.lower()) for pattern in clear_policy_terms):
                return True
        
        return False

    def _generate_summary(self, content: str) -> str:
        """Generate a clean, readable summary from policy content"""
        if not content:
            return "No summary available"
        
        # Clean up the text first
        content = self._clean_text(content)
        
        # Simple extractive summary - take first few sentences
        sentences = content.split(". ")
        if len(sentences) > 3:
            summary = ". ".join(sentences[:3]) + "."
        else:
            summary = content[:300] + "..." if len(content) > 300 else content
        
        # Further clean the summary
        return self._clean_text(summary)
    
    def _clean_text(self, text: str) -> str:
        """Clean up text to make it more readable"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove common HTML artifacts
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        
        # Remove navigation and footer text
        text = re.sub(r'(Skip to main content|Skip to footer|Navigation|Footer|Home|About|Contact)', '', text, flags=re.IGNORECASE)
        
        # Remove common website artifacts
        text = re.sub(r'(Cookie Policy|Privacy Policy|Terms of Service|Copyright|All rights reserved)', '', text, flags=re.IGNORECASE)
        
        # Remove URLs and email addresses
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{2,}', '...', text)
        text = re.sub(r'[-]{2,}', '--', text)
        
        return text.strip()

    def _extract_date(self, search_item: dict[str, Any]) -> datetime:
        """Extract date from search item"""
        try:
            # Try published_date first
            if "published_date" in search_item:
                date_str = search_item["published_date"]
                if date_str:
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
            
            # Fallback to current date
            return datetime.now()
        except Exception:
            return datetime.now()

    def _extract_agency(self, url: str, level: GovernmentLevel) -> str:
        """Extract source agency from URL"""
        if not url:
            return "Unknown Agency"
        
        # Government level specific agency extraction
        if level == GovernmentLevel.FEDERAL:
            if "congress.gov" in url:
                return "U.S. Congress"
            elif "whitehouse.gov" in url:
                return "White House"
            elif "regulations.gov" in url:
                return "Federal Regulations"
            else:
                return "Federal Agency"
        elif level == GovernmentLevel.STATE:
            if "leginfo.legislature.ca.gov" in url:
                return "California Legislature"
            elif "ca.gov" in url:
                return "State of California"
            else:
                return "California State Agency"
        elif level == GovernmentLevel.LOCAL:
            if "sfgov.org" in url:
                return "City of San Francisco"
            elif "sfplanning.org" in url:
                return "SF Planning Department"
            else:
                return "San Francisco Local Agency"
        
        return "Unknown Agency"

    def _classify_document_type(self, title: str, url: str) -> str:
        """Classify the type of policy document with improved specificity"""
        title_lower = title.lower()
        url_lower = url.lower()
        
        # Check for specific bill patterns
        if re.search(r'\b(ab|sb|hr|s\.)\s*\d+', title_lower):
            return "Legislative Bill"
        elif "bill" in title_lower:
            return "Bill"
        elif "ordinance" in title_lower:
            return "Municipal Ordinance"
        elif "regulation" in title_lower or "rule" in title_lower:
            return "Regulation"
        elif "executive order" in title_lower or re.search(r'\beo\s*\d+', title_lower):
            return "Executive Order"
        elif "resolution" in title_lower:
            return "Resolution"
        elif "statute" in title_lower or "code" in title_lower:
            return "Statute/Code"
        elif "act" in title_lower and ("law" in title_lower or "act" in title_lower):
            return "Act/Law"
        elif "proposition" in title_lower or re.search(r'\bprop\s*\d+', title_lower):
            return "Ballot Proposition"
        elif "initiative" in title_lower or "measure" in title_lower:
            return "Initiative/Measure"
        elif "policy" in title_lower:
            return "Policy Document"
        else:
            return "Government Document"

    def _calculate_confidence(self, search_item: dict[str, Any]) -> float:
        """Calculate confidence score for a policy result"""
        score = 0.5  # Base score
        
        # Score based on data completeness
        if search_item.get("title"):
            score += 0.1
        if search_item.get("url"):
            score += 0.1
        if search_item.get("text"):
            score += 0.1
        if search_item.get("published_date"):
            score += 0.1
        
        # Score based on source reliability
        url = search_item.get("url", "")
        if any(domain in url for domain in ["gov", "legislature", "congress"]):
            score += 0.2
        
        # Score based on content quality
        text = search_item.get("text", "")
        if len(text) > 100:
            score += 0.1
        if len(text) > 500:
            score += 0.1
        
        # Score based on title quality
        title = search_item.get("title", "")
        if len(title) > 10:
            score += 0.05
        if any(keyword in title.lower() for keyword in ["bill", "act", "law", "ordinance"]):
            score += 0.05
        
        return min(score, 1.0)

    def _create_stakeholder_impact_map(
        self, policies: list[PolicyResult], stakeholder_roles: list[str]
    ) -> dict[str, list[PolicyResult]]:
        """Create a map of stakeholder roles to relevant policies"""
        stakeholder_map = {}
        
        for role in stakeholder_roles:
            relevant_policies = []
            for policy in policies:
                # Check if policy impacts this stakeholder role
                for impact in policy.stakeholder_impacts:
                    if role in impact.stakeholder_group.lower():
                        relevant_policies.append(policy)
                        break
            
            stakeholder_map[role] = relevant_policies
        
        return stakeholder_map

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
            
            combined_text = f"{policy_text} {highlights_text}"
            
            for interest in user_context.interests:
                interest_words = interest.lower().split()
                for word in interest_words:
                    if len(word) > 2:  # Skip very short words
                        if word in policy_text:
                            interest_relevance += 0.15  # Higher weight for title/summary
                        elif word in highlights_text:
                            interest_relevance += 0.1   # Medium weight for highlights
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
        """Find related policies based on existing results"""
        related_policies = []
        
        # Extract key terms from existing policies
        key_terms = set()
        for policy in policies[:5]:  # Only use top 5 policies
            title_words = policy.title.lower().split()
            for word in title_words:
                if len(word) > 4:  # Only longer words
                    key_terms.add(word)
        
        # Search for related policies using key terms
        for term in list(key_terms)[:3]:  # Limit to 3 terms
            try:
                domains = ["ca.gov", "legislature.ca.gov"]
                results = await self.search_engine.search_policies(
                    query=term,
                    domains=domains,
                    max_results=5,
                    include_text=True
                )
                for result in results[:2]:  # Limit results per term
                    policy = self._create_policy_result(result, GovernmentLevel.STATE)
                    if policy:
                        related_policies.append(policy)
            except Exception as e:
                self.logger.error(f"Related policy search failed for term '{term}': {e}")
                continue
        
        return related_policies

    def _matches_regulation_timing(
        self, policy: PolicyResult, timing: RegulationTiming
    ) -> bool:
        """Check if policy matches the regulation timing preference"""
        if timing == RegulationTiming.ALL:
            return True
        elif timing == RegulationTiming.FUTURE:
            return policy.status == PolicyStatus.PROPOSED and not self._has_policy_taken_effect(policy)
        elif timing == RegulationTiming.CURRENT:
            return policy.status == PolicyStatus.ACTIVE or self._has_policy_taken_effect(policy)
        else:
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
        Format a single policy result into a comprehensive response
        
        Args:
            user_context: User context for personalization
            policy_result: The policy to format
            request_id: Optional request identifier
            
        Returns:
            PolicyDiscoveryResponse: Formatted response
        """
        
        # Create policy document
        policy_doc = PolicyDocument(
            title=policy_result.title,
            summary=policy_result.summary,
            url=policy_result.url,
            government_level=policy_result.government_level,
            domain=policy_result.domain,
            status=policy_result.status,
            source_agency=policy_result.source_agency,
            last_updated=policy_result.last_updated,
            stakeholder_impacts=policy_result.stakeholder_impacts
        )
        
        # Generate response
        response = PolicyDiscoveryResponse(
            request_id=request_id or f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_context=user_context,
            policy_document=policy_doc,
            relevance_score=policy_result.confidence_score,
            generated_at=datetime.now()
        )
        
        return response

    def format_response_as_json(self, response: PolicyDiscoveryResponse) -> dict:
        """Convert PolicyDiscoveryResponse to JSON-serializable dict"""
        from dataclasses import asdict
        return {
            "request_id": response.request_id,
            "user_context": asdict(response.user_context),
            "policy_document": asdict(response.policy_document),
            "relevance_score": response.relevance_score,
            "generated_at": response.generated_at.isoformat()
        } 