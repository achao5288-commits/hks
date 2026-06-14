# 🔄 拖拽式工作流自动化平台

> Cross-Application Drag-and-Drop Workflow Automation Platform

## 项目简介

一个桌面端跨应用工作流自动化平台，用户通过简单的**拖拽**来定义跨应用自动化工作流。支持网页抓取、数据清洗、Excel图表生成、邮件发送等节点类型，通过可视化画布串联成完整的自动化流程。

**核心亮点**：✨ AI 智能工作流生成器 — 用一句话描述需求，AI 自动设计节点、配置参数、创建完整工作流，全程无需手动配置。

## 技术架构

| 层级 | 技术栈 |
|------|--------|
| 桌面壳 | Electron — 窗口创建、IPC通信、前后端子进程管理 |
| 前端 | React 18 + React Flow + Zustand + TailwindCSS + Vite |
| 后端 | FastAPI + SQLAlchemy Core + SQLite |
| AI 引擎 | 硅基流动 DeepSeek-V3 — 自然语言→工作流全自动生成 |
| 爬虫 | Playwright (Chromium) — 无头浏览器，CSS选择器提取 |
| 数据处理 | pandas + openpyxl — 数据清洗、Excel生成、图表 |
| 邮件 | SMTP (QQ/163/Gmail) — 带重试机制 |

## 快速启动

### 环境要求

- **Node.js** 18+
- **Python** 3.10+
- **Playwright Chromium** (首次安装)

### 一键启动

```bash
# 1. 安装依赖
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
python -m playwright install chromium

# 2. 初始化数据库和演示数据
cd backend && python ../scripts/demo_data.py && cd ..

# 3. 启动服务

# Windows:
cd frontend && npx vite --port 5173 &
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 &

# Linux/Mac:
bash scripts/start.sh
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:5173 |
| 后端 API | http://localhost:8000/api |
| API 文档 (Swagger) | http://localhost:8000/docs |
| 舆情演示数据 | http://localhost:5173/demo-news.html |
| 世界杯演示数据 | http://localhost:5173/demo-worldcup.html |

> 在 `http://localhost:5173/demo-worldcup.html` 加入 `.team.home`, `.team.away`, `.score`, `.match-date`, `.match-venue`, `[data-round]`, `.match-log` 等8场比赛的2022卡塔尔世界杯淘汰赛数据。

## 功能特性

### 🎨 可视化工作流编辑

- **6 种预置节点**：定时触发、网页抓取、RSS监控、数据清洗、Excel生成、邮件发送
- **拖拽式画布**：从节点库拖拽到画布，支持缩放(20%~200%)、平移、框选批量操作
- **动态配置表单**：基于 JSON Schema 自动生成，每个节点有完整的中文配置界面
- **自动布局**：按拓扑顺序自动排列节点
- **工作流管理**：保存/加载/删除工作流，下拉选择器快速切换

### 🤖 AI 智能工作流生成

- **一句话生成工作流**：输入自然语言需求 → AI 自动设计节点、连线、配置 → 一键加载到画布
- **节点级 AI 辅助**：选中节点，输入需求描述 → AI 自动填充配置
- **全自动流程**：从"抓取数据"到"发送邮件"，AI 自动推断所需的所有参数

示例输入：
```
抓取世界杯淘汰赛比分，清洗后生成Excel报表，
从2459669124@qq.com发到17702229093@163.com
```

### ⚡ 并行执行引擎

- **拓扑层级分析**：自动识别无依赖关系的节点，归入同一执行阶段
- **ThreadPoolExecutor 并行执行**：同一阶段的节点同时运行
- **性能提升**：多爬虫并行抓取，耗时减少 50%+
- **执行日志**：`Stage X/Y: parallel execution of N node(s)` 清晰展示并行结构

### ⏱️ 执行超时控制

- 每个节点可配置 `_timeout` 参数（单位：秒）
- 超时自动终止，不影响其他阶段
- 默认 60 秒，可自定义

### 📊 实时状态可视化

- **节点动画**：待执行⬜ → 执行中⏳(蓝色旋转) → 成功✅(绿色发光) → 失败❌(红色发光)
- **耗时显示**：每个节点显示实际执行时间
- **WebSocket 实时推送**：日志毫秒级到达前端

