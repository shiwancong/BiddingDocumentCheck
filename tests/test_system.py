"""
测试脚本
用于验证招投标文件智能检查系统的功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_with_sample_document():
    """使用示例文档进行测试"""
    from src.orchestrator import BiddingDocumentOrchestrator

    print("="*60)
    print("招投标文件智能检查系统 - 测试")
    print("="*60)

    # 查找测试文档（使用glob避免编码问题）
    project_root = Path(__file__).parent.parent

    # 查找docx文件
    docx_files = list(project_root.glob("*.docx"))

    # 过滤掉测试文件本身（如果有的话）
    test_files = [f for f in docx_files if "题" not in f.name]

    if not test_files:
        print(f"\n错误: 未找到测试文档")
        print("\n请将测试文档放在项目根目录下")
        return False

    test_doc = test_files[0]

    print(f"\n使用测试文档: {test_doc.name}")

    # 创建主控Agent
    orchestrator = BiddingDocumentOrchestrator()

    # 执行检查
    print("\n开始处理...")
    result = orchestrator.process(
        str(test_doc),
        include_suggestions=True,
        save_intermediate=True
    )

    if result['success']:
        print("\n" + "="*60)
        print("测试结果")
        print("="*60)

        summary = result['summary']
        print(f"\n质量等级: {summary['level']}")
        print(f"质量分数: {summary['score']:.1f}/100")
        print(f"\n条款统计:")
        print(f"  - 废标条款: {summary['disqualification_count']} 项")
        print(f"  - 建议性要求: {summary['suggestion_count']} 项")
        print(f"  - 总条款数: {summary['total_clauses']} 项")

        # 显示各阶段统计
        stages = result.get('stages', {})

        if 'parsing' in stages:
            parsing = stages['parsing']
            print(f"\n文档解析:")
            print(f"  - 文件类型: {test_doc.suffix}")
            print(f"  - 总页数: {parsing.get('total_pages', 'N/A')}")
            print(f"  - 段落数: {parsing.get('paragraphs_count', 'N/A')}")
            print(f"  - 表格数: {parsing.get('tables_count', 'N/A')}")

        if 'identification' in stages:
            ident = stages['identification']
            print(f"\n条款识别:")
            print(f"  - 条款类型分布:")
            for sub_type, count in ident.get('sub_types', {}).items():
                print(f"      * {sub_type}: {count} 项")

        if 'validation' in stages:
            val = stages['validation']
            print(f"\n质量验证:")
            print(f"  - 等级: {val.get('level', 'N/A')}")
            print(f"  - 分数: {val.get('score', 'N/A')}")
            print(f"  - 问题数: {val.get('issues_count', 0)}")

        # 显示输出文件
        print(f"\n输出文件位置: {orchestrator.output_dir}")
        output_files = list(orchestrator.output_dir.glob("*"))
        if output_files:
            print("\n生成的文件:")
            for f in sorted(output_files):
                print(f"  - {f.name}")

        # 测试一些额外功能
        print("\n" + "="*60)
        print("功能测试")
        print("="*60)

        # 测试按类型获取条款
        print("\n1. 测试按类型获取条款...")
        disqualification = orchestrator.get_clauses_by_type("废标条款")
        print(f"   [OK] 获取到 {len(disqualification)} 个废标条款")

        # 测试按分类获取条款
        print("\n2. 测试按分类获取条款...")
        sign_seal = orchestrator.get_clauses_by_category("签字盖章")
        print(f"   [OK] 签字盖章类: {len(sign_seal)} 项")

        # 测试条款统计
        print("\n3. 条款分类统计:")
        categories = {}
        for clause in orchestrator.current_clauses:
            cat = clause.category.value
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {cat}: {count} 项")

        # 评估是否达到S级标准
        print("\n" + "="*60)
        print("等级评估")
        print("="*60)

        level = summary['level']
        score = summary['score']

        if 'S' in level:
            print("\n[恭喜!] 系统已达到S级标准!")
            print("   - 所有废标条款正确识别")
            print("   - 质量分数达标")
            print("   建议：用更多测试文档验证以确保稳定性")
        elif 'A' in level:
            print("\n[OK] 系统达到A级标准")
            print("   - 识别率超过90%")
            print(f"   - 当前分数: {score:.1f}/100")
            print("   建议：检查验证报告，优化后可达S级")
        elif 'B' in level:
            print("\n[INFO] 系统达到B级标准")
            print(f"   - 当前分数: {score:.1f}/100")
            print("   建议：查看验证报告，修复标注问题")
        else:
            print("\n[WARN] 系统当前为C级")
            print(f"   - 当前分数: {score:.1f}/100")
            print("   建议：查看验证报告，优化识别逻辑")

        return True

    else:
        print(f"\n[FAIL] 测试失败: {result.get('error')}")
        return False


def run_unit_tests():
    """运行单元测试"""
    print("\n" + "="*60)
    print("单元测试")
    print("="*60)

    # 测试1: 配置加载
    print("\n1. 测试配置加载...")
    try:
        from src.config import DISQUALIFICATION_KEYWORDS, CLAUSE_TYPES
        print(f"   [OK] 废标关键词: {len(DISQUALIFICATION_KEYWORDS)} 个")
        print(f"   [OK] 条款分类: {len(CLAUSE_TYPES)} 种")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        return False

    # 测试2: Agent初始化
    print("\n2. 测试Agent初始化...")
    try:
        from src.agents import DocumentParserAgent, ClauseIdentifierAgent, QualityValidatorAgent
        parser = DocumentParserAgent()
        identifier = ClauseIdentifierAgent()
        validator = QualityValidatorAgent()
        print("   [OK] 所有Agent初始化成功")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        return False

    # 测试3: 主控Agent
    print("\n3. 测试主控Agent...")
    try:
        from src.orchestrator import BiddingDocumentOrchestrator
        orch = BiddingDocumentOrchestrator()
        print("   [OK] 主控Agent初始化成功")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        return False

    print("\n[OK] 所有单元测试通过")
    return True


def main():
    """主测试函数"""
    import argparse

    parser = argparse.ArgumentParser(description="测试招投标文件智能检查系统")
    parser.add_argument("--unit", action="store_true", help="只运行单元测试")
    parser.add_argument("--file", help="指定测试文件路径")

    args = parser.parse_args()

    # 运行单元测试
    if not run_unit_tests():
        sys.exit(1)

    # 运行集成测试
    if not args.unit:
        if args.file:
            # 使用指定文件测试
            from src.orchestrator import BiddingDocumentOrchestrator
            orch = BiddingDocumentOrchestrator()
            result = orch.process(args.file)
            sys.exit(0 if result['success'] else 1)
        else:
            # 使用示例文档测试
            if not test_with_sample_document():
                sys.exit(1)

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    main()
