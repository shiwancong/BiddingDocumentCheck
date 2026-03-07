"""
招投标文件智能检查清单生成系统
主入口文件

使用方法:
    python main.py <招标文件路径>

示例:
    python main.py 招标文件.docx
    python main.py 招标文件.pdf
"""

import sys
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator import check_bidding_document, BiddingDocumentOrchestrator


def main():
    parser = argparse.ArgumentParser(
        description="招投标文件智能检查清单生成系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s 招标文件.docx              # 完整检查
  %(prog)s 招标文件.docx --no-suggest  # 只提取废标条款
  %(prog)s 招标文件.docx --export      # 导出Excel报告
        """
    )

    parser.add_argument(
        "file",
        help="招标文件路径（支持.docx, .doc, .pdf）"
    )

    parser.add_argument(
        "--no-suggest",
        action="store_true",
        help="不包含建议性要求，只提取废标条款"
    )

    parser.add_argument(
        "--export",
        action="store_true",
        help="导出Excel格式报告"
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help="指定输出目录（默认为data/output）"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细信息"
    )

    args = parser.parse_args()

    # 检查文件是否存在
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"错误: 文件不存在 - {file_path}")
        sys.exit(1)

    # 检查文件类型
    if file_path.suffix.lower() not in ['.docx', '.doc', '.pdf']:
        print(f"警告: 不支持的文件类型 - {file_path.suffix}")
        print("支持的格式: .docx, .doc, .pdf")

    # 执行检查
    try:
        orchestrator = BiddingDocumentOrchestrator(output_dir=args.output_dir)

        result = orchestrator.process(
            str(file_path),
            include_suggestions=not args.no_suggest,
            save_intermediate=True
        )

        if result['success']:
            # 显示结果摘要
            summary = result['summary']
            print("\n" + "="*50)
            print("处理完成!")
            print("="*50)
            print(f"质量等级: {summary['level']}")
            print(f"质量分数: {summary['score']:.1f}/100")
            print(f"废标条款: {summary['disqualification_count']} 项")
            print(f"建议性要求: {summary['suggestion_count']} 项")
            print(f"总条款数: {summary['total_clauses']} 项")

            if args.verbose:
                # 显示详细统计
                stages = result.get('stages', {})
                if 'identification' in stages:
                    ident = stages['identification']
                    print(f"\n条款类型分布:")
                    for sub_type, count in ident.get('sub_types', {}).items():
                        print(f"  - {sub_type}: {count} 项")

            # 导出Excel
            if args.export:
                print("\n正在导出Excel...")
                orchestrator.export_to_excel()

            # 显示输出文件位置
            print(f"\n输出文件位置: {orchestrator.output_dir}")

            # 根据质量等级给出提示
            level = summary['level']
            if 'S' in level:
                print("\n🎉 已达到S级标准！")
            elif 'A' in level:
                print("\n✓ 质量良好，接近S级标准")
            elif 'B' in level:
                print("\n△ 质量合格，建议检查验证报告中的问题")
            else:
                print("\n⚠ 质量有待提升，请查看验证报告并修正问题")

            sys.exit(0)

        else:
            print(f"\n处理失败: {result.get('error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)

    except Exception as e:
        print(f"\n错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 检查依赖
    try:
        import docx
    except ImportError:
        print("错误: 缺少必要的依赖库")
        print("请运行: pip install python-docx pdfplumber")
        sys.exit(1)

    main()
