import anthropic
import base64
import json
import re
from pathlib import Path

try:
    from config import ILMU_API_KEY
except ImportError:
    ILMU_API_KEY = os.environ.get("ILMU_API_KEY")

client = anthropic.Anthropic(
    base_url="https://api.ilmu.ai/anthropic",
    api_key=ILMU_API_KEY
)
# 存储用户数据
user_data = {
    "full_name": None,
    "ic_number": None,
    "address": None,
    "date_of_birth": None,
    "monthly_income": None,
    "employer": None,
    "parent_income": None,      # PTPTN 需要
    "course_code": None,        # PTPTN 需要
    "university": None,         # PTPTN 需要
    "epf_number": None,         # EPF 需要
    "tax_number": None          # LHDN 需要
}

# 跟踪已收集的信息
collected_fields = set()
current_portal = None

def get_next_question():
    """根据已收集的信息，返回下一个需要问的问题"""
    
    # 基础信息检查
    if not user_data["full_name"]:
        return "what is your full name?"
    if not user_data["ic_number"]:
        return "what is your IC number? (format: 990101-14-1234)"
    if not user_data["address"]:
        return "what is your home address?"
    if not user_data["date_of_birth"]:
        return "what is your date of birth?"
    
    # 根据用户选择的 portal 收集额外信息
    if current_portal == "PTPTN":
        if not user_data["parent_income"]:
            return "For PTPTN loan application, what is your parent's monthly income?"
        if not user_data["course_code"]:
            return "What is your course code for the PTPTN application?"
        if not user_data["university"]:
            return "Which university/institution are you studying at?"
        return None
        
    elif current_portal == "EPF":
        if not user_data["epf_number"]:
            return "What is your EPF membership number?"
        if not user_data["employer"]:
            return "Who is your current employer?"
        if not user_data["monthly_income"]:
            return "What is your monthly salary?"
        return None
        
    elif current_portal == "LHDN":
        if not user_data["tax_number"]:
            return "What is your income tax number (No. Cukai Pendapatan)?"
        if not user_data["monthly_income"]:
            return "What is your estimated annual/monthly income for tax filing?"
        return None
    
    # 所有信息收集完毕
    return None

def format_data_summary():
    """格式化显示已收集的数据"""
    summary = "📋 **Data Collected So Far:**\n\n"
    
    if user_data["full_name"]:
        summary += f"👤 Name: {user_data['full_name']}\n"
    if user_data["ic_number"]:
        summary += f"🆔 IC: {user_data['ic_number']}\n"
    if user_data["address"]:
        summary += f"📍 Address: {user_data['address']}\n"
    if user_data["date_of_birth"]:
        summary += f"🎂 DOB: {user_data['date_of_birth']}\n"
    if user_data["monthly_income"]:
        summary += f"💰 Income: RM {user_data['monthly_income']}\n"
    if user_data["employer"]:
        summary += f"🏢 Employer: {user_data['employer']}\n"
    if user_data["parent_income"]:
        summary += f"👪 Parent Income: RM {user_data['parent_income']}\n"
    if user_data["course_code"]:
        summary += f"📚 Course Code: {user_data['course_code']}\n"
    if user_data["university"]:
        summary += f"🎓 University: {user_data['university']}\n"
    if user_data["epf_number"]:
        summary += f"💳 EPF Number: {user_data['epf_number']}\n"
    if user_data["tax_number"]:
        summary += f"📄 Tax Number: {user_data['tax_number']}\n"
    
    return summary

def update_user_data(extracted):
    """更新用户数据并记录已收集的字段"""
    for key, value in extracted.items():
        if value and value != "Not found" and value != "null" and value != "None":
            user_data[key] = value
            collected_fields.add(key)

