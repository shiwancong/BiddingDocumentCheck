"""
统一文件转Markdown工具
支持：PDF、Word (DOCX)、Excel (XLSX/XLS) 格式

使用方法：
    python convert_to_md.py 文件路径 [输出路径]

示例：
    python convert_to_md.py 招标文件.pdf
    python convert_to_md.py 招标文件.docx
    python convert_to_md.py 招标文件.xlsx
    python convert_to_md.py 招标文件.pdf 输出文件.md
"""

import sys
import os
from pathlib import Path
from typing import Optional


class FileConverter:
    """统一文件转换器"""

    SUPPORTED_FORMATS = {
        '.pdf': 'PDF',
        '.docx': 'Word',
        '.doc': 'Word',
        '.xlsx': 'Excel',
        '.xls': 'Excel'
    }

    def __init__(self, file_path: str, output_path: Optional[str] = None):
        """
        初始化转换器

        Args:
            file_path: 输入文件路径
            output_path: 输出文件路径（可选）
        """
        self.file_path = Path(file_path)
        self.output_path = Path(output_path) if output_path else self._default_output_path()
        self.file_type = self._detect_file_type()

    def _default_output_path(self) -> Path:
        """生成默认输出路径"""
        return self.file_path.with_suffix('.md')

    def _detect_file_type(self) -> str:
        """检测文件类型"""
        suffix = self.file_path.suffix.lower()

        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"不支持的文件格式: {suffix}\n"
                f"支持的格式: {', '.join(self.SUPPORTED_FORMATS.keys())}"
            )

        return self.SUPPORTED_FORMATS[suffix]

    def convert(self) -> Path:
        """执行转换"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")

        print(f"[检测] 文件类型: {self.file_type}")
        print(f"[输入] {self.file_path}")
        print(f"[输出] {self.output_path}")

        # 根据文件类型调用相应的转换器
        if self.file_type == 'PDF':
            return self._convert_pdf()
        elif self.file_type == 'Word':
            return self._convert_word()
        elif self.file_type == 'Excel':
            return self._convert_excel()
        else:
            raise ValueError(f"未实现的文件类型: {self.file_type}")

    def _convert_pdf(self) -> Path:
        """转换PDF文件"""
        try:
            from convert_pdf_to_md_advanced import pdf_to_markdown

            return pdf_to_markdown(
                pdf_path=str(self.file_path),
                output_path=str(self.output_path),
                include_images=True,
                image_format='base64'
            )
        except ImportError as e:
            raise ImportError(
                f"PDF转换需要安装依赖库: {e}\n"
                f"请运行: pip install PyMuPDF"
            )

    def _convert_word(self) -> Path:
        """转换Word文件"""
        try:
            from convert_docx_to_md import docx_to_markdown

            return docx_to_markdown(
                docx_path=str(self.file_path),
                output_path=str(self.output_path),
                include_images=True,
                image_format='base64'
            )
        except ImportError as e:
            raise ImportError(
                f"Word转换需要安装依赖库: {e}\n"
                f"请运行: pip install python-docx"
            )

    def _convert_excel(self) -> Path:
        """转换Excel文件"""
        try:
            from convert_excel_to_md import excel_to_markdown

            return excel_to_markdown(
                excel_path=str(self.file_path),
                output_path=str(self.output_path),
                skip_empty_sheets=True,
                max_rows=None
            )
        except ImportError as e:
            raise ImportError(
                f"Excel转换需要安装依赖库: {e}\n"
                f"请运行: pip install pandas openpyxl"
            )


def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("统一文件转Markdown工具")
        print("\n使用方法:")
        print("  python convert_to_md.py 文件路径 [输出路径]")
        print("\n示例:")
        print("  python convert_to_md.py 招标文件.pdf")
        print("  python convert_to_md.py 招标文件.docx")
        print("  python convert_to_md.py 招标文件.xlsx")
        print("  python convert_to_md.py 招标文件.pdf 输出文件.md")
        print("\n支持的格式:")
        print("  - PDF: .pdf")
        print("  - Word: .docx, .doc")
        print("  - Excel: .xlsx, .xls")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # 执行转换
    try:
        converter = FileConverter(input_file, output_file)
        result = converter.convert()

        print("\n" + "=" * 50)
        print("转换成功!")
        print("=" * 50)
        print(f"输出文件: {result}")

    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except ImportError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"转换失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
