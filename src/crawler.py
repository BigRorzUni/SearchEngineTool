from __future__ import annotations

import time
from collections import deque
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests import Response
from rich.console import Console
from tqdm import tqdm


class Crawler:
    def __init__(
        self,
        base_url: str,
        politeness_delay: float = 6.0,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = self._normalise_url(base_url)
        self.politeness_delay = politeness_delay
        self.timeout = timeout
        self.console = Console()
        self.session = requests.Session()
        self._last_request_time: float | None = None

    def _wait_if_needed(self) -> None:
        if self._last_request_time is None:
            return

        elapsed = time.time() - self._last_request_time
        remaining = self.politeness_delay - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _get(self, url: str) -> Response | None:
        self._wait_if_needed()

        try:
            response = self.session.get(url, timeout=self.timeout)
            self._last_request_time = time.time()
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            self.console.print(f"[red]Request failed for {url}: {exc}[/red]")
            return None

    def _normalise_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path or "/"

        if not path.endswith("/"):
            path += "/"

        return f"{parsed.scheme}://{parsed.netloc}{path}"

    def _is_internal_url(self, url: str) -> bool:
        return urlparse(url).netloc == urlparse(self.base_url).netloc

    def _is_allowed_page(self, url: str) -> bool:
        """
        Restrict crawling to the main quote listing pages.

        Allowed:
        - /
        - /page/<n>/
        """
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")

        return path == "" or path.startswith("/page")

    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> list[str]:
        links: list[str] = []

        for anchor in soup.find_all("a", href=True):
            absolute = urljoin(current_url, anchor["href"])
            absolute = self._normalise_url(absolute)

            if self._is_internal_url(absolute) and self._is_allowed_page(absolute):
                links.append(absolute)

        return links

    def _extract_visible_text(self, soup: BeautifulSoup) -> str:
        """
        Extract useful text from the page.

        For quotes.toscrape.com, the meaningful content is mainly:
        - quote text
        - author names
        - tags
        """
        quote_blocks = soup.select(".quote")

        if quote_blocks:
            parts: list[str] = []

            for block in quote_blocks:
                text_element = block.select_one(".text")
                author_element = block.select_one(".author")
                tag_elements = block.select(".tags .tag")

                if text_element is not None:
                    parts.append(text_element.get_text(" ", strip=True))

                if author_element is not None:
                    parts.append(author_element.get_text(" ", strip=True))

                for tag in tag_elements:
                    parts.append(tag.get_text(" ", strip=True))

            return " ".join(parts)

        if soup.body is not None:
            return soup.body.get_text(" ", strip=True)

        return ""

    def crawl(self) -> list[dict[str, Any]]:
        """
        Crawl the site and return a list of extracted documents.

        Each document contains:
        - url
        - title
        - text
        """
        queue = deque([self.base_url])
        seen: set[str] = {self.base_url}
        visited: set[str] = set()
        documents: list[dict[str, Any]] = []

        progress = tqdm(desc="Crawling", unit="page")

        while queue:
            url = queue.popleft()

            if url in visited:
                continue

            visited.add(url)

            response = self._get(url)
            if response is None:
                progress.update(1)
                continue

            soup = BeautifulSoup(response.text, "lxml")
            title = soup.title.get_text(strip=True) if soup.title else url
            text = self._extract_visible_text(soup)

            documents.append(
                {
                    "url": url,
                    "title": title,
                    "text": text,
                }
            )

            for link in self._extract_links(soup, url):
                if link not in seen:
                    queue.append(link)
                    seen.add(link)

            progress.update(1)

        progress.close()
        return documents