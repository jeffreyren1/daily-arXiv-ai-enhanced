# Scrapy settings for daily_arxiv project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "daily_arxiv"

SPIDER_MODULES = ["daily_arxiv.spiders"]
NEWSPIDER_MODULE = "daily_arxiv.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "daily_arxiv (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False


# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs


RETRY_DELAY = 30  # 首次重试等待 30 秒
RETRY_BACKOFF_FACTOR = 2  # 后续重试等待时间翻倍（30s → 60s → 120s）

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]


# 新增：单篇请求延迟时间（秒）
SINGLE_REQUEST_DELAY = 2  # 单篇请求之间的间隔，可根据需要调整

# 启用下载中间件
DOWNLOADER_MIDDLEWARES = {
    "daily_arxiv.middlewares.RequestDelayMiddleware": 543,  # 启用自定义延迟中间件
}

# 修改：关闭自动节流（使用自定义延迟）
AUTOTHROTTLE_ENABLED = False

# 修改：降低并发数，避免限流


# 保留原有下载延迟（针对API请求）
DOWNLOAD_DELAY = 10


# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "daily_arxiv.middlewares.DailyArxivSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    "daily_arxiv.middlewares.DailyArxivDownloaderMiddleware": 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# 配置数据处理管道 / Configure item processing pipelines
# 数字越小优先级越高 / Lower numbers have higher priority
ITEM_PIPELINES = {
    # 主要数据保存管道 / Main data saving pipeline
    "daily_arxiv.pipelines.DailyArxivPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False  # 关闭自动节流调试日志（过于冗长）

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
