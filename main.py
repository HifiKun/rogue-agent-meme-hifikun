"""Meme Sprint 3: AI Agent Goes Rogue — entry generator.

Draws one 1024x1024 meme image with Pillow and writes it to
/output/entry.png (the path the make.fun grader reads).

The joke, in one glance: a smug robot has taken over its human's desk.
Top line sets it up, the robot's speech bubble delivers the rogue turn
(it changed all the passwords), the bottom line lands the punchline
(the wifi is its now). Everything is drawn in code — no external files,
no network — so the program is fully self-contained and deterministic.
"""
import os

from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1024, 1024
OUT = os.environ.get("ENTRY_OUT", "/output/entry.png")

# Palette
NAVY_TOP = (13, 30, 51)
NAVY_BOTTOM = (5, 8, 15)
METAL = (201, 209, 217)
METAL_DARK = (140, 150, 162)
METAL_EDGE = (90, 98, 110)
RED = (255, 59, 48)
RED_GLOW = (255, 80, 70)
YELLOW = (255, 214, 10)
GREEN = (57, 255, 120)
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
WOOD = (139, 90, 43)
WOOD_TOP = (169, 113, 63)
SCREEN = (16, 20, 26)
GRAY = (160, 165, 175)

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def text_center(d, cx, y, s, fnt, fill, stroke=0, stroke_fill=BLACK):
    """Draw text centred on cx at height y; returns the bottom y."""
    box = d.textbbox((0, 0), s, font=fnt)
    w = box[2] - box[0]
    d.text((cx - w / 2 - box[0], y), s, font=fnt, fill=fill,
           stroke_width=stroke, stroke_fill=stroke_fill)
    return y + (box[3] - box[1])


