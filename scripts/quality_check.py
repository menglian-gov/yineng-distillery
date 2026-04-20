#!/usr/bin/env python3
"""
异能蒸馏炉 · 晶核质量自检脚本
用法：python3 quality_check.py <晶核SKILL.md路径>
输出：逐项 PASS/FAIL + 总评分 + 改进建议
"""

import sys
import re
from pathlib import Path


def load_skill(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"❌ 找不到文件：{path}")
        sys.exit(1)


def check_frontmatter(content: str) -> dict:
    """检查frontmatter的完整性"""
    results = {}
    fm_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        results['frontmatter_exists'] = (False, "缺少frontmatter")
        return results
    
    fm = fm_match.group(1)
    results['frontmatter_exists'] = (True, "frontmatter存在")
    results['has_domain'] = (
        'domain:' in fm,
        "有domain字段" if 'domain:' in fm else "缺少domain字段（能力域定义）"
    )
    results['has_domain_keywords'] = (
        'domain_keywords:' in fm,
        "有domain_keywords" if 'domain_keywords:' in fm else "缺少domain_keywords（触发词）"
    )
    results['has_routing'] = (
        'out_of_domain_routing:' in fm,
        "有out_of_domain_routing" if 'out_of_domain_routing:' in fm else "缺少路由目标字段"
    )
    return results


def check_domain_boundary(content: str) -> dict:
    """检查域边界定义的质量"""
    results = {}
    
    # 检查域边界section是否存在
    has_boundary = '域边界' in content or '域内' in content
    results['has_domain_section'] = (
        has_boundary,
        "有域边界声明" if has_boundary else "⚠️ 缺少域边界声明（最重要的section）"
    )
    
    # 检查域内问题数量
    domain_in_matches = re.findall(r'域内.{0,200}', content)
    in_count = sum(1 for m in domain_in_matches if len(m) > 20)
    results['domain_in_examples'] = (
        in_count >= 3,
        f"域内示例：{in_count}个{'（合格，需≥3）' if in_count >= 3 else '（不足，需≥3）'}"
    )
    
    # 检查域外问题数量
    domain_out_matches = re.findall(r'域外.{0,200}', content)
    out_count = sum(1 for m in domain_out_matches if len(m) > 20)
    results['domain_out_examples'] = (
        out_count >= 3,
        f"域外示例：{out_count}个{'（合格，需≥3）' if out_count >= 3 else '（不足，需≥3）'}"
    )
    
    # 检查路由话术
    has_routing_speech = '路由话术' in content or '超出了我的' in content
    results['has_routing_speech'] = (
        has_routing_speech,
        "有路由话术模板" if has_routing_speech else "⚠️ 缺少路由话术（域外拒绝时的标准回应）"
    )
    
    return results


def check_three_layers(content: str) -> dict:
    """检查三层结构（感知/判断/行动）的完整性"""
    results = {}
    
    # 感知层
    has_perception = '感知层' in content or '感知维度' in content
    perception_dims = len(re.findall(r'维度\d|感知维度\d|关注信号', content))
    results['has_perception_layer'] = (
        has_perception,
        "有感知层" if has_perception else "⚠️ 缺少感知层"
    )
    results['perception_dimensions'] = (
        3 <= perception_dims <= 5,
        f"感知维度数量：{perception_dims}个{'（合格，应3-5个）' if 3 <= perception_dims <= 5 else '（不合格，需3-5个）'}"
    )
    
    # 判断层
    has_judgment = '判断层' in content or '心智模型' in content
    model_count = len(re.findall(r'#### 模型\d|### 模型\d|\*\*模型\d', content))
    if model_count == 0:
        model_count = len(re.findall(r'模型\d：|Model \d:', content))
    results['has_judgment_layer'] = (
        has_judgment,
        "有判断层" if has_judgment else "⚠️ 缺少判断层"
    )
    results['mental_model_count'] = (
        2 <= model_count <= 4,
        f"心智模型数量：{model_count}个{'（合格，应2-4个）' if 2 <= model_count <= 4 else '（不合格，需2-4个）'}"
    )
    
    # 决策启发式
    heuristic_count = len(re.findall(r'\d+\.\s+\*\*.*启发式|如果.*则.*案例', content))
    if heuristic_count == 0:
        heuristic_count = len(re.findall(r'^\d+\.\s+\*\*', content, re.MULTILINE))
    results['heuristic_count'] = (
        5 <= heuristic_count <= 8,
        f"决策启发式：{heuristic_count}条{'（合格，应5-8条）' if 5 <= heuristic_count <= 8 else '（不合格，需5-8条）'}"
    )
    
    # 反直觉判断
    has_counterintuitive = '反直觉' in content
    results['has_counterintuitive'] = (
        has_counterintuitive,
        "有反直觉判断" if has_counterintuitive else "建议：增加反直觉判断（通常是最有价值的部分）"
    )
    
    # 行动层
    has_action = '行动层' in content or '行动序列' in content
    results['has_action_layer'] = (
        has_action,
        "有行动层" if has_action else "⚠️ 缺少行动层"
    )
    
    return results


