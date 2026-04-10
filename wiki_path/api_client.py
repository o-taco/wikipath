"""Wikipedia MediaWiki API client."""

import asyncio
from typing import Optional

import httpx

WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "WikiPathFinder/1.0"


class WikiApiClient:
    def __init__(self, semaphore_limit: int = 20):
        self._semaphore = asyncio.Semaphore(semaphore_limit)
        self._client: Optional[httpx.AsyncClient] = None
        self._link_cache: dict[str, list[str]] = {}

    async def __aenter__(self) -> "WikiApiClient":
        self._client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=30.0,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()

    async def _get(self, params: dict, retries: int = 5) -> dict:
        assert self._client is not None
        full_params = {**params, "format": "json", "formatversion": "2"}
        for attempt in range(retries):
            try:
                async with self._semaphore:
                    resp = await self._client.get(WIKI_API_URL, params=full_params)
                if resp.status_code == 429:
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue
                resp.raise_for_status()
                return resp.json()
            except (httpx.TimeoutException, httpx.HTTPStatusError):
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))
        return {}

    async def resolve_title(self, title: str) -> tuple[str, bool, bool]:
        """Return (canonical_title, exists, is_disambiguation)."""
        data = await self._get({
            "action": "query",
            "titles": title,
            "redirects": "1",
            "prop": "pageprops",
        })
        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return title, False, False
        page = pages[0]
        if page.get("missing"):
            return title, False, False
        canonical = page.get("title", title)
        is_disambig = "disambiguation" in page.get("pageprops", {})
        return canonical, True, is_disambig

    async def fetch_outbound_links(self, title: str) -> list[str]:
        cache_key = f"out:{title}"
        if cache_key in self._link_cache:
            return self._link_cache[cache_key]

        links: list[str] = []
        params: dict = {
            "action": "query",
            "titles": title,
            "redirects": "1",
            "prop": "links",
            "pllimit": "max",
            "plnamespace": "0",
        }

        while True:
            data = await self._get(params)
            for page in data.get("query", {}).get("pages", []):
                for link in page.get("links", []):
                    links.append(link["title"])

            cont = data.get("continue", {})
            if "plcontinue" not in cont:
                break
            params = {**params, "plcontinue": cont["plcontinue"]}

        self._link_cache[cache_key] = links
        return links

    async def fetch_inbound_links(self, title: str) -> list[str]:
        cache_key = f"in:{title}"
        if cache_key in self._link_cache:
            return self._link_cache[cache_key]

        links: list[str] = []
        params: dict = {
            "action": "query",
            "titles": title,
            "redirects": "1",
            "prop": "linkshere",
            "lhlimit": "max",
            "lhnamespace": "0",
            "lhshow": "!redirect",
        }

        while True:
            data = await self._get(params)
            for page in data.get("query", {}).get("pages", []):
                for link in page.get("linkshere", []):
                    links.append(link["title"])

            cont = data.get("continue", {})
            if "lhcontinue" not in cont:
                break
            params = {**params, "lhcontinue": cont["lhcontinue"]}

        self._link_cache[cache_key] = links
        return links

    async def fetch_links_batch(
        self,
        titles: list[str],
        direction: str = "outbound",
    ) -> dict[str, list[str]]:
        """Fetch links for multiple titles concurrently."""
        if not titles:
            return {}

        fetch_fn = (
            self.fetch_outbound_links
            if direction == "outbound"
            else self.fetch_inbound_links
        )

        results = await asyncio.gather(
            *[fetch_fn(t) for t in titles],
            return_exceptions=True,
        )

        return {
            title: links if isinstance(links, list) else []
            for title, links in zip(titles, results)
        }
