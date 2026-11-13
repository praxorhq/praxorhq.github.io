"""Картинки для превью ссылок (og:image), 1200x630.

Запуск из корня репозитория: python3 _build/og.py
Нужен Pillow: pip install pillow
Пишет og/<slug>.png для каждой статьи и og/home.png для лендинга.
"""
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "_build" / "fonts"
OUT = ROOT / "og"

W, H = 1200, 630
PAD = 80
BG = "#FBFAF8"
INK = "#0E1116"
MUTED = "#5B646E"
LINE = "#E2DFDA"
ACCENT = "#1B4DE4"


def font(name, size, weight):
    f = ImageFont.truetype(str(FONTS / name), size)
    try:
        f.set_variation_by_axes([weight])
    except OSError:
        pass
    return f


def glue(text):
    # Короткие слова и числа не оставляем в конце строки.
    words, out = text.split(), []
    for w in words:
        if out and (len(out[-1].split("\u00a0")[-1]) <= 2 or out[-1][-1].isdigit()):
            out[-1] += "\u00a0" + w
        else:
            out.append(w)
    return out


def wrap(draw, text, f, width):
    lines, cur = [], ""
    for word in glue(text):
        test = f"{cur} {word}".strip()
        if draw.textlength(test, font=f) <= width:
            cur = test
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def card(path, kicker, title):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, W, 8], fill=ACCENT)
    d.text((PAD, 72), "Праксор", font=font("Geist.ttf", 34, 600), fill=INK)
    d.text((PAD, 124), kicker.upper(), font=font("JetBrainsMono.ttf", 22, 500), fill=ACCENT)

    width = W - 2 * PAD
    for size in (68, 60, 54, 48):
        f = font("Geist.ttf", size, 500)
        lines = wrap(d, title, f, width)
        if len(lines) <= 4:
            break
    lh = int(size * 1.18)
    y = 200 + (4 - len(lines)) * lh // 2
    for line in lines:
        d.text((PAD, y), line.replace("\u00a0", " "), font=f, fill=INK)
        y += lh

    d.line([PAD, H - 96, W - PAD, H - 96], fill=LINE, width=2)
    small = font("JetBrainsMono.ttf", 22, 400)
    d.text((PAD, H - 72), "praxor.ru", font=small, fill=MUTED)
    tag = "AI SDLC для инженерных команд"
    d.text((W - PAD - d.textlength(tag, font=small), H - 72), tag, font=small, fill=MUTED)

    img.save(path, optimize=True)


def main():
    OUT.mkdir(exist_ok=True)
    card(OUT / "home.png", "AI SDLC-консалтинг", "Выстраиваем AI SDLC на пилотной команде за 3 месяца")
    for src in sorted((ROOT / "_build" / "content").glob("*.html")):
        meta = json.loads(re.search(r"<!--meta\s*(\{.*?\})\s*-->", src.read_text(), re.S).group(1))
        card(OUT / f"{src.stem}.png", "Материалы", meta["h1"])
        print(src.stem)


if __name__ == "__main__":
    main()
