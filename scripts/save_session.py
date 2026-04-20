#!/usr/bin/env python3
"""
异能蒸馏炉 v2.0 · 会话记忆保存脚本
用法：python3 save_session.py <晶核目录> <摘要内容文本文件或直接输入>

功能：
  1. 将本次对话总结保存至 [晶核目录]/sessions/YYYY-MM-DD_N.md
  2. 更新晶核 SKILL.md 末尾的「会话记忆」section
  3. 更新 skill-registry.md 中的会话数计数
  4. 输出下次激活时的上下文加载指引

触发方式：
  - 用户在晶核对话中输入「总结这次对话」
  - 晶核激活协议触发此脚本
  - 也可手动调用：python3 save_session.py <晶核目录>
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime


# ─────────────────────────────────────────
# 会话摘要的标准格式模板（AI填充内容）
# ─────────────────────────────────────────
SESSION_TEMPLATE = """# 会话记忆 · {date}

**会话ID**：{session_id}  
**晶核**：{skill_id}  
**时间**：{datetime_full}

---

## 本次聚焦的主题

{topic}

---

## 核心结论

{conclusions}

---

## 用到的关键框架/模型

{frameworks}

---

## 本次对话中发现的晶核局限

{limitations}

---

## 未解决的问题 / 建议后续调研

{open_questions}

---

## 对晶核的反馈（可选）

{feedback}

---

*保存时间：{datetime_full}*
*字数：{word_count}字*
"""

# ─────────────────────────────────────────
# 为生成的晶核SKILL.md注入的激活时读取指令
# （放在 ## 激活协议 section 的开头）
# ─────────────────────────────────────────
MEMORY_ACTIVATION_INSTRUCTION = """
### 历史会话加载（v2.0）

**激活时自动执行**：

