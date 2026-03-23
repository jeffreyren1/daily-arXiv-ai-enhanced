import scrapy
import os
import xml.etree.ElementTree as ET
from scrapy import signals


class ArxivSpider(scrapy.Spider):
    name = "arxiv"
    allowed_domains = ["export.arxiv.org"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. 配置项 - 固定关键词和数量
        self.keywords = os.environ.get("KEYWORDS", "ISAC,vital signs").split(",")
        self.keywords = [kw.strip() for kw in self.keywords if kw.strip()]
        self.target_categories = os.environ.get("CATEGORIES", "").split(",")
        self.target_categories = set([cat.strip() for cat in self.target_categories if cat.strip()])
        self.max_results = 50  # 只获取前50篇
        self.collected_count = 0  # 已收集的论文数量
        self.start = 0  # 分页起始位置（仅用于首次请求）

        # 2. 构造首次请求URL
        self.start_urls = [self._build_api_url()]

    def _build_api_url(self):
        """构造API请求URL，确保按日期降序排序，只返回指定数量"""
        # 关键词处理：abs:关键词 表示在摘要中匹配
        keyword_queries = []
        for kw in self.keywords:
            clean_kw = kw.replace(" ", "+")
            keyword_queries.append(f"abs:{clean_kw}")
        keyword_str = "+OR+".join(keyword_queries)

        # 固定参数：按提交日期降序、只返回max_results篇
        params = {
            "search_query": keyword_str,
            "start": self.start,
            "max_results": self.max_results,
            "sortBy": "submittedDate",  # 按提交日期排序
            "sortOrder": "descending",  # 从近到远
        }
        url_parts = [f"{k}={v}" for k, v in params.items()]
        return "https://export.arxiv.org/api/query?" + "&".join(url_parts)

    def parse(self, response):
        """解析XML响应，只提取前50篇符合条件的论文"""
        # 处理XML命名空间
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            self.logger.error("Failed to parse XML response")
            return

        # 提取论文条目
        entries = root.findall("atom:entry", ns)
        if not entries:
            self.logger.info("No papers found for current query")
            return

        # 遍历解析每篇论文，直到收集满50篇
        for entry in entries:
            # 达到50篇上限则停止
            if self.collected_count >= self.max_results:
                self.logger.info(f"已收集满{self.max_results}篇论文，停止解析")
                return

            # 1. 论文ID
            id_elem = entry.find("atom:id", ns)
            arxiv_id = id_elem.text.split("/abs/")[-1].strip() if id_elem is not None else ""
            if not arxiv_id:
                continue

            # 2. 标题
            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else ""

            # 3. 摘要
            summary_elem = entry.find("atom:summary", ns)
            abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else ""

            # 4. 作者
            authors = []
            for auth_elem in entry.findall("atom:author/atom:name", ns):
                authors.append(auth_elem.text.strip())

            # 5. 分类
            categories = []
            for cat_elem in entry.findall("atom:category", ns):
                cat = cat_elem.get("term")
                if cat:
                    categories.append(cat)
            paper_categories = set(categories)

            # 过滤分类（如果设置了目标分类）
            if self.target_categories and not paper_categories.intersection(self.target_categories):
                self.logger.debug(f"Skipped {arxiv_id} (category not match: {paper_categories})")
                continue

            # 单篇请求：构造arxiv详情页的请求（模拟单篇请求）
            detail_url = f"https://arxiv.org/abs/{arxiv_id}"
            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_single_paper,
                meta={
                    "paper_basic": {
                        "id": arxiv_id,
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "categories": list(paper_categories),
                        "url": detail_url,
                    }
                },
                # 每个单篇请求添加延迟（关键：避免限流）
                dont_filter=True,
            )

            self.collected_count += 1
            self.logger.info(f"已收集 {self.collected_count}/{self.max_results} 篇论文")

        self.logger.info(f"本次解析完成，共收集 {self.collected_count} 篇有效论文")

    def parse_single_paper(self, response):
        """解析单篇论文的详情页（单篇请求的回调）"""
        basic_info = response.meta.get("paper_basic", {})

        # 这里可以解析详情页的更多信息（如全文链接、引用等）
        # 示例：提取页面标题确认请求成功
        page_title = response.xpath('//title/text()').get() or ""

        # 合并数据并输出
        yield {
            **basic_info,
            "detail_page_title": page_title.strip(),
            "detail_page_status": "success" if response.status == 200 else "failed",
        }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """注册信号，确保爬虫停止在收集满50篇时"""
        spider = super(ArxivSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        """爬虫关闭时的日志"""
        self.logger.info(f"爬虫结束，最终收集到 {self.collected_count} 篇论文（目标：{self.max_results}篇）")
