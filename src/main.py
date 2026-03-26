import asyncio
import logging
from models import AsyncCrawler, HTTPParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


async def run_day2_parser_tests() -> None:
    parser = HTTPParser()
    failed: list[str] = []

    def check(condition: bool, message: str) -> None:
        if condition:
            print(f"PASSED!!! {message}")
        else:
            print(f"FAILED!!! {message}")
            failed.append(message)

    # 1) Валидный HTML
    valid_html = """
    <html>
      <head>
        <title>Example Domain</title>
        <meta name="description" content="Example description">
        <meta name="keywords" content="example,test">
      </head>
      <body>
        <a href="/page1">Page 1</a>
        <a href="https://example.com/page2">Page 2</a>
      </body>
    </html>
    """
    result_valid = await parser.parse_html(valid_html, "https://example.com")
    check(result_valid.get("title") == "Example Domain", "Валидный HTML: title извлекается")
    check(isinstance(result_valid.get("links"), list), "Валидный HTML: links имеет тип list")

    # 2) Битый HTML
    broken_html = "<html><head><title>Broken</title><body><a href='/x'>x"
    result_broken = await parser.parse_html(broken_html, "https://example.com")
    check(isinstance(result_broken, dict), "Битый HTML: парсер не падает")
    check(result_broken.get("url") == "https://example.com", "Битый HTML: возвращается частичный результат")

    # 3) Извлечение ссылок
    links_html = """
    <html><body>
      <a href="/about">About</a>
      <a href="https://example.com/docs">Docs</a>
      <a>No href</a>
    </body></html>
    """
    result_links = await parser.parse_html(links_html, "https://example.com/base/")
    check(len(result_links.get("links", [])) >= 2, "Извлечение ссылок: ссылки находятся")

    # 4) Конвертация относительных URL
    rel_html = """
    <html><body>
      <a href="contacts">Contacts</a>
      <a href="/pricing">Pricing</a>
    </body></html>
    """
    result_rel = await parser.parse_html(rel_html, "https://example.com/base/")
    rel_links = result_rel.get("links", [])
    check(
        "https://example.com/base/contacts" in rel_links,
        "Относительный URL contacts -> абсолютный URL",
    )
    check(
        "https://example.com/pricing" in rel_links,
        "Относительный URL /pricing -> абсолютный URL",
    )

    if failed:
        raise AssertionError(f"Тесты провалены ({len(failed)}): {failed}")
    print("\n🎉 Все учебные тесты пункта 8 прошли успешно")

async def main():
    crawler = AsyncCrawler(max_concurrent=5)
    urls = [
        "https://google.com",
        "https://yandex.com",
        "https://bing.com",
    ]

    try:
        results = await crawler.fetch_urls(urls)
        print(f"Загружено {len(results)} страниц")
    finally:
        await crawler.close()

if __name__ == "__main__":
    asyncio.run(run_day2_parser_tests())
    asyncio.run(main())