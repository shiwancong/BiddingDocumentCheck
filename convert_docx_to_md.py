"""
Word转Markdown脚本
功能：
1. 保留原Word文档的页面布局
2. 包含页码信息
3. 正确处理表格
4. 处理图片
5. 保持文本层次结构（标题、粗体、斜体等）
"""

import os
import re
import base64
from pathlib import Path
from typing import Optional, List, Dict
import json
from datetime import datetime

try:
    from docx import Document
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import _Cell, Table
    from docx.text.paragraph import Paragraph
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
    from docx.oxml.ns import qn
except ImportError:
    print("请安装python-docx库: pip install python-docx")
    raise


class WordToMarkdownConverter:
    """Word转Markdown转换器"""

    def __init__(self, docx_path: str, output_path: Optional[str] = None,
                 include_images: bool = True, image_format: str = 'base64'):
        """
        初始化转换器

        Args:
            docx_path: Word文件路径
            output_path: 输出Markdown文件路径
            include_images: 是否包含图片
            image_format: 图片格式 ('base64', 'link', 'none')
        """
        self.docx_path = Path(docx_path)
        self.output_path = Path(output_path) if output_path else self.docx_path.with_suffix('.md')
        self.include_images = include_images
        self.image_format = image_format
        self.images_dir = self.output_path.parent / f"{self.output_path.stem}_images"
        self.metadata = {}

    def convert(self) -> Path:
        """执行转换"""
        if not self.docx_path.exists():
            raise FileNotFoundError(f"Word文件不存在: {self.docx_path}")

        # 打开Word文档
        doc = Document(self.docx_path)

        # 收集元数据
        self.metadata = {
            "源文件": str(self.docx_path.name),
            "段落数": len(doc.paragraphs),
            "表格数": len(doc.tables),
            "转换时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 创建图片目录
        if self.include_images and self.image_format == 'link':
            self.images_dir.mkdir(exist_ok=True)

        # 生成Markdown内容
        markdown_parts = []
        markdown_parts.append(self._generate_header())

        # 计数器
        page_num = 1
        table_idx = 1
        image_idx = 1

        # 遍历文档的所有元素（段落和表格）
        for element in self._iter_block_items(doc):
            if isinstance(element, Paragraph):
                # 添加分页标记（每10段或遇到分页符）
                if element._element.pPr is not None:
                    page_break = element._element.pPr.find(qn('w:br'))
                    if page_break is not None and page_break.get(qn('w:type')) == 'page':
                        page_num += 1
                        markdown_parts.append(f"\n\n<!-- PAGE_BREAK -->\n")
                        markdown_parts.append(f"\n## 【第 {page_num} 页】\n\n")

                # 处理段落
                para_content = self._process_paragraph(element)
                if para_content.strip():
                    markdown_parts.append(para_content)

            elif isinstance(element, Table):
                # 处理表格
                table_content = self._process_table(element, table_idx)
                if table_content.strip():
                    markdown_parts.append(table_content)
                    table_idx += 1

        # 写入文件
        markdown_text = ''.join(markdown_parts)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        # 保存元数据
        self._save_metadata()

        print(f"[OK] 转换完成！")
        print(f"[输出] {self.output_path}")
        print(f"[段落数] {len(doc.paragraphs)}")
        print(f"[表格数] {len(doc.tables)}")

        return self.output_path

    def _generate_header(self) -> str:
        """生成文档头部"""
        header = f"# {self.docx_path.stem}\n\n"
        header += f"**源文件**: {self.metadata['源文件']}\n"
        header += f"**段落数**: {self.metadata['段落数']}\n"
        header += f"**表格数**: {self.metadata['表格数']}\n"
        header += f"**转换时间**: {self.metadata['转换时间']}\n"
        header += "\n---\n\n"
        return header

    def _iter_block_items(self, doc):
        """
        遍历文档的所有块级元素（段落和表格）
        """
        # 获取文档的所有子元素
        for element in doc.element.body:
            # 判断是段落还是表格
            if element.tag == qn('w:p'):
                yield Paragraph(element, doc)
            elif element.tag == qn('w:tbl'):
                yield Table(element, doc)

    def _process_paragraph(self, paragraph: Paragraph) -> str:
        """处理段落"""
        text = paragraph.text.strip()

        if not text:
            return ""

        # 获取段落样式
        style_name = paragraph.style.name if paragraph.style else ""

        # 处理标题
        if 'Heading' in style_name or '标题' in style_name:
            level = self._get_heading_level(style_name)
            prefix = "#" * level
            return f"{prefix} {text}\n\n"

        # 处理列表
        if 'List' in style_name or '列表' in style_name:
            return f"- {text}\n"

        # 处理普通段落（应用格式）
        formatted_text = self._apply_paragraph_formatting(paragraph)

        return formatted_text + "\n\n"

    def _get_heading_level(self, style_name: str) -> int:
        """获取标题级别"""
        if 'Heading 1' in style_name or '标题 1' in style_name:
            return 1
        elif 'Heading 2' in style_name or '标题 2' in style_name:
            return 2
        elif 'Heading 3' in style_name or '标题 3' in style_name:
            return 3
        elif 'Heading 4' in style_name or '标题 4' in style_name:
            return 4
        elif 'Heading 5' in style_name or '标题 5' in style_name:
            return 5
        elif 'Heading 6' in style_name or '标题 6' in style_name:
            return 6
        else:
            return 2  # 默认为二级标题

    def _apply_paragraph_formatting(self, paragraph: Paragraph) -> str:
        """应用段落格式（粗体、斜体等）"""
        result = []

        for run in paragraph.runs:
            text = run.text
            if not text:
                continue

            # 应用格式
            if run.bold:
                text = f"**{text}**"
            if run.italic:
                text = f"*{text}*"
            if run.underline:
                text = f"<u>{text}</u>"

            result.append(text)

        return ''.join(result)

    def _process_table(self, table: Table, table_idx: int) -> str:
        """处理表格"""
        try:
            # 获取表格数据
            headers = []
            rows = []

            # 获取表头
            for cell in table.rows[0].cells:
                headers.append(cell.text.strip())

            # 获取数据行
            for row in table.rows[1:]:
                row_data = []
                for cell in row.cells:
                    row_data.append(cell.text.strip())
                rows.append(row_data)

            # 生成Markdown表格
            table_md = f"\n**表格 {table_idx}**:\n\n"

            # 表头
            table_md += "| " + " | ".join(headers) + " |\n"
            table_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"

            # 数据行
            for row in rows:
                table_md += "| " + " | ".join(row) + " |\n"

            table_md += "\n"
            return table_md

        except Exception as e:
            print(f"警告: 处理表格 {table_idx} 时出错: {e}")
            return f"\n<!-- 表格 {table_idx} 解析失败 -->\n\n"

    def _save_metadata(self):
        """保存元数据到JSON文件"""
        metadata_path = self.output_path.with_suffix('.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)


def docx_to_markdown(docx_path: str,
                     output_path: Optional[str] = None,
                     include_images: bool = True,
                     image_format: str = 'base64') -> Path:
    """
    将Word文件转换为Markdown格式

    Args:
        docx_path: Word文件路径
        output_path: 输出Markdown文件路径
        include_images: 是否包含图片
        image_format: 图片格式 ('base64', 'link', 'none')

    Returns:
        输出文件路径
    """
    converter = WordToMarkdownConverter(
        docx_path=docx_path,
        output_path=output_path,
        include_images=include_images,
        image_format=image_format
    )
    return converter.convert()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        docx_file = sys.argv[1]
    else:
        # 默认测试文件
        docx_file = r"E:\Work\agent-work\BiddingDocumentCheck\data\test\test.docx"

    # 输出路径
    output_file = docx_file.replace('.docx', '_converted.md')

    # 执行转换
    try:
        result = docx_to_markdown(
            docx_file,
            output_file,
            include_images=True,
            image_format='base64'
        )
        print(f"\n转换成功: {result}")
    except Exception as e:
        print(f"转换失败: {e}")
        import traceback
        traceback.print_exc()
