#!/usr/bin/env python3
"""
异能蒸馏炉 · 调研摘要生成脚本
用法：python3 merge_research.py <晶核目录路径>
功能：扫描 references/research/01-05.md，统计信息质量，输出Phase 1.5检查点摘要
"""

import sys
import re
from pathlib import Path


RESEARCH_FILES = {
    "01-ability-in-action.md": "能力展示案例",
    "02-mechanism.md": "能力机制分析",
    "03-expression-dna.md": "表达风格DNA",
    "04-failure-cases.md": "失效与局限案例",
    "05-related-abilities.md": "相关能力图谱",
}


def load_research_file(filepath: Path) -> str | None:
    if not filepath.exists():
        return None
    return filepath.read_text(encoding="utf-8")


def analyze_file(content: str, filename: str) -> dict:
    """分析单个调研文件的质量"""
    if content is None:
        return {
            "status": "缺失",
            "line_count": 0,
            "primary_source_count": 0,
            "secondary_source_count": 0,
            "case_count": 0,
            "has_source_urls": False,
            "quality": "D",
        }
    
    lines = content.splitlines()
    line_count = len([l for l in lines if l.strip()])
    
    # 一手来源标记检测
    primary_markers = ['一手', '本人', '原文', '访谈原文', '来源：本人', '直接引用']
    primary_count = sum(content.count(m) for m in primary_markers)
    
    # 二手来源标记检测  
    secondary_markers = ['二手', '据称', '据报道', '转述', '分析称', '外部视角']
    secondary_count = sum(content.count(m) for m in secondary_markers)
    
    # URL数量检测
    url_count = len(re.findall(r'https?://', content))
    
    # 案例数量（针对01文件）
    case_count = len(re.findall(r'情境|案例\d|Case \d|###', content))
    
    # 质量评级
    if line_count >= 100 and (primary_count > 0 or url_count >= 3):
        quality = "A"
    elif line_count >= 50 and url_count >= 1:
        quality = "B"
    elif line_count >= 20:
        quality = "C"
    else:
        quality = "D"
    
    return {
        "status": "存在",
        "line_count": line_count,
        "primary_source_count": primary_count,
        "secondary_source_count": secondary_count,
        "case_count": case_count,
        "has_source_urls": url_count > 0,
        "url_count": url_count,
        "quality": quality,
    }


def extract_key_findings(content: str, filename: str) -> list[str]:
    """从调研文件中提取关键发现"""
    if content is None:
        return ["无内容"]
    
    findings = []
    
    if "01-ability-in-action" in filename:
        # 提取案例标题
        cases = re.findall(r'###\s+(.+)', content)
        findings = cases[:3] if cases else ["内容解析失败"]
        
    elif "02-mechanism" in filename:
        # 提取机制要点
        bullets = re.findall(r'^[-*]\s+(.{10,60})', content, re.MULTILINE)
        findings = bullets[:3] if bullets else ["内容解析失败"]
        
    elif "03-expression-dna" in filename:
        # 提取风格特征
        headers = re.findall(r'###\s+(.+)|^\*\*(.+?)\*\*', content, re.MULTILINE)
        findings = [h[0] or h[1] for h in headers[:3]] if headers else ["内容解析失败"]
        
    elif "04-failure-cases" in filename:
        # 提取失效情形
        failures = re.findall(r'情境.*?[:：]\s*(.{10,50})|失效.*?[:：]\s*(.{10,50})', content)
        findings = [f[0] or f[1] for f in failures[:3]] if failures else ["内容解析失败"]
        
    elif "05-related-abilities" in filename:
        # 提取相关能力
        abilities = re.findall(r'前置[：:]\s*(.+)|后置[：:]\s*(.+)|协作[：:]\s*(.+)', content)
        findings = [a[0] or a[1] or a[2] for a in abilities[:3]] if abilities else ["内容解析失败"]
    
    return findings if findings else ["未找到关键内容"]


def detect_contradictions(contents: dict) -> list[str]:
    """检测不同调研文件之间的矛盾"""
    contradictions = []
    
    # 简单检测：成功案例文件和失效案例文件是否在同一维度有相反结论
    action_content = contents.get("01-ability-in-action.md", "") or ""
    failure_content = contents.get("04-failure-cases.md", "") or ""
    
    if action_content and failure_content:
        # 提取两个文件中共同提及的关键词
        action_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,4}', action_content))
        failure_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,4}', failure_content))
        overlap = action_keywords & failure_keywords
        
        # 如果重叠词超过某个阈值，可能有矛盾点
        if len(overlap) > 20:
            contradictions.append(f"Agent1(案例)与Agent4(失效)在以下维度可能有张力：{', '.join(list(overlap)[:5])}")
    
    return contradictions


