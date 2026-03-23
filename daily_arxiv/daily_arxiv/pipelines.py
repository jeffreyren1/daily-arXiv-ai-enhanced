# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# 移除不需要的 arxiv 库导入（避免依赖）
# import arxiv

class DailyArxivPipeline:
    def __init__(self):
        # 移除 arXiv Client 初始化（不再使用）
        pass

    def process_item(self, item: dict, spider):
        # 1. 补充 pdf 和 abs 链接（保留原有逻辑）
        item["pdf"] = f"https://arxiv.org/pdf/{item['id']}"
        item["abs"] = f"https://arxiv.org/abs/{item['id']}"
        
        # 2. 移除所有调用 arXiv API 的代码（核心修复）
        # 直接使用爬虫爬取阶段已提取的字段，无需二次请求
        # 字段映射：爬虫的 abstract → summary，保持原有 key 兼容
        if "abstract" in item:
            item["summary"] = item.pop("abstract")  # 把 abstract 重命名为 summary
        
        # 3. 补充可选字段的默认值（避免 KeyError）
        item.setdefault("comment", "")  # 评论字段默认空
        
        # 4. 保留打印逻辑（方便调试）
        print(item)
        return item