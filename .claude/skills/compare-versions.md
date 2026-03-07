---
description: 对比不同版本的招标文件，识别差异条款
---

# 对比招标文件版本

对比两份不同版本的招标文件，识别条款差异。

## 使用方法

```python
import sys
sys.path.insert(0, '.')

from src.orchestrator import BiddingDocumentOrchestrator

orch = BiddingDocumentOrchestrator()

# 解析两份文件
doc1 = orch.parser.parse("<文件1路径>")
doc2 = orch.parser.parse("<文件2路径>")

# 识别条款
clauses1 = orch.identifier.identify_all(doc1)
clauses2 = orch.identifier.identify_all(doc2)

# 对比分析
print(f"文件1: {len(clauses1)} 个条款")
print(f"文件2: {len(clauses2)} 个条款")

# 找出差异
# 新增条款（在文件2中但不在文件1中）
check_items1 = {c.check_item for c in clauses1}
check_items2 = {c.check_item for c in clauses2}

new_clauses = [c for c in clauses2 if c.check_item not in check_items1]
removed_clauses = [c for c in clauses1 if c.check_item not in check_items2]

print(f"\n新增条款: {len(new_clauses)} 项")
for c in new_clauses[:5]:
    print(f"  + {c.check_item}")

print(f"\n删除条款: {len(removed_clauses)} 项")
for c in removed_clauses[:5]:
    print(f"  - {c.check_item}")

# 导出差异报告
diff_report = {
    "file1": doc1.filename,
    "file2": doc2.filename,
    "new_clauses": [{"item": c.check_item, "type": c.category.value} for c in new_clauses],
    "removed_clauses": [{"item": c.check_item, "type": c.category.value} for c in removed_clauses],
    "statistics": {
        "total_new": len(new_clauses),
        "total_removed": len(removed_clauses)
    }
}

import json
with open("diff_report.json", "w", encoding="utf-8") as f:
    json.dump(diff_report, f, ensure_ascii=False, indent=2)

print(f"\n差异报告已保存到: diff_report.json")
```

## 输出说明
- **新增条款**: 在新版本中添加的条款
- **删除条款**: 在新版本中移除的条款
- **变更条款**: 内容或类型发生变化的条款
