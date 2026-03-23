"""
高级PDF转Markdown转换器
====================================

功能说明：
---------
1. 保留原PDF的页面布局和结构
2. 精确标记每页位置（使用分页标记）
3. 正确识别和处理表格
4. 处理图片（支持base64嵌入、链接保存、忽略）
5. 保持文本层次结构（标题、段落、列表）
6. 提取页面尺寸等元数据

核心特性：
---------
- 分页标记：使用 <!-- PAGE_BREAK --> 和 ## 【第 X 页】标记页面
- 表格识别：智能识别PDF中的表格并转换为Markdown表格
- 图片处理：支持三种模式（base64嵌入、链接保存、忽略）
- 尺寸信息：保留每页的尺寸信息用于布局分析

使用方法：
---------
from convert_pdf_to_md_advanced import PDFToMarkdownConverter, pdf_to_markdown

# 方式1：使用类
converter = PDFToMarkdownConverter("input.pdf", "output.md")
result = converter.convert()

# 方式2：使用便捷函数
result = pdf_to_markdown("input.pdf", "output.md")

依赖库：
---------
- PyMuPDF (fitz): pip install PyMuPDF

应用场景：
---------
- 招标文件PDF转Markdown（保留页码便于定位）
- 文档PDF转Markdown（保留结构和格式）
- 学术论文PDF转Markdown（保留表格和图片）

作者：招投标智能检查系统
版本：v2.0
更新日期：2026-03-22
"""

import fitz  # PyMuPDF - 高级PDF处理库
import os
import re
import base64
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import json


