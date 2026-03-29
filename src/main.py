import asyncio
import json
from .models import AsyncCrawler


async def main():
    crawler = AsyncCrawler(max_concurrent=5)
    urls = [
        "https://google.com",
        "https://yandex.com",
        "https://bing.com",
    ]

    try:
        results = await crawler.fetch_and_parse_many(urls)
        with open("parsed_results.json", "w", encoding="utf-8") as f:
            # json.dump записывает объект в файл
            # indent=4 делает файл читаемым для человека
            # ensure_ascii=False сохраняет кириллицу
            json.dump(results, f, indent=4, ensure_ascii=False)

        for result in results:
            print(f"""
"url": "{result.get("url")}",
"title": "{result.get("title")}",
"text_length": "{len(result.get("text"))}",
"links_count": {len(result.get("links"))},
"links": [{result.get("links")}]
""")

    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())
