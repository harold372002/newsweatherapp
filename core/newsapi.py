# -*- coding: utf-8 -*-
"""
新闻 API 封装 — 改用 RSS 免费新闻源
无需 API Key，直接抓取 RSS 订阅源
"""
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup


class NewsAPI:
    """RSS 免费新闻源封装类（无需 API Key）"""

    RSS_FEEDS = {
        "top": [
            "http://feeds.bbci.co.uk/chinese/simp/rss.xml",
            "https://www.chinanews.com.cn/rss/scroll.xml",
        ],
        "technology": ["https://www.chinanews.com.cn/rss/it.xml"],
        "sports": ["https://www.chinanews.com.cn/rss/sports.xml"],
        "business": ["https://www.chinanews.com.cn/rss/finance.xml"],
        "entertainment": ["https://www.chinanews.com.cn/rss/ent.xml"],
    }

    KEYWORDS = {
        "technology": ["科技", "技术", "互联网", "AI", "芯片", "手机", "电脑", "软件"],
        "sports": ["体育", "足球", "篮球", "奥运", "比赛", "冠军", "联赛"],
        "business": ["经济", "金融", "股市", "商业", "投资", "基金", "银行"],
        "entertainment": ["娱乐", "电影", "音乐", "明星", "综艺", "电视剧"],
    }

    def __init__(self, api_key="", provider="rss"):
        self._cached_top = None

    def _is_ready(self):
        return True

    def get_headlines(self, category="top", page=1, page_size=20):
        feeds = self.RSS_FEEDS.get(category, self.RSS_FEEDS["top"])
        articles = []
        for feed_url in feeds:
            try:
                resp = requests.get(feed_url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                if resp.status_code != 200:
                    continue
                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                if not items:
                    items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
                for item in items:
                    title = self._get_text(item, "title")
                    if not title:
                        continue
                    link = self._get_text(item, "link")
                    pub_date = self._get_text(item, "pubDate") or self._get_text(item, "{http://www.w3.org/2005/Atom}published")
                    desc = self._get_text(item, "description") or self._get_text(item, "{http://www.w3.org/2005/Atom}summary")
                    if desc:
                        desc = BeautifulSoup(desc, "lxml").get_text(strip=True)
                    source_name = self._get_source(feed_url)
                    articles.append({"title": title, "source": source_name, "time": self._format_time(pub_date), "url": link, "content": desc or title, "description": desc or ""})
            except Exception:
                continue
        if category != "top" and len(articles) < 5:
            if self._cached_top is None:
                self._cached_top = self.get_headlines("top")
            keywords = self.KEYWORDS.get(category, [])
            for article in self._cached_top:
                if len(articles) >= page_size:
                    break
                title = article.get("title", "")
                if any(kw in title for kw in keywords):
                    if article not in articles:
                        articles.append(article)
        return articles[:page_size]

    def fetch_full_content(self, url):
        if not url:
            return "无法获取新闻全文，请访问原文链接查看。"
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            selectors = ["article", "div.article-body", "div.article-content", "div.content", "div.news_content", "div#article", "div.article", "main", "div.post-content", "div.article_content", "div.txt", "div.story-body", "div.main-content"]
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(separator="\n", strip=True)
                    if len(text) > 100:
                        return text
            paragraphs = soup.find_all("p")
            text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)
            return text if text else "无法获取新闻全文，请访问原文链接查看。"
        except Exception:
            return "无法获取新闻全文，请访问原文链接查看。"

    def _get_text(self, item, tag):
        elem = item.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
        return ""

    def _get_source(self, url):
        if "bbc" in url:
            return "BBC中文"
        elif "chinanews" in url:
            return "中新网"
        elif "36kr" in url:
            return "36氪"
        else:
            return "网络"

    def _format_time(self, time_str):
        if not time_str:
            return ""
        try:
            parts = time_str.split(" ")
            if len(parts) >= 5:
                return f"{parts[3]}-{parts[2]}-{parts[1]} {parts[4][:5]}"
        except Exception:
            pass
        return time_str[:19] if len(time_str) >= 19 else time_str
