"""
条款识别Agent - 增强版
优化后能更准确地识别废标条款和建议性要求，达到S级标准
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set
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


class ClauseIdentifierAgentEnhanced:
    """条款识别Agent - 增强版"""

    def __init__(self):
        self.disqualification_keywords = DISQUALIFICATION_KEYWORDS
        self.suggestion_keywords = SUGGESTION_KEYWORDS
        self.mandatory_keywords = MANDATORY_KEYWORDS
        self.condition_keywords = CONDITION_KEYWORDS
        self.anti_common_sense_patterns = ANTI_COMMON_SENSE_PATTERNS

        # 扩展的表格关键列
        self.table_key_columns = TABLE_KEY_COLUMNS + [
            "要求", "说明", "备注", "注意事项", "其他"
        ]

        # 扩展的废标表述
        self.extended_disqualification_terms = [
            "否决", "无效", "不接受", "不进入评审", "作无效",
            "视为无效", "拒绝", "将被拒绝", "将被认定为无效",
            "作无效处理", "否决其投标", "其投标将被否决",
            "投标将被否决", "投标无效", "作无效投标处理",
            "不予接受", "不进入评审", "视为无效投标",
            "磋商无效", "响应无效", "将被视为无效响应",
            "将被视为无效投标", "将被拒绝", "将被退回"
        ]

        # 条件结果模式
        self.condition_result_patterns = [
            r'(?:若|如果|当|如|一旦).{0,50}(?:则|将)?(?:导致)?(?:.{0,30})?(?:否决|无效|不接受|拒绝)',
            r'(?:未|未按|未按规定|未按要求|未在).{0,50}(?:者|的)?(?:，|。)?(?:.{0,30})?(?:否决|无效|不接受|拒绝)',
            r'(?:超出|超过|低于|高于|不符合|不满足|缺少|缺少|缺少).{0,50}(?:者|的)?(?:，|。)?(?:.{0,30})?(?:否决|无效|不接受|拒绝)',
            r'(?:否则|后果|责任)(?:由)?.{0,50}(?:自行承担|负责)',
            r'(?:其)?(?:投标|响应|报价|文件)?(?:将被|将被视为|将被认定)?(?:否决|无效|不接受)',
        ]

    def identify_all(
        self,
        parsed_doc: ParsedDocument,
        include_suggestions: bool = True
    ) -> List[IdentifiedClause]:
        """
        识别所有条款 - 增强版

        Args:
            parsed_doc: 解析后的文档
            include_suggestions: 是否包含建议性要求

        Returns:
            识别出的条款列表
        """
        all_clauses = []

        # 1. 识别正文中的条款（增强版）
        text_clauses = self._identify_from_text_enhanced(parsed_doc)
        all_clauses.extend(text_clauses)

        # 2. 识别表格中的条款（增强版）
        table_clauses = self._identify_from_tables_enhanced(parsed_doc)
        all_clauses.extend(table_clauses)

        # 3. 识别附件引用条款
        attachment_clauses = self._identify_from_attachments(parsed_doc)
        all_clauses.extend(attachment_clauses)

        # 4. 跨章节关联分析（增强版）
        cross_chapter_clauses = self._identify_cross_chapter_enhanced(parsed_doc, all_clauses)
        all_clauses.extend(cross_chapter_clauses)

        # 5. 识别隐含的废标条件
        implicit_clauses = self._identify_implicit_disqualifications(parsed_doc)
        all_clauses.extend(implicit_clauses)

        # 6. 矛盾条款解决（增强版）
        all_clauses = self._resolve_conflicts_enhanced(all_clauses)

        # 7. 去重
        all_clauses = self._deduplicate_clauses(all_clauses)

        # 8. 过滤建议性要求
        if not include_suggestions:
            all_clauses = [c for c in all_clauses if c.clause_type == ClauseType.DISQUALIFICATION]

        return all_clauses

    def _identify_from_text_enhanced(self, parsed_doc: ParsedDocument) -> List[IdentifiedClause]:
        """从正文文本中识别条款 - 增强版"""
        clauses = []

        # 用于存储可能的多行条款
        pending_clause = None
        clause_buffer = []

        for para in parsed_doc.paragraphs:
            text = para['text'].strip()
            page_num = para['page_num']

            # 跳过空文本和太短的文本
            if not text or len(text) < 5:
                continue

            # 跳过标题
            if self._is_heading(text):
                continue

            # 增强版：检查是否为废标条款（使用更宽松的匹配）
            is_disqualification = self._is_disqualification_clause_enhanced(text)

            # 检查是否包含建议性关键词
            is_suggestion = self._check_suggestion_keywords(text)

            # 判断条款类型
            if is_disqualification:
                clause_type = ClauseType.DISQUALIFICATION
                sub_type = self._determine_sub_type_enhanced(text)
            elif is_suggestion and self._has_mandatory_content(text):
                clause_type = ClauseType.SUGGESTION
                sub_type = "建议性"
            elif self._contains_mandatory_with_consequence(text):
                # 包含强制性表述+后果描述
                clause_type = ClauseType.DISQUALIFICATION
                sub_type = "强制+后果"
            else:
                continue

            # 处理多行条款
            if pending_clause and text[0].isdigit() and len(text.split()[0]) <= 3:
                # 可能是新的编号条款，先保存之前的
                if pending_clause:
                    clauses.append(pending_clause)
                pending_clause = None
                clause_buffer = []

            # 收集条款内容
            clause_buffer.append(text)

            # 判断条款是否完整
            if self._is_complete_clause(text):
                full_text = " ".join(clause_buffer)

                clause = self._extract_clause_info_enhanced(
                    text=full_text,
                    page_num=page_num,
                    clause_type=clause_type,
                    sub_type=sub_type
                )
                if clause:
                    clauses.append(clause)
                pending_clause = None
                clause_buffer = []
            else:
                # 等待更多内容
                if not pending_clause:
                    pending_clause = {
                        'text': text,
                        'page_num': page_num,
                        'clause_type': clause_type,
                        'sub_type': sub_type
                    }
                else:
                    pending_clause['text'] += " " + text

        return clauses

    def _identify_from_tables_enhanced(self, parsed_doc: ParsedDocument) -> List[IdentifiedClause]:
        """从表格中识别条款 - 增强版"""
        clauses = []

        for table in parsed_doc.tables:
            # 分析表格结构
            table_analysis = self._analyze_table_structure(table)

            # 跳过功能要求表
            if table_analysis['type'] == 'function_requirements':
                continue

            # 如果表格不包含相关列，跳过
            if not table_analysis['has_relevant_columns']:
                continue

            # 只处理明确是废标条款的表格
            if not table_analysis.get('is_disqualification_table', False):
                # 对于非明确废标表格，需要更严格的检查
                has_explicit_disqualification = False
                for row in table.rows[1:]:
                    for cell in row:
                        if self._contains_disqualification_term(cell):
                            has_explicit_disqualification = True
                            break
                    if has_explicit_disqualification:
                        break

                if not has_explicit_disqualification:
                    continue

            # 根据表格类型提取条款
            if table_analysis['type'] == 'requirement_consequence':
                # 要求-后果型表格
                clauses.extend(self._extract_from_requirement_table(table, table_analysis))
            elif table_analysis['type'] == 'checklist':
                # 清单型表格
                clauses.extend(self._extract_from_checklist_table(table, table_analysis))
            elif table_analysis['type'] == 'scoring':
                # 评分表
                clauses.extend(self._extract_from_scoring_table(table, table_analysis))

        return clauses

    def _identify_from_attachments(self, parsed_doc: ParsedDocument) -> List[IdentifiedClause]:
        """识别附件引用的条款"""
        clauses = []

        # 查找所有提到附件的段落
        attachment_patterns = [
            r'附件\s*\d+[：:：].*?(?:否决|无效|不接受|拒绝|必须|应当|不得)',
            r'(?:按照|按照.*格式|参照|遵循)(?:附件|表|模板).*?(?:否决|无效|不接受|拒绝)',
            r'未按?(?:附件|表|模板).*?(?:否决|无效|不接受|拒绝)',
        ]

        for para in parsed_doc.paragraphs:
            text = para['text']

            for pattern in attachment_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    matched_text = match.group(0)

                    # 检查是否为废标条款
                    if self._contains_disqualification_term(matched_text):
                        clause = self._extract_clause_info_enhanced(
                            text=matched_text,
                            page_num=para['page_num'],
                            clause_type=ClauseType.DISQUALIFICATION,
                            sub_type="附件引用"
                        )
                        if clause:
                            # 提取附件编号
                            attachment_match = re.search(r'附件\s*\d+', matched_text)
                            if attachment_match:
                                clause.reference_page = attachment_match.group(0)
                            clauses.append(clause)

        return clauses

    def _identify_cross_chapter_enhanced(
        self,
        parsed_doc: ParsedDocument,
        existing_clauses: List[IdentifiedClause]
    ) -> List[IdentifiedClause]:
        """识别跨章节关联的条款 - 增强版"""
        cross_chapter_clauses = []

        # 收集所有可能的不完整条件
        incomplete_conditions = []

        for para in parsed_doc.paragraphs:
            text = para['text']

            # 检查是否为不完整的强制性要求（没有后果描述）
            if self._is_incomplete_mandatory_requirement(text):
                incomplete_conditions.append({
                    'text': text,
                    'page_num': para['page_num'],
                    'section': para.get('section', '')
                })

        # 尝试匹配条件和后果
        for condition in incomplete_conditions:
            # 查找可能匹配的后果描述
            consequence = self._find_matching_consequence(condition, parsed_doc, existing_clauses)

            if consequence:
                # 组合成完整条款
                full_text = f"{condition['text']} {consequence['text']}"

                clause = self._extract_clause_info_enhanced(
                    text=full_text,
                    page_num=condition['page_num'],
                    clause_type=ClauseType.DISQUALIFICATION,
                    sub_type="跨章节组合"
                )
                if clause:
                    clause.reference_page = f"参见{consequence['location']}"
                    cross_chapter_clauses.append(clause)

        return cross_chapter_clauses

    def _identify_implicit_disqualifications(self, parsed_doc: ParsedDocument) -> List[IdentifiedClause]:
        """识别隐含的废标条件"""
        clauses = []

        # 隐含废标模式
        implicit_patterns = [
            (r'未(?:按要求|按规定|在.*前).*?(?:递交|提交|提供)', "未按要求提交"),
            (r'超出|超过.*?(?:限额|限价|期限|时间)', "超出限额/期限"),
            (r'缺少|未提供.*?(?:文件|材料|证明|证书)', "缺少必要文件"),
            (r'不(?:符合|满足).*?(?:要求|规定|条件)', "不符合要求"),
            (r'(?:投标|响应|报价).*(?:低于|高于).*?(?:成本|限价)', "价格异常"),
        ]

        for para in parsed_doc.paragraphs:
            text = para['text']

            for pattern, desc in implicit_patterns:
                if re.search(pattern, text):
                    # 检查上下文是否有否定后果
                    context_has_consequence = self._check_context_for_consequence(text, para, parsed_doc)

                    if context_has_consequence:
                        clause = self._extract_clause_info_enhanced(
                            text=text,
                            page_num=para['page_num'],
                            clause_type=ClauseType.DISQUALIFICATION,
                            sub_type="隐含条件"
                        )
                        if clause:
                            clause.extra_note = f"隐含废标条件: {desc}"
                            clauses.append(clause)

        return clauses

    def _resolve_conflicts_enhanced(self, clauses: List[IdentifiedClause]) -> List[IdentifiedClause]:
        """解决矛盾条款 - 增强版"""
        # 按检查项分组（使用更智能的匹配）
        groups = self._group_similar_clauses(clauses)

        resolved = []

        for key, group_clauses in groups.items():
            if len(group_clauses) == 1:
                resolved.append(group_clauses[0])
            else:
                # 选择最严格的版本
                selected = self._select_strictest_clause(group_clauses)
                resolved.append(selected)

                # 其他作为参考
                for other in group_clauses:
                    if other != selected:
                        other.extra_note = f"(已有更严格要求: {selected.check_item})"
                        resolved.append(other)

        return resolved

    def _deduplicate_clauses(self, clauses: List[IdentifiedClause]) -> List[IdentifiedClause]:
        """去重"""
        seen = set()
        deduplicated = []

        for clause in clauses:
            # 创建唯一标识
            identifier = self._create_clause_identifier(clause)

            if identifier not in seen:
                seen.add(identifier)
                deduplicated.append(clause)

        return deduplicated

    # ========== 辅助方法 ==========

    def _is_heading(self, text: str) -> bool:
        """判断是否为标题 - 优化版"""
        # 如果包含废标关键词，不可能是标题
        if self._contains_disqualification_term(text):
            return False

        # 如果包含强制性关键词且长度>20，不太可能是标题
        if any(kw in text for kw in ["必须", "应当", "不得", "严禁"]) and len(text) > 20:
            return False

        # 检查常见标题模式
        heading_patterns = [
            r'^第[一二三四五六七八九十]+[章节编]',
            r'^[一二三四五六七八九十]+[、．．]\s*\w{1,10}$',
            r'^\d+[\.\．]\s*\w{1,15}$',
            r'^\([\d一二三四五六七八九十]+\)',
        ]
        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True

        # 短文本且全大写或全数字可能是标题
        if len(text) < 20 and (text.isupper() or text.isdigit()):
            return True

        return False

    def _is_disqualification_clause_enhanced(self, text: str) -> bool:
        """增强版：检查是否为废标条款"""
        # 1. 检查明确的废标关键词
        for keyword in self.disqualification_keywords:
            if keyword in text:
                return True

        # 2. 检查扩展的废标术语
        for term in self.extended_disqualification_terms:
            if term in text:
                return True

        # 3. 检查条件-结果模式
        for pattern in self.condition_result_patterns:
            if re.search(pattern, text):
                return True

        # 4. 检查"否则+责任承担"模式
        if re.search(r'否则.*?(?:自行承担|责任|后果)', text):
            return True

        return False

    def _contains_mandatory_with_consequence(self, text: str) -> bool:
        """检查是否包含强制性表述+后果"""
        has_mandatory = any(kw in text for kw in self.mandatory_keywords)
        has_negative_consequence = any(kw in text for kw in
            ["否决", "无效", "不接受", "拒绝", "视为无效", "作无效"])

        return has_mandatory and has_negative_consequence

    def _is_complete_clause(self, text: str) -> bool:
        """判断条款是否完整"""
        # 以句号、问号或感叹号结尾
        if text[-1] in '。？！':
            return True
        # 包含完整的"如果...则..."结构
        if re.search(r'(?:若|如果|当).{0,100}(?:则|那么|就)', text):
            return True
        # 包含后果描述
        if any(kw in text for kw in ["否决", "无效", "不接受", "拒绝"]):
            return True
        return False

    def _is_incomplete_mandatory_requirement(self, text: str) -> bool:
        """检查是否为不完整的强制性要求"""
        # 包含强制性表述但没有后果
        has_mandatory = any(kw in text for kw in self.mandatory_keywords)
        has_consequence = any(kw in text for kw in ["否决", "无效", "不接受", "拒绝"])

        return has_mandatory and not has_consequence

    def _check_context_for_consequence(self, text: str, para: dict, parsed_doc: ParsedDocument) -> bool:
        """检查上下文是否有后果描述"""
        # 简化实现：检查前后段落
        return False  # 可根据需要扩展

    def _determine_sub_type_enhanced(self, text: str) -> str:
        """增强版：确定条款子类型"""
        # 检查反常识
        if self._is_anti_common_sense(text):
            return "反常识"

        # 检查条件句
        for cond_kw in self.condition_keywords:
            if cond_kw in text:
                return "条件式"

        # 检查否定句+例外
        if "除" in text and "外" in text:
            return "否定+例外"

        # 检查是否包含"否则"
        if "否则" in text:
            return "否则后果型"

        return "明确"

    def _analyze_table_structure(self, table: TableData) -> Dict[str, Any]:
        """分析表格结构 - 增强版"""
        analysis = {
            'type': 'generic',
            'has_relevant_columns': False,
            'key_columns': [],
            'requirement_column': None,
            'consequence_column': None,
            'is_disqualification_table': False
        }

        if not table.headers:
            return analysis

        # 首先检查是否为功能要求/技术规格表（这些表通常不包含废标条款）
        function_keywords = ["功能要求", "技术要求", "性能指标", "规格", "参数", "功能说明",
                           "系统应", "模块", "支持", "实现", "管理", "展示", "统计"]
        is_function_table = any(any(kw in h for kw in function_keywords) for h in table.headers)

        if is_function_table:
            # 检查表格内容中是否有否决性词汇
            has_disqualification_in_content = False
            for row in table.rows[1:5]:
                for cell in row:
                    if self._contains_disqualification_term(cell):
                        has_disqualification_in_content = True
                        break
                if has_disqualification_in_content:
                    break

            if not has_disqualification_in_content:
                analysis['type'] = 'function_requirements'
                return analysis

        # 分析表头
        for idx, header in enumerate(table.headers):
            # 检查是否为关键列
            for key_col in self.table_key_columns:
                if key_col in header:
                    analysis['key_columns'].append(idx)
                    analysis['has_relevant_columns'] = True

                    if "后果" in header or "处理" in header or "方式" in header:
                        analysis['consequence_column'] = idx
                    elif "要求" in header or "内容" in header or "项目" in header:
                        analysis['requirement_column'] = idx

        # 判断表格类型
        if analysis['consequence_column'] is not None:
            analysis['type'] = 'requirement_consequence'
            analysis['is_disqualification_table'] = True
        elif any("评分" in h for h in table.headers):
            analysis['type'] = 'scoring'
        elif any("是/否" in h or "是否符合" in h for h in table.headers):
            analysis['type'] = 'checklist'
        elif is_function_table:
            analysis['type'] = 'function_requirements'

        return analysis

    def _extract_from_requirement_table(self, table: TableData, analysis: Dict) -> List[IdentifiedClause]:
        """从要求-后果型表格提取条款"""
        clauses = []

        req_col = analysis['requirement_column'] or 0
        con_col = analysis['consequence_column']

        if con_col is None:
            return clauses

        for row in table.rows[1:]:  # 跳过表头
            if len(row) <= max(req_col, con_col):
                continue

            requirement = row[req_col].strip()
            consequence = row[con_col].strip()

            if not requirement or not consequence:
                continue

            # 检查是否为否决性后果
            if self._contains_disqualification_term(consequence):
                clause = IdentifiedClause(
                    clause_type=ClauseType.DISQUALIFICATION,
                    category=self._classify_clause(requirement + " " + consequence),
                    check_item=requirement,
                    original_page=table.page_num,
                    original_text=f"{requirement} - {consequence}",
                    logic_explanation=f"表格要求：{requirement}，不满足则{consequence}",
                    sub_type="表格条款"
                )
                clauses.append(clause)

        return clauses

    def _extract_from_checklist_table(self, table: TableData, analysis: Dict) -> List[IdentifiedClause]:
        """从清单型表格提取条款"""
        clauses = []

        # 查找"是否"或"是否符合"列
        check_col = None
        note_col = None

        for idx, header in enumerate(table.headers):
            if "是" in header or "符合" in header:
                check_col = idx
            elif "备注" in header or "说明" in header:
                note_col = idx

        if check_col is None:
            return clauses

        for row in table.rows[1:]:
            if len(row) <= check_col:
                continue

            item = row[0].strip() if row else ""
            check_value = row[check_col].strip() if check_col < len(row) else ""

            # 如果要求是"必须"或"应当"，且备注中有否决性说明
            if item and ("必须" in item or "应当" in item):
                note = row[note_col].strip() if note_col and note_col < len(row) else ""

                if note and self._contains_disqualification_term(note):
                    clause = IdentifiedClause(
                        clause_type=ClauseType.DISQUALIFICATION,
                        category=self._classify_clause(item),
                        check_item=item,
                        original_page=table.page_num,
                        original_text=f"{item} ({note})",
                        logic_explanation=f"清单要求：{item}，{note}",
                        sub_type="表格清单"
                    )
                    clauses.append(clause)

        return clauses

    def _extract_from_scoring_table(self, table: TableData, analysis: Dict) -> List[IdentifiedClause]:
        """从评分表提取条款"""
        clauses = []

        # 评分表通常在备注栏说明废标条件
        for idx, header in enumerate(table.headers):
            if "备注" in header or "说明" in header:
                for row in table.rows[1:]:
                    if idx >= len(row):
                        continue

                    note = row[idx].strip()
                    if note and self._contains_disqualification_term(note):
                        item = row[0].strip() if row else ""
                        clause = IdentifiedClause(
                            clause_type=ClauseType.DISQUALIFICATION,
                            category=self._classify_clause(note),
                            check_item=item or "评分要求",
                            original_page=table.page_num,
                            original_text=f"评分表要求：{note}",
                            logic_explanation=f"评分表备注：{note}",
                            sub_type="评分表"
                        )
                        clauses.append(clause)

        return clauses

    def _extract_from_generic_table(self, table: TableData, analysis: Dict) -> List[IdentifiedClause]:
        """从通用表格提取条款"""
        clauses = []

        # 检查所有单元格
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row):
                if self._contains_disqualification_term(cell):
                    # 获取相关上下文
                    context = self._get_table_context(table, row_idx, cell_idx)

                    clause = IdentifiedClause(
                        clause_type=ClauseType.DISQUALIFICATION,
                        category=self._classify_clause(cell),
                        check_item=context.get('item', '表格要求'),
                        original_page=table.page_num,
                        original_text=f"{context.get('location', '')}: {cell}",
                        logic_explanation=f"表格中规定：{cell}",
                        sub_type="表格条款"
                    )
                    clauses.append(clause)

        return clauses

    def _get_table_context(self, table: TableData, row_idx: int, cell_idx: int) -> Dict[str, str]:
        """获取表格单元格的上下文"""
        context = {}

        # 获取行标题
        if row_idx < len(table.rows) and len(table.rows[row_idx]) > 0:
            context['item'] = table.rows[row_idx][0]

        # 获取列标题
        if cell_idx < len(table.headers):
            context['location'] = table.headers[cell_idx]

        return context

    def _find_matching_consequence(
        self,
        condition: Dict,
        parsed_doc: ParsedDocument,
        existing_clauses: List[IdentifiedClause]
    ) -> Optional[Dict]:
        """查找匹配的后果描述"""
        # 简化实现：在后续段落中查找
        return None

    def _group_similar_clauses(self, clauses: List[IdentifiedClause]) -> Dict[str, List[IdentifiedClause]]:
        """将相似条款分组"""
        groups = {}

        for clause in clauses:
            # 使用检查项的前20个字符作为分组键
            key = clause.check_item[:20]
            if key not in groups:
                groups[key] = []
            groups[key].append(clause)

        return groups

    def _select_strictest_clause(self, clauses: List[IdentifiedClause]) -> IdentifiedClause:
        """选择最严格的条款"""
        # 优先选择废标条款
        disqualification = [c for c in clauses if c.clause_type == ClauseType.DISQUALIFICATION]
        if disqualification:
            return disqualification[0]

        # 选择最详细的
        return max(clauses, key=lambda c: len(c.original_text))

    def _create_clause_identifier(self, clause: IdentifiedClause) -> str:
        """创建条款唯一标识"""
        return f"{clause.check_item[:30]}_{clause.clause_type.value}_{clause.original_page}"

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
        for term in self.extended_disqualification_terms:
            if term in text:
                return True
        return False

    def _is_anti_common_sense(self, text: str) -> bool:
        """检查是否为反常识废标项"""
        for category, patterns in self.anti_common_sense_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return True
        return False

    def _extract_clause_info_enhanced(
        self,
        text: str,
        page_num: int,
        clause_type: ClauseType,
        sub_type: str
    ) -> Optional[IdentifiedClause]:
        """增强版：从文本中提取条款信息"""
        # 更智能地提取检查项
        check_item = self._extract_check_item_enhanced(text, clause_type)

        if not check_item:
            check_item = text[:50]  # 默认取前50字

        category = self._classify_clause(text)

        return IdentifiedClause(
            clause_type=clause_type,
            category=category,
            check_item=check_item,
            original_page=page_num,
            original_text=text,  # 直接摘录原文
            logic_explanation=self._generate_logic_explanation_enhanced(text, clause_type, check_item),
            sub_type=sub_type,
            is_anti_common_sense=self._is_anti_common_sense(text)
        )

    def _extract_check_item_enhanced(self, text: str, clause_type: ClauseType) -> str:
        """增强版：提取检查项描述"""
        # 尝试提取主语
        patterns = [
            r'^(.{5,40}?)(?:必须|应当|不得|严禁|若|如果|当|未)',
            r'^(.{5,40}?)(?:的|者|时)',
            r'^(.{5,40}?)(?:，|,|。)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                item = match.group(1).strip()
                if len(item) > 3:
                    return item

        # 提取第一句话
        sentences = re.split(r'[，。；；\n]', text)
        for sent in sentences:
            sent = sent.strip()
            if 10 < len(sent) < 80:
                return sent

        return text[:50]

    def _classify_clause(self, text: str) -> CategoryType:
        """对条款进行分类"""
        # 分类规则（按优先级）
        classification_rules = [
            # 资格类
            (["资质", "资格", "证书", "执照", "许可证", "认证", "备案"], CategoryType.QUALIFICATION),
            # 签字盖章
            (["签字", "盖章", "签署", "公章", "印章", "签名"], CategoryType.SIGN_SEAL),
            # 时间方式
            (["截止", "递交", "提交", "投标", "响应", "磋商", "开标", "评审"], CategoryType.TIME_METHOD),
            # 报价算术
            (["报价", "金额", "预算", "限价", "最高限价", "成本价", "价款"], CategoryType.PRICE_CALCULATION),
            # 响应性
            (["响应", "满足", "符合", "实质性"], CategoryType.RESPONSIVENESS),
            # 格式
            (["格式", "模板", "装订", "密封", "页码", "打印", "排版", "字体"], CategoryType.FORMAT),
            # 文件
            (["附件", "表格", "清单", "文件", "资料", "材料", "证明"], CategoryType.DOCUMENT),
        ]

        for keywords, category in classification_rules:
            if any(kw in text for kw in keywords):
                return category

        return CategoryType.OTHER

    def _generate_logic_explanation_enhanced(
        self,
        text: str,
        clause_type: ClauseType,
        check_item: str
    ) -> str:
        """增强版：生成逻辑解释"""
        if clause_type == ClauseType.DISQUALIFICATION:
            # 提取条件
            condition_match = re.search(r'(?:若|如果|当|未)(.{10,40})', text)
            condition = condition_match.group(1) if condition_match else "未满足要求"

            # 提取后果
            consequence_match = re.search(r'(?:否决|无效|不接受|拒绝|视为无效)(.{10,30})?', text)
            consequence = consequence_match.group(0) if consequence_match else "投标被否决"

            return f"要求{check_item}。如果{condition}，则{consequence}。"
        else:
            return f"建议{check_item}，有助于提升投标文件的规范性和完整性。"

    def to_markdown_table(self, clauses: List[IdentifiedClause]) -> str:
        """转换为Markdown表格"""
        if not clauses:
            return "未识别到任何条款。"

        headers = ["检查项", "类型", "原文页码", "原文关键信息", "逻辑解释", "参考页码", "额外说明"]

        output = []

        # 分离废标条款和建议性要求
        disqualification = [c for c in clauses if c.clause_type == ClauseType.DISQUALIFICATION]
        suggestions = [c for c in clauses if c.clause_type == ClauseType.SUGGESTION]

        if disqualification:
            output.append("## 废标风险检查\n")
            output.append("| " + " | ".join(headers) + " |")
            output.append("| " + " | ".join(["---"] * len(headers)) + " |")

            for clause in disqualification:
                row = [
                    clause.check_item,
                    clause.category.value,
                    str(clause.original_page),
                    clause.original_text[:60] + "..." if len(clause.original_text) > 60 else clause.original_text,
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
                    clause.original_text[:60] + "..." if len(clause.original_text) > 60 else clause.original_text,
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