def extract_birthday_from_ic(ic_number):
    """从 IC 号码提取出生日期"""
    ic_clean = re.sub(r'[-\s]', '', ic_number)
    
    if len(ic_clean) < 6:
        return None
    
    yy = ic_clean[0:2]
    mm = ic_clean[2:4]
    dd = ic_clean[4:6]
    
    year = int(yy)
    if year <= 24:
        full_year = f"20{yy}"
    else:
        full_year = f"19{yy}"
    
    months = {
        "01": "January", "02": "February", "03": "March",
        "04": "April", "05": "May", "06": "June",
        "07": "July", "08": "August", "09": "September",
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
    """从文档中提取信息"""
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
                        "text": """Extract all information from this document.
Return ONLY a JSON object with these fields:
{
  "full_name": "extracted name or null",
  "ic_number": "extracted IC or null",
  "address": "extracted address or null",
  "date_of_birth": "extracted DOB or null",
  "monthly_income": "extracted income or null",
  "employer": "extracted employer or null"
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

def extract_from_text(user_text):
    """从文本中提取信息"""
    response = client.messages.create(
        model="ilmu-glm-5.1",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": f"""Parse this text and extract any personal details.
Output a valid JSON object with these exact keys.
If a value is not found, use null.

Input: {user_text}

Output format:
{{
  "full_name": null,
  "ic_number": null,
  "address": null,
  "date_of_birth": null,
  "monthly_income": null,
  "employer": null,
  "parent_income": null,
  "course_code": null,
  "university": null,
  "epf_number": null,
  "tax_number": null
}}

Return ONLY the JSON object."""
            }
        ]
    )
    
    raw = response.content[0].text.strip()
    json_match = re.search(r'\{.*?\}', raw, re.DOTALL)
    
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    
    # Fallback 手动提取
    result = {k: None for k in ["full_name", "ic_number", "address", "date_of_birth", 
                                 "monthly_income", "employer", "parent_income", "course_code",
                                 "university", "epf_number", "tax_number"]}
    
    # IC 提取
    ic_match = re.search(r'(\d{6}-\d{2}-\d{4})', user_text)
    if ic_match:
        result["ic_number"] = ic_match.group(1)
        birthday = extract_birthday_from_ic(result["ic_number"])
        if birthday:
            result["date_of_birth"] = birthday["formatted"]
    
    # 姓名提取
    name_match = re.search(r'(?:my name is|name[:\s]+)([A-Za-z\s]+?)(?:,|IC|$)', user_text, re.IGNORECASE)
    if name_match:
        result["full_name"] = name_match.group(1).strip()
    
    # 地址提取
    address_match = re.search(r'(?:address|alamat)[:\s]+(.+?)(?:$)', user_text, re.IGNORECASE)
    if address_match:
        result["address"] = address_match.group(1).strip()
    
    # 收入提取
    income_match = re.search(r'(?:income|salary|gaji)[:\s]+(\d+(?:,\d+)?)', user_text, re.IGNORECASE)
    if income_match:
        result["monthly_income"] = income_match.group(1)
    
    return result

def chat_response(message):
    """生成聊天回复，根据上下文智能回应"""
    
    # 先尝试从消息中提取数据
    extracted = extract_from_text(message)
    update_user_data(extracted)
    
    # 检查是否有数据被提取
    if any(extracted.values()):
        summary = format_data_summary()
        next_q = get_next_question()
        
        if next_q:
            reply = f"✅ Got your details!\n\n{summary}\n\n❓ {next_q}"
        else:
            reply = f"✅ All data collected!\n\n{summary}\n\n🎉 You're all set! Select a service (PTPTN/EPF/LHDN) to continue."
        
        return reply
    
    # 检查是否是 portal 选择
    if message.upper() in ["PTPTN", "EPF", "LHDN"]:
        global current_portal
        current_portal = message.upper()
        next_q = get_next_question()
        if next_q:
            return f"📋 You selected **{message.upper()}**.\n\n❓ {next_q}"
        else:
            return f"📋 You selected **{message.upper()}**.\n\n✅ All your information is ready! You can now proceed to fill forms on the portal."
    
    # 普通对话
    response = client.messages.create(
        model="ilmu-glm-5.1",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": f"""You are GovEase AI, a friendly assistant helping Malaysians with government services like LHDN, PTPTN, EPF.
Current portal selected: {current_portal or 'None'}
Collected data: {format_data_summary()}

Rules:
1. Be helpful, friendly, and short (2-3 sentences max)
2. If user provides information, acknowledge and show what's been collected
3. Suggest typing PTPTN, EPF, or LHDN to start an application
4. Reply in the same language as the user

User message: {message}"""
            }
        ]
    )
    return response.content[0].text

# 导出函数供 app.py 使用
def get_user_data():
    return user_data

def clear_user_data():
    global user_data, collected_fields, current_portal
    user_data = {
        "full_name": None, "ic_number": None, "address": None,
        "date_of_birth": None, "monthly_income": None, "employer": None,
        "parent_income": None, "course_code": None, "university": None,
        "epf_number": None, "tax_number": None
    }
    collected_fields = set()
    current_portal = None