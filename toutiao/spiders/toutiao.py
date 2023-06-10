import logging
import time

import scrapy
from lxml import etree
from scrapy import Request
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from toutiao.items import ArticleItem

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


class ToutiaoSpider(scrapy.Spider):
    name = "toutiao"
    allowed_domains = ["toutiao.com"]
    start_urls = ["https://www.toutiao.com"]

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.options = Options()
        # self.options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=self.options)

    def start_requests(self):
        """
        启动请求
        :return:
        """
        for url in self.start_urls:
            self.driver.get(url)
            time.sleep(3)
            text = self.driver.page_source
            for article_url in self.get_article_url(text):
                yield Request(article_url, callback=self.parse)
        self.driver.close()

    def get_article_url(self, text):
        """

        :param text:
        :return:
        """
        path = '//*[@id="root"]//div[@class="show-monitor"]//div[@class="feed-card-wrapper feed-card-article-wrapper"]//a/@href'
        html = etree.HTML(text)
        urls = html.xpath(path)
        for url in filter(lambda x: x.startswith("https"), urls):
            yield url

    def parse(self, response: HtmlResponse, **kwargs):
        """
        TODO 增加不同类型的文章的解析
        解析详情
        :param response:
        :return:
        """
        title_path = '//*[@id="root"]//div[@class="article-content"]//h1/text()'
        content_path = '//*[@id="root"]//div[@class="article-content"]//p/text()'
        author_path = '//*[@id="root"]//div[@class="article-meta"]/span[@class="name"]//text()'
        publish_time_path = '//*[@id="root"]//div[@class="article-meta"]/span[1]//text()'
        text = response.body.decode('utf-8')
        html = etree.HTML(text)
        title = html.xpath(title_path)
        content = html.xpath(content_path)
        author = html.xpath(author_path)
        publish_time = html.xpath(publish_time_path)
        item = ArticleItem()
        item['title'] = title[0]
        item['content'] = ''.join(content)
        item['url'] = response.url
        item['author'] = author[0]
        item['publish_time'] = publish_time[0]
        # loader.add_xpath('title', title_path, TakeFirst())
        # loader.add_xpath('content', content_path, Join('\n'))
        # loader.add_value('url', response.url)
        # loader.add_value('author','test')
        # loader.add_value('publish_time', datetime.datetime.now())
        yield item

        url_path = '//*[@id="root"]//div[@class="feed-card-wrapper feed-card-article-wrapper"]//div[@class="feed-card-article-l"]/a/@href'
        other_urls = html.xpath(url_path)
        for url in other_urls:
            yield Request(url, callback=self.parse)
