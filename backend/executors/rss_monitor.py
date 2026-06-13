"""
RSS feed monitor executor using feedparser.
Fetches and optionally filters RSS/Atom feeds.
"""
import time
from .base import BaseExecutor, WorkflowExecutionError


class RssMonitorExecutor(BaseExecutor):

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "title": "RSS监控配置",
            "properties": {
                "rss_url": {
                    "type": "string",
                    "title": "RSS源URL",
                    "description": "RSS或Atom feed地址",
                },
                "keywords": {
                    "type": "array",
                    "title": "关键词过滤",
                    "description": "只保留标题或摘要中包含这些关键词的条目",
                    "items": {"type": "string"},
                },
                "max_items": {
                    "type": "number",
                    "title": "最大条目数",
                    "description": "最多获取的条目数量",
                    "default": 20,
                },
                "filter_by_keyword": {
                    "type": "boolean",
                    "title": "启用关键词过滤",
                    "default": False,
                },
            },
            "required": ["rss_url"],
        }

    def execute(self, config: dict, context: dict) -> dict:
        try:
            import feedparser
        except ImportError:
            raise WorkflowExecutionError("DEP_MISSING", "feedparser is not installed", "rss_monitor")

        rss_url = config.get("rss_url", "")
        keywords = config.get("keywords", [])
        max_items = config.get("max_items", 20)
        filter_enabled = config.get("filter_by_keyword", False)

        if not rss_url:
            raise WorkflowExecutionError("CFG_INVALID", "RSS URL is required", "rss_monitor")

        try:
            feed = feedparser.parse(rss_url)
        except Exception as e:
            raise WorkflowExecutionError("FETCH_ERROR", f"Failed to fetch RSS feed: {e}", "rss_monitor")

        if feed.bozo and not feed.entries:
            raise WorkflowExecutionError(
                "PARSE_ERROR",
                f"Failed to parse RSS feed: {feed.bozo_exception}",
                "rss_monitor",
            )

        items = []
        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            published = entry.get("published", entry.get("updated", ""))
            summary = entry.get("summary", entry.get("description", ""))

            # Strip HTML from summary
            summary = self._strip_html(summary)

            # Keyword filtering
            if filter_enabled and keywords:
                search_text = f"{title} {summary}".lower()
                if not any(kw.lower() in search_text for kw in keywords):
                    continue

            items.append({
                "title": title,
                "link": link,
                "published": published,
                "summary": summary[:500],  # Truncate long summaries
            })

            if len(items) >= max_items:
                break

        return {
            "status": "success",
            "data": {
                "feed_title": feed.feed.get("title", rss_url),
                "feed_link": feed.feed.get("link", ""),
                "items": items,
                "item_count": len(items),
            },
        }

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.compile(r'<[^>]+>')
        return clean.sub('', text).strip()


class ScheduleTriggerExecutor(BaseExecutor):
    """Schedule trigger executor - records trigger configuration.
    Actual scheduling is managed by the workflow engine / APScheduler."""

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "title": "定时触发配置",
            "properties": {
                "cron_expression": {
                    "type": "string",
                    "title": "Cron表达式",
                    "description": "如 '0 9 * * *' 表示每天9点执行，'*/30 * * * *' 每30分钟",
                    "default": "0 9 * * *",
                },
                "timezone": {
                    "type": "string",
                    "title": "时区",
                    "default": "Asia/Shanghai",
                },
                "max_executions": {
                    "type": "number",
                    "title": "最大执行次数",
                    "description": "0表示无限制",
                    "default": 0,
                },
            },
            "required": ["cron_expression"],
        }

    def execute(self, config: dict, context: dict) -> dict:
        cron_expr = config.get("cron_expression", "0 9 * * *")
        timezone = config.get("timezone", "Asia/Shanghai")
        max_exec = config.get("max_executions", 0)

        # Parse cron expression into human-readable description
        cron_desc = self._describe_cron(cron_expr)

        return {
            "status": "success",
            "data": {
                "trigger_time": cron_desc,
                "next_trigger": f"根据 {cron_expr} ({timezone}) 计算",
                "cron_expression": cron_expr,
                "timezone": timezone,
                "max_executions": max_exec if max_exec > 0 else "unlimited",
            },
        }

    @staticmethod
    def _describe_cron(expr: str) -> str:
        """Convert a cron expression to human-readable description."""
        try:
            from cron_descriptor import get_description
            return get_description(expr)
        except ImportError:
            pass

        parts = expr.strip().split()
        if len(parts) < 5:
            return f"Cron: {expr}"

        minute, hour, day_of_month, month, day_of_week = parts[:5]

        if minute == "*" and hour != "*":
            desc_map = {
                "0": "午夜", "1": "凌晨1点", "2": "凌晨2点", "3": "凌晨3点",
                "6": "早上6点", "7": "早上7点", "8": "早上8点", "9": "早上9点",
                "10": "上午10点", "12": "中午12点", "14": "下午2点",
                "18": "下午6点", "20": "晚上8点", "22": "晚上10点",
            }
            time_desc = desc_map.get(hour, f"{hour}:00")
            return f"每天 {time_desc}"

        if minute.startswith("*/"):
            interval = minute.split("/")[1]
            return f"每 {interval} 分钟"

        return f"Cron表达式: {expr}"
