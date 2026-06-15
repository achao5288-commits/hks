"""Generate roadshow PPT for Workflow Automation Platform."""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Colors
DARK_BG = RGBColor(0x0D, 0x11, 0x1A)
PURPLE = RGBColor(0x8B, 0x5C, 0xF6)
BLUE = RGBColor(0x3B, 0x82, 0xF6)
GREEN = RGBColor(0x22, 0xC5, 0x5E)
GOLD = RGBColor(0xF5, 0x9E, 0x0B)
RED = RGBColor(0xEF, 0x44, 0x44)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY = RGBColor(0x9C, 0xA3, 0xAF)
DARK_GRAY = RGBColor(0x6B, 0x72, 0x80)
LIGHT_GRAY = RGBColor(0xD1, 0xD5, 0xDB)

def add_bg(slide, color=DARK_BG):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_title(slide, text, y=Inches(0.3), size=Pt(40), color=WHITE):
    txBox = slide.shapes.add_textbox(Inches(0.8), y, Inches(11.7), Inches(1))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = size
    p.font.color.rgb = color
    p.font.bold = True
    return tf

def add_subtitle(slide, text, y=Inches(1.3), size=Pt(20), color=GRAY):
    txBox = slide.shapes.add_textbox(Inches(0.8), y, Inches(11.7), Inches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = size
    p.font.color.rgb = color
    return tf

def add_body(slide, text, y=Inches(2.0), size=Pt(18), color=LIGHT_GRAY):
    txBox = slide.shapes.add_textbox(Inches(0.8), y, Inches(11.7), Inches(4.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, line in enumerate(text.split('\n')):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = size
        p.font.color.rgb = color
        p.space_after = Pt(6)
    return tf

def add_accent_bar(slide, y=Inches(0.15), color=PURPLE):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.3), y, Inches(0.06), Inches(0.5))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()

def add_footer(slide, text='拖拽式工作流自动化平台 | 路演演示'):
    txBox = slide.shapes.add_textbox(Inches(0.8), Inches(6.95), Inches(11.7), Inches(0.35))
    p = txBox.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(10)
    p.font.color.rgb = DARK_GRAY

def add_card(slide, x, y, w, h, title, body, icon_color=PURPLE):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    shape.line.color.rgb = RGBColor(0x33, 0x33, 0x55)
    shape.line.width = Pt(1)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.12)
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(15)
    p.font.color.rgb = icon_color
    p.font.bold = True
    p2 = tf.add_paragraph()
    p2.text = body
    p2.font.size = Pt(11)
    p2.font.color.rgb = GRAY
    p2.space_before = Pt(6)
    return shape

def add_hero_bg(slide):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(2.2), prs.slide_width, Inches(3.2))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0x1A, 0x0E, 0x2E)
    shape.line.fill.background()

# ============================================
# Slide 1: Title
# ============================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_hero_bg(slide)
add_accent_bar(slide, Inches(2.6), PURPLE)
add_title(slide, '拖拽式工作流自动化平台', Inches(2.8), Pt(48))
add_subtitle(slide, 'Cross-Application Drag-and-Drop Workflow Automation', Inches(3.7), Pt(22))
add_subtitle(slide, '像搭积木一样构建跨应用自动化流程  |  AI 一句话生成工作流', Inches(4.3), Pt(18))
add_footer(slide)

# ============================================
# Slide 2: Problem & Solution
# ============================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_title(slide, '痛点与解决方案', size=Pt(36))

body_text = (
    '痛点 1：跨应用数据搬运，重复机械劳动多\n'
    '   从浏览器复制 > 粘贴到 Excel > 生成图表 > 写邮件发附件，每天耗时 15+ 分钟\n'
    '\n'
    '痛点 2：自动化工具门槛高\n'
    '   RPA 工具需编程基础，Zapier/n8n 依赖 API，传统网页无 API 可用\n'
    '\n'
    '痛点 3：非技术人员被排除在自动化之外\n'
    '   不懂 CSS 选择器、不会配置 SMTP、不会写 Cron 表达式\n'
    '\n'
    '我们的方案：拖拽式可视化工作流 + AI 智能配置生成\n'
    '   一句话描述需求 > AI 自动创建完整工作流 > 一键执行 > 4 秒完成'
)
add_body(slide, body_text, Inches(2.2), Pt(17))

