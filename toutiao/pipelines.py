# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import pymongo
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class ToutiaoPipeline:

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        return item


class MongoPipeline:
    collection_name = 'toutiao'

    # TODO 增加去重功能 可以使用scrapy自带的RFPDupeFilter或者是布隆过滤器，数据量小的情况下也可以直接使用set

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.urls_seen = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(mongo_uri=crawler.settings.get("MONGO_URI"),
                   mongo_db=crawler.settings.get("MONGO_DATABASE", "items"))

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        # 将已经保存的url地址加载进set中
        urls = self.db[self.collection_name].find({}, {"url": 1, "_id": 0})
        for url in urls:
            self.urls_seen.add(url.get('url'))

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if adapter["url"] in self.urls_seen:
            raise DropItem(f"duplicated item:{item}")
        else:
            self.urls_seen.add(adapter['url'])
            self.db[self.collection_name].insert_one(adapter.asdict())
            return item
