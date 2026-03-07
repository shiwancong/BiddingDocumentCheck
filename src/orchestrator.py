"""
主控Agent (Orchestrator)
负责协调整个检查流程的执行
"""

import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .agents import (
    DocumentParserAgent,
    ClauseIdentifierAgent,
    QualityValidatorAgent,
    ParsedDocument,
    IdentifiedClause,
    ValidationReport
)
from .agents.clause_identifier_enhanced import ClauseIdentifierAgentEnhanced


class BiddingDocumentOrchestrator:
    """
    招投标文件智能检查清单生成系统
    主控Agent
    """

    def __init__(self, output_dir: str = None):
        """
        初始化主控Agent

        Args:
            output_dir: 输出目录路径
        """
        self.parser = DocumentParserAgent()
        # 使用增强版条款识别器以提高识别率
        self.identifier = ClauseIdentifierAgentEnhanced()
        self.validator = QualityValidatorAgent()

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path.cwd() / "data" / "output"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 存储处理过程数据
        self.current_doc: Optional[ParsedDocument] = None
        self.current_clauses: Optional[List[IdentifiedClause]] = None
        self.current_report: Optional[ValidationReport] = None

    def process(
        self,
        file_path: str,
        include_suggestions: bool = True,
        save_intermediate: bool = True
    ) -> dict:
        """
        执行完整的检查流程

        Args:
            file_path: 招标文件路径
            include_suggestions: 是否包含建议性要求
            save_intermediate: 是否保存中间结果

        Returns:
            包含处理结果的字典
        """
        print(f"\n{'='*60}")
        print(f"开始处理招标文件: {Path(file_path).name}")
        print(f"{'='*60}\n")

        result = {
            'success': False,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'stages': {}
        }

        try:
            # Stage 1: 文档解析
            print("Stage 1: 正在解析文档...")
            self.current_doc = self.parser.parse(file_path)
            print(f"  [OK] 解析完成")
            print(f"    - 文件类型: {self.current_doc.file_type}")
            print(f"    - 总页数: {self.current_doc.total_pages}")
            print(f"    - 段落数: {len(self.current_doc.paragraphs)}")
            print(f"    - 表格数: {len(self.current_doc.tables)}")

            result['stages']['parsing'] = {
                'status': 'success',
                'total_pages': self.current_doc.total_pages,
                'paragraphs_count': len(self.current_doc.paragraphs),
                'tables_count': len(self.current_doc.tables)
            }

            if save_intermediate:
                intermediate_path = self.output_dir / f"{Path(file_path).stem}_parsed.json"
                self.parser.save_to_json(self.current_doc, str(intermediate_path))
                print(f"    - 已保存中间结果: {intermediate_path.name}")

            # Stage 2: 条款识别
            print("\nStage 2: 正在识别条款...")
            self.current_clauses = self.identifier.identify_all(
                self.current_doc,
                include_suggestions=include_suggestions
            )

            disqualification_count = len([c for c in self.current_clauses if c.clause_type.value == "废标条款"])
            suggestion_count = len([c for c in self.current_clauses if c.clause_type.value == "建议性要求"])

            print(f"  [OK] 识别完成")
            print(f"    - 总条款数: {len(self.current_clauses)}")
            print(f"    - 废标条款: {disqualification_count}")
            print(f"    - 建议性要求: {suggestion_count}")

            # 统计子类型
            sub_types = {}
            for clause in self.current_clauses:
                sub_types[clause.sub_type] = sub_types.get(clause.sub_type, 0) + 1

            print(f"    - 条款类型分布: {sub_types}")

            result['stages']['identification'] = {
                'status': 'success',
                'total_clauses': len(self.current_clauses),
                'disqualification_count': disqualification_count,
                'suggestion_count': suggestion_count,
                'sub_types': sub_types
            }

            if save_intermediate:
                clauses_path = self.output_dir / f"{Path(file_path).stem}_clauses.json"
                self.identifier.save_to_json(self.current_clauses, str(clauses_path))
                print(f"    - 已保存条款数据: {clauses_path.name}")

            # Stage 3: 质量验证
            print("\nStage 3: 正在验证质量...")
            self.current_report = self.validator.validate(
                self.current_clauses,
                self.current_doc,
                strict_mode=True
            )

            print(f"  [OK] 验证完成")
            print(f"    - 质量等级: {self.current_report.level}")
            print(f"    - 质量分数: {self.current_report.score:.1f}/100")

            if self.current_report.issues:
                error_count = len([i for i in self.current_report.issues if i.severity.value == "错误"])
                warning_count = len([i for i in self.current_report.issues if i.severity.value == "警告"])
                print(f"    - 发现问题: {error_count}个错误, {warning_count}个警告")
            else:
                print(f"    - 未发现问题")

            result['stages']['validation'] = {
                'status': 'success',
                'level': self.current_report.level,
                'score': self.current_report.score,
                'issues_count': len(self.current_report.issues)
            }

            # Stage 4: 生成输出
            print("\nStage 4: 正在生成输出...")

            # 生成Markdown报告
            markdown_content = self._generate_final_report()
            markdown_path = self.output_dir / f"{Path(file_path).stem}_检查清单.md"
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"  [OK] 已生成Markdown报告: {markdown_path.name}")

            # 生成验证报告
            validation_content = self.validator.generate_report(self.current_report)
            validation_path = self.output_dir / f"{Path(file_path).stem}_验证报告.md"
            with open(validation_path, 'w', encoding='utf-8') as f:
                f.write(validation_content)
            print(f"  [OK] 已生成验证报告: {validation_path.name}")

            result['stages']['output'] = {
                'status': 'success',
                'markdown_path': str(markdown_path),
                'validation_path': str(validation_path)
            }

            result['success'] = True
            result['summary'] = {
                'level': self.current_report.level,
                'score': self.current_report.score,
                'total_clauses': len(self.current_clauses),
                'disqualification_count': disqualification_count,
                'suggestion_count': suggestion_count
            }

            print(f"\n{'='*60}")
            print(f"处理完成! 质量等级: {self.current_report.level}")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"\n[FAIL] 处理失败: {str(e)}")
            result['error'] = str(e)
            result['stages']['error'] = {
                'status': 'failed',
                'message': str(e)
            }

        return result

    def _generate_final_report(self) -> str:
        """生成最终报告"""
        lines = []
        lines.append("# 招投标文件智能检查清单\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**文件名称**: {self.current_doc.filename if self.current_doc else 'N/A'}")
        lines.append(f"**总页数**: {self.current_doc.total_pages if self.current_doc else 'N/A'}")
        lines.append("")

        # 添加统计信息
        if self.current_clauses:
            disqualification = [c for c in self.current_clauses if c.clause_type.value == "废标条款"]
            suggestions = [c for c in self.current_clauses if c.clause_type.value == "建议性要求"]

            lines.append("## 统计摘要\n")
            lines.append(f"- **废标条款**: {len(disqualification)}项")
            lines.append(f"- **建议性要求**: {len(suggestions)}项")
            lines.append("")

        # 添加条款表格
        lines.append(self.identifier.to_markdown_table(self.current_clauses or []))

        # 添加附录
        lines.append("\n## 附录\n")
        lines.append("### 条款类型说明\n")
        lines.append("- **资格**: 投标人主体资格、资质、业绩、人员条件")
        lines.append("- **文件**: 是否提供某一文件或材料")
        lines.append("- **签字盖章**: 签字、盖章、签署主体")
        lines.append("- **时间方式**: 递交时间、截止时间、投标方式")
        lines.append("- **报价算术**: 报价计算错误、大小写不一致等")
        lines.append("- **响应性**: 是否实质性响应招标文件")
        lines.append("- **格式**: 页码、装订、密封、排版")
        lines.append("- **模板**: 是否使用指定模板、是否擅自修改模板")
        lines.append("- **其他**: 无法归入上述类别的情况")
        lines.append("")

        return "\n".join(lines)

    def get_clauses_by_type(self, clause_type: str) -> List[IdentifiedClause]:
        """按类型获取条款"""
        if not self.current_clauses:
            return []

        return [
            c for c in self.current_clauses
            if c.clause_type.value == clause_type
        ]

    def get_clauses_by_category(self, category: str) -> List[IdentifiedClause]:
        """按分类获取条款"""
        if not self.current_clauses:
            return []

        return [
            c for c in self.current_clauses
            if c.category.value == category
        ]

    def export_to_excel(self, output_path: str = None):
        """导出到Excel格式（需要pandas/openpyxl）"""
        try:
            import pandas as pd

            if not self.current_clauses:
                print("没有可导出的数据")
                return

            # 准备数据
            data = []
            for clause in self.current_clauses:
                data.append({
                    '检查项': clause.check_item,
                    '类型': clause.category.value,
                    '条款类型': clause.clause_type.value,
                    '原文页码': clause.original_page,
                    '原文关键信息': clause.original_text,
                    '逻辑解释': clause.logic_explanation,
                    '参考页码': clause.reference_page,
                    '额外说明': clause.extra_note,
                    '子类型': clause.sub_type,
                    '反常识项': '是' if clause.is_anti_common_sense else '否'
                })

            df = pd.DataFrame(data)

            if output_path is None:
                output_path = self.output_dir / f"{self.current_doc.filename}_检查清单.xlsx"

            df.to_excel(output_path, index=False, engine='openpyxl')
            print(f"已导出到Excel: {output_path}")

        except ImportError:
            print("导出Excel需要安装 pandas 和 openpyxl")
            print("请运行: pip install pandas openpyxl")


# 便捷函数
def check_bidding_document(file_path: str, **kwargs) -> dict:
    """
    便捷函数：检查招标文件

    Args:
        file_path: 招标文件路径
        **kwargs: 其他参数传递给Orchestrator.process()

    Returns:
        处理结果字典
    """
    orchestrator = BiddingDocumentOrchestrator()
    return orchestrator.process(file_path, **kwargs)


# 使用示例
if __name__ == "__main__":
    # 使用主控Agent处理文件
    orchestrator = BiddingDocumentOrchestrator()

    # 处理招标文件
    result = orchestrator.process("招标文件.docx")

    # 或者使用便捷函数
    # result = check_bidding_document("招标文件.docx")

    # 查看结果
    if result['success']:
        print(f"处理成功! 等级: {result['summary']['level']}")
    else:
        print(f"处理失败: {result.get('error')}")