cards_data = [
    (Inches(0.8), '手动操作 15 分钟', RED),
    (Inches(4.8), '拖拽建模 30 秒', GOLD),
    (Inches(8.8), '自动执行 4 秒', GREEN),
]
for x, label, color in cards_data:
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(5.8), Inches(3.6), Inches(0.8))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    shape.line.color.rgb = color
    shape.line.width = Pt(2)
    tf = shape.text_frame
    tf.paragraphs[0].text = label
    tf.paragraphs[0].font.size = Pt(18)
    tf.paragraphs[0].font.color.rgb = color
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER

add_footer(slide)

# ============================================
# Slide 3: Architecture
# ============================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_title(slide, '技术架构', size=Pt(36))
add_subtitle(slide, '四层架构 · 前后端分离 · 执行器插件化', Inches(1.1), Pt(16))

add_card(slide, Inches(0.8), Inches(2.0), Inches(3.6), Inches(1.0),
    'Electron 桌面壳',
    '窗口创建 · 子进程管理 · IPC 安全桥接 · 进程生命周期自动管理', BLUE)
add_card(slide, Inches(4.8), Inches(2.0), Inches(3.6), Inches(1.0),
    'React 前端可视化层',
    'React Flow 画布 · 节点库 · 配置抽屉 · AI面板 · 实时日志 · 数据预览', PURPLE)
add_card(slide, Inches(8.8), Inches(2.0), Inches(3.6), Inches(1.0),
    'FastAPI 业务逻辑层',
    'DAG拓扑排序 · 并行调度 · 超时控制 · 表达式解析 · 循环检测', GREEN)

add_card(slide, Inches(0.8), Inches(3.4), Inches(5.7), Inches(1.0),
    'AI 引擎 (硅基流动 DeepSeek-V3)',
    '单节点智能配置填充 + 全自动工作流生成 · 自然语言 > 节点设计 > 连线规划 > 参数填充 > 一键创建', GOLD)
add_card(slide, Inches(6.9), Inches(3.4), Inches(5.7), Inches(1.0),
    '执行器层 (插件化架构)',
    'Playwright 抓取 | pandas 清洗 | openpyxl Excel | SMTP 邮件 | feedparser RSS | Cron 定时', GRAY)

add_body(slide,
    '技术栈：Electron + React 18 + Vite + React Flow + Zustand + TailwindCSS  |  FastAPI + SQLAlchemy + SQLite  |  硅基流动 DeepSeek-V3',
    Inches(4.8), Pt(13), DARK_GRAY)
add_footer(slide)

# ============================================
# Slide 4: Core Features
# ============================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_title(slide, '核心功能', size=Pt(36))

add_card(slide, Inches(0.8), Inches(1.8), Inches(2.9), Inches(1.4),
    '可视化画布',
    '6 种预置节点拖拽即用\n连线建立数据流\n缩放 20%-200% + 平移\n自动布局 + 框选批量操作\n实时节点状态动画', BLUE)
add_card(slide, Inches(3.9), Inches(1.8), Inches(2.9), Inches(1.4),
    '并行执行引擎',
    'Kahn 算法拓扑排序\n无依赖节点同一阶段并行\nThreadPoolExecutor 线程池\n性能提升 50%+\n每节点独立超时控制', GREEN)
add_card(slide, Inches(7.0), Inches(1.8), Inches(2.9), Inches(1.4),
    'AI 一句话生成',
    '自然语言描述完整需求\nAI 自动设计节点+连线+配置\n单节点 AI 智能填充\n年份感知路由\nDeepSeek-V3 驱动', PURPLE)
add_card(slide, Inches(10.1), Inches(1.8), Inches(2.5), Inches(1.4),
    '数据可视化',
    '点击连线预览数据流\n紫色高亮选中连接\nWebSocket 实时日志\n节点耗时显示\n下载日志文件', GOLD)

add_card(slide, Inches(0.8), Inches(3.5), Inches(2.9), Inches(1.4),
    '邮件通知',
    'QQ/163/Gmail SMTP\nHTML 正文 + 附件\n失败自动重试 3 次\n测试模式(dry_run)\n附件表达式引用', RED)