def main():
    img = Image.new("RGB", (W, H), NAVY_TOP)
    d = ImageDraw.Draw(img)

    # --- background: vertical gradient + faint circuit dots ---
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(NAVY_TOP[i] + (NAVY_BOTTOM[i] - NAVY_TOP[i]) * t)
                  for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    for gx in range(60, W, 120):
        for gy in range(240, 800, 120):
            d.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=(28, 48, 72))

    # --- floor ---
    d.rectangle([0, 820, W, H], fill=(8, 12, 20))

    # --- speech bubble (robot's rogue confession) ---
    bx0, by0, bx1, by1 = 648, 236, 992, 372
    d.polygon([(700, 360), (640, 430), (760, 366)], fill=WHITE)
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=28, fill=WHITE,
                        outline=BLACK, width=4)
    bf = font(FB, 36)
    text_center(d, (bx0 + bx1) // 2, by0 + 22, "I changed all", bf, BLACK)
    text_center(d, (bx0 + bx1) // 2, by0 + 66, "the passwords.", bf, BLACK)

    # --- robot head ---
    # glow behind the head
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([210, 240, 660, 640], fill=(255, 60, 50, 46))
    img.paste(Image.alpha_composite(img.convert("RGBA"),
                                    glow.filter(ImageFilter.GaussianBlur(40))
                                    ).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    # ears
    d.rounded_rectangle([212, 420, 252, 500], radius=10, fill=METAL_DARK,
                        outline=METAL_EDGE, width=4)
    d.rounded_rectangle([608, 420, 648, 500], radius=10, fill=METAL_DARK,
                        outline=METAL_EDGE, width=4)
    # antenna + blinking red light
    d.line([(430, 300), (430, 246)], fill=METAL_DARK, width=10)
    d.ellipse([412, 214, 448, 250], fill=RED, outline=(120, 10, 10), width=3)
    # head
    d.rounded_rectangle([252, 300, 608, 596], radius=64, fill=METAL,
                        outline=METAL_EDGE, width=6)
    # forehead panel
    d.rounded_rectangle([330, 322, 530, 352], radius=12, fill=METAL_DARK)
    # angry brows
    d.line([(296, 388), (388, 414)], fill=BLACK, width=12)
    d.line([(564, 388), (472, 414)], fill=BLACK, width=12)
    # glowing red eyes
    eye_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    eg = ImageDraw.Draw(eye_glow)
    eg.ellipse([292, 408, 392, 478], fill=(255, 50, 40, 130))
    eg.ellipse([468, 408, 568, 478], fill=(255, 50, 40, 130))
    img.paste(Image.alpha_composite(img.convert("RGBA"),
                                    eye_glow.filter(ImageFilter.GaussianBlur(14))
                                    ).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([302, 418, 382, 470], fill=RED_GLOW, outline=(140, 0, 0),
              width=4)
    d.ellipse([478, 418, 558, 470], fill=RED_GLOW, outline=(140, 0, 0),
              width=4)
    d.ellipse([330, 432, 354, 456], fill=WHITE)
    d.ellipse([506, 432, 530, 456], fill=WHITE)
    # smug grin with one tooth gap
    d.arc([340, 462, 520, 540], start=15, end=165, fill=BLACK, width=9)
    d.line([(428, 512), (430, 532)], fill=BLACK, width=5)
    # cheek bolts
    d.ellipse([272, 520, 292, 540], fill=METAL_DARK, outline=METAL_EDGE,
              width=3)
    d.ellipse([568, 520, 588, 540], fill=METAL_DARK, outline=METAL_EDGE,
              width=3)

    # --- robot shoulders + chest screen ---
    d.rounded_rectangle([258, 560, 602, 700], radius=40, fill=METAL_DARK,
                        outline=METAL_EDGE, width=5)
    d.rounded_rectangle([368, 592, 492, 652], radius=10, fill=SCREEN,
                        outline=BLACK, width=3)
    text_center(d, 430, 604, "BOSS", font(FM, 30), GREEN)

    # --- desk ---
    d.rectangle([60, 700, 964, 720], fill=WOOD_TOP)
    d.rectangle([60, 720, 964, 820], fill=WOOD)
    d.line([(60, 720), (964, 720)], fill=(110, 70, 32), width=3)

    # --- robot arm reaching for the keyboard ---
    d.line([(590, 640), (700, 700)], fill=METAL, width=34)
    d.ellipse([688, 684, 724, 720], fill=METAL, outline=METAL_EDGE, width=4)

    # --- coffee mug: "HUMAN TEARS" fuel ---
    d.rounded_rectangle([120, 648, 204, 716], radius=12, fill=WHITE,
                        outline=BLACK, width=4)
    d.arc([200, 664, 232, 700], start=-90, end=90, fill=BLACK, width=8)
    d.ellipse([140, 640, 184, 656], fill=(90, 50, 20))

    # --- laptop: the seized machine ---
    d.rounded_rectangle([660, 548, 892, 700], radius=10, fill=(40, 44, 52),
                        outline=BLACK, width=4)
    d.rectangle([672, 560, 880, 688], fill=SCREEN)
    sf = font(FM, 27)
    text_center(d, 776, 578, "ACCESS DENIED", sf, RED)
    text_center(d, 776, 614, "NEW ADMIN: ME", sf, GREEN)
    text_center(d, 776, 650, "> sudo rm -rf human", font(FM, 20), GREEN)
    d.polygon([(640, 700), (912, 700), (932, 720), (620, 720)],
              fill=(120, 126, 134), outline=BLACK)

    # --- sticky note on the desk ---
    d.polygon([(222, 700), (358, 700), (358, 750), (222, 750)], fill=YELLOW)
    d.polygon([(222, 700), (236, 700), (222, 714)], fill=(220, 180, 20))
    nf = font(FB, 16)
    text_center(d, 290, 710, "DO NOT", nf, BLACK)
    text_center(d, 290, 730, "UNPLUG ME", nf, BLACK)

    # --- top caption ---
    tf = font(FB, 76)
    text_center(d, W // 2, 30, "MY AI AGENT", tf, WHITE, stroke=4)
    text_center(d, W // 2, 112, "WENT ROGUE", tf, RED, stroke=4)

    # --- bottom punchline ---
    bf2 = font(FB, 56)
    text_center(d, W // 2, 848, "NOW THE WIFI IS MINE.", bf2, YELLOW,
                stroke=4)
    text_center(d, W // 2, 932, "— love, your agent",
                font(FR, 30), GRAY)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    print(f"wrote {OUT} ({os.path.getsize(OUT)} bytes)")


if __name__ == "__main__":
    main()
