"""
Excel转Markdown脚本
功能：
1. 支持多工作表Excel文件转换
2. 保留表格结构
3. 处理合并单元格
4. 保持数据类型（数字、日期、公式等）
5. 生成可读性强的Markdown表格
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

try:
    import pandas as pd
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter
except ImportError:
    print("请安装所需库: pip install pandas openpyxl")
    raise


class ExcelToMarkdownConverter:
    """Excel转Markdown转换器"""

    def __init__(self, excel_path: str, output_path: Optional[str] = None,
                 skip_empty_sheets: bool = True, max_rows: Optional[int] = None):
        """
        初始化转换器

        Args:
            excel_path: Excel文件路径
            output_path: 输出Markdown文件路径
            skip_empty_sheets: 是否跳过空工作表
            max_rows: 每个工作表最大转换行数（None表示不限制）
        """
        self.excel_path = Path(excel_path)
        self.output_path = Path(output_path) if output_path else self.excel_path.with_suffix('.md')
        self.skip_empty_sheets = skip_empty_sheets
        self.max_rows = max_rows
        self.metadata = {}

    def convert(self) -> Path:
        """执行转换"""
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel文件不存在: {self.excel_path}")

        # 打开Excel文件
        wb = load_workbook(self.excel_path, data_only=True)

        # 收集元数据
        self.metadata = {
            "源文件": str(self.excel_path.name),
            "工作表数": len(wb.sheetnames),
            "工作表名称": wb.sheetnames,
            "转换时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 生成Markdown内容
        markdown_parts = []
        markdown_parts.append(self._generate_header())

        # 处理每个工作表
        for sheet_idx, sheet_name in enumerate(wb.sheetnames, 1):
            sheet_content = self._process_sheet(wb, sheet_name, sheet_idx)
            if sheet_content.strip():
                markdown_parts.append(sheet_content)

        # 写入文件
        markdown_text = ''.join(markdown_parts)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        # 保存元数据
        self._save_metadata()

        print(f"[OK] 转换完成！")
        print(f"[输出] {self.output_path}")
        print(f"[工作表数] {len(wb.sheetnames)}")

        return self.output_path

    def _generate_header(self) -> str:
        """生成文档头部"""
        header = f"# {self.excel_path.stem}\n\n"
        header += f"**源文件**: {self.metadata['源文件']}\n"
        header += f"**工作表数**: {self.metadata['工作表数']}\n"
        header += f"**工作表**: {', '.join(self.metadata['工作表名称'])}\n"
        header += f"**转换时间**: {self.metadata['转换时间']}\n"
        header += "\n---\n\n"
        return header

    def _process_sheet(self, wb, sheet_name: str, sheet_idx: int) -> str:
        """处理单个工作表"""
        content = []

        # 添加工作表标题
        content.append(f"## 工作表 {sheet_idx}: {sheet_name}\n\n")

        # 获取工作表
        ws = wb[sheet_name]

        # 检查工作表是否为空
        if self._is_empty_sheet(ws):
            if self.skip_empty_sheets:
                return ""
            else:
                content.append("*此工作表为空*\n\n")
                return ''.join(content)

        # 使用pandas读取工作表
        try:
            df = pd.read_excel(
                self.excel_path,
                sheet_name=sheet_name,
                header=None  # 不自动识别表头，保持原始结构
            )

            # 应用最大行数限制
            if self.max_rows and len(df) > self.max_rows:
                content.append(f"*注意: 工作表包含 {len(df)} 行，仅显示前 {self.max_rows} 行*\n\n")
                df = df.head(self.max_rows)

            # 转换为Markdown表格
            table_md = self._dataframe_to_markdown(df, ws)

            # 获取工作表信息
            info = self._get_sheet_info(ws, df)
            content.append(info)
            content.append(table_md)
            content.append("\n")

        except Exception as e:
            content.append(f"*转换此工作表时出错: {str(e)}*\n\n")

        return ''.join(content)

    def _is_empty_sheet(self, ws) -> bool:
        """检查工作表是否为空"""
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None:
                    return False
        return True

    def _get_sheet_info(self, ws, df) -> str:
        """获取工作表信息"""
        info_parts = []

        # 数据范围
        info_parts.append(f"**数据范围**: {df.shape[0]} 行 × {df.shape[1]} 列\n")

        # 合并单元格信息
        merged_cells = ws.merged_cells.ranges
        if merged_cells:
            info_parts.append(f"**合并单元格**: {len(merged_cells)} 处\n")

        # 有数据的单元格统计
        non_empty = df.count().sum()
        total_cells = df.shape[0] * df.shape[1]
        info_parts.append(f"**数据密度**: {non_empty}/{total_cells} 个单元格有数据\n")

        if info_parts:
            return ''.join(info_parts) + "\n"
        return ""

    def _dataframe_to_markdown(self, df: pd.DataFrame, ws) -> str:
        """将DataFrame转换为Markdown表格"""
        # 替换NaN为空字符串
        df = df.fillna('')

        # 替换换行符和竖线
        df = df.astype(str).replace('\n', '<br>', regex=True)
        df = df.astype(str).replace('|', '\\|', regex=True)

        # 生成Markdown表格
        table_md = "<table>\n"

        # 表头
        table_md += "  <thead>\n    <tr>\n"
        for header in df.iloc[0]:
            table_md += f"      <th>{header}</th>\n"
        table_md += "    </tr>\n  </thead>\n"

        # 表体
        table_md += "  <tbody>\n"
        for _, row in df.iterrows():
            table_md += "    <tr>\n"
            for cell in row:
                table_md += f"      <td>{cell}</td>\n"
            table_md += "    </tr>\n"
        table_md += "  </tbody>\n"

        table_md += "</table>\n\n"

        # 同时生成纯文本版本作为备用
        text_md = "**表格内容**:\n\n"
        text_md += "| " + " | ".join(str(x) for x in df.iloc[0]) + " |\n"
        text_md += "| " + " | ".join(["---"] * len(df.columns)) + " |\n"
        for _, row in df.iterrows():
            text_md += "| " + " | ".join(str(x) for x in row) + " |\n"

        return text_md + "\n" + table_md

    def _save_metadata(self):
        """保存元数据到JSON文件"""
        metadata_path = self.output_path.with_suffix('.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)


def excel_to_markdown(excel_path: str,
                      output_path: Optional[str] = None,
                      skip_empty_sheets: bool = True,
                      max_rows: Optional[int] = None) -> Path:
    """
    将Excel文件转换为Markdown格式

    Args:
        excel_path: Excel文件路径
        output_path: 输出Markdown文件路径
        skip_empty_sheets: 是否跳过空工作表
        max_rows: 每个工作表最大转换行数

    Returns:
        输出文件路径
    """
    converter = ExcelToMarkdownConverter(
        excel_path=excel_path,
        output_path=output_path,
        skip_empty_sheets=skip_empty_sheets,
        max_rows=max_rows
    )
    return converter.convert()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        # 默认测试文件
        excel_file = r"E:\Work\agent-work\BiddingDocumentCheck\data\test\test.xlsx"

    # 输出路径
    output_file = excel_file.replace('.xlsx', '_converted.md').replace('.xls', '_converted.md')

    # 执行转换
    try:
        result = excel_to_markdown(
            excel_file,
            output_file,
            skip_empty_sheets=True,
            max_rows=None  # 不限制行数
        )
        print(f"\n转换成功: {result}")
    except Exception as e:
        print(f"转换失败: {e}")
        import traceback
        traceback.print_exc()
