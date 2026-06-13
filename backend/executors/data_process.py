"""
Data process executor using pandas.
Cleans, transforms, and reshapes data from upstream nodes.
"""
import json
from .base import BaseExecutor, WorkflowExecutionError


class DataProcessExecutor(BaseExecutor):

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "title": "数据清洗配置",
            "properties": {
                "field_mapping": {
                    "type": "object",
                    "title": "字段映射",
                    "description": "旧字段名到新字段名的映射，如 {'old_name': 'new_name'}",
                },
                "columns_to_keep": {
                    "type": "array",
                    "title": "保留列",
                    "description": "只保留这些列，留空保留全部",
                    "items": {"type": "string"},
                },
                "drop_duplicates": {
                    "type": "boolean",
                    "title": "去重",
                    "default": True,
                },
                "fill_missing": {
                    "type": "string",
                    "title": "缺失值填充",
                    "description": "用于填充空值的字符串，留空不填充",
                    "default": "",
                },
                "data_type_conversions": {
                    "type": "object",
                    "title": "数据类型转换",
                    "description": "列名到目标类型的映射，如 {'price': 'float', 'count': 'int'}",
                },
                "sort_by": {
                    "type": "string",
                    "title": "排序列",
                    "description": "按此列排序",
                    "default": "",
                },
                "sort_ascending": {
                    "type": "boolean",
                    "title": "升序排列",
                    "default": True,
                },
                "filters": {
                    "type": "array",
                    "title": "过滤条件",
                    "description": "数据过滤规则",
                    "items": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string", "title": "列名"},
                            "operator": {
                                "type": "string",
                                "title": "运算符",
                                "enum": ["equals", "not_equals", "contains", "greater_than", "less_than"],
                            },
                            "value": {"type": "string", "title": "值"},
                        },
                    },
                },
            },
            "required": [],
        }

    def execute(self, config: dict, context: dict) -> dict:
        try:
            import pandas as pd
        except ImportError:
            raise WorkflowExecutionError("DEP_MISSING", "pandas is not installed", "data_process")

        # Collect upstream data
        upstream_data = self._collect_upstream(context)
        if not upstream_data:
            return {
                "status": "success",
                "data": {"rows": [], "columns": [], "row_count": 0},
            }

        # Auto-detect input format and convert to DataFrame
        df = self._to_dataframe(upstream_data)

        # Apply field mapping (rename)
        field_mapping = config.get("field_mapping", {})
        if field_mapping:
            df = df.rename(columns=field_mapping)

        # Keep specific columns
        columns_to_keep = config.get("columns_to_keep", [])
        if columns_to_keep:
            existing = [c for c in columns_to_keep if c in df.columns]
            df = df[existing]

        # Drop duplicates
        if config.get("drop_duplicates", True):
            df = df.drop_duplicates()

        # Fill missing values
        fill_value = config.get("fill_missing", "")
        if fill_value:
            df = df.fillna(fill_value)

        # Data type conversions
        conversions = config.get("data_type_conversions", {})
        for col, dtype in conversions.items():
            if col in df.columns:
                try:
                    if dtype == "int":
                        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
                    elif dtype == "float":
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    elif dtype == "str":
                        df[col] = df[col].astype(str)
                    elif dtype == "datetime":
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                except Exception:
                    pass

        # Apply filters
        filters = config.get("filters", [])
        for f in filters:
            col = f.get("column", "")
            op = f.get("operator", "equals")
            val = f.get("value", "")
            if col in df.columns:
                try:
                    if op == "equals":
                        df = df[df[col].astype(str) == val]
                    elif op == "not_equals":
                        df = df[df[col].astype(str) != val]
                    elif op == "contains":
                        df = df[df[col].astype(str).str.contains(val, na=False)]
                    elif op == "greater_than":
                        df = df[pd.to_numeric(df[col], errors="coerce") > float(val)]
                    elif op == "less_than":
                        df = df[pd.to_numeric(df[col], errors="coerce") < float(val)]
                except Exception:
                    pass

        # Sort
        sort_by = config.get("sort_by", "")
        if sort_by and sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=config.get("sort_ascending", True))

        # Convert to records
        rows = df.to_dict(orient="records")
        # Handle non-JSON-serializable types
        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()
                elif hasattr(v, "item"):
                    row[k] = v.item()

        return {
            "status": "success",
            "data": {
                "rows": rows,
                "columns": list(df.columns),
                "row_count": len(rows),
            },
        }

    def _collect_upstream(self, context: dict) -> list:
        """Collect data from all upstream nodes in context."""
        all_rows = []
        for node_id, result in context.items():
            data = result.get("data", result)
            if isinstance(data, dict):
                # Check for common patterns
                if "rows" in data:
                    all_rows.extend(data["rows"])
                elif "items" in data:
                    all_rows.extend(data["items"])
                elif "selector_results" in data:
                    # Flatten web crawler results into rows
                    sr = data["selector_results"]
                    # Get max length of any result array
                    max_len = max((len(v) for v in sr.values() if isinstance(v, list)), default=0)
                    for i in range(max_len):
                        row = {}
                        for k, v in sr.items():
                            if isinstance(v, list) and i < len(v):
                                row[k] = v[i]
                            elif not isinstance(v, list):
                                row[k] = v
                        if row:
                            all_rows.append(row)
                else:
                    # Try to use the dict as-is
                    all_rows.append(data)
            elif isinstance(data, list):
                all_rows.extend(data)
        return all_rows

    def _to_dataframe(self, data: list) -> "pd.DataFrame":
        import pandas as pd
        if not data:
            return pd.DataFrame()
        if isinstance(data[0], dict):
            return pd.DataFrame(data)
        elif isinstance(data[0], list):
            return pd.DataFrame(data)
        else:
            return pd.DataFrame({"value": data})
