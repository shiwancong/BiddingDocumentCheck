# 项目结构说明

## 📁 目录结构

```
BiddingDocumentCheck/
├── 📄 核心Python脚本
│   ├── analyze_bidding_doc.py           # 招标文件分析主程序
│   ├── convert_to_md.py                 # 统一文件转换工具（入口）
│   ├── convert_pdf_to_md_advanced.py    # PDF转Markdown（高级版）
│   ├── convert_docx_to_md.py            # Word转Markdown
│   ├── convert_excel_to_md.py           # Excel转Markdown
│   └── generate_comprehensive_checklist.py  # 清单生成器
│
├── 📁 .claude/                          # Claude Code配置和技能
│   ├── settings.local.json              # 本地配置
│   └── skills/                          # 技能目录
│       ├── check-bidding-doc/           # 废标条款检查技能（主要）
│       ├── check-suggestions/           # 建议项生成技能
│       ├── compare-versions/            # 版本对比技能
│       ├── extract-clauses/             # 条款提取技能
│       ├── learn-from-mistakes/         # 错误学习技能
│       ├── process-chunk/               # 分块处理技能
│       └── validate-clauses/            # 条款验证技能
│
├── 📁 data/                             # 数据目录
│   ├── knowledge/                       # 知识库
│   │   ├── config/                      # 配置文件
│   │   ├── rules.md                     # 基础规则
│   │   ├── rules-core.md                # 核心规则
│   │   ├── regulations-database.md      # 法规数据库
│   │   ├── examples.md                  # 示例库
│   │   ├── accuracy-improvement.md      # 准确性改进
│   │   └── complete-cases.md            # 完整案例
│   │
│   ├── output/                          # 输出结果目录
│   │   └── *_检查清单.md                # 生成的检查清单
│   │
│   └── test/                            # 测试文件目录
│       ├── *.pdf                        # 原始PDF文件
│       ├── *_converted.md               # 转换后的Markdown
│       └── *_converted.json             # 提取的JSON数据
│
├── 📄 文档和配置
│   ├── README.md                        # 项目主说明
│   ├── QUICKSTART.md                    # 快速开始指南
│   ├── ARCHITECTURE.md                  # 架构说明
│   ├── CONVERTER_README.md              # 转换器说明
│   ├── PROJECT_STRUCTURE.md             # 本文件
│   └── config.yaml                      # 配置文件
│
└── 📁 其他
    ├── .git/                            # Git版本控制
    ├── .idea/                           # IDE配置
    └── __pycache__/                     # Python缓存（临时）
```

## 🔧 核心功能文件说明

### 1. 文件转换工具

| 文件名 | 功能 | 输入 | 输出 | 用途 |
|--------|------|------|------|------|
| convert_to_md.py | 统一转换入口 | PDF/Word/Excel | Markdown | 自动识别格式并转换 |
| convert_pdf_to_md_advanced.py | PDF转换 | PDF | Markdown | 保留页码、表格、图片 |
| convert_docx_to_md.py | Word转换 | DOCX/DOC | Markdown | 保留标题层级、表格 |
| convert_excel_to_md.py | Excel转换 | XLSX/XLS | Markdown | 支持多工作表 |

### 2. 分析处理工具

| 文件名 | 功能 | 输入 | 输出 | 用途 |
|--------|------|------|------|------|
| analyze_bidding_doc.py | 招标文件分析 | JSON数据 | 检查清单 | 识别废标条款 |
| generate_comprehensive_checklist.py | 清单生成 | 分析结果 | Markdown | 生成结构化清单 |

## 📚 知识库文件说明

### data/knowledge/ 目录

| 文件名 | 内容 | 用途 |
|--------|------|------|
| regulations-database.md | 法规数据库 | 存储招投标相关法律法规 |
| rules-core.md | 核心规则 | 废标条款识别的核心规则 |
| rules.md | 基础规则 | 基础检查规则 |
| examples.md | 示例库 | 典型案例和示例 |
| accuracy-improvement.md | 准确性改进 | 识别准确性提升方法 |
| complete-cases.md | 完整案例 | 完整的检查案例 |

## 🎯 使用流程

### 完整工作流程

```
1. 文件准备
   ├─ 将招标文件（PDF/Word/Excel）放入 data/test/ 目录
   └─ 或直接提供招标文件路径

2. 文件转换（如需要）
   ├─ PDF: convert_pdf_to_md_advanced.py
   ├─ Word: convert_docx_to_md.py
   └─ Excel: convert_excel_to_md.py

3. 招标文件分析
   └─ analyze_bidding_doc.py

4. 生成检查清单
   └─ 自动生成到 data/output/ 目录

5. 结果审核
   └─ 人工复核检查清单
```

### 快速使用

```bash
# 方式1：使用Claude Code技能
/check-bidding-doc 招标文件.pdf

# 方式2：使用Python脚本
python convert_to_md.py 招标文件.pdf
python analyze_bidding_doc.py
```

## 🗑️ 已清理文件

以下文件已被删除（重复或过时）：

- `convert_pdf_to_md.py` - 已被advanced版本替代
- `extract_docx.py` - 功能已整合
- `extract_docx_content.py` - 功能重复
- `extract_specific_docx.py` - 功能重复
- `generate_excel.py` - 功能单一

## 📝 核心脚本注释说明

所有核心Python文件已添加详细注释：

1. **文件头部注释**：说明功能、使用方法、依赖库
2. **类注释**：说明类的用途和核心功能
3. **函数注释**：说明参数、返回值、使用示例
4. **关键代码注释**：解释复杂逻辑和关键步骤

## ⚙️ 配置文件说明

### config.yaml
项目全局配置，包括：
- 文件路径配置
- 分析参数设置
- 输出格式选项

### .claude/settings.local.json
Claude Code本地配置，包括：
- 技能路径配置
- 模型参数设置
- 输出选项

## 📦 依赖库安装

```bash
# PDF处理
pip install PyMuPDF

# Word处理
pip install python-docx

# Excel处理
pip install pandas openpyxl

# 全部安装
pip install PyMuPDF python-docx pandas openpyxl
```

## 🔍 文件命名规范

### 输入文件
- 原始文件：保持原始名称
- 转换后：添加 `_converted` 后缀

### 输出文件
- 检查清单：`{项目名}_检查清单.md`
- 核对报告：`{项目名}_覆盖核对报告.md`
- 分析结果：`{项目名}_分析结果.json`

## 📈 项目统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 核心Python脚本 | 6 | 转换和分析工具 |
| Claude技能 | 7 | 各类检查和分析技能 |
| 知识库文件 | 7 | 法规、规则、案例 |
| 文档文件 | 6 | 说明文档 |
| 总代码行数 | ~5000 | 包含注释和文档 |

## 🎓 学习路径

1. **初级用户**：
   - 阅读 QUICKSTART.md
   - 使用 `/check-bidding-doc` 技能
   - 查看生成的检查清单

2. **中级用户**：
   - 阅读 ARCHITECTURE.md
   - 了解各种转换工具
   - 自定义配置参数

3. **高级用户**：
   - 修改技能文件
   - 扩展知识库
   - 优化识别规则

---

**更新日期**：2026-03-22
**维护者**：招投标智能检查系统
