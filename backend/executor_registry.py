"""
Executor Registry — maps node type names to executor classes.
New executor types are registered here.
"""
from executors import (
    BaseExecutor,
    WebCrawlerExecutor,
    DataProcessExecutor,
    ExcelChartExecutor,
    EmailSenderExecutor,
    RssMonitorExecutor,
    ScheduleTriggerExecutor,
)


class ExecutorRegistry:
    """Global registry for node type -> executor class mapping."""

    def __init__(self):
        self._registry: dict[str, type[BaseExecutor]] = {}

    def register(self, typename: str, executor_class: type[BaseExecutor]):
        """Register an executor class for a node type."""
        if not issubclass(executor_class, BaseExecutor):
            raise TypeError(f"{executor_class} must be a subclass of BaseExecutor")
        self._registry[typename] = executor_class

    def get(self, typename: str) -> BaseExecutor:
        """Get an executor instance for the given node type."""
        if typename not in self._registry:
            raise KeyError(f"No executor registered for type: {typename}")
        return self._registry[typename]()

    def get_all_types(self) -> list[str]:
        """List all registered node types."""
        return list(self._registry.keys())

    def get_all_schemas(self) -> dict:
        """Return {typename: config_schema} for all registered types."""
        result = {}
        for typename, cls in self._registry.items():
            try:
                instance = cls()
                result[typename] = instance.get_config_schema()
            except Exception:
                result[typename] = {"error": "Failed to load schema"}
        return result

    def get_type_info(self) -> list[dict]:
        """Return list of {type, label, description, icon} for all node types."""
        info_map = {
            "web_crawler": {
                "label": "网页抓取",
                "description": "抓取网页数据，支持CSS选择器",
                "icon": "Globe",
                "color": "#3B82F6",
            },
            "rss_monitor": {
                "label": "RSS监控",
                "description": "监控RSS源更新",
                "icon": "Rss",
                "color": "#F97316",
            },
            "data_process": {
                "label": "数据清洗",
                "description": "清洗和转换数据",
                "icon": "Filter",
                "color": "#22C55E",
            },
            "excel_chart": {
                "label": "Excel生成",
                "description": "生成Excel表格和图表",
                "icon": "FileSpreadsheet",
                "color": "#EAB308",
            },
            "email_sender": {
                "label": "邮件发送",
                "description": "发送邮件报告",
                "icon": "Mail",
                "color": "#EF4444",
            },
            "schedule_trigger": {
                "label": "定时触发",
                "description": "定时触发工作流",
                "icon": "Clock",
                "color": "#8B5CF6",
            },
        }
        result = []
        for typename in self._registry:
            info = info_map.get(typename, {
                "label": typename,
                "description": "",
                "icon": "Box",
                "color": "#6B7280",
            })
            info["type"] = typename
            result.append(info)
        return result


# Global singleton instance
registry = ExecutorRegistry()

# Register built-in executor types
registry.register("web_crawler", WebCrawlerExecutor)
registry.register("rss_monitor", RssMonitorExecutor)
registry.register("data_process", DataProcessExecutor)
registry.register("excel_chart", ExcelChartExecutor)
registry.register("email_sender", EmailSenderExecutor)
registry.register("schedule_trigger", ScheduleTriggerExecutor)
