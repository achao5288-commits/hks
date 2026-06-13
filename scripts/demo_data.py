"""
Initialize demo data for the workflow automation platform.
Creates a pre-configured "舆情监控日报" workflow template.
"""
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models import create_tables, get_connection, node_presets_table, workflows_table


def init_demo():
    """Create demo workflow template and presets."""
    create_tables()
    conn = get_connection()

    # Check if demo data already exists
    existing = conn.execute(workflows_table.select().limit(1)).fetchone()
    if existing:
        print("Demo data already exists, skipping initialization.")
        conn.close()
        return

    # ---- Demo workflow: 舆情监控日报 ----
    demo_nodes = [
        {
            "id": "node_trigger",
            "type": "schedule_trigger",
            "config": {
                "cron_expression": "0 9 * * *",
                "timezone": "Asia/Shanghai",
                "max_executions": 0,
            },
            "position": {"x": 100, "y": 100},
        },
        {
            "id": "node_crawler",
            "type": "web_crawler",
            "config": {
                "url": "http://localhost:5173/demo-news.html",
                "selectors": [
                    {"name": "title", "selector": ".title"},
                    {"name": "summary", "selector": ".summary"},
                    {"name": "source", "selector": ".source"},
                    {"name": "time", "selector": ".time"},
                ],
                "wait_time": 2,
                "scroll_to_bottom": False,
                "timeout": 30,
            },
            "position": {"x": 380, "y": 100},
        },
        {
            "id": "node_process",
            "type": "data_process",
            "config": {
                "field_mapping": {
                    "time": "发布时间",
                    "source": "来源",
                    "title": "标题",
                    "summary": "摘要",
                },
                "drop_duplicates": True,
                "fill_missing": "N/A",
                "sort_by": "发布时间",
                "sort_ascending": False,
            },
            "position": {"x": 660, "y": 100},
        },
        {
            "id": "node_excel",
            "type": "excel_chart",
            "config": {
                "sheet_name": "舆情日报",
                "create_chart": True,
                "chart_type": "bar",
                "chart_title": "舆情来源统计",
                "chart_category_column": "来源",
                "chart_value_column": "",
                "auto_fit_columns": True,
            },
            "position": {"x": 940, "y": 100},
        },
        {
            "id": "node_email",
            "type": "email_sender",
            "config": {
                "provider": "qq",
                "smtp_host": "smtp.qq.com",
                "smtp_port": 465,
                "smtp_user": "",
                "smtp_password": "",
                "to": "",
                "subject": "舆情监控日报 - ${node_trigger.data.trigger_time}",
                "body": "<h2>📊 舆情监控日报</h2><p>以下是今日舆情汇总，共抓取 ${node_process.data.row_count} 条舆情数据。</p><p>详细数据请见附件Excel文件。</p>",
                "is_html": True,
                "attachments": ["${node_excel.data.file_path}"],
                "dry_run": True,
            },
            "position": {"x": 1220, "y": 100},
        },
    ]

    demo_edges = [
        {"id": "edge_trigger_crawler", "source": "node_trigger", "target": "node_crawler"},
        {"id": "edge_crawler_process", "source": "node_crawler", "target": "node_process"},
        {"id": "edge_process_excel", "source": "node_process", "target": "node_excel"},
        {"id": "edge_excel_email", "source": "node_excel", "target": "node_email"},
    ]

    # Insert demo workflow
    conn.execute(workflows_table.insert().values(
        name="舆情监控日报（演示）",
        description="自动抓取舆情新闻 → 数据清洗 → 生成Excel报表 → 邮件发送日报。拖拽到画布即可体验完整自动化流程。",
        nodes_json=json.dumps(demo_nodes, ensure_ascii=False),
        edges_json=json.dumps(demo_edges, ensure_ascii=False),
    ))

    # Insert node presets
    presets = [
        {
            "node_type": "web_crawler",
            "name": "舆情新闻抓取模板",
            "config_json": json.dumps({
                "url": "http://localhost:5173/demo-news.html",
                "selectors": [
                    {"name": "title", "selector": ".title"},
                    {"name": "summary", "selector": ".summary"},
                    {"name": "source", "selector": ".source"},
                    {"name": "time", "selector": ".time"},
                ],
                "wait_time": 2,
            }, ensure_ascii=False),
        },
        {
            "node_type": "data_process",
            "name": "标准清洗模板",
            "config_json": json.dumps({
                "drop_duplicates": True,
                "fill_missing": "N/A",
            }, ensure_ascii=False),
        },
        {
            "node_type": "excel_chart",
            "name": "日报Excel模板",
            "config_json": json.dumps({
                "sheet_name": "数据报表",
                "create_chart": True,
                "chart_type": "bar",
                "chart_title": "数据统计",
            }, ensure_ascii=False),
        },
        {
            "node_type": "email_sender",
            "name": "QQ邮箱发送模板",
            "config_json": json.dumps({
                "provider": "qq",
                "smtp_host": "smtp.qq.com",
                "smtp_port": 465,
                "dry_run": True,
            }, ensure_ascii=False),
        },
    ]

    for p in presets:
        conn.execute(node_presets_table.insert().values(**p))

    conn.commit()
    conn.close()

    print("=" * 60)
    print("  ✅ 演示数据初始化完成!")
    print("=" * 60)
    print()
    print("  已创建:")
    print("    - 1 个演示工作流: 舆情监控日报（演示）")
    print("    - 4 个节点配置预设模板")
    print()
    print("  启动应用后:")
    print("    1. 打开 http://localhost:5173")
    print("    2. 加载演示工作流")
    print("    3. 配置邮箱信息（可选，默认dry_run模式）")
    print("    4. 点击执行，观察实时日志")
    print()


if __name__ == "__main__":
    init_demo()
