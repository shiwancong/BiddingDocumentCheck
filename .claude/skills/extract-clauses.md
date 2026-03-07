---
description: 从招标文件中提取条款（废标条款或建议性要求）
---

# 提取招标文件条款

从招标文件中提取废标条款或建议性要求。

## 使用方法

### 基本用法
```python
import sys
sys.path.insert(0, '.')

from src.orchestrator import BiddingDocumentOrchestrator

orch = BiddingDocumentOrchestrator()

# 先解析文档
doc = orch.parser.parse("<文件路径>")

# 识别条款（只提取废标条款）
clauses = orch.identifier.identify_all(
    doc,
    include_suggestions=False  # False=只提取废标条款, True=包含建议性要求
)

# 输出结果
print(f"识别到 {len(clauses)} 个废标条款")
for clause in clauses:
    print(f"- [{clause.category.value}] {clause.check_item}")
```

### 按类型过滤
```python
# 只获取废标条款
disqualification = [c for c in clauses if c.clause_type.value == "废标条款"]

# 只获取建议性要求
suggestions = [c for c in clauses if c.clause_type.value == "建议性要求"]

# 按分类获取
sign_seal = [c for c in clauses if c.category.value == "签字盖章"]
```

### 保存结果
```python
# 保存为JSON
orch.identifier.save_to_json(clauses, "output.json")

# 保存为Markdown
markdown = orch.identifier.to_markdown_table(clauses)
with open("output.md", "w", encoding="utf-8") as f:
    f.write(markdown)
```
