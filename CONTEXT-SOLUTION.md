# 上下文窗口限制 - 解决方案指南

## 问题说明

当出现 `API Error: The model has reached its context window limit` 错误时，说明：
- Skill 提示词 + 知识库 + 招标文件内容超过了模型的上下文窗口
- 需要减少单次处理的文本量

## 快速解决方案

### 方案1：使用精简版 Skill（推荐首选）

```
/check-bidding-doc-v2 招标文件.docx
```

**特点**：
- Skill 文件从 550 行精简到 60 行
- 核心规则存储在独立的知识库文件
- 适合中等大小文档（<50KB）

### 方案2：分块处理大文档

```
/process-chunk 招标文件.docx
```

**特点**：
- 自动将大文档分块处理
- 按章节或页码范围分块
- 最后自动合并结果
- 适合大型文档（>50KB 或 >30页）

### 方案3：手动分块处理

如果上述方案仍不奏效，可以手动指定处理范围：

```
# 第一部分
/process-chunk 招标文件.docx --范围=1-30页

# 第二部分
/process-chunk 招标文件.docx --范围=31-60页
```

## Skill 对比

| Skill | 文件大小 | 适用文档 | 使用命令 |
|-------|---------|---------|---------|
| check-bidding-doc | ~550行 | 小文档(<20KB) | `/check-bidding-doc` |
| check-bidding-doc-v2 | ~60行 | 中文档(20-50KB) | `/check-bidding-doc-v2` |
| process-chunk | ~80行 | 大文档(>50KB) | `/process-chunk` |

## 新增文件

```
BiddingDocumentCheck/
├── .claude/skills/
│   ├── check-bidding-doc-v2/    # 精简版 Skill
│   │   └── SKILL.md
│   └── process-chunk/            # 分块处理 Skill
│       └── SKILL.md
└── data/knowledge/
    ├── rules-core.md             # 核心规则（精简版）
    └── config/
        └── context-management.md # 上下文管理配置
```

## 错误恢复步骤

如果遇到上下文限制错误：

1. **清除对话历史**
   ```
   开始新对话或使用 /clear
   ```

2. **使用精简版 Skill**
   ```
   /check-bidding-doc-v2 招标文件.docx
   ```

3. **如果仍失败，使用分块处理**
   ```
   /process-chunk 招标文件.docx
   ```

## 最佳实践

### 选择合适的 Skill

```
┌─────────────────────────────────────────────────────┐
│  文档大小检测                                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  < 20KB          │  /check-bidding-doc             │
│  (小文档)        │  (完整版 Skill)                 │
│                                                     │
│  20KB - 50KB     │  /check-bidding-doc-v2          │
│  (中等文档)      │  (精简版 Skill)                 │
│                                                     │
│  > 50KB          │  /process-chunk                 │
│  (大文档)        │  (分块处理)                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 优化建议

1. **定期清理对话历史**
   - 处理完一个文档后，开始新对话
   - 避免历史内容累积

2. **使用输出文件**
   - 结果保存到本地文件
   - 减少上下文中的重复内容

3. **分批处理**
   - 超大文档可以分多次处理
   - 手动合并结果

## 技术说明

### 上下文窗口大小

| 模型 | 上下文窗口 |
|------|-----------|
| Claude Opus 4.5 | 200K tokens |
| Claude Sonnet 4 | 200K tokens |
| Claude Haiku 4 | 200K tokens |

### 内存估算

- 1 token ≈ 0.75 个汉字
- 200K tokens ≈ 150K 汉字 ≈ 300KB 文本

**安全预留**：建议只使用 70% 的上下文窗口，留出空间给响应。

## 检查清单

使用前检查：

- [ ] 确认文档大小
- [ ] 选择合适的 Skill
- [ ] 清理对话历史
- [ ] 确保有足够的上下文空间

使用后检查：

- [ ] 结果完整性
- [ ] 是否有遗漏章节
- [ ] Excel 文件是否正常生成
