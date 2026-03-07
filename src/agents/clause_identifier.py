"""
条款识别Agent
负责识别招标文件中的废标条款和建议性要求
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from .document_parser import ParsedDocument, TableData
from ..config import (
    DISQUALIFICATION_KEYWORDS,
    SUGGESTION_KEYWORDS,
    MANDATORY_KEYWORDS,
    CONDITION_KEYWORDS,
    ANTI_COMMON_SENSE_PATTERNS,
    TABLE_KEY_COLUMNS,
    CLAUSE_TYPES
)


class ClauseType(Enum):
    """条款类型"""
    DISQUALIFICATION = "废标条款"
    SUGGESTION = "建议性要求"


class CategoryType(Enum):
    """分类类型"""
    QUALIFICATION = "资格"
    DOCUMENT = "文件"
    SIGN_SEAL = "签字盖章"
    TIME_METHOD = "时间方式"
    PRICE_CALCULATION = "报价算术"
    RESPONSIVENESS = "响应性"
    FORMAT = "格式"
    TEMPLATE = "模板"
    OTHER = "其他"


@dataclass
class IdentifiedClause:
    """识别出的条款"""
    clause_type: ClauseType  # 废标/建议
    category: CategoryType   # 分类
    check_item: str          # 检查项
    original_page: int       # 原文页码
    original_text: str       # 原文关键信息
    logic_explanation: str   # 逻辑解释
    reference_page: str = ""  # 参考页码
    extra_note: str = ""      # 额外说明
    sub_type: str = ""        # 子类型（明确/条件/表格/跨章节等）
    is_anti_common_sense: bool = False  # 是否反常识


class ClauseIdentifierAgent:
    """条款识别Agent"""

    def __init__(self):
        self.disqualification_keywords = DISQUALIFICATION_KEYWORDS
        self.suggestion_keywords = SUGGESTION_KEYWORDS
        self.mandatory_keywords = MANDATORY_KEYWORDS
        self.condition_keywords = CONDITION_KEYWORDS
        self.anti_common_sense_patterns = ANTI_COMMON_SENSE_PATTERNS
        self.table_key_columns = TABLE_KEY_COLUMNS

    def identify_all(
        self,
        parsed_doc: ParsedDocument,
        include_suggestions: bool = True
    ) -> List[IdentifiedClause]:
        """
        识别所有条款

        Args:
            parsed_doc: 解析后的文档
            include_suggestions: 是否包含建议性要求

        Returns:
            识别出的条款列表
        """
        all_clauses = []

        # 1. 识别正文中的条款
        text_clauses = self._identify_from_text(parsed_doc)
        all_clauses.extend(text_clauses)

        # 2. 识别表格中的条款
        table_clauses = self._identify_from_tables(parsed_doc)
        all_clauses.extend(table_clauses)

        # 3. 跨章节关联分析
        cross_chapter_clauses = self._identify_cross_chapter(parsed_doc, all_clauses)
        all_clauses.extend(cross_chapter_clauses)

        # 4. 矛盾条款解决
        all_clauses = self._resolve_conflicts(all_clauses)

        # 5. 过滤建议性要求
        if not include_suggestions:
            all_clauses = [c for c in all_clauses if c.clause_type == ClauseType.DISQUALIFICATION]

        return all_clauses

    def _identify_from_text(self, parsed_doc: ParsedDocument) -> List[IdentifiedClause]:
        """从正文文本中识别条款"""
        clauses = []

        for para in parsed_doc.paragraphs:
            text = para['text']
            page_num = para['page_num']

            # 跳过空文本和太短的文本
            if not text or len(text) < 10:
                continue

            # 检查是否包含废标关键词
            disqualification_found = self._check_disqualification_keywords(text)

            # 检查是否包含建议性关键词
            is_suggestion = self._check_suggestion_keywords(text)

            # 判断条款类型
            if disqualification_found:
                clause_type = ClauseType.DISQUALIFICATION
                sub_type = self._determine_sub_type(text)
            elif is_suggestion and self._has_mandatory_content(text):
                clause_type = ClauseType.SUGGESTION
                sub_type = "建议性"
            else:
                continue

            # 提取条款信息
            clause = self._extract_clause_info(
                text=text,
                page_num=page_num,
                clause_type=clause_type,
                sub_type=sub_type
            )
            if clause:
                clauses.append(clause)

        return clauses

    def _identify_from_tables(self, parsed_doc: ParsedDocument) -> List[IdentifiedClause]:
        """从表格中识别条款"""
        clauses = []

        for table in parsed_doc.tables:
            # 查找关键列
            key_col_idx = self._find_key_column(table)

            if key_col_idx is None:
                continue

            # 提取该列为"否决/无效"的行
            for row_idx, row in enumerate(table.rows[1:], start=1):  # 跳过表头
                if key_col_idx >= len(row):
                    continue

                cell_text = row[key_col_idx]

                if self._contains_disqualification_term(cell_text):
                    # 提取检查项（通常是第一列）
                    check_item = row[0] if row else ""

                    clause = IdentifiedClause(
                        clause_type=ClauseType.DISQUALIFICATION,
                        category=self._classify_clause(check_item + " " + cell_text),
                        check_item=check_item,
                        original_page=table.page_num,
                        original_text=f"检查项: {check_item}, 处理方式: {cell_text}",
                        logic_explanation=f"表格要求{check_item}，{cell_text}",
                        sub_type="表格条款"
                    )
                    clauses.append(clause)

        return clauses

    def _identify_cross_chapter(
        self,
        parsed_doc: ParsedDocument,
        existing_clauses: List[IdentifiedClause]
    ) -> List[IdentifiedClause]:
        """识别跨章节关联的条款"""
        # 这里需要更复杂的语义分析
        # 简化实现：查找包含"参见"、"详见"等引用词的条款

        cross_chapter_clauses = []
        reference_patterns = [
            r'(参见|详见|见|按照.*规定|遵循.*要求)(第?\d*[章节])',
            r'(按照|遵循)(附件\d+)',
        ]

        for para in parsed_doc.paragraphs:
            text = para['text']

            for pattern in reference_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    # 如果找到引用且包含废标相关的描述
                    if self._check_disqualification_keywords(text):
                        clause = self._extract_clause_info(
                            text=text,
                            page_num=para['page_num'],
                            clause_type=ClauseType.DISQUALIFICATION,
                            sub_type="跨章节"
                        )
                        if clause:
                            # 提取参考页码
                            clause.reference_page = match.group(2)
                            cross_chapter_clauses.append(clause)

        return cross_chapter_clauses

    def _resolve_conflicts(self, clauses: List[IdentifiedClause]) -> List[IdentifiedClause]:
        """解决矛盾条款，选择更严格的版本"""
        # 按检查项分组
        groups: Dict[str, List[IdentifiedClause]] = {}

        for clause in clauses:
            key = self._normalize_check_item(clause.check_item)
            if key not in groups:
                groups[key] = []
            groups[key].append(clause)

        resolved = []

        for key, group_clauses in groups.items():
            if len(group_clauses) == 1:
                resolved.append(group_clauses[0])
            else:
                # 选择最严格的（废标 > 建议）
                disqualification = [c for c in group_clauses if c.clause_type == ClauseType.DISQUALIFICATION]
                suggestions = [c for c in group_clauses if c.clause_type == ClauseType.SUGGESTION]

                if disqualification:
                    # 有废标条款，选择废标
                    resolved.extend(disqualification)
                    # 建议性降级或合并
                    for sug in suggestions:
                        sug.extra_note = f"(已有更严格要求: {disqualification[0].check_item})"
                        resolved.append(sug)
                else:
                    resolved.extend(group_clauses)

        return resolved

    # ========== 辅助方法 ==========

    def _check_disqualification_keywords(self, text: str) -> bool:
        """检查是否包含废标关键词"""
        for keyword in self.disqualification_keywords:
            if keyword in text:
                return True
        return False

    def _check_suggestion_keywords(self, text: str) -> bool:
        """检查是否包含建议性关键词"""
        for keyword in self.suggestion_keywords:
            if keyword in text:
                return True
        return False

    def _has_mandatory_content(self, text: str) -> bool:
        """检查是否包含强制性内容"""
        for keyword in self.mandatory_keywords:
            if keyword in text:
                return True
        return False

    def _contains_disqualification_term(self, text: str) -> bool:
        """检查文本是否包含否决/无效等术语"""
        terms = ["否决", "无效", "不接受", "不进入评审", "作无效", "拒绝"]
        return any(term in text for term in terms)

    def _determine_sub_type(self, text: str) -> str:
        """确定条款子类型"""
        # 检查是否为条件句
        for cond_kw in self.condition_keywords:
            if cond_kw in text:
                return "条件式"

        # 检查是否为反常识
        if self._is_anti_common_sense(text):
            return "反常识"

        # 检查是否为否定句+例外
        if "除" in text and "外" in text:
            return "否定+例外"

        return "明确"

    def _is_anti_common_sense(self, text: str) -> bool:
        """检查是否为反常识废标项"""
        for category, patterns in self.anti_common_sense_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return True
        return False

    def _find_key_column(self, table: TableData) -> Optional[int]:
        """在表格中查找关键列（不满足后果/处理方式等）"""
        if not table.headers:
            return None

        for idx, header in enumerate(table.headers):
            for key_col in self.table_key_columns:
                if key_col in header:
                    return idx
        return None

    def _extract_clause_info(
        self,
        text: str,
        page_num: int,
        clause_type: ClauseType,
        sub_type: str
    ) -> Optional[IdentifiedClause]:
        """从文本中提取条款信息"""
        # 提取关键信息（这里简化处理，实际需要更复杂的NLP）
        check_item = self._extract_check_item(text)

        if not check_item:
            return None

        category = self._classify_clause(text)

        return IdentifiedClause(
            clause_type=clause_type,
            category=category,
            check_item=check_item,
            original_page=page_num,
            original_text=text,  # 直接摘录原文
            logic_explanation=self._generate_logic_explanation(text, clause_type),
            sub_type=sub_type,
            is_anti_common_sense=self._is_anti_common_sense(text)
        )

    def _extract_check_item(self, text: str) -> str:
        """提取检查项描述"""
        # 简化实现：提取前30个字符作为检查项
        # 实际需要更智能的句子分割和主语识别
        sentences = re.split(r'[，。；；\n]', text)
        for sent in sentences:
            sent = sent.strip()
            if sent and len(sent) > 5:
                # 检查是否包含强制性或条件性表述
                if any(kw in sent for kw in ["必须", "应当", "不得", "若", "如果", "当", "未"]):
                    return sent[:50]  # 限制长度
        return text[:50] if text else ""

    def _classify_clause(self, text: str) -> CategoryType:
        """对条款进行分类"""
        # 根据关键词分类
        if any(kw in text for kw in ["资质", "资格", "证书", "执照", "许可证"]):
            return CategoryType.QUALIFICATION
        elif any(kw in text for kw in ["签字", "盖章", "签署", "公章"]):
            return CategoryType.SIGN_SEAL
        elif any(kw in text for kw in ["时间", "截止", "递交", "提交"]):
            return CategoryType.TIME_METHOD
        elif any(kw in text for kw in ["报价", "金额", "预算", "限价"]):
            return CategoryType.PRICE_CALCULATION
        elif any(kw in text for kw in ["响应", "满足", "符合要求"]):
            return CategoryType.RESPONSIVENESS
        elif any(kw in text for kw in ["格式", "模板", "装订", "密封", "页码"]):
            return CategoryType.FORMAT
        elif any(kw in text for kw in ["附件", "表格", "清单"]):
            return CategoryType.DOCUMENT
        else:
            return CategoryType.OTHER

    def _generate_logic_explanation(self, text: str, clause_type: ClauseType) -> str:
        """生成逻辑解释"""
        if clause_type == ClauseType.DISQUALIFICATION:
            return f"该条款要求{text[:30]}...，如不满足将导致投标被否决。"
        else:
            return f"该条款建议{text[:30]}...，不满足通常不会直接导致废标。"

    def _normalize_check_item(self, check_item: str) -> str:
        """标准化检查项（用于分组）"""
        # 移除空格和标点
        normalized = re.sub(r'[，。；；\s]', '', check_item)
        return normalized.lower()[:50]

    def to_markdown_table(self, clauses: List[IdentifiedClause]) -> str:
        """转换为Markdown表格"""
        if not clauses:
            return "未识别到任何条款。"

        # 表头
        headers = ["检查项", "类型", "原文页码", "原文关键信息", "逻辑解释", "参考页码", "额外说明"]

        # 分离废标条款和建议性要求
        disqualification = [c for c in clauses if c.clause_type == ClauseType.DISQUALIFICATION]
        suggestions = [c for c in clauses if c.clause_type == ClauseType.SUGGESTION]

        output = []

        if disqualification:
            output.append("## 废标风险检查\n")
            output.append("| " + " | ".join(headers) + " |")
            output.append("| " + " | ".join(["---"] * len(headers)) + " |")

            for clause in disqualification:
                row = [
                    clause.check_item,
                    clause.category.value,
                    str(clause.original_page),
                    clause.original_text[:50] + "..." if len(clause.original_text) > 50 else clause.original_text,
                    clause.logic_explanation,
                    clause.reference_page or "",
                    clause.extra_note or ""
                ]
                output.append("| " + " | ".join(str(x) for x in row) + " |")

        if suggestions:
            output.append("\n## 建议项清单\n")
            output.append("| " + " | ".join(headers) + " |")
            output.append("| " + " | ".join(["---"] * len(headers)) + " |")

            for clause in suggestions:
                row = [
                    clause.check_item,
                    clause.category.value,
                    str(clause.original_page),
                    clause.original_text[:50] + "..." if len(clause.original_text) > 50 else clause.original_text,
                    clause.logic_explanation,
                    clause.reference_page or "",
                    clause.extra_note or ""
                ]
                output.append("| " + " | ".join(str(x) for x in row) + " |")

        return "\n".join(output)

    def save_to_json(self, clauses: List[IdentifiedClause], output_path: str):
        """保存为JSON文件"""
        data = []
        for clause in clauses:
            data.append({
                'check_item': clause.check_item,
                'type': clause.category.value,
                'clause_type': clause.clause_type.value,
                'original_page': clause.original_page,
                'original_text': clause.original_text,
                'logic_explanation': clause.logic_explanation,
                'reference_page': clause.reference_page,
                'extra_note': clause.extra_note,
                'sub_type': clause.sub_type,
                'is_anti_common_sense': clause.is_anti_common_sense
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 使用示例
if __name__ == "__main__":
    identifier = ClauseIdentifierAgent()
    # 使用示例
    # clauses = identifier.identify_all(parsed_doc)
    # print(identifier.to_markdown_table(clauses))