add_card(slide, Inches(3.9), Inches(3.5), Inches(2.9), Inches(1.4),
    '数据管理',
    'SQLite 持久化存储\n工作流 CRUD\n下拉选择 + 一键删除\n节点配置预设模板\n表达式数据引用', GRAY)
add_card(slide, Inches(7.0), Inches(3.5), Inches(5.7), Inches(1.4),
    '容错与可靠性',
    '超时控制：每节点可配超时，超时自动终止不卡死\n重试机制：邮件发送失败自动重试3次（5秒间隔）\n错误隔离：单节点失败不影响已完成的节点结果\nWebSocket 毫秒级日志推送', LIGHT_GRAY)

add_footer(slide)

# ============================================
# Slide 5: AI Demo Flow
# ============================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_title(slide, 'AI 工作流生成器 —— 核心亮点', size=Pt(36))
add_subtitle(slide, '从"一句话"到"完整可执行工作流"的全程自动化', Inches(1.1), Pt(18))

body_text = (
    '用户输入（自然语言）：\n'
    '  "抓取舆情新闻，筛选出AI芯片相关的内容，生成专题Excel报告，从xxx@qq.com发送到xxx@163.com"\n'
    '\n'
    '  AI 自动分析 (DeepSeek-V3, 约 60 秒)\n'
    '\n'
    'AI 输出（完整工作流）：\n'
    '  5 个节点：定时触发 > 网页抓取 > 数据清洗(含AI芯片过滤) > Excel生成 > 邮件发送\n'
    '  4 条连线：trigger > crawler > process > excel > email\n'
    '  42 项配置：URL、6个CSS选择器、字段映射、图表设置、SMTP参数、HTML邮件正文\n'
    '  自动保存 > 一键加载到画布 > 点击执行 > 4 秒完成'
)
add_body(slide, body_text, Inches(2.0), Pt(16))

# AI capability cards
add_card(slide, Inches(0.8), Inches(5.5), Inches(5.7), Inches(1.0),
    'AI 自动推断能力',
    '自动推断节点类型和数量 | 自动匹配 CSS 选择器 | 自动填充 SMTP 配置 | 自动处理年份路由(2022/2026世界杯)', PURPLE)
add_card(slide, Inches(6.9), Inches(5.5), Inches(5.7), Inches(1.0),
    '6 个稳定演示示例（AI 一句生成）',
    '舆情日报 · 舆情+图表 · AI芯片专题 · 新能源汽车专题 · 舆情+Excel桌面 · 舆情+去重排序', GREEN)
add_footer(slide)

# ============================================
# Slide 6: Demo Scenarios
# ============================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_title(slide, '演示场景', size=Pt(36))

add_card(slide, Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.3),
    '场景一：舆情监控日报（完整版）',
    '定时触发(每天9:00) > 网页抓取(5条舆情新闻) > 数据清洗(去重/排序/字段映射) > Excel生成(含柱状图) > 邮件发送(HTML表格+附件)\n'
    '输入：抓取舆情新闻数据，清洗去重后生成Excel日报，发到邮箱  |  执行时间：4 秒  |  结果：收件箱收到含附件的专业日报',
    BLUE)

add_card(slide, Inches(0.8), Inches(3.4), Inches(11.7), Inches(1.3),
    '场景二：世界杯比分数据报告',
    '定时触发 > 网页抓取(8场淘汰赛比分+比赛日志) > 数据清洗 > Excel生成(图表) > 邮件发送(HTML表格+附件Excel)\n'
    '输入：抓取世界杯淘汰赛比分和比赛日志，清洗后生成Excel发邮件  |  执行时间：5 秒  |  数据源：2022卡塔尔世界杯淘汰赛真实数据',
    GOLD)

add_card(slide, Inches(0.8), Inches(5.0), Inches(11.7), Inches(1.3),
    '场景三：AI芯片专题报告（AI智能筛选）',
    '定时触发 > 网页抓取(5条新闻) > 数据清洗(筛选"AI芯片"关键词) > 专题Excel > 邮件发送\n'
    '输入：抓取舆情新闻，筛选出AI芯片相关的内容，生成专题Excel报告并发送邮件\n'
    'AI 自动生成过滤条件：{"column":"标题","operator":"contains","value":"AI芯片"}  |  执行时间：4 秒',
    PURPLE)

