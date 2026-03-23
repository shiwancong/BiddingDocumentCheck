# 上下文窗口管理配置

## 上下文控制策略

### 自动检测与适配

当检测到以下情况时，自动启用相应的处理模式：

| 场景 | 检测条件 | 处理策略 |
|------|---------|---------|
| **小文档** | 内容 < 20KB | 直接使用 check-bidding-doc |
| **中等文档** | 20KB <= 内容 < 50KB | 使用 check-bidding-doc-v2（精简版） |
| **大文档** | 内容 >= 50KB 或 >30页 | 使用 process-chunk 分块处理 |
| **超大文档** | 内容 > 200KB 或 >100页 | 分块 + 精简 Skill |

### 推荐使用方式

#### 小文档（<20KB）
```
/check-bidding-doc 招标文件.docx
```

#### 中等文档（20-50KB）
```
/check-bidding-doc-v2 招标文件.docx
```

#### 大文档（>50KB）
```
/process-chunk 招标文件.docx
```

## Skill 精简对比

| Skill | 内容大小 | 适用场景 |
|-------|---------|---------|
| check-bidding-doc | ~550行 | 小文档，需要详细指导 |
| check-bidding-doc-v2 | ~60行 | 中等文档，核心规则在知识库 |
| process-chunk | ~80行 | 大文档，分块处理 |

## 内存优化技巧

### 1. 按需加载知识库

不要一次性加载所有知识库文件：
- 核心规则：`rules-core.md`（约100行）
- 详细规则：`rules.md`（仅在需要时读取）
- 示例：`examples.md`（仅在遇到疑难时读取）

### 2. 分块处理参数

```python
# 分块建议参数
MAX_CHUNK_SIZE = 3000  # 每块最大字数
MAX_PAGES_PER_CHUNK = 20  # 每块最大页数
OVERLAP_SIZE = 100  # 块之间重叠字数（避免边界遗漏）
```

### 3. 输出优化

- 先输出中间结果到临时文件
- 使用增量式构建最终报告
- 避免在上下文中重复存储相同内容

## 错误恢复

如果遇到 "context window limit" 错误：

1. **重试**：切换到精简版 Skill
2. **分块**：使用 process-chunk 重新处理
3. **清理**：清除对话历史中的冗余内容
4. **分段**：手动指定处理范围（如"先处理前30页"）

## 配置建议

### Claude Code 配置

在 `.claude/settings.local.json` 中：

```json
{
  "maxContextTokens": 180000,
  "preferredModel": "claude-opus-4-5-20251101"
}
```

### MCP 配置优化

如果使用 MCP 处理文档：
- 设置合理的文档提取限制
- 使用增量式读取
- 缓存已处理内容
