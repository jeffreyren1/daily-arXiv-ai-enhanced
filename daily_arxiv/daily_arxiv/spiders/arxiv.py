import scrapy
import os
import xml.etree.ElementTree as ET
from scrapy import signals


class ArxivSpider(scrapy.Spider):
    name = "arxiv"
    allowed_domains = ["export.arxiv.org"]

    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/atom+xml,application/xml,text/xml',
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. 从环境变量读取配置（精准匹配用）
        # 关键词（摘要中匹配，多个关键词用OR连接）
        self.keywords = os.environ.get("KEYWORDS", "ISAC,vital signs").split(",")
        self.keywords = [kw.strip() for kw in self.keywords if kw.strip()]
        # 兜底：默认关键词
        if not self.keywords:
            self.keywords = ["ISAC", "vital signs"]

        # 目标分类（必须匹配其中之一）
        self.target_categories = os.environ.get("CATEGORIES", "").split(",")
        self.target_categories = set([cat.strip() for cat in self.target_categories if cat.strip()])

        # 2. 核心配置：只取前100篇，按日期降序
        self.max_results = 100  # 最终只取100篇
        self.collected_count = 0  # 已收集的符合条件的论文数
        self.start = 0  # 分页起始位置（仅首次请求）

        # 3. 构造精准搜索的URL
        self.start_urls = [self._build_api_url()]

    def _build_api_url(self):
        """构造精准搜索URL：关键词+按日期降序+仅返回指定数量"""
        # 关键词处理：abs:关键词 → 仅在摘要中匹配，多个关键词用OR连接
        keyword_queries = []
        for kw in self.keywords:
            clean_kw = kw.replace(" ", "+")
            keyword_queries.append(f"abs:{clean_kw}")
        keyword_str = "+OR+".join(keyword_queries)

        # 核心参数：精准搜索+日期降序+只取max_results篇
        params = {
            "search_query": keyword_str,
            "start": self.start,
            "max_results": self.max_results,  # 直接请求100篇
            "sortBy": "submittedDate",  # 按提交日期排序
            "sortOrder": "descending",  # 从近到远
        }
        url_parts = [f"{k}={v}" for k, v in params.items()]
        return "https://export.arxiv.org/api/query?" + "&".join(url_parts)

    def parse(self, response):
        """解析API响应：只提取符合关键词+分类的前100篇论文"""
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            self.logger.error("XML解析失败，停止爬取")
            return

        # 提取论文条目（API已按日期降序返回）
        entries = root.findall("atom:entry", ns)
        if not entries:
            self.logger.info("未找到符合条件的论文")
            return

        # 遍历解析，只取前100篇符合条件的
        for entry in entries:
            # 达到100篇上限，直接停止
            if self.collected_count >= self.max_results:
                self.logger.info(f"已收集满{self.max_results}篇符合条件的论文，停止解析")
                return

            # 1. 提取基础信息
            id_elem = entry.find("atom:id", ns)
            arxiv_id = id_elem.text.split("/abs/")[-1].strip() if id_elem is not None else ""
            if not arxiv_id:
                continue

            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else ""

            summary_elem = entry.find("atom:summary", ns)
            abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else ""

            authors = [auth_elem.text.strip() for auth_elem in entry.findall("atom:author/atom:name", ns)]

            # 提取分类（用于过滤）
            categories = [
                cat_elem.get("term") for cat_elem in entry.findall("atom:category", ns) if cat_elem.get("term")
            ]
            paper_categories = set(categories)

            # 2. 精准过滤：必须匹配指定分类（核心）
            if self.target_categories and not paper_categories.intersection(self.target_categories):
                self.logger.debug(f"跳过 {arxiv_id}（分类不匹配：{paper_categories}）")
                continue

            # 3. 构造单篇请求（按日期排序的第N篇）
            self.collected_count += 1
            detail_url = f"https://arxiv.org/abs/{arxiv_id}"
            self.logger.info(f"收集第 {self.collected_count}/{self.max_results} 篇论文（ID：{arxiv_id}）")

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_single_paper,
                meta={
                    "paper_info": {
                        "id": arxiv_id,
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "categories": list(paper_categories),
                        "url": detail_url,
                        "order": self.collected_count,  # 标记是按日期排序的第N篇
                    }
                },
                dont_filter=True,
            )

        # 若当前页无足够数据，停止（避免分页）
        if self.collected_count < self.max_results:
            self.logger.info(f"仅找到 {self.collected_count} 篇符合条件的论文（目标100篇），已无更多数据")

    def parse_single_paper(self, response):
        """解析单篇论文详情页（添加间隔避免限流）"""
        paper_info = response.meta.get("paper_info", {})

        # 解析详情页额外信息
        page_title = response.xpath('//title/text()').get() or ""

        # 输出最终结果（包含排序序号）
        yield {
            "order": paper_info.get("order"),  # 按日期从近到远的序号（1-100）
            "id": paper_info.get("id"),
            "title": paper_info.get("title"),
            "abstract": paper_info.get("abstract"),
            "authors": paper_info.get("authors"),
            "categories": paper_info.get("categories"),
            "url": paper_info.get("url"),
            "detail_page_title": page_title.strip(),
            "detail_page_status": "success" if response.status == 200 else "failed",
        }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """注册信号，确保爬虫正常关闭"""
        spider = super(ArxivSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        """爬虫关闭日志"""
        self.logger.info(
            f"爬虫结束 | 最终收集 {self.collected_count} 篇符合条件的论文（目标100篇）\n"
            f"关键词：{','.join(self.keywords)} | 分类：{','.join(self.target_categories)}"
        )
