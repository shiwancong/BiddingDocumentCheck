"""
MCP服务器
提供招投标文件检查的核心能力
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

# MCP SDK
try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
except ImportError:
    # 如果没有安装MCP SDK，提供模拟接口
    class Server:
        def __init__(self, name: str, version: str):
            self.name = name
            self.version = version

        async def list_tools(self):
            return []

        async def call_tool(self, name, arguments):
            return []

    class InitializationOptions:
        pass

    class NotificationOptions:
        pass

    stdio_server = None

# 导入核心模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from orchestrator import BiddingDocumentOrchestrator
from config import DISQUALIFICATION_KEYWORDS, CLAUSE_TYPES


# 创建MCP服务器实例
server = Server("bidding-doc-check", "1.0.0")

# 全局状态
orchestrator: Optional[BiddingDocumentOrchestrator] = None


def get_orchestrator() -> BiddingDocumentOrchestrator:
    """获取或创建主控Agent实例"""
    global orchestrator
    if orchestrator is None:
        output_dir = Path.cwd() / "data" / "output"
        orchestrator = BiddingDocumentOrchestrator(str(output_dir))
    return orchestrator


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """列出可用的资源"""
    return [
        Resource(
            uri="file:///knowledge/keywords",
            name="废标关键词库",
            description="招投标文件中用于识别废标条款的关键词列表",
            mimeType="application/json",
        ),
        Resource(
            uri="file:///knowledge/categories",
            name="条款分类定义",
            description="条款分类的类型定义和说明",
            mimeType="application/json",
        ),
        Resource(
            uri="file:///knowledge/anti_common_sense",
            name="反常识废标项库",
            description="容易被忽略的非常规废标条款特征",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """读取资源内容"""
    if uri == "file:///knowledge/keywords":
        return json.dumps({
            "disqualification_keywords": DISQUALIFICATION_KEYWORDS,
            "description": "废标条款关键词列表",
            "updated_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)

    elif uri == "file:///knowledge/categories":
        return json.dumps({
            "categories": CLAUSE_TYPES,
            "description": "条款分类定义",
            "updated_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)

    elif uri == "file:///knowledge/anti_common_sense":
        from config import ANTI_COMMON_SENSE_PATTERNS
        return json.dumps({
            "patterns": ANTI_COMMON_SENSE_PATTERNS,
            "description": "反常识废标项特征库",
            "updated_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)

    else:
        return json.dumps({"error": "Resource not found"}, ensure_ascii=False)


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="parse_document",
            description="解析招标文件（支持docx/pdf），提取结构化内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "招标文件路径（支持.docx, .doc, .pdf）"
                    },
                    "save_intermediate": {
                        "type": "boolean",
                        "description": "是否保存中间解析结果",
                        "default": True
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="identify_clauses",
            description="从解析后的文档中识别废标条款和建议性要求",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "招标文件路径（如果已解析则使用缓存）"
                    },
                    "include_suggestions": {
                        "type": "boolean",
                        "description": "是否包含建议性要求",
                        "default": True
                    },
                    "clause_type_filter": {
                        "type": "string",
                        "description": "过滤条款类型：disqualification(废标)/suggestion(建议)/all(全部)",
                        "default": "all"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="validate_clauses",
            description="验证条款识别结果的准确性和完整性",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "招标文件路径"
                    },
                    "strict_mode": {
                        "type": "boolean",
                        "description": "严格模式（要求100%准确）",
                        "default": True
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="check_document",
            description="一键执行完整的文档检查流程（解析→识别→验证→输出）",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "招标文件路径"
                    },
                    "include_suggestions": {
                        "type": "boolean",
                        "description": "是否包含建议性要求",
                        "default": True
                    },
                    "save_intermediate": {
                        "type": "boolean",
                        "description": "是否保存中间结果",
                        "default": True
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="search_keyword",
            description="在文档中搜索关键词，返回匹配的段落和页码",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "招标文件路径"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "要搜索的关键词"
                    }
                },
                "required": ["file_path", "keyword"]
            }
        ),
        Tool(
            name="get_statistics",
            description="获取文档和条款识别的统计信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "招标文件路径"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="export_report",
            description="导出检查报告（支持Markdown、JSON、Excel格式）",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "招标文件路径"
                    },
                    "format": {
                        "type": "string",
                        "description": "导出格式：markdown/json/excel",
                        "default": "markdown"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "输出文件路径（可选，默认使用默认路径）"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="add_keyword",
            description="向关键词库添加新的废标关键词（动态学习）",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "要添加的关键词"
                    },
                    "category": {
                        "type": "string",
                        "description": "关键词类别：disqualification/suggestion/mandatory",
                        "default": "disqualification"
                    }
                },
                "required": ["keyword"]
            }
        ),
        Tool(
            name="get_result",
            description="获取最近一次检查的结果（条款列表、验证报告等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "result_type": {
                        "type": "string",
                        "description": "结果类型：clauses/validation/summary",
                        "default": "summary"
                    },
                    "filter": {
                        "type": "string",
                        "description": "过滤条件（如按类型、分类筛选）",
                        "default": ""
                    }
                }
            }
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    """处理工具调用"""

    try:
        if name == "parse_document":
            orch = get_orchestrator()
            doc = orch.parser.parse(arguments["file_path"])

            result = {
                "success": True,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "total_pages": doc.total_pages,
                "paragraphs_count": len(doc.paragraphs),
                "tables_count": len(doc.tables),
                "sections_count": len(doc.sections)
            }

            if arguments.get("save_intermediate", True):
                import json
                output_dir = Path.cwd() / "data" / "output"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{Path(arguments['file_path']).stem}_parsed.json"
                orch.parser.save_to_json(doc, str(output_path))
                result["saved_to"] = str(output_path)

            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        elif name == "identify_clauses":
            orch = get_orchestrator()

            # 确保文档已解析
            if orch.current_doc is None or orch.current_doc.filename != Path(arguments["file_path"]).name:
                orch.current_doc = orch.parser.parse(arguments["file_path"])

            clauses = orch.identifier.identify_all(
                orch.current_doc,
                include_suggestions=arguments.get("include_suggestions", True)
            )

            # 应用过滤
            filter_type = arguments.get("clause_type_filter", "all")
            if filter_type == "disqualification":
                clauses = [c for c in clauses if c.clause_type.value == "废标条款"]
            elif filter_type == "suggestion":
                clauses = [c for c in clauses if c.clause_type.value == "建议性要求"]

            orch.current_clauses = clauses

            result = {
                "success": True,
                "total_clauses": len(clauses),
                "disqualification_count": len([c for c in clauses if c.clause_type.value == "废标条款"]),
                "suggestion_count": len([c for c in clauses if c.clause_type.value == "建议性要求"]),
                "clauses": [
                    {
                        "check_item": c.check_item,
                        "type": c.category.value,
                        "clause_type": c.clause_type.value,
                        "page": c.original_page,
                        "sub_type": c.sub_type
                    }
                    for c in clauses[:20]  # 限制返回数量
                ]
            }

            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        elif name == "validate_clauses":
            orch = get_orchestrator()

            # 确保有数据可验证
            if orch.current_doc is None or orch.current_clauses is None:
                # 先执行解析和识别
                orch.process(arguments["file_path"], save_intermediate=False)

            report = orch.validator.validate(
                orch.current_clauses,
                orch.current_doc,
                strict_mode=arguments.get("strict_mode", True)
            )

            orch.current_report = report

            result = {
                "success": True,
                "level": report.level,
                "score": report.score,
                "total_clauses": report.total_clauses,
                "disqualification_count": report.disqualification_count,
                "suggestion_count": report.suggestion_count,
                "issues_count": len(report.issues),
                "issues": [
                    {
                        "severity": i.severity.value,
                        "category": i.category,
                        "description": i.description,
                        "suggestion": i.suggestion
                    }
                    for i in report.issues[:10]
                ]
            }

            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        elif name == "check_document":
            orch = get_orchestrator()
            result = orch.process(
                arguments["file_path"],
                include_suggestions=arguments.get("include_suggestions", True),
                save_intermediate=arguments.get("save_intermediate", True)
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        elif name == "search_keyword":
            orch = get_orchestrator()

            # 确保文档已解析
            if orch.current_doc is None or orch.current_doc.filename != Path(arguments["file_path"]).name:
                orch.current_doc = orch.parser.parse(arguments["file_path"])

            results = orch.parser.search_by_keyword(orch.current_doc, arguments["keyword"])

            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "keyword": arguments["keyword"],
                    "matches": len(results),
                    "results": results[:10]  # 限制返回数量
                }, ensure_ascii=False, indent=2)
            )]

        elif name == "get_statistics":
            orch = get_orchestrator()

            # 确保文档已处理
            if orch.current_doc is None or orch.current_doc.filename != Path(arguments["file_path"]).name:
                orch.process(arguments["file_path"], save_intermediate=False)

            stats = {
                "success": True,
                "document": {
                    "filename": orch.current_doc.filename,
                    "file_type": orch.current_doc.file_type,
                    "total_pages": orch.current_doc.total_pages,
                    "paragraphs_count": len(orch.current_doc.paragraphs),
                    "tables_count": len(orch.current_doc.tables),
                    "sections_count": len(orch.current_doc.sections)
                },
                "clauses": {
                    "total": len(orch.current_clauses) if orch.current_clauses else 0,
                    "by_type": {},
                    "by_category": {},
                    "by_subtype": {}
                }
            }

            if orch.current_clauses:
                for clause in orch.current_clauses:
                    # 按类型统计
                    ct = clause.clause_type.value
                    stats["clauses"]["by_type"][ct] = stats["clauses"]["by_type"].get(ct, 0) + 1

                    # 按分类统计
                    cat = clause.category.value
                    stats["clauses"]["by_category"][cat] = stats["clauses"]["by_category"].get(cat, 0) + 1

                    # 按子类型统计
                    sub = clause.sub_type
                    stats["clauses"]["by_subtype"][sub] = stats["clauses"]["by_subtype"].get(sub, 0) + 1

            # 添加验证信息
            if orch.current_report:
                stats["validation"] = {
                    "level": orch.current_report.level,
                    "score": orch.current_report.score,
                    "issues_count": len(orch.current_report.issues)
                }

            return [TextContent(
                type="text",
                text=json.dumps(stats, ensure_ascii=False, indent=2)
            )]

        elif name == "export_report":
            orch = get_orchestrator()

            # 确保有数据可导出
            if orch.current_doc is None or orch.current_clauses is None:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "没有可导出的数据，请先执行检查"}, ensure_ascii=False)
                )]

            format_type = arguments.get("format", "markdown")
            output_dir = Path.cwd() / "data" / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            base_name = Path(arguments["file_path"]).stem

            if format_type == "markdown":
                content = orch._generate_final_report()
                output_path = output_dir / f"{base_name}_检查清单.md"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            elif format_type == "json":
                import json as json_lib
                data = {
                    "document": {
                        "filename": orch.current_doc.filename,
                        "total_pages": orch.current_doc.total_pages
                    },
                    "clauses": [
                        {
                            "check_item": c.check_item,
                            "type": c.category.value,
                            "clause_type": c.clause_type.value,
                            "page": c.original_page,
                            "original_text": c.original_text,
                            "logic_explanation": c.logic_explanation,
                            "reference_page": c.reference_page,
                            "extra_note": c.extra_note
                        }
                        for c in orch.current_clauses
                    ]
                }
                output_path = output_dir / f"{base_name}_检查清单.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json_lib.dump(data, f, ensure_ascii=False, indent=2)

            elif format_type == "excel":
                try:
                    orch.export_to_excel()
                    output_path = output_dir / f"{base_name}_检查清单.xlsx"
                except ImportError:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "导出Excel需要安装 pandas 和 openpyxl"}, ensure_ascii=False)
                    )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"不支持的格式: {format_type}"}, ensure_ascii=False)
                )]

            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "format": format_type,
                    "saved_to": str(output_path)
                }, ensure_ascii=False, indent=2)
            )]

        elif name == "add_keyword":
            keyword = arguments["keyword"]
            category = arguments.get("category", "disqualification")

            # 这里可以实现将关键词保存到知识库的逻辑
            # 简化实现：仅返回确认信息

            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"关键词'{keyword}'已添加到{category}类别",
                    "keyword": keyword,
                    "category": category
                }, ensure_ascii=False, indent=2)
            )]

        elif name == "get_result":
            orch = get_orchestrator()

            if orch.current_clauses is None:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "没有可用的结果，请先执行检查"}, ensure_ascii=False)
                )]

            result_type = arguments.get("result_type", "summary")
            filter_cond = arguments.get("filter", "")

            if result_type == "clauses":
                # 返回条款列表
                clauses = orch.current_clauses
                if filter_cond:
                    # 应用过滤
                    if filter_cond == "disqualification":
                        clauses = [c for c in clauses if c.clause_type.value == "废标条款"]
                    elif filter_cond == "suggestion":
                        clauses = [c for c in clauses if c.clause_type.value == "建议性要求"]

                result = {
                    "success": True,
                    "total": len(clauses),
                    "clauses": [
                        {
                            "check_item": c.check_item,
                            "type": c.category.value,
                            "clause_type": c.clause_type.value,
                            "page": c.original_page,
                            "original_text": c.original_text[:100],
                            "logic_explanation": c.logic_explanation
                        }
                        for c in clauses
                    ]
                }

            elif result_type == "validation":
                # 返回验证报告
                if orch.current_report is None:
                    result = {"error": "没有验证报告"}
                else:
                    result = {
                        "success": True,
                        "level": orch.current_report.level,
                        "score": orch.current_report.score,
                        "issues": [
                            {
                                "severity": i.severity.value,
                                "category": i.category,
                                "description": i.description,
                                "suggestion": i.suggestion
                            }
                            for i in orch.current_report.issues
                        ]
                    }

            else:  # summary
                # 返回摘要
                result = {
                    "success": True,
                    "summary": {
                        "document": orch.current_doc.filename if orch.current_doc else "N/A",
                        "total_clauses": len(orch.current_clauses),
                        "disqualification_count": len([c for c in orch.current_clauses if c.clause_type.value == "废标条款"]),
                        "suggestion_count": len([c for c in orch.current_clauses if c.clause_type.value == "建议性要求"]),
                        "level": orch.current_report.level if orch.current_report else "N/A",
                        "score": orch.current_report.score if orch.current_report else 0
                    }
                }

            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"未知的工具: {name}"}, ensure_ascii=False)
            )]

    except Exception as e:
        import traceback
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "traceback": traceback.format_exc()
            }, ensure_ascii=False, indent=2)
        )]


async def main():
    """启动MCP服务器"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="bidding-doc-check",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    if stdio_server is None:
        print("MCP SDK未安装。请运行: pip install mcp")
        print("或者直接使用主控Agent:")
        print("  from src.orchestrator import check_bidding_document")
        print("  result = check_bidding_document('招标文件.docx')")
    else:
        asyncio.run(main())
