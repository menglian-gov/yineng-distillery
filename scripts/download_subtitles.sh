#!/bin/bash
# 异能蒸馏炉 · 字幕下载脚本
# 用法：bash download_subtitles.sh <YouTube_URL> [输出目录]
# 自动优先：人工字幕 → 中文 → 英文 → 自动生成字幕

set -e

URL="$1"
OUTPUT_DIR="${2:-.}"

if [ -z "$URL" ]; then
    echo "用法：bash download_subtitles.sh <YouTube_URL> [输出目录]"
    echo "示例：bash download_subtitles.sh https://youtube.com/watch?v=xxx ./sources/transcripts"
    exit 1
fi

# 检查yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo "❌ 需要安装 yt-dlp"
    echo "安装方法：pip install yt-dlp  或  brew install yt-dlp"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "📥 开始下载字幕：$URL"
echo "📁 输出目录：$OUTPUT_DIR"

# 优先级1：人工中文字幕
echo "尝试下载人工中文字幕..."
if yt-dlp \
    --skip-download \
    --write-subs \
    --sub-langs "zh-Hans,zh-Hant,zh" \
    --sub-format "srt/vtt/best" \
    --no-write-auto-subs \
    -o "$OUTPUT_DIR/%(title)s.%(ext)s" \
    "$URL" 2>/dev/null; then
    echo "✅ 人工中文字幕下载成功"
    exit 0
fi

# 优先级2：人工英文字幕
echo "尝试下载人工英文字幕..."
if yt-dlp \
    --skip-download \
    --write-subs \
    --sub-langs "en" \
    --sub-format "srt/vtt/best" \
    --no-write-auto-subs \
    -o "$OUTPUT_DIR/%(title)s.%(ext)s" \
    "$URL" 2>/dev/null; then
    echo "✅ 人工英文字幕下载成功"
    exit 0
fi

# 优先级3：自动生成中文字幕
echo "尝试下载自动生成中文字幕..."
if yt-dlp \
    --skip-download \
    --write-auto-subs \
    --sub-langs "zh-Hans,zh-Hant,zh" \
    --sub-format "srt/vtt/best" \
    -o "$OUTPUT_DIR/%(title)s.%(ext)s" \
    "$URL" 2>/dev/null; then
    echo "✅ 自动中文字幕下载成功（质量较低，请人工校验关键段落）"
    exit 0
fi

# 优先级4：自动生成英文字幕
echo "尝试下载自动生成英文字幕..."
if yt-dlp \
    --skip-download \
    --write-auto-subs \
    --sub-langs "en" \
    --sub-format "srt/vtt/best" \
    -o "$OUTPUT_DIR/%(title)s.%(ext)s" \
    "$URL" 2>/dev/null; then
    echo "✅ 自动英文字幕下载成功（质量较低，请人工校验关键段落）"
    echo "💡 提示：使用 srt_to_transcript.py 清洗后用于调研"
    exit 0
fi

echo "❌ 所有字幕下载方式均失败"
echo "可能原因："
echo "  · 该视频没有任何字幕"
echo "  · 视频受地区限制"
echo "  · URL格式不正确"
echo ""
echo "备选方案：使用 gemini-video skill 直接转写视频内容"
exit 1
