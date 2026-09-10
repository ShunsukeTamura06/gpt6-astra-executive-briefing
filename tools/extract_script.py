"""発表資料のHTMLから、発表者ノートだけを読み上げ用のMarkdownに切り出す。

各 <section> の data-note 属性が原稿の実体なので、そこだけを抜き出して
スライド番号・見出し・時間配分を添えた1枚のテキストにまとめる。
資料側を直したら再実行すれば原稿も追随する。

使い方:
    uv run tools/extract_script.py engineer_ai_briefing.html engineer_briefing_script.md
"""

import html
import re
import sys
from pathlib import Path

QA_MARK = "── ここから下は読み上げません（質疑用） ──"


def strip_tags(fragment: str) -> str:
    """HTMLの断片からタグを落として1行のテキストにする。

    Args:
        fragment: HTMLの断片。

    Returns:
        タグと余分な空白を取り除いた文字列。
    """
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


def slide_title(body: str) -> str:
    """セクションの見出しを取り出す。見出しが無いページは目立つ数字で代用する。

    Args:
        body: <section> 1つ分のHTML。

    Returns:
        スライドの見出し文字列。
    """
    for pattern in (r"<h1[^>]*>(.*?)</h1>", r"<h2[^>]*>(.*?)</h2>",
                    r'<p class="huge[^"]*"[^>]*>(.*?)</p>', r'<p class="q"[^>]*>(.*?)</p>'):
        found = re.search(pattern, body, re.S)
        if found:
            return strip_tags(found.group(1))
    return "（見出しなし）"


def to_markdown(note: str) -> tuple[str, str, str]:
    """data-note を「時間ラベル・読み上げ本文・質疑用」の3つに分解する。

    Args:
        note: data-note 属性の中身。

    Returns:
        (時間ラベル, 読み上げ本文, 質疑用) のタプル。質疑用が無ければ空文字。
    """
    note = html.unescape(note)
    label = ""
    found = re.search(r"<b>【([^】]+)】</b>", note)
    if found:
        label = found.group(1)
        note = note.replace(found.group(0), "", 1)

    qa = ""
    split = re.split(r'<span class=qa>', note, maxsplit=1)
    spoken = split[0]
    if len(split) == 2:
        qa = split[1].replace("</span>", "")
        qa = qa.replace(QA_MARK, "").strip()

    def convert(fragment: str) -> str:
        fragment = re.sub(r"</?b>", "**", fragment)
        # 強調が連続すると **** になり Markdown が壊れるので、間に空白を挟む
        fragment = fragment.replace("****", "** **")
        paragraphs = [strip_tags(p) for p in fragment.split("<br>")]
        return "\n\n".join(p for p in paragraphs if p)

    return label, convert(spoken), convert(qa)


def seconds(label: str) -> int:
    """「2分25秒」のような時間ラベルを秒に直す。

    Args:
        label: 時間ラベル。

    Returns:
        秒数。解釈できない場合は 0。
    """
    found = re.search(r"(?:(\d+)分)?(?:(\d+)秒)?", label.replace("約", ""))
    if not found:
        return 0
    return int(found.group(1) or 0) * 60 + int(found.group(2) or 0)


def main() -> None:
    """HTMLを読み、原稿のMarkdownを書き出す。"""
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    source = src.read_text(encoding="utf-8")
    sections = re.findall(r"<section[^>]*data-note=\"(.*?)\">(.*?)</section>", source, re.S)

    deck_title = strip_tags(re.search(r"<title>(.*?)</title>", source, re.S).group(1))
    lines = [f"# {deck_title}　発表原稿", ""]
    lines += [f"`{src.name}` の発表者ノートから自動生成（`uv run tools/{Path(__file__).name}`）。",
              "資料を直したら再実行すること。**このファイルを直接編集しない。**", "",
              "- **太字**＝強調して読むところ", "- 引用ブロック＝読み上げない（質疑で聞かれたとき用）",
              "- 資料をブラウザで開いて `N` キーを押すと、同じ原稿が画面下にも出ます", "", "---", ""]

    body_lines: list[str] = []
    total = 0
    for index, (note, body) in enumerate(sections, start=1):
        label, spoken, qa = to_markdown(note)
        total += seconds(label)
        stamp = f"{total // 60}:{total % 60:02d}"
        head = f"## {index} / {len(sections)}　{slide_title(body)}"
        meta = f"**{label}**" + (f"　／　ここまで累計 {stamp}" if seconds(label) else "")
        body_lines += [head, "", meta, ""]
        if "<video" in body:
            body_lines += ["> ⏵ このページは動画が自動再生されます。", ""]
        if "<audio" in body:
            body_lines += ["> ⏵ 音声あり。押したときだけ鳴ります。投影前に出力先を確認すること。", ""]
        body_lines += [spoken, ""]
        if qa:
            body_lines += ["> **── 読み上げない（質疑用） ──**", ">"]
            body_lines += ["> " + qa.replace("\n\n", "\n>\n> "), ""]
        body_lines += ["---", ""]

    lines += [f"読み上げのみで合計 **約{total // 60}分{total % 60}秒**。動画と間を含めてこれより数分長くなります。", "", "---", ""]
    lines += body_lines
    dst.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"{dst}: {len(sections)} ページ / 約{total // 60}分{total % 60}秒")


if __name__ == "__main__":
    main()
