import argparse
import scrapy
from scrapy.loader import ItemLoader
from scrapy.crawler import CrawlerProcess

class AmazonItem(scrapy.Item):
    model = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    rating = scrapy.Field()
    reviews = scrapy.Field()

class AmazonSpider(scrapy.Spider):
    name = "amazon_spider"
    max_pages = 5 # the maximum number of pages to scrape for each model

    def __init__(self, models=None, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        self.models = models.split(',')
        self.start_urls = [f"https://www.amazon.com/s?k={model}" for model in self.models]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'})

    def parse(self, response):
        for item in response.css('div.a-section.a-spacing-base, div.a-section'):
            l = ItemLoader(item = AmazonItem(), selector=item)
            l.add_value('model', response.css('input#twotabsearchtextbox::attr(value)').get())
            l.add_css('title', 'span.a-size-base-plus.a-color-base.a-text-normal::text, span.a-size-medium.a-color-base.a-text-normal::text')
            l.add_css('price', 'span.a-offscreen::text')
            l.add_css('rating', 'span.a-icon-alt::text')
            l.add_css('reviews', 'span.a-size-base.s-underline-text::text')

            yield l.load_item()

        # handling pagination
        next_page_url = response.css('span.s-pagination-item.s-pagination-next a::attr(href)').get()
        if next_page_url and self.page_number < self.max_pages:
            self.page_number += 1
            yield scrapy.Request(response.urljoin(next_page_url), 
                                callback=self.parse, 
                                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Amazon for product info")
    parser.add_argument("models", help="Models to search for (comma-separated)")
    args = parser.parse_args()

    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'FEED_FORMAT': 'csv',
        'FEED_EXPORT_FIELDS': ['model', 'title', 'price', 'rating', 'reviews']  # specify the order of fields
    })

    models = [model.strip() for model in args.models.split(',')]
    process.crawl(AmazonSpider, models=models)
    process.start()
