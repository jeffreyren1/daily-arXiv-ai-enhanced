import scrapy
import os
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
        
        # 2. 构造官方API的URL
        self.start_urls = [self._build_api_url()]

    name = "arxiv"
    allowed_domains = ["export.arxiv.org"]

    def _build_api_url(self):
        """简化API查询，避免嵌套逻辑和编码问题"""
        # 关键词处理：替换空格为+，避免编码错误
        keyword_queries = []
        for kw in self.keywords:
            clean_kw = kw.replace(" ", "+")
            keyword_queries.append(f"abs:{clean_kw}")  # 仅匹配摘要，精准度高
        keyword_str = "+OR+".join(keyword_queries) if keyword_queries else "abs:ISAC"
        
        # 构造参数（手动拼接，避免urllib二次编码）
        params = {
            "search_query": keyword_str,
            "start": self.start,
            "max_results": self.per_page,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        url_parts = [f"{k}={v}" for k, v in params.items()]
        return "https://export.arxiv.org/api/query?" + "&".join(url_parts)

    def parse(self, response):
        """解析XML响应，兼容arXiv API格式"""
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
        
        # 遍历解析每篇论文
        item_count = 0
        for entry in entries:
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
            
            # 本地过滤分类（核心）
            if self.target_categories and not paper_categories.intersection(self.target_categories):
                self.logger.debug(f"Skipped {arxiv_id} (category not match: {paper_categories})")
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
            item_count += 1
        
        self.logger.info(f"Scraped {item_count} valid papers in this page")
        
        # 分页（限制最大页数，避免无限循环）
        self.start += self.per_page
        if self.start < 500 and item_count > 0:  # 有数据才继续分页
            next_url = self._build_api_url()
            yield scrapy.Request(next_url, callback=self.parse)
        else:
            self.logger.info("Crawling finished (no more data or reach max pages)")