def check_expression_dna(content: str) -> dict:
    """检查表达DNA的完整性"""
    results = {}
    
    dna_fields = ['开场方式', '核心词汇', '禁忌词', '判断句式', '确定性风格']
    found_fields = sum(1 for f in dna_fields if f in content)
    
    results['dna_completeness'] = (
        found_fields >= 4,
        f"表达DNA完整度：{found_fields}/5个字段{'（合格）' if found_fields >= 4 else '（不足）'}"
    )
    
    return results


def check_failure_conditions(content: str) -> dict:
    """检查失效条件的质量"""
    results = {}
    
    has_failure = '失效条件' in content or '情境局限' in content
    results['has_failure_section'] = (
        has_failure,
        "有失效条件" if has_failure else "⚠️ 缺少失效条件（最常被忽略的关键section）"
    )
    
    # 计算失效条件数量
    failure_items = len(re.findall(r'^\d+\.\s+\*\*\[情境类型|^\d+\.\s+\*\*', content, re.MULTILINE))
    if '不可蒸馏的部分' in content:
        failure_items += 1
    if '先决条件' in content or '能力先决条件' in content:
        failure_items += 1
        
    results['failure_condition_count'] = (
        failure_items >= 5,
        f"失效条件数量：约{failure_items}条{'（合格，需≥5条）' if failure_items >= 5 else '（不足，需≥5条）'}"
    )
    
    has_undistillable = '不可蒸馏' in content
    results['has_undistillable_note'] = (
        has_undistillable,
        "有「不可蒸馏部分」说明" if has_undistillable else "建议：说明哪些部分无法被语言化蒸馏"
    )
    
    return results


def check_agentic_protocol(content: str) -> dict:
    """检查Agentic Protocol的质量"""
    results = {}
    
    has_protocol = 'Agentic Protocol' in content or '回答工作流' in content
    results['has_protocol'] = (
        has_protocol,
        "有Agentic Protocol" if has_protocol else "⚠️ 缺少回答工作流（AI不会主动使用工具）"
    )
    
    # Step 2的研究维度是否来自感知层（简单检测：是否有具体搜索方向）
    has_specific_research = bool(re.search(r'搜索：|搜.*数据|查.*结构|找.*案例', content))
    results['protocol_specificity'] = (
        has_specific_research,
        "Step2研究维度有具体搜索方向" if has_specific_research else "⚠️ Step2研究维度太通用，应基于感知层推导具体搜索方向"
    )
    
    return results


def check_related_abilities(content: str) -> dict:
    """检查相关能力图谱"""
    results = {}
    
    has_map = '相关能力图谱' in content or ('前置' in content and '后置' in content)
    results['has_ability_map'] = (
        has_map,
        "有相关能力图谱" if has_map else "建议：增加相关能力图谱（路由系统的基础）"
    )
    
    has_routing_types = all(t in content for t in ['前置', '后置', '协作'])
    results['map_completeness'] = (
        has_routing_types,
        "图谱包含前置/后置/协作" if has_routing_types else "建议：图谱应包含↑前置、↓后置、↔协作三种关系"
    )
    
    return results


def check_honest_boundary(content: str) -> dict:
    """检查诚实边界"""
    results = {}
    
    has_boundary = '诚实边界' in content
    results['has_honest_boundary'] = (
        has_boundary,
        "有诚实边界" if has_boundary else "⚠️ 缺少诚实边界"
    )
    
    has_date = bool(re.search(r'调研截止|调研时间|YYYY-MM|\d{4}-\d{2}', content))
    results['has_research_date'] = (
        has_date,
        "有调研时间标注" if has_date else "⚠️ 缺少调研时间（晶核可能已过期）"
    )
    
    has_confidence = '可信度评级' in content or '可信度：' in content
    results['has_confidence_rating'] = (
        has_confidence,
        "有可信度评级" if has_confidence else "建议：标注可信度评级（A/B/C）"
    )
    
    return results


