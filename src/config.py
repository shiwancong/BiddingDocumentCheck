"""
招投标文件智能检查清单生成系统
配置文件
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
OUTPUT_DIR = DATA_DIR / "output"
TEST_DIR = DATA_DIR / "test"

# 确保目录存在
for dir_path in [DATA_DIR, KNOWLEDGE_DIR, OUTPUT_DIR, TEST_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 废标条款关键词库
DISQUALIFICATION_KEYWORDS = [
    "投标将被否决",
    "投标无效",
    "作无效投标处理",
    "不予接受",
    "不进入评审",
    "视为无效投标",
    "拒绝投标",
    "将被拒绝",
    "将被认定为无效",
    "作无效处理",
    "否决其投标",
    "其投标将被否决",
    "投标将被认定为无效"
]

# 建议性要求关键词（非强制）
SUGGESTION_KEYWORDS = [
    "建议",
    "原则上",
    "推荐",
    "最好",
    "可以",
    "鼓励",
    "宜"
]

# 强制性表述关键词
MANDATORY_KEYWORDS = [
    "必须",
    "应当",
    "不得",
    "严禁",
    "必需",
    "需要"
]

# 条件标记词
CONDITION_KEYWORDS = [
    "如果",
    "若",
    "当",
    "在...情况下",
    "如",
    "一旦"
]

# 反常识废标项特征库
ANTI_COMMON_SENSE_PATTERNS = {
    "字体要求": ["字体", "宋体", "黑体", "楷体", "字体大小"],
    "文件大小": ["文件大小", "不超过.*MB", "不得超过.*MB"],
    "文件命名": ["命名", "文件名", "命名格式"],
    "目录顺序": ["目录顺序", "按顺序", "装订顺序"],
    "扫描清晰度": ["清晰", "可辨", "扫描件"],
    "装订方式": ["装订", "胶装", "线装"],
    "页码格式": ["页码", "页码格式"],
    "行间距": ["行距", "行间距"]
}

# 条款类型分类
CLAUSE_TYPES = {
    "资格": "投标人主体资格、资质、业绩、人员条件",
    "文件": "是否提供某一文件或材料",
    "签字盖章": "签字、盖章、签署主体",
    "时间方式": "递交时间、截止时间、投标方式",
    "报价算术": "报价计算错误、大小写不一致等",
    "响应性": "是否实质性响应招标文件",
    "格式": "页码、装订、密封、排版",
    "模板": "是否使用指定模板、是否擅自修改模板",
    "其他": "无法归入上述类别的情况"
}

# 表格中需要关注的列名
TABLE_KEY_COLUMNS = [
    "不满足后果",
    "不符合处理方式",
    "评审结论",
    "处理方式",
    "验收标准",
    "否决条件"
]

# 支持的文件类型
SUPPORTED_FILE_TYPES = ['.docx', '.doc', '.pdf']

# 输出格式配置
OUTPUT_COLUMNS = [
    "检查项",
    "类型",
    "原文页码",
    "原文关键信息",
    "逻辑解释",
    "参考页码",
    "额外说明"
]
