from PIL import Image, ImageDraw, ImageFont
import os
from datetime import date

def add_watermark(image_path: str, portal: str = "LHDN") -> str:
    portal_texts = {
        "LHDN": "FOR LHDN USE ONLY",
        "PTPTN": "FOR PTPTN USE ONLY",
        "EPF": "FOR EPF USE ONLY"
    }
    
    watermark_text = portal_texts.get(portal, f"FOR {portal} USE ONLY")
    watermark_text += f" | GovEase AI | {date.today()}"
    
    img = Image.open(image_path)
    
    # FIX: Convert RGBA to RGB to support JPEG
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Draw watermark diagonally
    for y in range(0, height, 200):
        draw.text(
            (width // 6, y),
            watermark_text,
            fill=(255, 0, 0),
            font=font
        )
    
    # Always save as PNG to avoid JPEG issues
    output_path = image_path.rsplit(".", 1)[0] + f"_watermarked_{portal}.png"
    img.save(output_path, "PNG")
    
    print(f"Watermark applied: {output_path}")
    return output_path

def watermark_for_all_portals(image_path: str) -> dict:
    results = {}
    for portal in ["LHDN", "PTPTN", "EPF"]:
        results[portal] = add_watermark(image_path, portal)
    return results