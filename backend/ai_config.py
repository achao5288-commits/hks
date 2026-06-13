"""
AI-powered node configuration generator using Silicon Flow (硅基流动) API.
Takes a user's natural language requirement and generates appropriate config values.
"""
import json
import requests
from typing import Optional

SILICON_FLOW_API = "https://api.siliconflow.cn/v1/chat/completions"
SILICON_FLOW_KEY = "sk-rxjyoehcradmpjkjvadsyanlsgudzwuxaqketukgwhvjjgcj"
DEFAULT_MODEL = "deepseek-ai/DeepSeek-V3"

SYSTEM_PROMPT = """You are an expert workflow automation configuration assistant.
Given a user's natural language requirement and a JSON Schema describing a node's configuration fields,
you must output a VALID JSON object with the config values filled in.

Rules:
1. Output ONLY the JSON object, no markdown code fences, no explanation.
2. Fill EVERY field that you can infer from the user's requirement.
3. For fields you cannot infer, use the schema's default value.
4. For URLs, only use real, accessible URLs that you know exist. If the user wants to scrape a specific site, extract the URL from their requirement.
5. For CSS selectors, infer reasonable selectors based on common HTML patterns for the content described.
6. For email-related fields, extract addresses and subjects from the requirement.
7. For cron expressions, convert natural language time descriptions to standard cron format.
8. All string values must be in the same language as the user's requirement.
9. For array/object fields, output proper JSON arrays/objects, not placeholder text.
10. The field "selectors" (when type is array) should be an array of objects with "name" and "selector" fields.

JSON Schema for reference:
{json_schema}

User requirement: {user_input}

Output ONLY the JSON config object:"""