def calculate_overall_quality(analyses: dict) -> str:
    """计算整体信息质量"""
    quality_scores = {"A": 4, "B": 3, "C": 2, "D": 1}
    scores = [quality_scores[a["quality"]] for a in analyses.values() if a["status"] == "存在"]
    
    if not scores:
        return "D — 调研文件全部缺失，无法继续"
    
    avg = sum(scores) / len(scores)
    missing_count = sum(1 for a in analyses.values() if a["status"] == "缺失")
    
    if avg >= 3.5 and missing_count == 0:
        return "A — 调研充足，可以进入Phase 2"
    elif avg >= 2.5 and missing_count <= 1:
        return "B — 调研基本够用，可以继续，但某些维度信息偏少"
    elif avg >= 1.5 or missing_count <= 2:
        return "C — 调研偏少，建议补充本地素材后再继续，或降低期望"
    else:
        return "D — 调研严重不足，不建议直接进入Phase 2"


def print_summary(skill_dir: str, analyses: dict, contents: dict):
    """打印Phase 1.5检查点摘要"""
    
    # 尝试从目录名提取晶核名称
    dir_path = Path(skill_dir)
    skill_name = dir_path.name
    
    print("\n" + "="*65)
    print(f"  调研质量摘要 · {skill_name}")
    print("="*65)
    print(f"  {'维度':<18} {'状态':<6} {'质量':<5} {'行数':<6} URL数  关键发现")
    print("-"*65)
    
    for filename, display_name in RESEARCH_FILES.items():
        analysis = analyses[filename]
        content = contents.get(filename)
        
        status = "✅" if analysis["status"] == "存在" else "❌缺失"
        quality = analysis["quality"]
        lines = analysis["line_count"]
        urls = analysis.get("url_count", 0)
        
        findings = extract_key_findings(content, filename) if content else ["无内容"]
        first_finding = findings[0][:25] + "..." if len(findings[0]) > 25 else findings[0]
        
        print(f"  {display_name:<16} {status:<6} {quality:<5} {lines:<6} {urls:<5} {first_finding}")
    
    print("-"*65)
    
    # 矛盾点检测
    contradictions = detect_contradictions(contents)
    print(f"\n  矛盾/张力点：{len(contradictions)}处")
    for c in contradictions:
        print(f"    · {c}")
    
    # 整体质量
    overall = calculate_overall_quality(analyses)
    print(f"\n  整体信息质量：{overall}")
    
    # 缺失维度提示
    missing = [RESEARCH_FILES[f] for f, a in analyses.items() if a["status"] == "缺失"]
    if missing:
        print(f"\n  ⚠️ 缺失维度：{', '.join(missing)}")
        print("     → 对应Agent可能超时或无有价值结果，在Phase 2中标注「信息不足」")
    
    print("\n  ─── 继续？ ───")
    print("  质量A/B → 确认后进入Phase 2")
    print("  质量C   → 建议补充本地素材，或告知用户降低期望")
    print("  质量D   → 强烈建议在继续前补充调研")
    print("="*65 + "\n")


def main():
    if len(sys.argv) < 2:
        print("用法：python3 merge_research.py <晶核目录路径>")
        print("示例：python3 merge_research.py .claude/skills/musk-biz-core")
        sys.exit(1)
    
    skill_dir = sys.argv[1]
    research_dir = Path(skill_dir) / "references" / "research"
    
    if not research_dir.exists():
        print(f"❌ 调研目录不存在：{research_dir}")
        print("请先确认已运行Phase 0.5创建目录结构")
        sys.exit(1)
    
    # 加载所有调研文件
    contents = {}
    analyses = {}
    
    for filename in RESEARCH_FILES:
        filepath = research_dir / filename
        content = load_research_file(filepath)
        contents[filename] = content
        analyses[filename] = analyze_file(content, filename)
    
    # 输出摘要
    print_summary(skill_dir, analyses, contents)


if __name__ == "__main__":
    main()