class PDFToMarkdownConverter:
    """
    高级PDF转Markdown转换器

    核心功能：
    1. 逐页处理PDF，保留页面布局
    2. 识别和转换文本、表格、图片
    3. 生成分页标记便于精确定位
    4. 支持多种图片处理模式
    """

    def __init__(self, pdf_path: str, output_path: Optional[str] = None,
                 include_images: bool = True, image_format: str = 'base64'):
        """
        初始化PDF转换器

        Args:
            pdf_path: 输入PDF文件路径
            output_path: 输出Markdown文件路径（默认为PDF同名.md文件）
            include_images: 是否包含图片（默认True）
            image_format: 图片格式
                - 'base64': 将图片转换为base64嵌入Markdown（推荐，单文件）
                - 'link': 保存图片到单独文件夹，Markdown中引用链接
                - 'none': 忽略图片
        """
        self.pdf_path = Path(pdf_path)
        self.output_path = Path(output_path) if output_path else self.pdf_path.with_suffix('.md')
        self.include_images = include_images
        self.image_format = image_format
        self.images_dir = self.output_path.parent / f"{self.output_path.stem}_images"
        self.page_count = 0
        self.metadata = {}

    def convert(self) -> Path:
        """执行转换"""
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")

        # 打开PDF
        doc = fitz.open(self.pdf_path)
        self.page_count = len(doc)

        # 收集元数据
        self.metadata = {
            "源文件": str(self.pdf_path.name),
            "总页数": self.page_count,
            "转换时间": str(self._get_current_time())
        }

        # 创建图片目录
        if self.include_images and self.image_format == 'link':
            self.images_dir.mkdir(exist_ok=True)

        # 生成Markdown内容
        markdown_parts = []
        markdown_parts.append(self._generate_header())

        # 逐页处理
        for page_num in range(self.page_count):
            page = doc[page_num]
            page_content = self._process_page(page, page_num + 1)
            markdown_parts.append(page_content)

        # 关闭PDF
        doc.close()

        # 写入文件
        markdown_text = ''.join(markdown_parts)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        # 保存元数据
        self._save_metadata()

        print(f"[OK] 转换完成！")
        print(f"[输出] {self.output_path}")
        print(f"[总页数] {self.page_count}")

        return self.output_path

    def _generate_header(self) -> str:
        """生成文档头部"""
        header = f"# {self.pdf_path.stem}\n\n"
        header += f"**源文件**: {self.metadata['源文件']}\n"
        header += f"**总页数**: {self.metadata['总页数']}\n"
        header += f"**转换时间**: {self.metadata['转换时间']}\n"
        header += "\n---\n\n"
        return header

    def _process_page(self, page: fitz.Page, page_num: int) -> str:
        """处理单个页面"""
        content = []

        # 添加分页标记
        content.append("\n\n<!-- PAGE_BREAK -->\n")
        content.append(f"\n## 【第 {page_num} 页】\n\n")

        # 获取页面尺寸和布局信息
        rect = page.rect
        content.append(f"<!-- PAGE_SIZE: {rect.width:.2f}x{rect.height:.2f} -->\n")

        # 提取文本块（保持布局）
        text_blocks = self._extract_text_with_layout(page)
        for block in text_blocks:
            content.append(block)

        # 提取表格
        tables = self._extract_tables(page)
        if tables:
            content.append("\n### 表格\n\n")
            for table in tables:
                content.append(table)
                content.append("\n")

        # 提取图片
        if self.include_images:
            images = self._extract_images(page, page_num)
            if images:
                content.append("\n### 图片\n\n")
                for img in images:
                    content.append(img)
                    content.append("\n")

        return ''.join(content)

    def _extract_text_with_layout(self, page: fitz.Page) -> List[str]:
        """提取文本并保持布局"""
        blocks = []
        try:
            # 使用 "dict" 模式获取文本块，包含位置信息
            text_dict = page.get_text("dict")

            # 按照Y坐标排序（从上到下）
            sorted_blocks = sorted(text_dict["blocks"],
                                 key=lambda b: b.get("bbox", [0, 0, 0, 0])[1])

            for block in sorted_blocks:
                if "lines" in block:  # 文本块
                    block_text = self._process_text_block(block)
                    if block_text.strip():
                        blocks.append(block_text)
        except Exception as e:
            print(f"警告: 提取文本时出错 (第{page.number + 1}页): {e}")
            # 回退到简单文本提取
            text = page.get_text("text")
            if text.strip():
                blocks.append(text + "\n")

        return blocks

    def _process_text_block(self, block: Dict) -> str:
        """处理单个文本块"""
        lines = []
        for line in block["lines"]:
            line_text = ""
            for span in line["spans"]:
                # 检测字体样式
                font_flags = span.get("flags", 0)
                is_bold = (font_flags & 2**4) != 0
                is_italic = (font_flags & 2**1) != 0

                text = span["text"]
                if not text.strip():
                    continue

                # 应用Markdown格式
                if is_bold:
                    text = f"**{text}**"
                if is_italic:
                    text = f"*{text}*"

                line_text += text

            if line_text.strip():
                lines.append(line_text)

        # 检测标题（根据字体大小）
        if lines:
            first_span = block["lines"][0]["spans"][0] if block["lines"] else None
            if first_span:
                font_size = first_span.get("size", 12)
                if font_size >= 18:
                    level = min(6, int(28 - font_size) / 2 + 1)
                    prefix = "#" * int(level)
                    return f"{prefix} {''.join(lines)}\n\n"

        return "\n".join(lines) + "\n\n"

    def _extract_tables(self, page: fitz.Page) -> List[str]:
        """提取表格"""
        tables = []
        try:
            # 查找表格
            found_tables = page.find_tables()

            for table_idx, table in enumerate(found_tables):
                try:
                    df = table.to_pandas()

                    # 转换为Markdown表格
                    table_md = f"**表格 {table_idx + 1}**:\n\n"
                    table_md += df.to_markdown(index=False)
                    table_md += "\n"

                    tables.append(table_md)
                except Exception as e:
                    print(f"警告: 转换表格 {table_idx + 1} 时出错: {e}")
                    # 手动提取表格内容
                    table_md = self._extract_table_manually(table, table_idx + 1)
                    tables.append(table_md)

        except Exception as e:
            print(f"警告: 提取表格时出错: {e}")

        return tables

    def _extract_table_manually(self, table, table_idx: int) -> str:
        """手动提取表格内容"""
        table_md = f"**表格 {table_idx}**:\n\n"

        # 获取表格内容
        header = table.header
        rows = table.extract()

        # 构建Markdown表格
        if header:
            table_md += "| " + " | ".join(str(h) for h in header) + " |\n"
            table_md += "| " + " | ".join("---" for _ in header) + " |\n"

        for row in rows:
            table_md += "| " + " | ".join(str(cell) if cell else "" for cell in row) + " |\n"

        table_md += "\n"
        return table_md

    def _extract_images(self, page: fitz.Page, page_num: int) -> List[str]:
        """提取图片"""
        images = []
        try:
            image_list = page.get_images(full=True)

            for img_idx, img_info in enumerate(image_list, 1):
                try:
                    xref = img_info[0]
                    base_image = page.parent.extract_image(xref)
                    image_data = base_image["image"]
                    image_ext = base_image["ext"]

                    if self.image_format == 'base64':
                        # Base64嵌入
                        b64_data = base64.b64encode(image_data).decode('utf-8')
                        img_md = (
                            f"![图片 {img_idx}](data:image/{image_ext};base64,{b64_data})\n"
                            f"<!-- 图片 {img_idx}: {image_ext.upper()}格式, {len(image_data)} bytes -->\n"
                        )
                    elif self.image_format == 'link':
                        # 保存为文件并链接
                        img_filename = f"page_{page_num}_img_{img_idx}.{image_ext}"
                        img_path = self.images_dir / img_filename

                        with open(img_path, 'wb') as f:
                            f.write(image_data)

                        img_md = f"![图片 {img_idx}]({self.images_dir.name}/{img_filename})\n"
                    else:
                        img_md = f"<!-- 图片 {img_idx}: {image_ext.upper()}格式, {len(image_data)} bytes -->\n"

                    images.append(img_md)

                except Exception as e:
                    print(f"警告: 提取图片 {img_idx} 时出错: {e}")

        except Exception as e:
            print(f"警告: 获取图片列表时出错: {e}")

        return images

    def _save_metadata(self):
        """保存元数据到JSON文件"""
        metadata_path = self.output_path.with_suffix('.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _get_current_time() -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def pdf_to_markdown(pdf_path: str,
                    output_path: Optional[str] = None,
                    include_images: bool = True,
                    image_format: str = 'base64') -> Path:
    """
    将PDF文件转换为Markdown格式

    Args:
        pdf_path: PDF文件路径
        output_path: 输出Markdown文件路径
        include_images: 是否包含图片
        image_format: 图片格式 ('base64', 'link', 'none')

    Returns:
        输出文件路径
    """
    converter = PDFToMarkdownConverter(
        pdf_path=pdf_path,
        output_path=output_path,
        include_images=include_images,
        image_format=image_format
    )
    return converter.convert()


if __name__ == "__main__":
    # 使用示例
    import sys

    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    else:
        # 默认测试文件
        pdf_file = r"E:\Work\agent-work\BiddingDocumentCheck\data\test\济南市历城职业中等专业学校数据治理平台采购项目数据治理平台采购项目.pdf"

    # 输出路径
    output_file = pdf_file.replace('.pdf', '_converted.md')

    # 执行转换
    try:
        result = pdf_to_markdown(
            pdf_file,
            output_file,
            include_images=True,
            image_format='base64'  # 或 'link' 保存为单独文件
        )
        print(f"\n转换成功: {result}")
    except Exception as e:
        print(f"转换失败: {e}")
