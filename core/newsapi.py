# -*- coding: utf-8 -*-
"""
新闻 API 封装
支持两种数据源：
  1. NewsAPI (https://newsapi.org)  — 国际新闻，免费版每天 100 次
  2. 聚合数据 (https://www.juhe.cn) — 国内新闻，免费版每天 100 次
"""
import requests
from bs4 import BeautifulSoup


class NewsAPI:
    """新闻 API 封装类，支持 NewsAPI 和聚合数据两种数据源"""

    # 分类映射
    CATEGORY_MAP_NEWSAPI = {
        "top": None,           # 头条（不传 category 参数）
        "technology": "technology",
        "sports": "sports",
        "business": "business",
        "entertainment": "entertainment"
    }

    CATEGORY_MAP_JUHE = {
        "top": "top",
        "technology": "keji",
        "sports": "tiyu",
        "business": "caijing",
        "entertainment": "yule"
    }

    def __init__(self, api_key, provider="newsapi"):
        self.api_key = api_key
        self.provider = provider

    def _is_ready(self):
        """检查 API Key 是否已配置"""
        return bool(self.api_key)

    def get_headlines(self, category="top", page=1, page_size=20):
        """
        获取新闻列表
        :param category: 分类 key（top/technology/sports/business/entertainment）
        :return: 新闻列表，每项为 dict（title / source / time / url / content / description）
        """
        if not self._is_ready():
            return []
        if self.provider == "newsapi":
            return self._get_newsapi(category, page, page_size)
        elif self.provider == "juhe":
            return self._get_juhe(category)
        return []

    # ────────────── NewsAPI ──────────────

    def _get_newsapi(self, category, page, page_size):
        """从 NewsAPI 获取新闻"""
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": self.api_key,
            "page": page,
            "pageSize": page_size,
            "country": "cn"
        }
        cat = self.CATEGORY_MAP_NEWSAPI.get(category)
        if cat:
            params["category"] = cat

        try:
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            if data.get("status") == "ok":
                articles = data.get("articles", [])
                return [self._format_newsapi_article(a) for a in articles]
            return []
        except Exception:
            return []

    def _format_newsapi_article(self, a):
        """格式化 NewsAPI 文章"""
        return {
            "title": a.get("title") or "无标题",
            "source": a.get("source", {}).get("name", "未知来源"),
            "time": (a.get("publishedAt") or "")[:19].replace("T", " "),
            "url": a.get("url", ""),
            "content": a.get("content") or a.get("description") or "",
            "description": a.get("description") or ""
        }

    # ────────────── 聚合数据 ──────────────

    def _get_juhe(self, category):
        """从聚合数据获取新闻"""
        url = "http://v.juhe.cn/toutiao/index"
        type_code = self.CATEGORY_MAP_JUHE.get(category, "top")
        params = {"key": self.api_key, "type": type_code}

        try:
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            if data.get("error_code") == 0:
                articles = data.get("result", {}).get("data", [])
                return [self._format_juhe_article(a) for a in articles]
            return []
        except Exception:
            return []

    def _format_juhe_article(self, a):
        """格式化聚合数据文章"""
        return {
            "title": a.get("title") or "无标题",
            "source": a.get("author_name") or "未知来源",
            "time": (a.get("date") or "")[:19],
            "url": a.get("url", ""),
            "content": a.get("title", ""),   # 聚合数据不返回正文，需从 URL 抓取
            "description": a.get("title", "")
        }

    # ────────────── 全文抓取 ──────────────

    def fetch_full_content(self, url):
        """
        从新闻 URL 抓取全文
        使用 BeautifulSoup 解析 HTML，尝试多种常见的内容选择器
        """
        if not url:
            return "无法获取新闻全文，请访问原文链接查看。"
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=15)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "lxml")

            # 移除脚本和样式
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # 尝试多种常见的内容选择器
            selectors = [
                "article", "div.article-body", "div.article-content",
                "div.content", "div.news_content", "div#article",
                "div.article", "main", "div.post-content",
                "div.article_content", "div.txt"
            ]
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(separator="\n", strip=True)
                    if len(text) > 100:
                        return text

            # 回退：获取所有段落
            paragraphs = soup.find_all("p")
            text = "\n".join(
                p.get_text(strip=True) for p in paragraphs
                if len(p.get_text(strip=True)) > 20
            )
            return text if text else "无法获取新闻全文，请访问原文链接查看。"
        except Exception:
            return "无法获取新闻全文，请访问原文链接查看。"
