# 🔄 拖拽式工作流自动化平台

> Drag-and-Drop Cross-Application Workflow Automation Platform

## 项目简介

一个桌面端工作流自动化平台，用户通过简单的**拖拽**来定义跨应用工作流。支持网页抓取、数据清洗、Excel生成、邮件发送等节点，通过可视化画布串联成完整的自动化流程。

**核心亮点**：AI 智能工作流生成器 — 用一句话描述需求，AI 自动设计节点、配置参数、创建完整工作流。

## 技术栈

| 层级 | 技术 |
|------|------|
| 桌面壳 | Electron |
| 前端 | React 18 + React Flow + Zustand + TailwindCSS + Vite |
| 后端 | FastAPI + SQLAlchemy + SQLite |
| AI | 硅基流动 DeepSeek-V3 |
| 爬虫 | Playwright (Chromium) |
| 数据处理 | pandas + openpyxl + plotly |
| 邮件 | SMTP (QQ/163/Gmail) |

## 快速启动

### 环境要求
- Node.js 18+
- Python 3.10+
- Playwright Chromium

### 一键启动

```bash
# 安装依赖
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
python -m playwright install chromium

# 启动服务
# Windows:
scripts\start.bat

# Linux/Mac:
bash scripts/start.sh
```

启动后访问：
- 前端界面：http://localhost:5173
- 后端 API：http://localhost:8000/api
- API 文档：http://localhost:8000/docs
- 演示数据页：http://localhost:5173/demo-news.html
- 世界杯数据页：http://localhost:5173/demo-worldcup.html

## 功能特性

### 可视化工作流编辑
- 6 种预置节点类型：定时触发、网页抓取、RSS监控、数据清洗、Excel生成、邮件发送
- 拖拽式画布操作，支持缩放、平移、自动布局
- 节点配置表单自动生成（基于 JSON Schema）
- 实时执行日志（WebSocket 推送）

### AI 智能配置
- **节点级 AI 配置**：选中节点，输入自然语言需求，AI 自动填充配置
- **工作流级 AI 生成**：一句话描述完整需求，AI 自动设计节点、连线、配置
- 支持硅基流动 API（DeepSeek-V3 等模型）

### 工作流引擎
- 有向图解析 + Kahn 算法拓扑排序
- 循环检测（自动拒绝含环工作流）
- `${node.field}` 表达式跨节点数据引用
- 错误处理与部分失败策略

### 执行器
- **网页抓取**：Playwright 无头浏览器，CSS 选择器提取
- **数据清洗**：pandas 驱动的字段映射、去重、排序、过滤
- **Excel生成**：openpyxl 写表格 + 柱状图/折线图/饼图
- **邮件发送**：SMTP 发送，支持附件、重试、测试模式

## 目录结构

```
├── backend/                # FastAPI 后端
│   ├── main.py             # 应用入口、路由、WebSocket
│   ├── models.py           # SQLite 数据模型
│   ├── schemas.py          # Pydantic 请求/响应模型
│   ├── workflow_engine.py  # 拓扑排序、表达式解析、执行引擎
│   ├── executor_registry.py# 执行器注册表
│   ├── ai_config.py        # AI 智能配置与工作流生成
│   ├── executors/          # 执行器实现
│   │   ├── web_crawler.py  # Playwright 网页抓取
│   │   ├── data_process.py # pandas 数据清洗
│   │   ├── excel_chart.py  # openpyxl Excel生成
│   │   ├── email_sender.py # SMTP 邮件发送
│   │   └── rss_monitor.py  # RSS 监控 + 定时触发
│   └── ui_automation/      # 预留：跨应用UI自动化适配器
├── frontend/               # React 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── WorkflowCanvas/    # React Flow 画布
│   │   │   ├── AIWorkflowGenerator/ # AI 工作流生成器
│   │   │   ├── NodePanel/         # 节点库
│   │   │   ├── ConfigDrawer/      # 配置抽屉（含AI面板）
│   │   │   └── LogConsole/        # 实时日志
│   │   ├── stores/                # Zustand 状态管理
│   │   └── api/                   # API 客户端
│   └── public/
│       ├── demo-news.html         # 舆情演示页
│       └── demo-worldcup.html     # 世界杯演示页
├── desktop/                # Electron 桌面壳
└── scripts/                # 启动脚本
```

## 演示场景

### 场景一：舆情监控日报
> 定时触发 → 网页抓取(5条舆情) → 数据清洗 → Excel生成(含图表) → 邮件发送

### 场景二：世界杯比分报告
> 定时触发 → 网页抓取(8场淘汰赛) → 数据清洗 → Excel生成 → 邮件发送(+附件)

## License

MIT