def generate_config(
    user_input: str,
    node_type: str,
    config_schema: dict,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Call Silicon Flow API to generate node configuration from natural language input.

    Args:
        user_input: The user's natural language requirement
        node_type: The type of node being configured (e.g., 'web_crawler')
        config_schema: The JSON Schema for this node type's config
        model: Silicon Flow model to use

    Returns:
        dict: Generated config values matching the schema
    """
    schema_str = json.dumps(config_schema, ensure_ascii=False, indent=2)
    prompt = SYSTEM_PROMPT.format(json_schema=schema_str, user_input=user_input)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise JSON generator. Output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,  # Low temperature for deterministic output
        "max_tokens": 4096,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {SILICON_FLOW_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(SILICON_FLOW_API, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()

        # Remove markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        config = json.loads(content)

        # Merge with defaults from schema to ensure all fields exist
        if "properties" in config_schema:
            for key, prop in config_schema["properties"].items():
                if key not in config and "default" in prop:
                    config[key] = prop["default"]

        return config

    except json.JSONDecodeError as e:
        raise ValueError(f"AI returned invalid JSON: {content[:200]}... Error: {e}")
    except requests.RequestException as e:
        raise ConnectionError(f"Silicon Flow API error: {e}")
    except Exception as e:
        raise RuntimeError(f"AI config generation failed: {e}")


def generate_config_stream(
    user_input: str,
    node_type: str,
    config_schema: dict,
    model: str = DEFAULT_MODEL,
):
    """
    Streaming version — yields content chunks.
    """
    schema_str = json.dumps(config_schema, ensure_ascii=False, indent=2)
    prompt = SYSTEM_PROMPT.format(json_schema=schema_str, user_input=user_input)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise JSON generator. Output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
        "stream": True,
    }

    headers = {
        "Authorization": f"Bearer {SILICON_FLOW_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(SILICON_FLOW_API, json=payload, headers=headers, timeout=60, stream=True)
    response.raise_for_status()

    full_content = ""
    for line in response.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data["choices"][0].get("delta", {})
                    content_chunk = delta.get("content", "")
                    if content_chunk:
                        full_content += content_chunk
                        yield content_chunk
                except json.JSONDecodeError:
                    continue

    # Clean and parse final result
    content = full_content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)
    yield "\n__FINAL__" + content


# ============================================================
# Full Auto Workflow Generation
# ============================================================

WORKFLOW_GEN_TEMPLATE = """You are an expert workflow automation architect. Given a user's natural language requirement, you must design a complete workflow.

Available node types:
- web_crawler: Scrape web pages with CSS selectors. Config: url, selectors (array of name/selector/attribute), wait_time, user_agent, scroll_to_bottom, click_load_more, timeout, screenshot
- rss_monitor: Monitor RSS feeds. Config: rss_url, keywords (array), max_items, filter_by_keyword
- data_process: Clean/transform data with pandas. Config: field_mapping (object), columns_to_keep (array), drop_duplicates, fill_missing, data_type_conversions (object), sort_by, sort_ascending, filters (array)
- excel_chart: Generate Excel with charts. Config: output_path, sheet_name, create_chart, chart_type (bar/line/pie), chart_title, chart_category_column, chart_value_column, column_widths (object), auto_fit_columns
- email_sender: Send emails via SMTP. Config: provider (qq/163/gmail/custom), smtp_host, smtp_port, smtp_user, smtp_password, to, subject, body, is_html, cc, bcc, attachments (array), dry_run
- schedule_trigger: Cron-based trigger. Config: cron_expression, timezone, max_executions

Rules:
1. Output ONLY a valid JSON object. No markdown code fences, no explanation.
2. The JSON must have this EXACT structure (replace placeholders with real values):
  - "name": workflow name in Chinese
  - "description": one-line description
  - "nodes": array of node objects, each with: id, type, label, config (all required fields filled), pos_x, pos_y
  - "edges": array of edge objects, each with: id, source, target
3. Node positions: space 300px horizontally (80, 380, 680, 980, 1280), keep Y around 120-250.
4. Include a schedule_trigger node at the START of every workflow unless the user explicitly says manual trigger.
5. ALWAYS include data_process between crawler/rss and excel/email for data cleaning.
6. CRITICAL for URLs: ALWAYS use local demo pages for scraping. For world cup/sports use http://localhost:5173/demo-worldcup.html. For news/media use http://localhost:5173/demo-news.html. Never use external URLs unless the user explicitly provides one.
7. CRITICAL for CSS selectors on demo pages:
   - For demo-worldcup.html (World Cup page): use ".team.home" for home team, ".team.away" for away team, ".score" for score, ".match-date" for date, ".match-venue" for venue, "[data-round]" for round/stage, ".match-log" for match events log.
   - For demo-news.html (News page): use ".title" for title, ".summary" for summary, ".source" for source, ".time" for time.
   Each selector object MUST have "name" (Chinese field name) and "selector" (CSS selector string). The "attribute" field must be empty string "" (NOT "textContent") to get text content. Each selector object must have "name" and "selector" fields.
8. For email - extract sender, recipient, password from the user's words. Set dry_run to false when real credentials are provided.
9. Generate meaningful Chinese labels for each node.
10. For email body: use HTML with inline table showing data rows. Use expressions like ${node_id.data.rows[0].field} to embed upstream data. The field names should match the data_process output column names.
11. For email attachments: ALWAYS use expression format ${excel_node_id.data.file_path} to reference the Excel file, NEVER hardcode a path.
12. For data_process field_mapping: the keys are the web_crawler selector "name" values, the values are Chinese display names. Keep the mapping direction correct.
13. For QQ email, use provider="qq", smtp_host="smtp.qq.com", smtp_port=465. For 163, use provider="163", smtp_host="smtp.163.com", smtp_port=465.
12. Create a sensible pipeline: trigger -> data_source -> process -> output -> notify.

User requirement: %s

Output ONLY the JSON:"""


def generate_full_workflow(user_input: str, model: str = DEFAULT_MODEL) -> dict:
    """
    Generate a complete workflow (nodes + edges + configs) from natural language input.
    """
    prompt = WORKFLOW_GEN_TEMPLATE % user_input

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a workflow automation architect. Output ONLY valid JSON, no markdown."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 8192,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {SILICON_FLOW_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(SILICON_FLOW_API, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()

        # Clean markdown code fences
        if content.startswith("```"):
            lines = content.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        workflow = json.loads(content)

        # Validate structure
        if "nodes" not in workflow or "edges" not in workflow:
            raise ValueError("AI response missing 'nodes' or 'edges'")

        # Ensure each node has required fields
        for node in workflow["nodes"]:
            if "id" not in node or "type" not in node:
                raise ValueError(f"Node missing id or type: {node}")

        return workflow

    except json.JSONDecodeError as e:
        raise ValueError(f"AI returned invalid JSON: {content[:300]}... Error: {e}")
    except requests.RequestException as e:
        raise ConnectionError(f"Silicon Flow API error: {e}")
    except Exception as e:
        raise RuntimeError(f"Auto workflow generation failed: {e}")
