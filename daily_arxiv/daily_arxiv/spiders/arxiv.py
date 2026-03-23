import scrapy
import os
import urllib.parse  # 用于URL编码关键词
import re

class ArxivSpider(scrapy.Spider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. 从环境变量获取配置：关键词（必填）、分类（可选）、每页数量
        self.keywords = os.environ.get("KEYWORDS", "ISAC,vital signs").split(",")
        self.keywords = [kw.strip() for kw in self.keywords if kw.strip()]  # 去空值
        self.target_categories = os.environ.get("CATEGORIES", "").split(",")
        self.target_categories = set([cat.strip() for cat in self.target_categories if cat.strip()])
        self.per_page = int(os.environ.get("PER_PAGE", 50))  # 每页爬取数量
        
        # 2. 构造检索URL（支持多关键词+分类组合）
        self.start_urls = [self._build_search_url()]

    name = "arxiv"  # 爬虫名称，保持不变
    allowed_domains = ["arxiv.org"]  # 允许爬取的域名

    def _build_search_url(self):
        """构造arxiv检索URL，支持关键词+分类筛选"""
        # 关键词拼接（OR逻辑，匹配标题/摘要/作者）
        keyword_str = " OR ".join(self.keywords)
        encoded_keywords = urllib.parse.quote(keyword_str)
        
        # 分类筛选（可选）
        cat_filter = ""
        if self.target_categories:
            cat_str = " OR ".join(self.target_categories)
            encoded_cat = urllib.parse.quote(cat_str)
            cat_filter = f"&categories={encoded_cat}"
        
        # 构造最终URL：按提交时间排序，最新优先
        base_url = "https://arxiv.org/search/?query={}&searchtype=all{}&size={}&order=-submitted_date"
        return base_url.format(encoded_keywords, cat_filter, self.per_page)

    def parse(self, response):
        """解析检索结果页，提取论文信息"""
        # 遍历每篇论文的条目
        for paper_item in response.css("li.arxiv-result"):
            # 提取论文ID（核心）
            arxiv_id = paper_item.css("p.title a::attr(href)").re_first(r"/abs/(\d+\.\d+|[\w-]+)")
            if not arxiv_id:
                self.logger.warning("Failed to extract arxiv ID")
                continue
            
            # 提取论文分类
            category_text = paper_item.css("span.subject::text").get()
            paper_categories = set()
            if category_text:
                # 解析分类（格式："Computer Vision (cs.CV), Signal Processing (eess.SP)"）
                paper_categories = set(re.findall(r'\(([^)]+)\)', category_text))
            
            # 过滤：如果指定了目标分类，仅保留交集论文
            if self.target_categories and not paper_categories.intersection(self.target_categories):
                self.logger.debug(f"Skipped paper {arxiv_id} (categories not match)")
                continue
            
            # 可选：提取更多信息（标题、摘要、作者）
            title = paper_item.css("p.title::text").get().strip() if paper_item.css("p.title::text").get() else ""
            abstract = paper_item.css("p.abstract::text").get().strip() if paper_item.css("p.abstract::text").get() else ""
            authors = [a.strip() for a in paper_item.css("p.authors a::text").getall()]
            
            # 输出最终数据
            yield {
                "id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": list(paper_categories),
                "url": f"https://arxiv.org/abs/{arxiv_id}"
            }
        
        # 可选：处理分页（爬取下一页）
        next_page = response.css("nav.pagination a.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)