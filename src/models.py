import aiohttp
import asyncio
import logging

from bs4 import BeautifulSoup
from urllib.parse import urljoin


class AsyncCrawler:

    def __init__(
        self, max_concurrent: int = 10
    ):  # инициализация с ограничением конкурентности
        self.sem = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self.session: aiohttp.ClientSession | None = None
        self.logger = logging.getLogger(__name__)

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=self.max_concurrent)
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session

    async def fetch_url(self, url: str) -> str:
        async with self.sem:
            try:
                session = await self._ensure_session()
                self.logger.info(f"Processing the {url}...")
                await asyncio.sleep(1)
                async with session.get(url) as response:
                    response.raise_for_status()
                    body = await response.text()
                    self.logger.info(f"The task with {url} ended successfully!")
                    return body

            except aiohttp.ClientResponseError as err:
                self.logger.warning(f"Client response error occurred for {url}: {err}")
            except aiohttp.ClientError as err:
                self.logger.warning(f"Client error occurred for {url}: {err}")
            except asyncio.TimeoutError as err:
                self.logger.warning(f"Timeout error occurred for {url}: {err}")

            return ""

    async def fetch_urls(self, urls: list[str]) -> dict[str, str]:
        tasks = []

        for url in urls:
            tasks.append(asyncio.create_task(self.fetch_url(url)))

        res = await asyncio.gather(*tasks)
        return dict(zip(urls, res))

    async def close(self) -> None:
        if self.session is not None and not self.session.closed:
            await self.session.close()

    async def fetch_and_parse(self, url: str) -> dict:
        html = await self.fetch_url(url)
        httpParser = HTTPParser()
        parsedDict: dict = await httpParser.parse_html(html, url)
        
        return parsedDict


class HTTPParser:    
    async def parse_html(self, html: str, url: str) -> dict:
        result = {
            'url': url,
            'title': '',
            'text': '',
            'links': [],
            'metadata': {
                'title': '',
                'description': '',
                'keywords': ''
            }
        }

        if not html: 
            return result
        
        try:
            soup = BeautifulSoup(html, 'lxml')
        except Exception:
            soup = BeautifulSoup(html, 'html.parser')

        try:
            metadata = await self.extract_metadata(soup)
            links = await self.extract_links(soup, url)
            text = await self.extract_text(soup)

            result['title'] = metadata.get('title', '')
            result['links'] = links
            result['text'] = text
            result['metadata'] = metadata


        except Exception:
            pass
        
        return result

    async def extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        links = []
        
        for link in soup.find_all('a'):
            href = link.get('href')
            if(href):
                if(base_url in href):
                    links.append(href)
                else:
                    links.append(urljoin(base_url, href))

        return links

    async def extract_text(self, soup: BeautifulSoup, selector: str = None) -> str:
        node = soup.select_one(selector) if selector else soup.body
        if not node:
            return ''
        else:
            return node.get_text(" ", strip=True)

    async def extract_metadata(self, soup: BeautifulSoup) -> dict:
        title = soup.title.string if soup.title and soup.title.string else ''

        description = ''
        d = soup.find('meta', attrs={'name': 'description'})
        if d and d.get('content'):
            description = d['content']

        keywords = ''
        k = soup.find('meta', attrs={'name': 'keywords'})
        if k and k.get('content'):
            keywords = k['content']

        return {
            'title': title,
            'description': description,
            'keywords': keywords
        }