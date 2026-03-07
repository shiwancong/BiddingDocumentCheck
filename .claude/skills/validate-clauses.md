---
description: 验证已有条款清单的准确性
---

# 验证条款清单

验证已有的条款识别结果是否准确和完整。

## 使用方法

### 验证Python脚本输出的结果
```python
import sys
sys.path.insert(0, '.')

from src.orchestrator import BiddingDocumentOrchestrator

orch = BiddingDocumentOrchestrator()

# 先执行检查
result = orch.process("<文件路径>")

# 查看验证报告
if result['success']:
    report = orch.current_report
    validator = orch.validator

    # 生成详细报告
    detailed_report = validator.generate_report(report)
    print(detailed_report)

    # 查看具体问题
    for issue in report.issues:
        print(f"[{issue.severity.value}] {issue.category}: {issue.description}")
        if issue.suggestion:
            print(f"  建议: {issue.suggestion}")
```

### 验证外部文件
如果用户提供了JSON格式的条款清单：

```python
import json

# 读取外部条款清单
with open("<清单文件路径>", "r", encoding="utf-8") as f:
    external_clauses = json.load(f)

# 重新解析原文档进行对比
from src.orchestrator import BiddingDocumentOrchestrator

orch = BiddingDocumentOrchestrator()
doc = orch.parser.parse("<原文路径>")
clauses = orch.identifier.identify_all(doc)

# 对比结果
print(f"外部清单: {len(external_clauses)} 项")
print(f"系统识别: {len(clauses)} 项")

# 执行验证
report = orch.validator.validate(clauses, doc)
print(f"\n质量等级: {report.level}")
print(f"质量分数: {report.score:.1f}/100")
```
