# 招投标文件智能检查清单生成系统 - 基于AI能力

## 系统架构

```
用户交互层
    ↓
Claude Code Skills
    ↓
MCP服务器（文档处理）
    ↓
知识库（规则+示例）
    ↓
AI分析（Claude模型）
    ↓
检查清单输出
```

## 使用方法

### 方法1：使用Claude Code Skills

```bash
# 在Claude Code中执行
/check-bidding-doc 招标文件.docx
```

### 方法2：使用MCP工具

```bash
# 使用Jina MCP读取文档
# 使用Claude分析内容
```

### 方法3：直接对话

```
请帮我检查这个招标文件：招标文件.docx
识别其中的废标条款和建议性要求
```

## 核心组件

### 1. Claude Code Skills

位置：`.claude/skills/`

- `check-bidding-doc.md` - 主技能，一键检查招标文件
- `extract-clauses.md` - 提取条款
- `validate-clauses.md` - 验证条款
- `compare-versions.md` - 对比版本

### 2. 知识库

位置：`data/knowledge/`

- `rules.md` - 识别规则和关键词库
- `examples.md` - 典型示例和处理技巧

### 3. MCP配置

位置：`mcp-config.json`

配置Jina MCP服务器用于文档处理。

## AI能力说明

本系统基于Claude的AI能力，无需复杂代码：

1. **文档理解**：Claude能够理解复杂的招标文件内容
2. **模式识别**：识别8种废标条款类型
3. **逻辑推理**：分析跨章节关联和条件句
4. **知识运用**：运用招投标领域知识
5. **结构化输出**：生成规范的检查清单表格

## 处理流程

```
输入：招标文件（.docx/.pdf）
  ↓
步骤1：文档解析
  - 使用MCP读取文档内容
  - 提取段落、表格、页码
  ↓
步骤2：条款识别
  - 扫描8种废标条款类型
  - 应用知识库规则
  - 使用Few-Shot学习
  ↓
步骤3：条款分类
  - 按照9种类型分类
  - 提取检查项
  ↓
步骤4：生成输出
  - 废标风险检查表
  - 建议项清单表
  ↓
输出：Markdown格式检查清单
```

## 优势

1. **无需编码**：基于AI能力，无需复杂Python代码
2. **易于维护**：规则存储在知识库中，方便更新
3. **可扩展性**：通过添加示例不断学习
4. **准确性高**：AI理解能力强，识别准确
5. **可解释性**：每个条款都有清晰的逻辑解释

## 配置要求

### Claude Code
需要安装Claude Code CLI

### MCP服务器（可选）
```bash
# 安装Jina MCP
npx -y @jina/mcp-server
```

### 知识库
已预配置在 `data/knowledge/` 目录

## 质量标准

- **C级**：识别全部明确写出的废标条款
- **B级**：C级 + 其他类型识别60%以上 + 标注页码
- **A级**：B级 + 其他类型识别90%以上 + 参考页码和额外说明
- **S级**：A级 + 所有条款正确识别 + 多文档测试通过

## 技术栈

- **AI模型**：Claude（无需额外安装）
- **文档处理**：Jina MCP（可选）
- **知识存储**：Markdown文件
- **配置**：JSON文件

## 文件结构

```
BiddingDocumentCheck/
├── .claude/
│   └── skills/           # Claude Code Skills
│       ├── check-bidding-doc.md
│       ├── extract-clauses.md
│       ├── validate-clauses.md
│       └── compare-versions.md
├── data/
│   └── knowledge/        # 知识库
│       ├── rules.md      # 识别规则
│       └── examples.md   # 示例库
├── mcp-config.json      # MCP配置
└── README-AI.md         # 本文件
```

## 使用示例

### 示例1：一键检查

```
用户: /check-bidding-doc 招标文件.docx

Claude:
正在处理招标文件...

已识别废标条款：16项
已识别建议性要求：8项

生成检查清单：data/output/检查清单.md
```

### 示例2：提取特定类型条款

```
用户: 提取所有签字盖章类的废标条款

Claude:
已提取签字盖章类废标条款：
1. 按规定签字盖章
2. 法定代表人签字
...
```

### 示例3：验证已有清单

```
用户: 验证这个清单是否正确：清单.json

Claude:
正在验证...

发现2个问题：
1. 条款"XXX"的分类可能有误
2. 缺少参考页码

建议修正...
```

## 维护指南

### 更新知识库

1. **更新规则**：编辑 `data/knowledge/rules.md`
2. **添加示例**：编辑 `data/knowledge/examples.md`
3. **立即生效**：Claude会自动使用最新知识

### 添加新Skill

1. 在 `.claude/skills/` 创建新文件
2. 按照格式编写Skill说明
3. 重启Claude Code即可使用

### 配置MCP

1. 编辑 `mcp-config.json`
2. 添加新的MCP服务器配置
3. 在Claude Code中启用

## 注意事项

1. **原文摘录**：必须直接摘录，不可改写
2. **页码准确**：确保页码标注准确
3. **逻辑清晰**：逻辑解释要通俗易懂
4. **参考完整**：需要参考的要标注参考页码
5. **分类准确**：按照9种类型准确分类

## 故障排除

### 问题1：文档无法读取

**解决方案**：
- 检查文件格式是否支持（.docx/.pdf）
- 尝试使用MCP文档处理工具
- 转换文件格式后重试

### 问题2：识别不完整

**解决方案**：
- 检查知识库规则是否完整
- 添加更多示例到示例库
- 使用Few-Shot提示

### 问题3：分类错误

**解决方案**：
- 查看 `data/knowledge/rules.md` 中的分类规则
- 在对话中明确分类依据
- 添加更多分类示例

## 扩展方向

1. **多语言支持**：添加英文等其他语言规则
2. **行业定制**：针对不同行业定制规则
3. **历史学习**：记录历史案例，持续优化
4. **批量处理**：支持批量检查多个文件