### 🔗 数据流预览

- **点击连线**：查看上下游节点信息
- **紫色高亮**：选中连接线高亮显示
- **配置预览**：显示上游节点的完整配置
- **表达式引用**：支持 `${node_id.data.field.path}` 跨节点数据引用

### 📁 Excel 文件管理

- **默认保存到桌面**：生成的 Excel 文件直接出现在桌面
- **支持图表**：柱状图、折线图、饼图
- **自适应列宽**、自定义列宽
- **附件发送**：邮件自动附带生成的 Excel 文件

## API 接口

### 工作流 CRUD

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/workflows` | 保存工作流 |
| GET | `/api/workflows` | 列出所有工作流 |
| GET | `/api/workflows/{id}` | 获取工作流详情 |
| DELETE | `/api/workflows/{id}` | 删除工作流 |

### 执行与监控

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/workflows/{id}/execute` | 执行工作流，返回 task_id |
| GET | `/api/tasks/{task_id}/status` | 轮询执行状态 |
| WS | `/ws/tasks/{task_id}/logs` | WebSocket 实时日志 |

### AI 接口

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/ai/generate-config` | AI 生成单节点配置 |
| POST | `/api/ai/auto-workflow` | AI 生成完整工作流 |

### 执行器信息

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/executors` | 获取所有注册的执行器类型及配置Schema |
| GET | `/api/presets` | 获取节点配置预设模板 |

### 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

错误码：`1` 参数错误 | `2` 执行超时 | `3` 节点配置无效 | `4` 依赖缺失

## 执行器详解

### 网页抓取 (web_crawler)

- **技术**：Playwright 同步API + Chromium 无头浏览器
- **能力**：CSS选择器提取、属性提取(href/src)、滚动到底部、点击"加载更多"
- **超时**：页面加载30秒，单选择器10秒
- **配置**：URL、选择器列表(名称+选择器+属性)、等待时间、User-Agent、截图

### 数据清洗 (data_process)

- **技术**：pandas DataFrame
- **能力**：字段重命名、列过滤、去重、缺失值填充、数据类型转换、排序、条件过滤
- **自动检测**：自动识别上游数据格式(JSON数组/对象列表/键值对)

### Excel生成 (excel_chart)

- **技术**：openpyxl
- **能力**：数据写入、柱状图/折线图/饼图、自适应列宽、自定义样式
- **保存**：默认保存到桌面，文件名 `workflow_report_时间戳.xlsx`

### 邮件发送 (email_sender)

- **技术**：SMTP (smtplib)
- **支持**：QQ邮箱(smtp.qq.com:465/SSL)、163邮箱(smtp.163.com:465/SSL)、Gmail
- **功能**：HTML正文、附件、抄送/密送、重试3次(间隔5秒)
- **测试模式**：dry_run=true 时不实际发送

### RSS监控 (rss_monitor)

- **技术**：feedparser
- **能力**：RSS/Atom源解析、关键词过滤、条目数限制

### 定时触发 (schedule_trigger)

- **Cron表达式**：标准5位cron
- **时区**：可配置(默认Asia/Shanghai)

## 数据库设计 (SQLite)

| 表 | 字段 | 说明 |
|----|------|------|
| workflows | id, name, description, nodes_json, edges_json, created_at, updated_at | 工作流定义 |
| executions | id, workflow_id, status, started_at, finished_at, task_id | 执行历史 |
| execution_logs | id, execution_id, node_id, level, message, timestamp | 节点执行日志 |
| node_presets | id, node_type, config_json, name | 节点配置预设 |

## 项目目录结构