def check_depth_vs_generic(content: str) -> dict:
    """检查深度：是否只是贴标签，还是真正蒸馏出了能力操作系统"""
    results = {}
    
    # 检查是否有「普通人会...但[来源者]会...」这类对比
    has_contrast = bool(re.search(r'普通人|常识|大多数人.{0,50}但|反而|不同的是', content))
    results['has_contrast_with_common'] = (
        has_contrast,
        "有与常识的对比描述" if has_contrast else "建议：增加与「普通人会怎么做」的对比，凸显能力的独特性"
    )
    
    # 检查是否有具体数字/门槛
    has_specifics = bool(re.search(r'\d+%|\d+倍|≥\d+|<\d+|>\d+', content))
    results['has_specific_thresholds'] = (
        has_specifics,
        "有具体数字/门槛" if has_specifics else "建议：增加具体的判断门槛（如「如果回报率<X，则」）"
    )
    
    # 检查是否有示例对话
    has_example = '示例对话' in content or '域内问题示例' in content
    results['has_example_dialogue'] = (
        has_example,
        "有示例对话" if has_example else "建议：增加示例对话（展示晶核激活后的真实工作方式）"
    )
    
    return results


def check_session_memory(content: str, skill_dir: str = None) -> dict:
    """检查v2.0会话记忆功能是否已集成"""
    results = {}
    
    has_memory_section = '会话记忆' in content
    results['has_memory_section'] = (
        has_memory_section,
        "有「会话记忆」section（v2.0）" if has_memory_section else "💡 建议：添加「会话记忆」section，支持跨会话上下文积累"
    )
    
    has_session_trigger = '总结这次对话' in content or 'save_session' in content
    results['has_session_trigger'] = (
        has_session_trigger,
        "有会话总结触发指令" if has_session_trigger else "💡 建议：在激活协议中添加「总结这次对话」触发指令"
    )
    
    # 检查sessions目录（如果提供了skill_dir）
    if skill_dir:
        from pathlib import Path
        sessions_dir = Path(skill_dir) / "sessions"
        results['has_sessions_dir'] = (
            sessions_dir.exists(),
            "sessions/目录存在" if sessions_dir.exists() else "💡 建议：创建 sessions/ 目录（运行Phase 0.5或手动mkdir）"
        )
    
    return results


def run_all_checks(content: str, skill_dir: str = None) -> dict:
    """运行所有检查"""
    all_results = {}
    all_results['【Frontmatter】'] = check_frontmatter(content)
    all_results['【域边界】'] = check_domain_boundary(content)
    all_results['【三层结构】'] = check_three_layers(content)
    all_results['【表达DNA】'] = check_expression_dna(content)
    all_results['【失效条件】'] = check_failure_conditions(content)
    all_results['【Agentic Protocol】'] = check_agentic_protocol(content)
    all_results['【相关能力图谱】'] = check_related_abilities(content)
    all_results['【诚实边界】'] = check_honest_boundary(content)
    all_results['【深度检查】'] = check_depth_vs_generic(content)
    all_results['【v2.0 会话记忆】'] = check_session_memory(content, skill_dir)
    return all_results


def print_report(all_results: dict):
    """打印质量报告"""
    total = 0
    passed = 0
    failures = []
    warnings = []
    
    print("\n" + "="*60)
    print("  异能蒸馏炉 · 晶核质量报告")
    print("="*60)
    
    for section, checks in all_results.items():
        print(f"\n{section}")
        for check_name, (result, message) in checks.items():
            total += 1
            if result:
                passed += 1
                print(f"  ✅ {message}")
            elif '建议' in message:
                warnings.append(message)
                print(f"  💡 {message}")
            else:
                failures.append(message)
                print(f"  ❌ {message}")
    
    score = round(passed / total * 100) if total > 0 else 0
    
    print("\n" + "="*60)
    print(f"  总评：{passed}/{total} 通过  |  得分：{score}分")
    
    if score >= 85:
        grade = "A — 可以交付"
    elif score >= 70:
        grade = "B — 建议修复❌项后交付"
    elif score >= 55:
        grade = "C — 需要重要修复，回溯Phase 2"
    else:
        grade = "D — 蒸馏质量严重不足，建议重新蒸馏"
    
    print(f"  等级：{grade}")
    
    if failures:
        print(f"\n  必须修复（{len(failures)}项）：")
        for f in failures:
            print(f"    · {f}")
    
    if warnings:
        print(f"\n  建议增强（{len(warnings)}项）：")
        for w in warnings:
            print(f"    · {w}")
    
    print("="*60 + "\n")
    
    return score


def main():
    if len(sys.argv) < 2:
        print("用法：python3 quality_check.py <晶核SKILL.md路径>")
        print("示例：python3 quality_check.py .claude/skills/musk-biz-core/SKILL.md")
        sys.exit(1)
    
    path = sys.argv[1]
    content = load_skill(path)
    # 传入晶核目录供会话记忆检查
    skill_dir = str(Path(path).parent) if Path(path).name == "SKILL.md" else None
    all_results = run_all_checks(content, skill_dir)
    score = print_report(all_results)
    
    # 退出码：>=70分返回0（成功），否则返回1（失败）
    sys.exit(0 if score >= 70 else 1)


if __name__ == "__main__":
    main()
