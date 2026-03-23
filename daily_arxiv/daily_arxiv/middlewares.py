# daily_arxiv/middlewares.py
import time
from scrapy import signals
from scrapy.http import Request


class RequestDelayMiddleware:
    """自定义中间件：为每个单篇请求添加间隔，避免API限流"""

    def __init__(self, delay=2):
        self.delay = delay
        self.last_request_time = {}

    @classmethod
    def from_crawler(cls, crawler):
        # 从配置文件读取延迟时间，默认2秒
        delay = crawler.settings.get('SINGLE_REQUEST_DELAY', 2)
        middleware = cls(delay)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def spider_opened(self, spider):
        spider.logger.info(f"RequestDelayMiddleware 已启用，单篇请求间隔：{self.delay}秒")

    def process_request(self, request, spider):
        """处理每个请求，添加间隔"""
        # 只对arxiv详情页请求添加延迟（过滤API请求）
        if "arxiv.org/abs/" in request.url:
            domain = "arxiv.org"
            current_time = time.time()

            # 如果是该域名的首次请求，直接记录时间
            if domain not in self.last_request_time:
                self.last_request_time[domain] = current_time
                return None

            # 计算需要等待的时间
            elapsed = current_time - self.last_request_time[domain]
            if elapsed < self.delay:
                sleep_time = self.delay - elapsed
                spider.logger.info(f"单篇请求限流保护：等待 {sleep_time:.1f} 秒")
                time.sleep(sleep_time)

            # 更新最后请求时间
            self.last_request_time[domain] = time.time()

        return None
