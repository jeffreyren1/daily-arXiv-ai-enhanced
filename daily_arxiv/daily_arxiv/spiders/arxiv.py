import scrapy
import os
import urllib.parse
import xml.etree.ElementTree as ET

class ArxivSpider(scrapy.Spider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. 从环境变量获取配置
        self.keywords = os.environ.get("KEYWORDS", "ISAC,vital signs").split(",")
        self.keywords = [kw.strip() for kw in self.keywords if kw.strip()]
        self.target_categories = os.environ.get("CATEGORIES", "").split(",")
        self.target_categories = set([cat.strip() for cat in self.target_categories if cat.strip()])
        self.per_page = int(os.environ.get("PER_PAGE", 50))
        self.start = 0  # 分页起始位置
        
        # 2. 构造官方API的URL（XML格式）
        self.start_urls = [self._build_api_url()]

    name = "arxiv"
    allowed_domains = ["export.arxiv.org"]  # API专属域名

    def _build_api_url(self):
        """构造arxiv官方API URL（XML格式，稳定）"""
        # 1. 拼接关键词（abs:摘要，ti:标题，all:全文）
        keyword_queries = [f"abs:{urllib.parse.quote(kw)}" for kw in self.keywords]
        keyword_str = "+OR+".join(keyword_queries)
        
        # 2. 拼接分类
        cat_queries = [f"cat:{cat}" for cat in self.target_categories] if self.target_categories else []
        cat_str = "+OR+".join(cat_queries)
        
        # 3. 组合查询（关键词 AND 分类）
        if keyword_str and cat_str:
            search_query = f"({keyword_str})+AND+({cat_str})"
        elif keyword_str:
            search_query = keyword_str
        elif cat_str:
            search_query = cat_str
        else:
            search_query = "abs:ISAC"
        
        # 4. 构造最终URL（XML格式）
        params = {
            "search_query": search_query,
            "start": self.start,
            "max_results": self.per_page,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        return "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)

    def parse(self, response):
        """解析XML格式的API响应"""
        # 解析XML根节点（处理命名空间）
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(response.text)
        entries = root.findall("atom:entry", ns)
        
        if not entries:
            self.logger.info("No more papers found")
            return
        
        # 遍历每篇论文
        for entry in entries:
            # 提取核心字段
            # 1. 论文ID
            id_elem = entry.find("atom:id", ns)
            arxiv_id = id_elem.text.split("/abs/")[-1] if id_elem is not None else ""
            
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
            
            # 分类过滤
            if self.target_categories and not paper_categories.intersection(self.target_categories):
                self.logger.debug(f"Skipped {arxiv_id} (category not match)")
                continue
            
            # 输出数据
            yield {
                "id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": list(paper_categories),
                "url": f"https://arxiv.org/abs/{arxiv_id}"
            }
        
        # 分页爬取（避免无限循环，限制最大页数）
        self.start += self.per_page
        if self.start < 100:  # 最多爬取500篇，可调整
            next_url = self._build_api_url()
            yield scrapy.Request(next_url, callback=self.parse)