#!/usr/bin/env python3
"""
异能蒸馏炉 · 字幕清洗脚本
将SRT/VTT字幕文件转为干净的可阅读文本，用于Agent调研分析
用法：python3 srt_to_transcript.py <input.srt> [output.txt]
"""

import sys
import re
from pathlib import Path


def clean_srt(content: str) -> str:
    """清洗SRT格式字幕"""
    lines = content.splitlines()
    cleaned = []
    prev_text = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过序号行（纯数字）
        if re.match(r'^\d+$', line):
            i += 1
            continue
        
        # 跳过时间戳行
        if re.match(r'\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}', line):
            i += 1
            continue
        
        # 跳过空行
        if not line:
            i += 1
            continue
        
        # 去除HTML标签
        line = re.sub(r'<[^>]+>', '', line)
        
        # 去除特殊标记（如 [音乐] [掌声] 等）
        # 保留内容性的方括号，只去除明显的音效标记
        line = re.sub(r'\[(?:音乐|掌声|笑声|鼓掌|音效|Music|Applause|Laughter)\]', '', line, flags=re.IGNORECASE)
        
        line = line.strip()
        
        if not line:
            i += 1
            continue
        
        # 去除连续重复行
        if line == prev_text:
            i += 1
            continue
        
        cleaned.append(line)
        prev_text = line
        i += 1
    
    return '\n'.join(cleaned)


def clean_vtt(content: str) -> str:
    """清洗VTT格式字幕"""
    # 移除VTT头部
    content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
    
    lines = content.splitlines()
    cleaned = []
    prev_text = None
    
    for line in lines:
        line = line.strip()
        
        # 跳过时间戳行
        if re.match(r'\d{2}:\d{2}[:.]\d{3}\s*-->', line):
            continue
        if re.match(r'\d{2}:\d{2}:\d{2}[:.]\d{3}\s*-->', line):
            continue
        
        # 跳过空行
        if not line:
            continue
        
        # 跳过NOTE行
        if line.startswith('NOTE'):
            continue
        
        # 去除HTML标签和VTT特殊标记
        line = re.sub(r'<[^>]+>', '', line)
        line = re.sub(r'&amp;', '&', line)
        line = re.sub(r'&lt;', '<', line)
        line = re.sub(r'&gt;', '>', line)
        
        line = line.strip()
        
        if not line or line == prev_text:
            continue
        
        cleaned.append(line)
        prev_text = line
    
    return '\n'.join(cleaned)


def merge_short_lines(text: str, min_length: int = 15) -> str:
    """合并过短的行（通常是断句造成的碎片）"""
    lines = text.splitlines()
    merged = []
    buffer = ""
    
    for line in lines:
        if len(buffer) == 0:
            buffer = line
        elif len(buffer) < min_length:
            # 当前buffer太短，尝试与下一行合并
            # 判断是否应该合并（没有句末标点）
            if buffer and buffer[-1] not in '。！？.!?':
                buffer = buffer + line
            else:
                merged.append(buffer)
                buffer = line
        else:
            merged.append(buffer)
            buffer = line
    
    if buffer:
        merged.append(buffer)
    
    return '\n'.join(merged)


def add_paragraph_breaks(text: str) -> str:
    """在自然断句处添加段落分隔，提高可读性"""
    # 在句末标点后添加换行（如果下一句是新话题）
    text = re.sub(r'([。！？!?])\s*(?=[A-Z\u4e00-\u9fff])', r'\1\n\n', text)
    return text


def process_file(input_path: str, output_path: str | None = None) -> str:
    """处理字幕文件"""
    path = Path(input_path)
    
    if not path.exists():
        print(f"❌ 找不到文件：{input_path}")
        sys.exit(1)
    
    content = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    
    # 根据格式选择清洗函数
    if suffix == '.srt':
        cleaned = clean_srt(content)
    elif suffix in ('.vtt', '.webvtt'):
        cleaned = clean_vtt(content)
    else:
        # 尝试自动检测
        if 'WEBVTT' in content[:20]:
            cleaned = clean_vtt(content)
        elif re.search(r'^\d+\n\d{2}:\d{2}:\d{2}', content, re.MULTILINE):
            cleaned = clean_srt(content)
        else:
            print("⚠️ 无法识别字幕格式，尝试通用清洗...")
            cleaned = clean_srt(content)  # 尝试SRT清洗
    
    # 后处理
    cleaned = merge_short_lines(cleaned)
    cleaned = add_paragraph_breaks(cleaned)
    
    # 统计信息
    original_lines = len(content.splitlines())
    cleaned_lines = len(cleaned.splitlines())
    original_chars = len(content)
    cleaned_chars = len(cleaned)
    
    print(f"✅ 清洗完成")
    print(f"   原始：{original_lines}行 / {original_chars}字符")
    print(f"   清洗后：{cleaned_lines}行 / {cleaned_chars}字符")
    print(f"   压缩率：{round((1 - cleaned_chars/original_chars) * 100)}%")
    
    # 输出
    if output_path:
        Path(output_path).write_text(cleaned, encoding="utf-8")
        print(f"   输出：{output_path}")
    
    return cleaned


def main():
    if len(sys.argv) < 2:
        print("用法：python3 srt_to_transcript.py <input.srt> [output.txt]")
        print("示例：python3 srt_to_transcript.py interview.srt ./sources/transcripts/interview_clean.txt")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if output_path is None:
        # 默认输出到同目录，同名但.txt后缀
        input_p = Path(input_path)
        output_path = str(input_p.parent / (input_p.stem + "_transcript.txt"))
        print(f"💡 未指定输出路径，默认输出到：{output_path}")
    
    process_file(input_path, output_path)


if __name__ == "__main__":
    main()
