from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

def add_watermark(image_path: str, portal: str = "LHDN") -> str:
    """
    为图片添加水印
    portal: LHDN, PTPTN, EPF
    """
    portal_texts = {
        "LHDN": "FOR LHDN USE ONLY",
        "PTPTN": "FOR PTPTN USE ONLY", 
        "EPF": "FOR EPF USE ONLY"
    }
    
    # 获取当前时间
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    watermark_text = portal_texts.get(portal, f"FOR {portal} USE ONLY")
    watermark_text += f" | GovEase AI | {timestamp}"
    
    # 打开图片
    img = Image.open(image_path)
    
    # 转换模式（支持 RGBA）
    if img.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        if img.mode == "RGBA":
            background.paste(img, mask=img.split()[-1])
        else:
            background.paste(img)
        img = background
    
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # 尝试使用系统字体，如果找不到则使用默认字体
    try:
        # 字体大小：图片宽度的 1/20
        font_size = max(20, int(width / 20))
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    # 计算文字位置（居中）
    try:
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        text_width = len(watermark_text) * font_size // 2
        text_height = font_size
    
    # 多行水印（对角线和中心）
    positions = [
        (width // 4, height // 4),
        (width // 2 - text_width // 2, height // 2 - text_height // 2),
        (width * 3 // 4 - text_width, height * 3 // 4 - text_height)
    ]
    
    for x, y in positions:
        draw.text((x, y), watermark_text, fill=(255, 0, 0, 128), font=font)
    
    # 保存水印图片
    output_filename = image_path.rsplit(".", 1)[0] + f"_watermarked_{portal}.png"
    img.save(output_filename, "PNG")
    
    print(f"[Guardian] Watermark applied: {output_filename}")
    return output_filename


def watermark_for_all_portals(image_path: str) -> dict:
    """为所有 portal 添加水印"""
    results = {}
    for portal in ["LHDN", "PTPTN", "EPF"]:
        results[portal] = add_watermark(image_path, portal)
    return results