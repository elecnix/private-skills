#!/usr/bin/env python3
"""generate-visuals.py — Create title cards, stat cards, quote cards for a podcast video.

Usage: python3 generate-visuals.py <topic_folder> --config <config_json>

The config JSON defines all visual assets and the section-to-visual timeline mapping.
It also generates the timeline.json (keyword matching for SRT-based video composition).

Example config:
{
    "brand": "THAT'S INTERESTING STUFF",
    "cards": [
        {"file": "title-card.png", "title": "", "subtitle": "The Courage to Be Disliked"},
        {"file": "section-1.png", "title": "Section 1", "subtitle": "Trauma Does Not Exist"},
        {"file": "quote-1.png", "quote": "Freedom is being disliked by other people.", "accent_color": "#4a90d9"}
    ],
    "sections": [
        {"id": "intro", "title": "Intro", "visual": "visuals/title-card.png", "keyword": "Hey.*question"},
        {"id": "section-1", "title": "Trauma", "visuals": ["visuals/section-1.png", "visuals/quote-1.png"],
         "keyword": "Trauma.*exist|provocative"}
    ]
}

If --config file not provided, uses cards and sections defined inline in the script args.
"""

import sys, os, json, textwrap
from PIL import Image, ImageDraw, ImageFont

# --- Defaults ---
W, H = 1920, 1080
CONTENT_H = 540
BG = "#0a0a1a"

FONTS = {
    "brand": {"path": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "size": 22},
    "title": {"path": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "size": 40},
    "subtitle": {"path": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "size": 24},
    "big": {"path": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "size": 72},
    "quote": {"path": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", "size": 30},
    "author": {"path": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "size": 20},
}


def load_font(name):
    f = FONTS[name]
    try:
        return ImageFont.truetype(f["path"], f["size"])
    except OSError:
        print(f"  Warning: Font {name} not found, using default")
        return ImageFont.load_default()


def text_width(text, font):
    return ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=font)[2]


def draw_centered(draw, text, y, font, color):
    tw = text_width(text, font)
    draw.text(((W - tw) / 2, y), text, fill=color, font=font)


def make_title_card(brand, title="", subtitle="", **kwargs):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    bf, sf, tf = load_font("brand"), load_font("subtitle"), load_font("title")

    bw = text_width(brand, bf)
    draw.text(((W - bw) / 2, 16), brand, fill="#e94560", font=bf)
    draw.line([(780, 48), (1140, 48)], fill="#e94560", width=2)

    if subtitle:
        lines = subtitle.split('\n')
        y = 160
        for line in lines:
            draw_centered(draw, line, y, tf, "white")
            y += 50

    draw.line([(180, CONTENT_H), (W - 180, CONTENT_H)], fill="#1a1a2a", width=2)
    return img


def make_stat_card(brand, big_text, subtitle="", subtitle2="", accent_color="#e94560", **kwargs):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    bf, sf, lf = load_font("brand"), load_font("subtitle"), load_font("big")

    bw = text_width(brand, bf)
    draw.text(((W - bw) / 2, 16), brand, fill=accent_color, font=bf)
    draw.line([(780, 48), (1140, 48)], fill=accent_color, width=2)

    bw2 = text_width(big_text, lf)
    draw.text(((W - bw2) / 2, 100), big_text, fill=accent_color, font=lf)
    if subtitle:
        sw = text_width(subtitle, sf)
        draw.text(((W - sw) / 2, 220), subtitle, fill="white", font=sf)
    if subtitle2:
        sw2 = text_width(subtitle2, sf)
        draw.text(((W - sw2) / 2, 250), subtitle2, fill="#999999", font=sf)

    draw.line([(180, CONTENT_H), (W - 180, CONTENT_H)], fill="#1a1a2a", width=2)
    return img