```
1. 检查 sessions/ 目录是否存在历史会话文件
2. 如果有：
   a. 读取最近3个会话文件（sessions/*.md，按日期倒序）
   b. 提取「核心结论」和「未解决问题」section
   c. 在内部建立上下文（不输出给用户）
   d. 第一次回答时，如果当前问题与历史会话有关联，自然引用
      例：「上次我们讨论了XX，你现在的问题延伸到了YY...」
3. 如果没有：正常激活，不需要任何提示

触发会话总结：用户输入「总结这次对话」→ 调用 save_session.py
```
"""


def get_skill_id(skill_dir: str) -> str:
    """从目录名推断晶核ID"""
    return Path(skill_dir).name


def get_next_session_id(sessions_dir: Path) -> str:
    """获取今天的下一个会话编号"""
    today = datetime.now().strftime("%Y-%m-%d")
    existing = list(sessions_dir.glob(f"{today}_*.md"))
    
    if not existing:
        return f"{today}_1"
    
    # 找最大的编号
    max_n = 0
    for f in existing:
        match = re.search(r'_(\d+)\.md$', f.name)
        if match:
            n = int(match.group(1))
            max_n = max(max_n, n)
    
    return f"{today}_{max_n + 1}"


def interactive_summary_input() -> dict:
    """交互式收集会话摘要内容"""
    print("\n" + "="*60)
    print("  异能蒸馏炉 v2.0 · 会话记忆生成器")
    print("  （每个字段直接回车可跳过）")
    print("="*60)
    
    def get_input(prompt: str, multiline: bool = False) -> str:
        if not multiline:
            return input(f"\n{prompt}: ").strip()
        else:
            print(f"\n{prompt}（输入完成后，空行+回车结束）:")
            lines = []
            while True:
                line = input()
                if line == "" and lines:
                    break
                if line:
                    lines.append(f"- {line}")
            return "\n".join(lines)
    
    topic = get_input("本次对话的主题是什么")
    print("\n核心结论（每条回车，空行结束）:")
    conclusions = []
    while True:
        c = input("结论: ").strip()
        if not c:
            break
        conclusions.append(f"{len(conclusions)+1}. {c}")
    
    frameworks = get_input("用到了哪些关键框架/心智模型（可简述）")
    limitations = get_input("本次对话中发现晶核有什么局限？（没有直接回车）")
    open_questions = get_input("还有什么未解决的问题需要后续调研？")
    feedback = get_input("对这个晶核有什么改进建议？（可选）")
    
    return {
        "topic": topic or "（未填写）",
        "conclusions": "\n".join(conclusions) if conclusions else "（未填写）",
        "frameworks": frameworks or "（未填写）",
        "limitations": limitations or "（本次未发现明显局限）",
        "open_questions": open_questions or "（无）",
        "feedback": feedback or "（无）",
    }


def create_session_file(skill_dir: str, summary_data: dict | None = None) -> Path:
    """创建会话文件"""
    skill_path = Path(skill_dir)
    sessions_dir = skill_path / "sessions"
    sessions_dir.mkdir(exist_ok=True)
    
    skill_id = get_skill_id(skill_dir)
    session_id = get_next_session_id(sessions_dir)
    
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    datetime_full = now.strftime("%Y-%m-%d %H:%M")
    
    # 如果没有提供摘要数据，启动交互式输入
    if summary_data is None:
        summary_data = interactive_summary_input()
    
    content = SESSION_TEMPLATE.format(
        date=date_str,
        session_id=session_id,
        skill_id=skill_id,
        datetime_full=datetime_full,
        topic=summary_data.get("topic", "（未填写）"),
        conclusions=summary_data.get("conclusions", "（未填写）"),
        frameworks=summary_data.get("frameworks", "（未填写）"),
        limitations=summary_data.get("limitations", "（本次未发现明显局限）"),
        open_questions=summary_data.get("open_questions", "（无）"),
        feedback=summary_data.get("feedback", "（无）"),
        word_count=len(summary_data.get("conclusions", "") + summary_data.get("topic", "")),
    )
    
    session_file = sessions_dir / f"{session_id}.md"
    session_file.write_text(content, encoding="utf-8")
    
    return session_file


def update_skill_memory_section(skill_dir: str, session_file: Path):
    """更新晶核SKILL.md末尾的会话记忆section"""
    skill_md = Path(skill_dir) / "SKILL.md"
    
    if not skill_md.exists():
        print(f"⚠️  未找到 SKILL.md，跳过更新")
        return
    
    content = skill_md.read_text(encoding="utf-8")
    
    # 读取session文件的摘要
    session_content = session_file.read_text(encoding="utf-8")
    
    # 提取核心结论
    conclusion_match = re.search(r'## 核心结论\n\n(.*?)\n\n---', session_content, re.DOTALL)
    conclusions = conclusion_match.group(1).strip() if conclusion_match else "（见会话文件）"
    
    # 提取主题
    topic_match = re.search(r'## 本次聚焦的主题\n\n(.*?)\n\n---', session_content, re.DOTALL)
    topic = topic_match.group(1).strip() if topic_match else "（见会话文件）"
    
    # 生成会话记录行
    date_str = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"\n### {date_str} — {topic[:30]}{'...' if len(topic) > 30 else ''}\n\n**文件**：`sessions/{session_file.name}`\n\n**核心结论摘要**：\n{conclusions[:200]}{'...' if len(conclusions) > 200 else ''}\n"
    
    # 找到「会话记忆」section，插入新记录
    memory_section_pattern = r'## 会话记忆\n\n> .*?\n\n\*（暂无历史会话）\*'
    memory_section_with_content = r'## 会话记忆'
    
    if re.search(memory_section_pattern, content):
        # 替换「暂无」占位符
        updated = re.sub(
            memory_section_pattern,
            f'## 会话记忆\n\n> 说明：以下是本晶核的历史使用记录。每次对话结束后，用户输入「总结这次对话」自动生成。\n{new_entry}',
            content
        )
    elif '## 会话记忆' in content:
        # 在section末尾插入
        updated = content.replace(
            '## 会话记忆',
            f'## 会话记忆\n{new_entry}\n##',
            1
        ).replace(
            f'\n{new_entry}\n##',
            f'\n{new_entry}##',
        )
        # 更简单的方式：在section后追加
        parts = content.split('## 会话记忆')
        if len(parts) == 2:
            updated = parts[0] + '## 会话记忆' + new_entry + parts[1]
        else:
            updated = content  # fallback，不修改
    else:
        # 没有会话记忆section，在末尾追加
        updated = content + f"\n\n## 会话记忆\n\n> 说明：以下是本晶核的历史使用记录。\n{new_entry}"
    
    skill_md.write_text(updated, encoding="utf-8")
    print(f"✅ 已更新 SKILL.md 的会话记忆section")


def update_registry(skill_dir: str):
    """更新skill-registry.md中的会话数"""
    skill_id = get_skill_id(skill_dir)
    
    # 查找registry文件
    registry_candidates = [
        Path(".claude/skills/skill-registry.md"),
        Path(skill_dir).parent / "skill-registry.md",
        Path(skill_dir).parent.parent / "skill-registry.md",
    ]
    
    registry_path = None
    for p in registry_candidates:
        if p.exists():
            registry_path = p
            break
    
    if registry_path is None:
        print("💡 未找到 skill-registry.md，跳过注册表更新")
        return
    
    content = registry_path.read_text(encoding="utf-8")
    
    # 找到对应行并更新会话数
    # 格式：| skill_id | ... | N |
    pattern = rf'\| `?{re.escape(skill_id)}`? \|(.+?)\| (\d+) \|'
    match = re.search(pattern, content)
    
    if match:
        current_count = int(match.group(2))
        new_count = current_count + 1
        updated = content.replace(match.group(0), match.group(0).replace(f'| {current_count} |', f'| {new_count} |'))
        registry_path.write_text(updated, encoding="utf-8")
        print(f"✅ 已更新注册表：{skill_id} 会话数 {current_count} → {new_count}")
    else:
        print(f"💡 在注册表中未找到 {skill_id}，如需追踪请手动添加")


def load_recent_sessions(skill_dir: str, n: int = 3) -> list[dict]:
    """加载最近N个会话摘要（供晶核激活时参考）"""
    sessions_dir = Path(skill_dir) / "sessions"
    
    if not sessions_dir.exists():
        return []
    
    session_files = sorted(sessions_dir.glob("*.md"), reverse=True)[:n]
    sessions = []
    
    for f in session_files:
        content = f.read_text(encoding="utf-8")
        
        topic_match = re.search(r'## 本次聚焦的主题\n\n(.*?)\n\n---', content, re.DOTALL)
        conclusion_match = re.search(r'## 核心结论\n\n(.*?)\n\n---', content, re.DOTALL)
        open_q_match = re.search(r'## 未解决的问题.*?\n\n(.*?)\n\n---', content, re.DOTALL)
        
        sessions.append({
            "file": f.name,
            "topic": topic_match.group(1).strip() if topic_match else "未知",
            "conclusions": conclusion_match.group(1).strip() if conclusion_match else "无",
            "open_questions": open_q_match.group(1).strip() if open_q_match else "无",
        })
    
    return sessions


def print_context_for_activation(skill_dir: str):
    """输出供晶核激活时读取的历史上下文"""
    sessions = load_recent_sessions(skill_dir)
    
    if not sessions:
        return
    
    print("\n" + "─"*60)
    print("  📚 历史会话上下文（最近3次）")
    print("─"*60)
    
    for i, s in enumerate(sessions, 1):
        print(f"\n  第{i}次会话 [{s['file']}]")
        print(f"  主题：{s['topic'][:50]}")
        print(f"  结论：{s['conclusions'][:100]}{'...' if len(s['conclusions']) > 100 else ''}")
        if s['open_questions'] != "（无）":
            print(f"  遗留问题：{s['open_questions'][:80]}")
    
    print("\n" + "─"*60)
    print("  激活晶核时，如当前问题与以上历史相关，请自然引用。")
    print("─"*60 + "\n")


def main():
    if len(sys.argv) < 2:
        print("用法：")
        print("  保存会话：python3 save_session.py <晶核目录>")
        print("  查看历史：python3 save_session.py <晶核目录> --show")
        print("示例：python3 save_session.py .claude/skills/musk-biz-core")
        sys.exit(1)
    
    skill_dir = sys.argv[1]
    
    if not Path(skill_dir).exists():
        print(f"❌ 目录不存在：{skill_dir}")
        sys.exit(1)
    
    # 查看模式
    if len(sys.argv) >= 3 and sys.argv[2] == "--show":
        print_context_for_activation(skill_dir)
        sys.exit(0)
    
    # 保存模式
    print(f"\n🔮 为晶核 [{get_skill_id(skill_dir)}] 保存会话记忆")
    
    session_file = create_session_file(skill_dir)
    print(f"\n✅ 会话文件已保存：{session_file}")
    
    update_skill_memory_section(skill_dir, session_file)
    update_registry(skill_dir)
    
    print("\n" + "="*60)
    print("  会话记忆已保存。")
    print(f"  下次激活 [{get_skill_id(skill_dir)}] 时将自动参考此记录。")
    print("  查看所有历史：python3 save_session.py <晶核目录> --show")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
