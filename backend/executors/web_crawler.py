"""
Web crawler executor using Playwright (sync API).
Extracts data from web pages using CSS selectors.
"""
import time
from .base import BaseExecutor, WorkflowExecutionError


class WebCrawlerExecutor(BaseExecutor):

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "title": "网页抓取配置",
            "properties": {
                "url": {
                    "type": "string",
                    "title": "目标URL",
                    "description": "要抓取的网页地址",
                },
                "selectors": {
                    "type": "array",
                    "title": "CSS选择器列表",
                    "description": "每个选择器包含名称和CSS选择器表达式",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "title": "字段名"},
                            "selector": {"type": "string", "title": "CSS选择器"},
                            "attribute": {
                                "type": "string",
                                "title": "提取属性",
                                "description": "留空提取文本内容，填写href/src等提取属性值",
                                "default": "",
                            },
                        },
                        "required": ["name", "selector"],
                    },
                },
                "wait_time": {
                    "type": "number",
                    "title": "等待时间(秒)",
                    "description": "页面加载后额外等待的时间",
                    "default": 3,
                },
                "user_agent": {
                    "type": "string",
                    "title": "User-Agent",
                    "description": "自定义用户代理字符串",
                    "default": "",
                },
                "scroll_to_bottom": {
                    "type": "boolean",
                    "title": "滚动到底部",
                    "description": "是否在提取前滚动到页面底部",
                    "default": False,
                },
                "click_load_more": {
                    "type": "string",
                    "title": "加载更多按钮选择器",
                    "description": "用于点击加载更多的CSS选择器，留空不点击",
                    "default": "",
                },
                "timeout": {
                    "type": "number",
                    "title": "超时(秒)",
                    "description": "页面加载超时时间",
                    "default": 30,
                },
                "screenshot": {
                    "type": "boolean",
                    "title": "保存截图",
                    "description": "是否保存页面截图",
                    "default": False,
                },
            },
            "required": ["url", "selectors"],
        }

    def execute(self, config: dict, context: dict) -> dict:
        url = config.get("url", "")
        selectors = config.get("selectors", [])
        wait_time = config.get("wait_time", 3)
        timeout = config.get("timeout", 30) * 1000  # ms
        user_agent = config.get("user_agent", "")
        scroll = config.get("scroll_to_bottom", False)
        click_more = config.get("click_load_more", "")
        take_screenshot = config.get("screenshot", False)

        if not url:
            raise WorkflowExecutionError("CFG_INVALID", "URL is required", "web_crawler")
        if not selectors:
            raise WorkflowExecutionError("CFG_INVALID", "At least one selector is required", "web_crawler")

        # Resolve expressions in URL and selectors using upstream context
        url = self._resolve_string(url, context)
        resolved_selectors = []
        for s in selectors:
            resolved_selectors.append({
                "name": self._resolve_string(s.get("name", ""), context),
                "selector": self._resolve_string(s.get("selector", ""), context),
                "attribute": self._resolve_string(s.get("attribute", ""), context),
            })

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise WorkflowExecutionError(
                "DEP_MISSING",
                "Playwright is not installed. Run: pip install playwright && playwright install chromium",
                "web_crawler",
            )

        browser = None
        try:
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(headless=True)
            context_opts = {}
            if user_agent:
                context_opts["user_agent"] = user_agent
            context = browser.new_context(**context_opts)
            page = context.new_page()
            page.set_default_timeout(timeout)

            page.goto(url, wait_until="domcontentloaded")
            time.sleep(wait_time)

            if scroll:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)

            if click_more:
                try:
                    page.click(click_more, timeout=10000)
                    time.sleep(2)
                except Exception:
                    pass  # Load more button might not exist

            selector_results = {}
            page_title = page.title()

            for sel in resolved_selectors:
                name = sel["name"]
                css = sel["selector"]
                attr = sel.get("attribute", "")

                try:
                    elements = page.query_selector_all(css)
                    values = []
                    # Attributes that should fall back to text content
                    TEXT_ATTRS = {"", "text", "textcontent", "innertext", "textContent", "innerText"}
                    for el in elements:
                        if attr and attr.lower() not in TEXT_ATTRS:
                            val = el.get_attribute(attr) or el.inner_text().strip()
                        else:
                            val = el.inner_text().strip()
                        values.append(val)
                    selector_results[name] = values
                except Exception as e:
                    selector_results[name] = []
                    selector_results[f"{name}_error"] = str(e)

            screenshot_path = None
            if take_screenshot:
                import tempfile, os
                screenshot_path = os.path.join(
                    tempfile.gettempdir(), f"crawler_screenshot_{int(time.time())}.png"
                )
                page.screenshot(path=screenshot_path, full_page=True)

            return {
                "status": "success",
                "data": {
                    "url": url,
                    "title": page_title,
                    "selector_results": selector_results,
                    "screenshot_path": screenshot_path,
                },
            }

        except Exception as e:
            raise WorkflowExecutionError(
                "CRAWL_ERROR", f"Web crawl failed: {str(e)}", "web_crawler"
            )
        finally:
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass

    @staticmethod
    def _resolve_string(value: str, context: dict) -> str:
        """Resolve ${node_id.field} expressions in a string."""
        import re
        pattern = re.compile(r'\$\{(\w+)\.(.+?)\}')
        def replacer(match):
            node_id = match.group(1)
            field_path = match.group(2)
            if node_id in context:
                result = _get_nested(context[node_id], field_path)
                if result is not None:
                    return str(result)
            return match.group(0)
        return pattern.sub(replacer, value)


def _get_nested(data: dict, path: str):
    """Access nested dict/list by dot/bracket path like 'items[0].title'."""
    import re
    parts = re.split(r'\.|\[|\]', path)
    current = data
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part.isdigit():
            if isinstance(current, list):
                current = current[int(part)]
            else:
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