```
hks/
├── README.md
├── package.json                    # 根工作空间
├── .gitignore
│
├── backend/                        # FastAPI 后端
│   ├── main.py                     # 应用入口、路由注册、WebSocket
│   ├── models.py                   # SQLAlchemy Core 数据模型
│   ├── schemas.py                  # Pydantic 请求/响应模型
│   ├── workflow_engine.py          # DAG解析、拓扑排序、并行执行引擎
│   ├── executor_registry.py        # 执行器注册表 (6种类型)
│   ├── ai_config.py                # AI智能配置 & 全自动工作流生成
│   ├── requirements.txt
│   ├── executors/
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseExecutor 抽象类
│   │   ├── web_crawler.py          # Playwright 网页抓取
│   │   ├── data_process.py         # pandas 数据清洗
│   │   ├── excel_chart.py          # openpyxl Excel + 图表生成
│   │   ├── email_sender.py         # SMTP 邮件发送
│   │   └── rss_monitor.py          # RSS监控 + 定时触发
│   └── ui_automation/              # 预留：跨应用UI自动化适配器
│       └── __init__.py
│
├── frontend/                       # React 前端
│   ├── package.json
│   ├── vite.config.js              # Vite 配置 (含API代理)
│   ├── tailwind.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.jsx                # React 入口
│   │   ├── App.jsx                 # 主布局组件
│   │   ├── index.css               # Tailwind + 自定义样式
│   │   ├── api/
│   │   │   └── client.js           # Axios + WebSocket API客户端
│   │   ├── stores/
│   │   │   └── workflowStore.js    # Zustand 全局状态管理
│   │   └── components/
│   │       ├── WorkflowCanvas/     # React Flow 画布
│   │       │   ├── index.jsx       # 画布主组件(工具栏/拖放/键盘快捷键)
│   │       │   └── WorkflowNode.jsx # 自定义节点(图标/状态/动画)
│   │       ├── NodePanel/          # 左侧节点库
│   │       │   └── index.jsx       # 可拖拽节点卡片 + 搜索
│   │       ├── ConfigDrawer/       # 右侧配置抽屉
│   │       │   └── index.jsx       # 动态表单 + AI智能填写面板
│   │       ├── AIWorkflowGenerator/ # AI工作流生成器
│   │       │   └── index.jsx       # 模态框：输入需求→全自动生成
│   │       └── LogConsole/         # 底部日志面板
│   │           └── index.jsx       # WebSocket实时日志 + 下载
│   └── public/
│       ├── demo-news.html          # 舆情监控演示数据 (5条)
│       └── demo-worldcup.html      # 世界杯演示数据 (8场)
│
├── desktop/                        # Electron 桌面壳
│   ├── main.js                     # 窗口创建、子进程管理
│   ├── preload.js                  # 安全API桥接
│   └── package.json
│
└── scripts/                        # 工具脚本
    ├── start.sh                    # Linux/Mac 一键启动
    ├── start.bat                   # Windows 一键启动
    └── demo_data.py                # 演示数据初始化
```

## 演示场景

### 场景一：舆情监控日报

```
定时触发(每天9:00) → 网页抓取(5条舆情新闻) → 数据清洗(去重/排序/字段映射)
→ Excel生成(含柱状图) → 邮件发送
```

**操作**：加载"舆情监控日报（演示）" → 配置邮箱 → 执行

### 场景二：世界杯比分报告

```
定时触发 → 网页抓取(8场淘汰赛比分+日志) → 数据清洗
→ Excel生成(含图表+附件) → 邮件发送(HTML表格+附件)
```

**操作**：点击 **✨ AI 生成** → 输入：
```
抓取世界杯淘汰赛比分，清洗后生成Excel报表，
从xxx@qq.com发到xxx@163.com
```
→ 自动生成并执行

### 场景三：自定义工作流

1. 从左侧节点库**拖拽**节点到画布
2. **连线**连接上下游
3. 点击节点→右侧配置抽屉填写参数(或点击 ✨ AI自动填写)
4. **保存** → **执行** → 查看实时日志

## 扩展性

### 添加新执行器

1. 在 `backend/executors/` 创建新文件
2. 继承 `BaseExecutor`，实现 `execute()` 和 `get_config_schema()`
3. 在 `__init__.py` 导入
4. 在 `executor_registry.py` 注册
5. 前端节点库自动显示新类型

### 预留接口

- `backend/ui_automation/` — 跨应用UI自动化适配器（OpenCV图像识别 + OCR）
- 节点配置支持 `target_app` 字段

## 性能指标

| 指标 | 数值 |
|------|------|
| 画布操作帧率 | ≥30fps |
| 工作流解析 | 100节点 <100ms |
| 单节点超时 | 默认60秒，可配置 |
| 并发执行 | 同一阶段无依赖节点并行(max 6) |
| 并行执行效率 | 多爬虫场景节省50%+时间 |

## License

MIT