add_footer(slide)

# ============================================
# Slide 7: Performance
# ============================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_title(slide, '性能指标', size=Pt(36))

add_card(slide, Inches(0.8), Inches(1.8), Inches(2.7), Inches(1.2),
    '解析性能',
    '100 节点 < 100ms\nDAG解析 + 拓扑排序\nKahn算法 O(V+E)', GREEN)
add_card(slide, Inches(3.9), Inches(1.8), Inches(2.7), Inches(1.2),
    '并行加速',
    '两爬虫 1.8s vs 3.6s\n节省 50% 时间\nThreadPoolExecutor', BLUE)
add_card(slide, Inches(7.0), Inches(1.8), Inches(2.7), Inches(1.2),
    'Excel生成',
    '< 1s (实测 0.6s)\n含图表 + 样式\n默认保存桌面', GOLD)
add_card(slide, Inches(10.1), Inches(1.8), Inches(2.4), Inches(1.2),
    '内存占用',
    '< 200MB (空闲)\nElectron + Python\n桌面级轻量', PURPLE)

# Comparison table
body_text = (
    '方案对比：\n'
    '                   传统 RPA      Zapier/n8n      自建脚本       本平台\n'
    '  可视化拖拽           Y             Y               N             Y\n'
    '  无API网页抓取        Y             N               Y             Y\n'
    '  AI 一句话生成        N             N               N             Y\n'
    '  并行执行引擎         N             N             需开发          Y\n'
    '  桌面端运行           Y             N               Y             Y\n'
    '  学习成本            高            中              高            低\n'
    '  价格             数千/月       数百/月           免费          免费'
)
add_body(slide, body_text, Inches(3.4), Pt(14))
add_footer(slide)

# ============================================
# Slide 8: Future Roadmap
# ============================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_accent_bar(slide)
add_title(slide, '未来规划', size=Pt(36))

add_card(slide, Inches(0.8), Inches(1.8), Inches(3.6), Inches(2.0),
    '短期 (1-3月)',
    '飞书/钉钉/企微通知节点\nMySQL/PostgreSQL 读写\n通用 HTTP API 调用节点\n真实浏览器操作(点击/填表)\n执行历史回溯\n撤销/重做 Ctrl+Z/Y',
    BLUE)

add_card(slide, Inches(4.8), Inches(1.8), Inches(3.6), Inches(2.0),
    '中期 (3-6月)',
    '条件分支 if/else 节点\n循环 for-each 节点\n子工作流调用\nOpenCV图像识别+OCR\n凭据加密管理\n定时调度增强(间隔/节假日)',
    PURPLE)

add_card(slide, Inches(8.8), Inches(1.8), Inches(3.6), Inches(2.0),
    '长期 (6-12月)',
    '多租户 + 团队协作\nGit 式版本管理(diff/回滚)\n工作流模板市场\n分布式执行(Celery/Redis)\n移动端监控小程序\n多轮对话修改工作流',
    GREEN)

add_body(slide,
    'GitHub: https://github.com/achao5288-commits/hks  |  MIT License  |  技术栈: Electron + React + FastAPI + 硅基流动 DeepSeek-V3',
    Inches(5.5), Pt(14), DARK_GRAY)
add_footer(slide, '拖拽式工作流自动化平台 | 未来可期')

# ============================================
# Slide 9: Thank You
# ============================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_hero_bg(slide)
add_accent_bar(slide, Inches(2.4), PURPLE)
add_title(slide, '感谢聆听', Inches(2.6), Pt(52))
add_subtitle(slide, '拖拽式工作流自动化平台', Inches(3.5), Pt(24))
add_subtitle(slide, '让自动化触手可及 · 像搭积木一样构建工作流', Inches(4.1), Pt(18))
add_subtitle(slide, 'GitHub: https://github.com/achao5288-commits/hks', Inches(4.9), Pt(16))

# Save
output = os.path.expanduser('~') + '/Desktop/工作流自动化平台_路演PPT.pptx'
prs.save(output)
print(f'PPT saved to: {output}')
print(f'Total slides: {len(prs.slides)}')
