"""縦書き・和紙風カードを描く。columns は右から左へ並ぶ1行ずつの文字列。"""
import random, re, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FONT_PATHS = ["/usr/share/fonts/opentype/noto/NotoSerifCJK-Medium.ttc",
              "/usr/share/fonts/opentype/noto-cjk/NotoSerifCJK-Medium.ttc"]
FOOTER = "辞めたい夜に読む言葉"
INK = (43, 38, 33)

def _font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size, index=0)
    raise FileNotFoundError("Noto Serif CJK が見つかりません")

def paper(seed=1):
    rnd = random.Random(seed)
    base = Image.new("RGB", (W, H), (244, 239, 227))
    noise = Image.effect_noise((W // 4, H // 4), 22).resize((W, H), Image.BICUBIC)
    noise = noise.filter(ImageFilter.GaussianBlur(3))
    tint = Image.new("RGB", (W, H), (226, 218, 200))
    img = Image.composite(base, tint, noise.point(lambda v: max(0, min(255, 150 + (v - 128)))))
    # ふち少し暗く
    vig = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(vig)
    d.rectangle([40, 40, W - 40, H - 40], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new("RGB", (W, H), (222, 214, 196))
    return Image.composite(img, dark, vig)

ROTATE = set("ー－—―…‥〜～（）()「」『』【】")
PUNCT = set("、。，．")
SMALL = set("ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ")
BRACKET_V = {"「": "﹁", "」": "﹂", "『": "﹃", "』": "﹄"}

def _tokens(s):
    # 半角数字・英字の2〜3文字は縦中横
    return re.findall(r"[0-9A-Za-z]{1,3}|.", s.replace("%", "％"))

def draw_column(img, text, x_center, y_top, size, font):
    d = ImageDraw.Draw(img)
    y = y_top
    for t in _tokens(text):
        if len(t) > 1 or (t.isascii() and t.isalnum()):
            f = _font(int(size * (0.7 if len(t) == 3 else 0.75 if len(t) == 2 else 0.9)))
            w = d.textlength(t, font=f)
            d.text((x_center - w / 2, y + size * 0.12), t, font=f, fill=INK)
        elif t in BRACKET_V:
            ch = BRACKET_V[t]
            w = d.textlength(ch, font=font)
            d.text((x_center - w / 2, y), ch, font=font, fill=INK)
        elif t in ROTATE:
            tile = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
            td = ImageDraw.Draw(tile)
            td.text((size, size), t, font=font, fill=INK + (255,), anchor="mm")
            tile = tile.rotate(-90, center=(size, size))
            img.paste(tile, (int(x_center - size), int(y + size * 0.62 - size)), tile)
        elif t in PUNCT:
            d.text((x_center - size * 0.5 + size * 0.6, y - size * 0.55), t, font=font, fill=INK)
        elif t in SMALL:
            w = d.textlength(t, font=font)
            d.text((x_center - w / 2 + size * 0.1, y - size * 0.1), t, font=font, fill=INK)
        else:
            w = d.textlength(t, font=font)
            d.text((x_center - w / 2, y), t, font=font, fill=INK)
        y += size * 1.12

def _len(col):
    return len(_tokens(col))

def render(columns, out_path, seed=1, size=None):
    img = paper(seed)
    n = len(columns)
    longest = max(_len(c) for c in columns)
    if size is None:
        size = int(min(80, 900 / (longest * 1.12), 700 / (n * 1.7)))
    font = _font(size)
    gap = size * 1.75
    block_w = gap * (n - 1)
    x0 = W / 2 + block_w / 2 + size * 0.15      # 一番右の列
    y_top = (H - longest * size * 1.12) / 2 - size * 0.6
    for i, col in enumerate(columns):
        draw_column(img, col, x0 - gap * i, y_top, size, font)
    # 左下の署名
    fs = 30
    draw_column(img, FOOTER, 100, H * 0.54, fs, _font(fs))
    img.save(out_path, quality=92)
    return out_path

