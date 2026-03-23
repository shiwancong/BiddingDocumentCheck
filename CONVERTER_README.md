# 文件转换工具使用说明

本工具包支持将多种格式的招标文件转换为Markdown格式，便于后续的智能检查和分析。

## 支持的文件格式

| 格式 | 扩展名 | 转换脚本 |
|------|--------|----------|
| PDF | .pdf | convert_pdf_to_md_advanced.py |
| Word | .docx, .doc | convert_docx_to_md.py |
| Excel | .xlsx, .xls | convert_excel_to_md.py |

## 快速开始

### 1. 安装依赖

```bash
# 安装所有依赖
pip install PyMuPDF python-docx pandas openpyxl
```

### 2. 使用统一转换工具（推荐）

```bash
# 自动识别文件格式并转换
python convert_to_md.py 招标文件.pdf
python convert_to_md.py 招标文件.docx
python convert_to_md.py 招标文件.xlsx

# 指定输出路径
python convert_to_md.py 招标文件.pdf 输出文件.md
```

### 3. 使用单独的转换脚本

#### PDF转Markdown

```python
from convert_pdf_to_md_advanced import pdf_to_markdown

result = pdf_to_markdown(
    pdf_path="招标文件.pdf",
    output_path="招标文件_converted.md",
    include_images=True,
    image_format='base64'
)
```

#### Word转Markdown

```python
from convert_docx_to_md import docx_to_markdown

result = docx_to_markdown(
    docx_path="招标文件.docx",
    output_path="招标文件_converted.md",
    include_images=True,
    image_format='base64'
)
```

#### Excel转Markdown

```python
from convert_excel_to_md import excel_to_markdown

result = excel_to_markdown(
    excel_path="招标文件.xlsx",
    output_path="招标文件_converted.md",
    skip_empty_sheets=True,
    max_rows=None
)
```

## 转换功能特性

### PDF转换功能

- ✅ 保留原PDF的页面布局
- ✅ 包含完整页码信息（`<!-- PAGE_BREAK -->`、`## 【第 X 页】`）
- ✅ 正确处理表格
- ✅ 支持图片处理（base64嵌入或保存为单独文件）
- ✅ 保持字体样式（粗体、斜体等）
- ✅ 智能识别标题（根据字体大小）

### Word转换功能

- ✅ 保留原Word的文档结构
- ✅ 识别标题层级（Heading 1-6）
- ✅ 正确处理表格
- ✅ 保留文本格式（粗体、斜体、下划线等）
- ✅ 支持列表格式
- ✅ 识别分页符

### Excel转换功能

- ✅ 支持多工作表转换
- ✅ 保留表格结构
- ✅ 处理合并单元格
- ✅ 保持数据类型
- ✅ 跳过空工作表
- ✅ 可限制最大行数

## 输出格式说明

### Markdown文件结构

```markdown
# 文件标题

**源文件**: 原文件名
**总页数**: XX
**转换时间**: YYYY-MM-DD HH:MM:SS

---

<!-- PAGE_BREAK -->

## 【第 1 页】

页面内容...

**表格 1**:

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |
```

### 元数据文件

转换后会生成同名的JSON文件，包含转换元数据：

```json
{
  "源文件": "招标文件.pdf",
  "总页数": 100,
  "转换时间": "2026-03-22 10:00:00"
}
```

## 高级用法

### 图片处理选项

- `image_format='base64'`：图片以base64格式嵌入到Markdown中（默认）
- `image_format='link'`：图片保存为单独文件，Markdown中引用链接
- `image_format='none'`：不包含图片

```python
# 图片保存为单独文件
result = pdf_to_markdown(
    pdf_path="招标文件.pdf",
    output_path="招标文件_converted.md",
    image_format='link'  # 图片保存在 招标文件_converted_images/ 目录
)
```

### Excel行数限制

```python
# 限制每个工作表最多转换1000行
result = excel_to_markdown(
    excel_path="招标文件.xlsx",
    max_rows=1000
)
```

### 跳过空工作表

```python
# 默认跳过空工作表
result = excel_to_markdown(
    excel_path="招标文件.xlsx",
    skip_empty_sheets=True
)
```

## 常见问题

### Q1：PDF转换后表格内容丢失？

**可能原因**：PDF中的表格是图片格式，无法直接提取。

**解决方案**：
1. 检查PDF是否为扫描件
2. 尝试使用OCR工具先将PDF转为可编辑格式
3. 手动补充表格内容

### Q2：Word转换后标题层级不正确？

**可能原因**：Word文档使用了自定义样式。

**解决方案**：
1. 检查Word文档的样式设置
2. 使用标准标题样式（Heading 1-6）
3. 手动调整转换后的Markdown标题层级

### Q3：Excel转换后数据格式不正确？

**可能原因**：Excel单元格包含特殊格式。

**解决方案**：
1. 在Excel中先将单元格格式设置为"文本"
2. 转换后手动调整数据格式
3. 使用`data_only=True`参数读取值而非公式

### Q4：转换后文件太大？

**可能原因**：包含大量图片或数据。

**解决方案**：
1. 使用`image_format='link'`将图片保存为单独文件
2. 使用`max_rows`参数限制Excel转换行数
3. 分批次转换大文件

## 技术支持

如有问题，请检查：
1. 依赖库是否正确安装
2. 文件路径是否正确
3. 文件格式是否支持
4. 文件是否损坏

## 版本历史

### v2.0 (2026-03-22)

- 新增Word转MD功能
- 新增Excel转MD功能
- 新增统一转换工具
- 优化PDF转换功能

### v1.0 (2026-03-22)

- 初始版本
- 支持PDF转MD功能