def make_quote_card(brand, quote, author=None, accent_color="#e94560", **kwargs):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    bf, qf, af = load_font("brand"), load_font("quote"), load_font("author")

    bw = text_width(brand, bf)
    draw.text(((W - bw) / 2, 16), brand, fill=accent_color, font=bf)
    draw.line([(780, 48), (1140, 48)], fill=accent_color, width=2)

    lines = textwrap.wrap(quote, width=55)
    y = 80
    for line in lines:
        draw_centered(draw, f"\u201c{line}\u201d", y, qf, "#e8e8e8")
        y += 46
    if author:
        draw_centered(draw, f"\u2014 {author}", y + 20, af, accent_color)

    draw.line([(180, CONTENT_H), (W - 180, CONTENT_H)], fill="#1a1a2a", width=2)
    return img


def make_section_card(brand, title="", subtitle="", accent_color="#e94560", **kwargs):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    bf, sf, tf = load_font("brand"), load_font("subtitle"), load_font("title")

    bw = text_width(brand, bf)
    draw.text(((W - bw) / 2, 16), brand, fill=accent_color, font=bf)
    draw.line([(780, 48), (1140, 48)], fill=accent_color, width=2)

    if title:
        draw_centered(draw, title, 110, sf, accent_color)
        dc = None
    if subtitle:
        draw_centered(draw, subtitle, 160, tf, "white")

    draw.line([(180, CONTENT_H), (W - 180, CONTENT_H)], fill="#1a1a2a", width=2)
    return img


CARD_TYPES = {"title": make_title_card, "stat": make_stat_card, "quote": make_quote_card, "section": make_section_card}


def detect_card_type(cfg):
    if "quote" in cfg: return "quote"
    if "big_text" in cfg: return "stat"
    if "title" in cfg and cfg.get("title") and cfg.get("subtitle"): return "section"
    return "title"


def main():
    topicdir = sys.argv[1] if len(sys.argv) > 1 else "."
    config_file = None

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--config" and i + 1 < len(sys.argv):
            config_file = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    if config_file and os.path.exists(config_file):
        with open(config_file) as f:
            config = json.load(f)
    else:
        print("Error: No config file provided or file not found")
        print(f"Usage: {sys.argv[0]} <topic_folder> --config <config.json>")
        sys.exit(1)

    brand = config.get("brand", "THAT'S INTERESTING STUFF")
    cards = config.get("cards", [])
    sections = config.get("sections", [])

    visuals_dir = os.path.join(topicdir, "visuals")
    os.makedirs(visuals_dir, exist_ok=True)

    # Generate cards
    print("=== Generating Visual Cards ===")
    for card_cfg in cards:
        card_type = card_cfg.get("type", detect_card_type(card_cfg))
        filename = card_cfg.get("file", f"{card_type}.png")

        card_cfg["brand"] = brand
        generator = CARD_TYPES.get(card_type)
        if generator:
            img = generator(**card_cfg)
            path = os.path.join(visuals_dir, filename)
            img.save(path, "PNG")
            print(f"  {card_type}: {filename}")
        else:
            print(f"  Unknown card type: {card_type}")

    # Generate timeline
    print("\n=== Generating Timeline ===")
    os.makedirs(os.path.join(visuals_dir), exist_ok=True)

    timeline = {"sections": []}
    for section in sections:
        sec = {
            "id": section["id"],
            "title": section.get("title", ""),
        }
        visuals = section.get("visuals", [section.get("visual", "")])
        if isinstance(visuals, str):
            visuals = [visuals]
        sec["visuals"] = visuals
        sec["keyword"] = section.get("keyword", section.get("id"))
        timeline["sections"].append(sec)

    with open(os.path.join(visuals_dir, "timeline.json"), 'w') as f:
        json.dump(timeline, f, indent=2)

    print(f"  Timeline: {len(timeline['sections'])} sections")
    print(f"\nDone: {len(cards)} cards + timeline.json in {visuals_dir}/")


if __name__ == "__main__":
    main()
