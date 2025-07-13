"""
Policy search engine implementation using Exa API
"""

import asyncio
import logging
from typing import Any

from exa_py import Exa

from .config import RATE_LIMITS, SEARCH_CONFIG


class PolicySearchEngine:
    """
    Search engine for discovering policies using Exa API
    """

    def __init__(self, exa_client: Exa):
        """
        Initialize the search engine

        Args:
            exa_client: Initialized Exa client
        """
        self.exa = exa_client
        self.logger = logging.getLogger(__name__)

        # Rate limiting
        self._request_semaphore = asyncio.Semaphore(
            RATE_LIMITS["max_concurrent_searches"]
        )
        self._last_request_time = None
        self._min_request_interval = 60 / RATE_LIMITS["exa_api_calls_per_minute"]

    async def search_policies(
        self,
        query: str,
        domains: list[str],
        max_results: int = 20,
        date_cutoff: str | None = None,
        include_text: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Search for policies using Exa API

        Args:
            query: Search query string
            domains: List of domains to search within
            max_results: Maximum number of results to return
            date_cutoff: Date cutoff for results (ISO format)
            include_text: Whether to include full text content

        Returns:
            List of search results
        """
        async with self._request_semaphore:
            await self._rate_limit()

            try:
                search_params = {
                    "query": query,
                    "num_results": max_results,
                    "include_domains": domains,
                    "start_crawl_date": date_cutoff
                    or SEARCH_CONFIG["default_date_cutoff"],
                    "type": "neural",  # Use neural search for better policy understanding
                    "category": "news",  # Focus on news category for policy content
                }

                self.logger.info(f"Executing Exa search: {query}")

                # Use search_and_contents to get text content with highlights for better relevance
                if include_text:
                    response = self.exa.search_and_contents(
                        text=True,
                        highlights=True,  # Add highlights for better content analysis
                        **search_params
                    )
                else:
                    response = self.exa.search(**search_params)

                # Process results
                results = []
                for result in response.results:
                    processed_result = {
                        "title": result.title,
                        "url": result.url,
                        "published_date": result.published_date,
                        "author": getattr(result, "author", None),
                        "score": getattr(result, "score", 0.0),
                    }

                    if include_text and hasattr(result, "text"):
                        processed_result["text"] = result.text
                    
                    # Add highlights if available for better relevance scoring
                    if hasattr(result, "highlights"):
                        processed_result["highlights"] = result.highlights
                        processed_result["highlight_scores"] = getattr(result, "highlight_scores", [])

                    results.append(processed_result)

                self.logger.info(f"Found {len(results)} results for query: {query}")
                return results

            except Exception as e:
                self.logger.error(f"Search failed for query '{query}': {e}")
                return []

    async def find_similar_policies(
        self, url: str, max_results: int = 5
    ) -> list[dict[str, Any]]:
        """
        Find policies similar to a given URL

        Args:
            url: URL to find similar content for
            max_results: Maximum number of similar results

        Returns:
            List of similar policy results
        """
        async with self._request_semaphore:
            await self._rate_limit()

            try:
                self.logger.info(f"Finding similar policies for: {url}")

                # Use find_similar_and_contents for better content retrieval
                response = self.exa.find_similar_and_contents(
                    url=url,
                    num_results=max_results,
                    text=True,
                    exclude_source_domain=True,  # Exclude results from same domain
                )

                results = []
                for result in response.results:
                    processed_result = {
                        "title": result.title,
                        "url": result.url,
                        "published_date": result.published_date,
                        "author": getattr(result, "author", None),
                        "score": getattr(result, "score", 0.0),
                    }

                    if hasattr(result, "text"):
                        processed_result["text"] = result.text

                    results.append(processed_result)

                self.logger.info(f"Found {len(results)} similar policies")
                return results

            except Exception as e:
                self.logger.error(f"Similar search failed for URL '{url}': {e}")
                return []

    async def get_policy_content(self, urls: list[str]) -> dict[str, dict[str, Any]]:
        """
        Get full content for specific policy URLs

        Args:
            urls: List of URLs to get content for

        Returns:
            Dictionary mapping URLs to content data
        """
        async with self._request_semaphore:
            await self._rate_limit()

            try:
                self.logger.info(f"Getting content for {len(urls)} URLs")

                # Use proper get_contents method with text parameter
                response = self.exa.get_contents(urls=urls, text=True)

                content_map = {}
                for result in response.results:
                    content_map[result.url] = {
                        "title": result.title,
                        "text": getattr(result, "text", ""),
                        "author": getattr(result, "author", None),
                        "published_date": result.published_date,
                    }

                return content_map

            except Exception as e:
                self.logger.error(f"Content retrieval failed: {e}")
                return {}

    async def _rate_limit(self):
        """Implement rate limiting for API calls"""
        if self._last_request_time is not None:
            time_since_last = asyncio.get_event_loop().time() - self._last_request_time
            if time_since_last < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - time_since_last)

        self._last_request_time = asyncio.get_event_loop().time()

    def create_government_specific_query(
        self, base_query: str, government_level: str, location: str = "San Francisco"
    ) -> str:
        """
        Create government-level specific search queries optimized for neural search

        Args:
            base_query: Base search terms
            government_level: 'federal', 'state', or 'local'
            location: Geographic location for local searches

        Returns:
            Optimized search query for neural search
        """
        if government_level == "federal":
            return f"Federal government {base_query} policy legislation regulation congressional bill"
        elif government_level == "state":
            return f"California state government {base_query} legislation bill assembly senate policy"
        elif government_level == "local":
            return f"{location} city government {base_query} ordinance municipal policy local legislation"
        else:
            return base_query

    def create_stakeholder_query(
        self, stakeholder_role: str, domain: str, government_level: str
    ) -> str:
        """
        Create stakeholder-specific search queries optimized for policy discovery

        Args:
            stakeholder_role: e.g., 'renter', 'business_owner'
            domain: Policy domain
            government_level: Level of government

        Returns:
            Stakeholder-focused search query optimized for neural search
        """
        role_terms = {
            "renter": "tenant renter housing rights lease protection",
            "homeowner": "property owner homeowner real estate zoning",
            "employee": "worker employee labor rights employment protection",
            "business_owner": "business owner entrepreneur small business regulation",
            "student": "student education policy school funding",
            "parent": "family children parent childcare education policy",
            "senior": "elderly senior retirement benefits healthcare",
            "immigrant": "immigrant visa citizenship naturalization policy",
        }

        base_terms = role_terms.get(stakeholder_role, stakeholder_role)

        query = f"{base_terms} {domain} policy impact"

        return self.create_government_specific_query(query, government_level)

    async def test_url_crawling(self, url: str) -> dict[str, Any]:
        """Test if a specific URL can be found or crawled by Exa"""
        async with self._request_semaphore:
            await self._rate_limit()
            
            try:
                self.logger.info(f"Testing URL crawling: {url}")
                
                # Try to get contents directly
                response = self.exa.get_contents([url], text=True)
                
                if response.results:
                    result = response.results[0]
                    self.logger.info(f"URL found in Exa: {result.title}")
                    return {
                        "found": True,
                        "title": result.title,
                        "text": getattr(result, "text", "")[:200]
                    }
                else:
                    self.logger.warning(f"URL not found in Exa index: {url}")
                    return {"found": False}
                    
            except Exception as e:
                self.logger.error(f"URL test failed: {e}")
                return {"found": False, "error": str(e)}

    async def test_specific_search(self, query: str, domains: list[str]) -> list[dict[str, Any]]:
        """Test search for specific terms to debug missing results"""
        async with self._request_semaphore:
            await self._rate_limit()
            
            try:
                self.logger.info(f"Testing specific search: {query}")
                
                search_params = {
                    "query": query,
                    "num_results": 10,
                    "include_domains": domains,
                    "type": "neural",
                }
                
                response = self.exa.search_and_contents(
                    text=True,
                    highlights=True,
                    **search_params
                )
                
                results = []
                for result in response.results:
                    processed_result = {
                        "title": result.title,
                        "url": result.url,
                        "published_date": result.published_date,
                        "score": getattr(result, "score", 0.0),
                    }
                    results.append(processed_result)
                
                self.logger.info(f"Test search found {len(results)} results")
                for result in results:
                    if "sb522" in result["url"].lower():
                        self.logger.info(f"Found SB522 in test search: {result}")
                
                return results
                
            except Exception as e:
                self.logger.error(f"Test search failed: {e}")
                return []

    async def analyze_policy_question(self, question: str) -> dict[str, Any]:
        """
        Use Exa's answer functionality to get AI-powered policy analysis
        
        Args:
            question: Natural language question about policy
            
        Returns:
            Dictionary with answer and citations
        """
        async with self._request_semaphore:
            await self._rate_limit()
            
            try:
                self.logger.info(f"Analyzing policy question: {question}")
                
                # Use Exa's answer method for AI-powered responses with citations
                response = self.exa.answer(
                    query=question,
                    text=True  # Include full text of citations
                )
                
                result = {
                    "answer": response.answer,
                    "citations": []
                }
                
                # Process citations
                for citation in response.citations:
                    citation_data = {
                        "title": citation.title,
                        "url": citation.url,
                        "published_date": citation.published_date,
                        "author": getattr(citation, "author", None),
                        "text": getattr(citation, "text", "")
                    }
                    result["citations"].append(citation_data)
                
                self.logger.info(f"Generated answer with {len(result['citations'])} citations")
                return result
                
            except Exception as e:
                self.logger.error(f"Policy question analysis failed: {e}")
                return {"answer": "", "citations": []} 