import anthropic
import base64
import json
from pathlib import Path

client = anthropic.Anthropic(
    base_url="https://api.ilmu.ai/anthropic",
    api_key=""  # paste complete sk-... key
)


def encode_image(image_path):
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    extension = Path(image_path).suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png"
    }
    media_type = media_types.get(extension, "image/jpeg")
    return image_data, media_type

def extract_document_data(image_path):
    image_data, media_type = encode_image(image_path)
    response = client.messages.create(
        model="ilmu-glm-5.1",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": """You are a document OCR agent for a Malaysian 
government service assistant. Extract all information 
from this document.

Return ONLY a JSON object:
{
  "document_type": "IC or salary_slip or unknown",
  "full_name": "extracted name or null",
  "ic_number": "extracted IC number or null",
  "address": "extracted address or null",
  "date_of_birth": "extracted DOB or null",
  "monthly_income": "extracted income or null",
  "employer": "extracted employer or null",
  "confidence": "high or medium or low"
}

Return ONLY the JSON. No explanation."""
                    }
                ]
            }
        ]
    )
    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def chat_response(message):
    response = client.messages.create(
        model="ilmu-glm-5.1",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": f"""You are GovEase AI, a friendly assistant helping 
Malaysians with government services like LHDN, PTPTN, EPF.
Be helpful, friendly, short. Reply in same language as user.
User message: {message}"""
            }
        ]
    )
    return response.content[0].text

def extract_from_text(user_text):
    response = client.messages.create(
        model="ilmu-glm-5.1",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": f"""Parse this text and extract any personal details you find.
Output a valid JSON object with these exact keys.
If a value is not found, use null.

Input: {user_text}

Output format (return this exact structure):
{{
  "full_name": null,
  "ic_number": null,
  "address": null,
  "date_of_birth": null,
  "monthly_income": null,
  "confidence": "high"
}}

Fill in the values you find. Return ONLY the JSON object."""
            }
        ]
    )
    
    raw = response.content[0].text.strip()
    print("GLM raw response:", raw)
    
    # Extract ONLY the JSON part using regex
    import re
    json_match = re.search(r'\{.*?\}', raw, re.DOTALL)
    
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    
    # Fallback — manual regex extraction
    result = {
        "full_name": None,
        "ic_number": None,
        "address": None,
        "date_of_birth": None,
        "monthly_income": None,
        "confidence": "low"
    }
    
    name_match = re.search(
        r'(?:my name is|name[:\s]+)([A-Za-z\s]+?)(?:,|IC|$)',
        user_text, re.IGNORECASE
    )
    ic_match = re.search(r'(\d{6}-\d{2}-\d{4})', user_text)
    address_match = re.search(
        r'(?:address|alamat)[:\s]+(.+?)(?:$)',
        user_text, re.IGNORECASE
    )
    
    if name_match:
        result["full_name"] = name_match.group(1).strip()
        result["confidence"] = "medium"
    if ic_match:
        result["ic_number"] = ic_match.group(1).strip()
        result["confidence"] = "medium"
    if address_match:
        result["address"] = address_match.group(1).strip()

    if result.get("ic_number") and not result.get("date_of_birth"):
        birthday = extract_birthday_from_ic(result["ic_number"])
        if birthday:
            result["date_of_birth"] = birthday["formatted"]
            result["dob_day"] = birthday["day"]
            result["dob_month"] = birthday["month"]
            result["dob_year"] = birthday["year"]
    
    result["confidence"] = result.get("confidence", "medium")
    return result

def extract_birthday_from_ic(ic_number):
    import re
    ic_clean = re.sub(r'[-\s]', '', ic_number)
    
    if len(ic_clean) < 6:
        return None
    
    yy = ic_clean[0:2]
    mm = ic_clean[2:4]
    dd = ic_clean[4:6]
    
    # Determine century
    year = int(yy)
    if year <= 24:  # 2000-2024
        full_year = f"20{yy}"
    else:           # 1925-1999
        full_year = f"19{yy}"
    
    months = {
        "01": "January", "02": "February", "03": "March",
        "04": "April",   "05": "May",      "06": "June",
        "07": "July",    "08": "August",   "09": "September",
        "10": "October", "11": "November", "12": "December"
    }
    
    month_name = months.get(mm, mm)
    
    return {
        "day": dd,
        "month": mm,
        "month_name": month_name,
        "year": full_year,
        "formatted": f"{dd} {month_name} {full_year}",
        "iso": f"{full_year}-{mm}-{dd}"
    }
