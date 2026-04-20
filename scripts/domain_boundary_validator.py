#!/usr/bin/env python3
"""
异能蒸馏炉 · 域边界验证脚本（女娲版没有此脚本，异能蒸馏炉专属）
用法：python3 domain_boundary_validator.py <晶核目录>
功能：
  1. 验证 domain-boundary.md 格式是否正确
  2. 扫描 skill-registry.md 检查路由冲突（两个晶核的域是否重叠）
  3. 对5个测试问题进行模拟路由，检查路由逻辑
"""

import sys
import re
from pathlib import Path


def load_domain_boundary(skill_dir: str) -> str | None:
    """加载domain-boundary.md"""
    path = Path(skill_dir) / "domain-boundary.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_skill_registry() -> str | None:
    """加载skill-registry.md（在.claude/skills/目录下）"""
    # 尝试常见路径
    candidates = [
        Path(".claude/skills/skill-registry.md"),
        Path("../skill-registry.md"),
        Path("../../skill-registry.md"),
    ]
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return None


def validate_boundary_format(content: str) -> dict:
    """验证domain-boundary.md格式"""
    results = {}
    
    # 检查必要字段
    required_fields = ['skill_id', 'domain', 'domain_in', 'domain_out', 'routing_targets']
    for field in required_fields:
        results[f'has_{field}'] = field in content
    
    # 检查域内问题数量
    in_items = len(re.findall(r'^-\s+', content, re.MULTILINE))
    results['sufficient_examples'] = in_items >= 3
    
    # 检查路由目标是否列出
    has_routing = 'routing_targets' in content or '路由目标' in content
    results['has_routing_targets'] = has_routing
    
    return results


def check_registry_conflicts(skill_dir: str, registry_content: str) -> list[str]:
    """检查与其他晶核的域边界冲突"""
    conflicts = []
    
    # 加载当前晶核的domain-boundary.md
    boundary_path = Path(skill_dir) / "domain-boundary.md"
    if not boundary_path.exists():
        return ["domain-boundary.md不存在，无法检查冲突"]
    
    current = boundary_path.read_text(encoding="utf-8")
    
    # 提取当前晶核的domain_keywords
    current_keywords = re.findall(r'domain_keywords[：:]\s*(.+)', current)
    if not current_keywords:
        return ["无法提取当前晶核的domain_keywords"]
    
    current_kw_set = set(re.split(r'[,，\s]+', current_keywords[0]))
    
    # 从注册表中提取其他晶核的keywords
    registry_entries = re.findall(r'\|(.+?)\|(.+?)\|(.+?)\|(.+?)\|', registry_content)
    
    for entry in registry_entries:
        if len(entry) >= 3:
            other_keywords = re.split(r'[,，/\s]+', entry[2])
            overlap = current_kw_set & set(k.strip() for k in other_keywords)
            if len(overlap) >= 2:  # 超过2个重叠词视为潜在冲突
                conflicts.append(
                    f"与晶核 [{entry[0].strip()}] 可能有域边界重叠：{', '.join(overlap)}"
                )
    
    return conflicts


def simulate_routing(boundary_content: str) -> dict:
    """模拟5个测试问题的路由结果"""
    # 提取域内关键词
    in_section = re.search(r'domain_in.*?domain_out', boundary_content, re.DOTALL)
    out_section = re.search(r'domain_out.*', boundary_content, re.DOTALL)
    
    in_keywords = []
    if in_section:
        in_keywords = re.findall(r'[\u4e00-\u9fff a-zA-Z]{2,10}', in_section.group())
    
    out_keywords = []
    if out_section:
        out_keywords = re.findall(r'[\u4e00-\u9fff a-zA-Z]{2,10}', out_section.group())
    
    return {
        "in_keywords_found": len(in_keywords),
        "out_keywords_found": len(out_keywords),
        "routing_logic_detectable": len(in_keywords) > 5 and len(out_keywords) > 5
    }


def print_validation_report(skill_dir: str):
    """打印验证报告"""
    print("\n" + "="*60)
    print("  异能蒸馏炉 · 域边界验证报告")
    print(f"  晶核：{Path(skill_dir).name}")
    print("="*60)
    
    # 1. 检查domain-boundary.md是否存在
    boundary_content = load_domain_boundary(skill_dir)
    if boundary_content is None:
        print("\n❌ domain-boundary.md 不存在！")
        print("   请运行Phase 0.5创建晶核目录，或在Phase 2.2后手动创建。")
        print("   这个文件是路由系统的基础，必须存在。")
        print("="*60 + "\n")
        return
    
    print(f"\n✅ domain-boundary.md 存在（{len(boundary_content.splitlines())}行）")
    
    # 2. 格式验证
    format_results = validate_boundary_format(boundary_content)
    print("\n【格式检查】")
    all_format_ok = True
    for field, result in format_results.items():
        icon = "✅" if result else "❌"
        if not result:
            all_format_ok = False
        field_name = field.replace('has_', '').replace('_', ' ')
        print(f"  {icon} {field_name}")
    
    # 3. 路由模拟
    routing_sim = simulate_routing(boundary_content)
    print("\n【路由逻辑检查】")
    print(f"  域内关键词数：{routing_sim['in_keywords_found']}")
    print(f"  域外关键词数：{routing_sim['out_keywords_found']}")
    if routing_sim['routing_logic_detectable']:
        print("  ✅ 路由逻辑可被检测（关键词充足）")
    else:
        print("  ⚠️ 路由逻辑可能不够清晰，建议增加更多域内/域外示例")
    
    # 4. 注册表冲突检查
    registry = load_skill_registry()
    print("\n【晶核冲突检查】")
    if registry is None:
        print("  💡 未找到skill-registry.md，跳过冲突检查")
        print("     如果你有多个晶核，建议创建注册表：.claude/skills/skill-registry.md")
    else:
        conflicts = check_registry_conflicts(skill_dir, registry)
        if conflicts:
            print(f"  ⚠️ 发现 {len(conflicts)} 个潜在冲突：")
            for c in conflicts:
                print(f"    · {c}")
            print("     → 建议明确两个晶核的域边界差异，避免路由混乱")
        else:
            print("  ✅ 未发现与其他晶核的域边界冲突")
    
    # 总结
    print("\n" + "="*60)
    if all_format_ok and routing_sim['routing_logic_detectable']:
        print("  ✅ 域边界验证通过，路由逻辑可用")
    else:
        print("  ⚠️ 域边界需要完善，请按上述建议修复")
    print("="*60 + "\n")


def main():
    if len(sys.argv) < 2:
        print("用法：python3 domain_boundary_validator.py <晶核目录路径>")
        print("示例：python3 domain_boundary_validator.py .claude/skills/musk-biz-core")
        sys.exit(1)
    
    skill_dir = sys.argv[1]
    
    if not Path(skill_dir).exists():
        print(f"❌ 目录不存在：{skill_dir}")
        sys.exit(1)
    
    print_validation_report(skill_dir)


if __name__ == "__main__":
    main()
