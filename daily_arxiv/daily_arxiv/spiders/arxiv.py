import scrapy
import os
import urllib.parse
import re
import json

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
    allowed_domains = ["export.arxiv.org"]  # API域名，不是arxiv.org

    def _build_api_url(self):
        """构造arxiv官方API URL（https://export.arxiv.org/api/query）"""
        # 拼接关键词查询（标题/摘要中包含任意关键词）
        keyword_queries = [f"abs:{kw}" for kw in self.keywords]  # abs: 匹配摘要，ti: 匹配标题
        keyword_str = "+OR+".join(keyword_queries)
        
        # 拼接分类查询
        cat_queries = [f"cat:{cat}" for cat in self.target_categories] if self.target_categories else []
        cat_str = "+OR+".join(cat_queries)
        
        # 组合查询条件（关键词 AND 分类）
        if keyword_str and cat_str:
            search_query = f"({keyword_str})+AND+({cat_str})"
        elif keyword_str:
            search_query = keyword_str
        elif cat_str:
            search_query = cat_str
        else:
            search_query = "abs:ISAC"  # 默认查询
        
        # 构造API URL
        params = {
            "search_query": search_query,
            "start": self.start,
            "max_results": self.per_page,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "format": "json"  # 返回JSON格式，易解析
        }
        base_url = "https://export.arxiv.org/api/query?"
        return base_url + urllib.parse.urlencode(params)

    def parse(self, response):
        """解析官方API的JSON响应"""
        try:
            # API返回的是XML，转JSON更易处理（或直接解析XML）
            # 注：arxiv API默认返回XML，这里改用JSON格式（需确认），若报错则解析XML
            data = json.loads(response.text)
        except:
            # 解析XML格式（API默认返回）
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            ns = {"arxiv": "http://www.w3.org/2005/Atom"}
            entries = root.findall("arxiv:entry", ns)
            data = {"entries": entries}
        
        # 解析论文数据
        if "entries" in data and data["entries"]:
            for entry in data["entries"]:
                # 解析XML格式的entry
                if isinstance(entry, ET.Element):
                    ns = {"arxiv": "http://www.w3.org/2005/Atom"}
                    # 提取论文ID
                    id_text = entry.find("arxiv:id", ns).text
                    arxiv_id = id_text.split("/abs/")[-1] if id_text else ""
                    # 提取标题
                    title = entry.find("arxiv:title", ns).text.strip() if entry.find("arxiv:title", ns) is not None else ""
                    # 提取摘要
                    abstract = entry.find("arxiv:summary", ns).text.strip() if entry.find("arxiv:summary", ns) is not None else ""
                    # 提取作者
                    authors = [author.find("arxiv:name", ns).text for author in entry.findall("arxiv:author", ns)]
                    # 提取分类
                    categories = [cat.text for cat in entry.findall("arxiv:category", ns)]
                    paper_categories = set(categories)
                else:
                    # 解析JSON格式（备用）
                    arxiv_id = entry.get("id", "").split("/abs/")[-1]
                    title = entry.get("title", "").strip()
                    abstract = entry.get("summary", "").strip()
                    authors = [a.get("name", "") for a in entry.get("authors", [])]
                    paper_categories = set(entry.get("categories", []))
                
                # 分类过滤
                if self.target_categories and not paper_categories.intersection(self.target_categories):
                    self.logger.debug(f"Skipped paper {arxiv_id} (categories not match)")
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
            
            # 处理分页
            self.start += self.per_page
            next_url = self._build_api_url()
            yield scrapy.Request(next_url, callback=self.parse)
        else:
            self.logger.info("No more papers to crawl")