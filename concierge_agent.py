import anthropic
import base64
import json
import re
import os
from pathlib import Path

# 从 config.py 读取 API Key
try:
    from config import ILMU_API_KEY
except ImportError:
    ILMU_API_KEY = os.environ.get("ILMU_API_KEY")

client = anthropic.Anthropic(
    base_url="https://api.ilmu.ai/anthropic",
    api_key=ILMU_API_KEY
)

# ============================================================
# 全局变量
# ============================================================
user_data = {
    "full_name": None,
    "ic_number": None,
    "address": None,
    "date_of_birth": None,
    "email": None,
    "phone": None,
    "gender": None,
    "monthly_income": None,
    "employer": None,
    "parent_income": None,
    "degree_name": None,
    "university": None,
    "epf_number": None,
    "tax_number": None,
    "withdrawal_type": None,
    "bank_name": None,
    "bank_account": None,
    "postcode": None,
    "city": None,
    "state": None
}

collected_fields = set()
current_portal = None
conversation_step = "asking_name"


# ============================================================
# Portal 文件要求
# ============================================================
portal_file_requirements = {
    "PTPTN": {
        "required": ["IC Photo", "Parent IC Photo", "Salary Slip of Parent", "Offer Letter from University"],
        "optional": ["SPM Result", "University Registration Slip"],
        "description": "For PTPTN loan application, please prepare: IC photo, parent's IC, parent's salary slip, and university offer letter."
    },
    "EPF": {
        "required": ["IC Photo", "EPF Statement", "Bank Account Book"],
        "optional": ["Employment Letter", "Salary Slip"],
        "description": "For EPF withdrawal, please prepare: IC photo, EPF statement, and bank account book."
    },
    "LHDN": {
        "required": ["IC Photo", "EA Form", "Salary Slip"],
        "optional": ["Rental Agreement", "Business Registration"],
        "description": "For LHDN tax filing, please prepare: IC photo, EA form, and salary slips."
    }
}


def get_file_requirements(portal):
    """获取指定 portal 的文件要求"""
    return portal_file_requirements.get(portal, portal_file_requirements["LHDN"])


# ============================================================
# 地址提取函数
# ============================================================
def extract_address_details(address):
    """从地址中提取 postcode, city, state"""
    result = {
        "postcode": None,
        "city": None,
        "state": None
    }
    
    if not address:
        return result
    
    # 提取 Postcode (5位数字)
    postcode_match = re.search(r'\b(\d{5})\b', address)
    if postcode_match:
        result["postcode"] = postcode_match.group(1)
    
    address_lower = address.lower()
    
    # State and City mapping
    state_city_map = [
        {"keywords": ["kuala lumpur", "kl", "wilayah persekutuan"], "state": "Kuala Lumpur", "city": "Kuala Lumpur"},
        {"keywords": ["selangor", "shah alam", "petaling jaya", "subang", "klang", "putrajaya", "cyberjaya"], "state": "Selangor", "city": "Shah Alam"},
        {"keywords": ["penang", "pulau pinang", "george town", "butterworth"], "state": "Penang", "city": "George Town"},
        {"keywords": ["johor", "johor bahru", "jb", "batu pahat", "muar"], "state": "Johor", "city": "Johor Bahru"},
        {"keywords": ["negeri sembilan", "seremban", "port dickson"], "state": "Negeri Sembilan", "city": "Seremban"},
        {"keywords": ["perak", "ipoh", "taiping", "teluk intan"], "state": "Perak", "city": "Ipoh"},
        {"keywords": ["pahang", "kuantan", "cameron highlands"], "state": "Pahang", "city": "Kuantan"},
        {"keywords": ["kedah", "alor setar", "sungai petani"], "state": "Kedah", "city": "Alor Setar"},
        {"keywords": ["kelantan", "kota bharu", "kota bahru"], "state": "Kelantan", "city": "Kota Bharu"},
        {"keywords": ["terengganu", "kuala terengganu"], "state": "Terengganu", "city": "Kuala Terengganu"},
        {"keywords": ["melaka", "malacca", "bandar melaka"], "state": "Melaka", "city": "Melaka"},
        {"keywords": ["perlis", "kangar"], "state": "Perlis", "city": "Kangar"},
        {"keywords": ["sabah", "kota kinabalu", "sandakan", "tawau"], "state": "Sabah", "city": "Kota Kinabalu"},
        {"keywords": ["sarawak", "kuching", "sibu", "miri", "bintulu"], "state": "Sarawak", "city": "Kuching"}
    ]
    
    for item in state_city_map:
        for keyword in item["keywords"]:
            if keyword in address_lower:
                result["state"] = item["state"]
                if result["city"] is None:
                    result["city"] = item["city"]
                break
        if result["state"]:
            break
    
    # 如果没匹配到州属，默认 Kuala Lumpur
    if not result["state"]:
        if "kuala lumpur" in address_lower or "kl" in address_lower:
            result["state"] = "Kuala Lumpur"
            result["city"] = "Kuala Lumpur"
    
    return result


# ============================================================
# 辅助函数
# ============================================================
def format_summary():
    """格式化显示已收集的数据"""
    summary = ""
    if user_data.get("full_name"):
        summary += f"\n👤 Name: {user_data['full_name']}"
    if user_data.get("ic_number"):
        summary += f"\n🆔 IC: {user_data['ic_number']}"
    if user_data.get("address"):
        summary += f"\n📍 Address: {user_data['address']}"
    if user_data.get("postcode"):
        summary += f"\n📮 Postcode: {user_data['postcode']}"
    if user_data.get("city"):
        summary += f"\n🏙️ City: {user_data['city']}"
    if user_data.get("state"):
        summary += f"\n🗺️ State: {user_data['state']}"
    if user_data.get("date_of_birth"):
        summary += f"\n🎂 DOB: {user_data['date_of_birth']}"
    if user_data.get("email"):
        summary += f"\n📧 Email: {user_data['email']}"
    if user_data.get("phone"):
        summary += f"\n📱 Phone: {user_data['phone']}"
    if user_data.get("gender"):                             
        summary += f"\n⚧ Gender: {user_data['gender']}"
    if user_data.get("monthly_income"):
        summary += f"\n💰 Income: RM {user_data['monthly_income']}"
    if user_data.get("employer"):
        summary += f"\n🏢 Employer: {user_data['employer']}"
    if user_data.get("parent_income"):
        summary += f"\n👪 Parent Income: RM {user_data['parent_income']}"
    if user_data.get("degree_name"):
        summary += f"\n🎓 Degree: {user_data['degree_name']}"
    if user_data.get("university"):
        summary += f"\n🏛️ University: {user_data['university']}"
    if user_data.get("epf_number"):
        summary += f"\n💳 EPF Number: {user_data['epf_number']}"
    if user_data.get("tax_number"):
        summary += f"\n📄 Tax Number: {user_data['tax_number']}"
    if user_data.get("withdrawal_type"):
        summary += f"\n📋 Withdrawal Type: {user_data['withdrawal_type']}"
    if user_data.get("bank_name"):
        summary += f"\n🏦 Bank: {user_data['bank_name']}"
    if user_data.get("bank_account"):
        summary += f"\n🔢 Bank Account: {user_data['bank_account']}"
    return summary


# ============================================================
# IC 生日提取函数
# ============================================================
def extract_birthday_from_ic(ic_number):
    """从 IC 号码提取生日"""
    if not ic_number or ic_number == "XXX":
        return None
    
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


# ============================================================
# 图像处理函数
# ============================================================
def encode_image(image_path):
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    extension = Path(image_path).suffix.lower()
    media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    media_type = media_types.get(extension, "image/jpeg")
    return image_data, media_type


def extract_document_data(image_path):
    """从图片中提取 IC 信息"""
    image_data, media_type = encode_image(image_path)
    
    response = client.messages.create(
        model="ilmu-glm-5.1",
        max_tokens=1000,
        messages=[{
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
                    "text": """Extract from this Malaysian IC card.

Return ONLY JSON: {"full_name": "...", "ic_number": "...", "address": "...", "date_of_birth": "..."}

If a field is not visible, use null."""
                }
            ]
        }]
    )
    
    raw = response.content[0].text.strip()
    print("RAW GLM RESPONSE:", raw)
    
    try:
        return json.loads(raw)
    except:
        json_match = re.search(r'\{[^{}]*\}', raw)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return {"full_name": None, "ic_number": None, "address": None, "date_of_birth": None}


# ============================================================
# 文本提取函数
# ============================================================
def extract_from_text(user_text):
    result = {
        "full_name": None,
        "ic_number": None,
        "address": None,
        "date_of_birth": None,
        "email": None,
        "phone": None,
        "monthly_income": None,
        "employer": None,
        "parent_income": None,
        "degree_name": None,
        "university": None,
        "epf_number": None,
        "tax_number": None,
        "withdrawal_type": None,
        "bank_name": None,
        "bank_account": None,
        "postcode": None,
        "city": None,
        "state": None
    }
    
    # 提取 IC
    ic_match = re.search(r'(\d{6}-\d{2}-\d{4})', user_text)
    if ic_match:
        result["ic_number"] = ic_match.group(1)
        birthday = extract_birthday_from_ic(result["ic_number"])
        if birthday:
            result["date_of_birth"] = birthday["formatted"]
    # Only extract name if we don't already have one
    if not user_data.get("full_name"):
        name_match = re.search(r'(?:my name is|name[:\s]+)([A-Za-z\s]{3,}?)(?:,|\.|IC|$)', user_text, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip()
            if len(full_name) > 2:
                result["full_name"] = full_name
        else:
            direct_match = re.search(r'^([A-Za-z\s]{3,})$', user_text.strip())
            if direct_match:
                result["full_name"] = direct_match.group(1).strip()
    # 提取姓名 - 修复版
    name_match = re.search(r'(?:my name is|name[:\s]+)([A-Za-z\s]{3,}?)(?:,|\.|IC|$)', user_text, re.IGNORECASE)
    if name_match:
        full_name = name_match.group(1).strip()
        if len(full_name) > 2:
            result["full_name"] = full_name
    else:
        direct_match = re.search(r'^([A-Za-z\s]{3,})$', user_text.strip())
        if direct_match:
            result["full_name"] = direct_match.group(1).strip()
    
    # 提取地址
    address_match = re.search(r'(?:address|alamat)[:\s]+(.+?)(?:$)', user_text, re.IGNORECASE)
    if address_match:
        result["address"] = address_match.group(1).strip()
        addr_details = extract_address_details(result["address"])
        if addr_details["postcode"]:
            result["postcode"] = addr_details["postcode"]
        if addr_details["city"]:
            result["city"] = addr_details["city"]
        if addr_details["state"]:
            result["state"] = addr_details["state"]
    
    # 提取邮箱
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_text)
    if email_match:
        result["email"] = email_match.group(0)
    
    # 提取电话
    phone_match = re.search(r'(\d{9,11})', user_text)
    if phone_match:
        result["phone"] = phone_match.group(1)
    
    # 提取收入
    income_match = re.search(r'(?:income|salary|gaji|ringgit|RM)\s*[:]?\s*(\d+(?:,\d+)?)', user_text, re.IGNORECASE)
    if income_match:
        result["monthly_income"] = income_match.group(1)
    
    # 提取父母收入
    parent_income_match = re.search(r'(?:parent income|parent\'s income|pendapatan ibu bapa)[:\s]+(\d+)', user_text, re.IGNORECASE)
    if parent_income_match:
        result["parent_income"] = parent_income_match.group(1)
    
    # 提取学位名称
    degree_match = re.search(r'(?:degree|course|program|ijazah)[:\s]+(.+?)(?:,|\.|$)', user_text, re.IGNORECASE)
    if degree_match:
        result["degree_name"] = degree_match.group(1).strip()
    
    # 提取大学名称 - 完全修复版
    # 方法1：匹配完整的 "University of XXX"
    uni_match_full = re.search(r'(University\s+of\s+[A-Za-z\s]+)', user_text, re.IGNORECASE)
    if uni_match_full:
        result["university"] = uni_match_full.group(1).strip()
        print(f"[DEBUG] Extracted university (full): {result['university']}")
    else:
        # 方法2：匹配 "university: XXX" 格式
        uni_match = re.search(r'(?:university|institution|universiti)[:\s]+([A-Za-z\s]+?)(?:,|\.|$)', user_text, re.IGNORECASE)
        if uni_match:
            uni_name = uni_match.group(1).strip()
            # 如果提取的是 "of Malaya"，尝试从原文中获取完整名称
            if uni_name.lower().startswith('of'):
                full_match = re.search(r'(University\s+of\s+[A-Za-z\s]+)', user_text, re.IGNORECASE)
                if full_match:
                    uni_name = full_match.group(1).strip()
            result["university"] = uni_name
            print(f"[DEBUG] Extracted university (fallback): {result['university']}")
    
    # 提取 EPF 号码
    epf_match = re.search(r'(?:epf|kwsp)[:\s]+(\d{7,})', user_text, re.IGNORECASE)
    if epf_match:
        result["epf_number"] = epf_match.group(1)
    
    # 提取雇主
    employer_match = re.search(r'(?:employer|company|majikan)[:\s]+([A-Za-z\s]+)(?:,|$)', user_text, re.IGNORECASE)
    if employer_match:
        result["employer"] = employer_match.group(1).strip()
    
    # 提取税务号码
    tax_match = re.search(r'(?:tax|SG)[:\s]*(SG\d+)', user_text, re.IGNORECASE)
    if tax_match:
        result["tax_number"] = tax_match.group(1)
    
    # 提取提款类型
    withdrawal_match = re.search(r'(?:withdrawal|pengeluaran)[:\s]+([A-Za-z\s]+)', user_text, re.IGNORECASE)
    if withdrawal_match:
        result["withdrawal_type"] = withdrawal_match.group(1).strip()
    
    # 提取银行名称
    bank_match = re.search(r'(?:bank|maybank|cimb|public|rhb|hong leong)[:\s]+([A-Za-z\s]+)', user_text, re.IGNORECASE)
    if bank_match:
        result["bank_name"] = bank_match.group(1).strip()
    
    # 提取银行账号
    account_match = re.search(r'(?:account|akaun)[:\s]+(\d{8,12})', user_text, re.IGNORECASE)
    if account_match:
        result["bank_account"] = account_match.group(1)
    
    
    return result

        # 提取姓名 - 修复版，排除服务名称
    # 排除的关键词
    excluded_names = ["PTPTN", "EPF", "LHDN", "NEW", "reset", "ptptn", "epf", "lhdn", "new"]

    name_match = re.search(r'(?:my name is|name[:\s]+)([A-Za-z\s]{3,}?)(?:,|\.|IC|$)', user_text, re.IGNORECASE)
    if name_match:
        full_name = name_match.group(1).strip()
        # 检查是否是服务名称
        if full_name.upper() not in [x.upper() for x in excluded_names] and len(full_name) > 2:
            result["full_name"] = full_name
            print(f"[DEBUG] Extracted full_name: {result['full_name']}")
    else:
        # 只有当用户输入不是服务名称时，才尝试直接匹配
        direct_match = re.search(r'^([A-Za-z\s]{3,})$', user_text.strip())
        if direct_match:
            potential_name = direct_match.group(1).strip()
            if potential_name.upper() not in [x.upper() for x in excluded_names]:
                result["full_name"] = potential_name
                print(f"[DEBUG] Extracted full_name (direct): {result['full_name']}")


# ============================================================
# 主对话函数
# ============================================================
def chat_response(message):
    global conversation_step, user_data, current_portal
    
    msg = message.strip()
    
    # 重置命令
    if msg.lower() == "reset":
        clear_user_data()
        return "🔄 Conversation reset. What is your full name?"
    
    # ========== NEW 命令 - 添加新服务（保留所有数据） ==========
    if msg.lower() == "new":
        # 不清空任何数据，只重置 portal 状态
        current_portal = None
        conversation_step = "asking_portal"
        if user_data.get("full_name") and len(user_data["full_name"]) <= 2:
            pass
        summary = format_summary()
        
        return f"""🔄 **Add another service to your profile!**

{summary}

📌 Your existing data is preserved.

Now tell me which **additional service** you need:

🏦 Type **PTPTN** for education loan
💼 Type **EPF** for savings
📄 Type **LHDN** for tax filing

Type 'reset' to clear all data."""
    
    # 如果数据为空但状态不对，强制重置到问姓名
    if not user_data.get("full_name") and conversation_step != "asking_name":
        conversation_step = "asking_name"
        return "Hello! I'm GovEase AI. What is your full name?"
    
    # ========== 步骤 1：问姓名 ==========
    if conversation_step == "asking_name":
        if msg:
            user_data["full_name"] = msg
            conversation_step = "asking_ic"
            return f"✅ Hi {msg}! Next, what is your IC number?\n\n📌 **Format:** XXXXXX-XX-XXXX"
        return "❓ What is your full name?"
    
    # ========== 步骤 2：问 IC（自动提取生日） ==========
    if conversation_step == "asking_ic":
        ic_match = re.search(r'(\d{6}-\d{2}-\d{4})', msg)
        if ic_match:
            user_data["ic_number"] = ic_match.group(1)
            birthday = extract_birthday_from_ic(user_data["ic_number"])
            if birthday:
                user_data["date_of_birth"] = birthday["formatted"]
                print(f"[DEBUG] Auto-extracted DOB: {user_data['date_of_birth']}")
            conversation_step = "asking_address"
            return f"✅ IC saved\n🎂 DOB auto-detected: {user_data['date_of_birth']}\n\n📍 What is your address?"
        else:
            return "❌ Invalid IC format.\n\n📌 **Please use format:** XXXXXX-XX-XXXX"
    
    # ========== 步骤 3：问地址（自动提取 postcode, city, state） ==========
    if conversation_step == "asking_address":
        if len(msg) > 3:
            user_data["address"] = msg
            # 自动提取地址详情并保存
            addr_details = extract_address_details(msg)
            if addr_details["postcode"]:
                user_data["postcode"] = addr_details["postcode"]
            if addr_details["city"]:
                user_data["city"] = addr_details["city"]
            if addr_details["state"]:
                user_data["state"] = addr_details["state"]
            print(f"[DEBUG] Extracted - Postcode: {user_data['postcode']}, City: {user_data['city']}, State: {user_data['state']}")
            conversation_step = "asking_email"
            return f"✅ Address saved.\n\n📧 **What is your email address?**"
        else:
            return "📍 Please provide a valid address."
    
    # ========== 步骤 4：问邮箱 ==========
    if conversation_step == "asking_email":
        if '@' in msg and '.' in msg:
            user_data["email"] = msg
            conversation_step = "asking_phone"
            return f"✅ Email saved.\n\n📱 **What is your phone number?**"
        elif len(msg) > 5:
            user_data["email"] = msg
            conversation_step = "asking_phone"
            return f"✅ Email saved.\n\n📱 **What is your phone number?**"
        else:
            return "📧 Please provide your email address."
    
    # ========== 步骤 5：问电话 ==========
    if conversation_step == "asking_phone":
        phone_match = re.search(r'(\d{9,11})', msg)
        if phone_match:
            user_data["phone"] = phone_match.group(1)
        elif len(msg) > 5:
            user_data["phone"] = msg
        else:
            user_data["phone"] = "0123456789"

        conversation_step = "asking_gender"
        return "✅ Phone saved.\n\n⚧ **What is your gender?**\n\nType **Male** or **Female**"

    # ========== 步骤 6：问性别 ==========
    if conversation_step == "asking_gender":
        msg_lower = msg.lower().strip()
        if msg_lower in ["male", "lelaki", "m", "laki"]:
            user_data["gender"] = "Male"
        elif msg_lower in ["female", "perempuan", "f", "wanita"]:
            user_data["gender"] = "Female"
        else:
            return "⚧ Please type **Male** or **Female**"
        
        conversation_step = "asking_portal"
        summary = format_summary()
        return f"""✅ Phone saved.{summary}

🎉 **Basic information collected!**

Now tell me which service you need:

🏦 Type **PTPTN** for education loan
💼 Type **EPF** for savings
📄 Type **LHDN** for tax filing"""
    
    # ========== 步骤 6：选择服务 ==========
    if conversation_step == "asking_portal":
        portal = msg.lower()
        
        if portal == "ptptn":
            current_portal = "PTPTN"
            conversation_step = "asking_ptptn_details"
            return f"""📚 You selected **PTPTN**!

What is your parent's monthly income?"""
        
        elif portal == "epf":
            current_portal = "EPF"
            conversation_step = "asking_epf_details"
            return f"""💼 You selected **EPF**!

What is your EPF membership number?"""
        
        elif portal == "lhdn":
            current_portal = "LHDN"
            conversation_step = "asking_lhdn_details"
            return f"""📄 You selected **LHDN**!

What is your income tax number?"""
        
        else:
            return "Please type: **PTPTN**, **EPF**, or **LHDN**"
    
    # ========== 步骤 7：PTPTN 额外信息 ==========
    if conversation_step == "asking_ptptn_details":
        if not user_data.get("parent_income"):
            income_match = re.search(r'(\d{4,})', msg)
            if income_match:
                user_data["parent_income"] = income_match.group(1)
                return f"✅ Parent income: RM {user_data['parent_income']}\n\nWhat is your degree/program name?"
            return "What is your parent's monthly income?"
        
        elif not user_data.get("degree_name"):
            if len(msg) > 2:
                user_data["degree_name"] = msg
                return f"✅ Degree: {user_data['degree_name']}\n\nWhich university do you attend?"
            return "What is your degree/program name?"
        
        elif not user_data.get("university"):
            if len(msg) > 2:
                # 强制保存，不做任何处理
                user_data["university"] = msg
                conversation_step = "ready"
                summary = format_summary()
                return f"""✅ Perfect! University saved as: {user_data['university']}

        {summary}

        🎯 Click 'Send Data to Browser Extension' to use this data.

        Type NEW to add another service."""
                summary = format_summary()
                return f"""✅ Perfect! Here's your complete information:{summary}

🎯 Click 'Send Data to Browser Extension' to use this data.

Type NEW to add another service."""
            return "What is the name of your university?"
        
        else:
            conversation_step = "ready"
            return f"""✅ Your data is ready!

🎯 Click 'Send Data to Browser Extension' to auto-fill forms.

Type NEW to add another service."""
    
    # ========== 步骤 8：EPF 额外信息 ==========
    if conversation_step == "asking_epf_details":
        if not user_data.get("epf_number"):
            if msg.isdigit() and len(msg) >= 7:
                user_data["epf_number"] = msg
                return f"✅ EPF number: {user_data['epf_number']}\n\nWho is your employer?"
            return "What is your EPF membership number?"
        
        elif not user_data.get("employer"):
            if msg and not msg.isdigit():
                user_data["employer"] = msg
                return f"✅ Employer: {user_data['employer']}\n\nWhat is your monthly income?"
            return "What is your employer's name?"
        
        elif not user_data.get("monthly_income"):
            income_match = re.search(r'(\d{4,})', msg)
            if income_match:
                user_data["monthly_income"] = income_match.group(1)
                return f"✅ Monthly income: RM {user_data['monthly_income']}\n\nWhat type of withdrawal? (Umur 50/55, Pengeluaran Perumahan, etc.)"
            return "What is your monthly income?"
        
        elif not user_data.get("withdrawal_type"):
            if len(msg) > 2:
                user_data["withdrawal_type"] = msg
                return f"✅ Withdrawal type: {user_data['withdrawal_type']}\n\nWhat is your bank name?"
            return "What type of withdrawal are you applying for?"
        
        elif not user_data.get("bank_name"):
            if len(msg) > 2:
                user_data["bank_name"] = msg
                return f"✅ Bank: {user_data['bank_name']}\n\nWhat is your bank account number?"
            return "What is your bank name?"
        
        elif not user_data.get("bank_account"):
            if msg.isdigit() and len(msg) >= 8:
                user_data["bank_account"] = msg
                conversation_step = "ready"
                summary = format_summary()
                return f"""✅ Perfect! Here's your complete information:{summary}

🎯 Click 'Send Data to Browser Extension' to use this data.

Type NEW to add another service."""
            return "What is your bank account number?"
        
        else:
            conversation_step = "ready"
            return f"""✅ Your data is ready!

🎯 Click 'Send Data to Browser Extension' to auto-fill forms.

Type NEW to add another service."""
    
    # ========== 步骤 9：LHDN 额外信息 ==========
    if conversation_step == "asking_lhdn_details":
        if not user_data.get("tax_number"):
            if len(msg) > 2:
                user_data["tax_number"] = msg
                return f"✅ Tax number: {user_data['tax_number']}\n\nWhat is your monthly income?"
            return "What is your income tax number?"
        
        elif not user_data.get("monthly_income"):
            income_match = re.search(r'(\d{4,})', msg)
            if income_match:
                user_data["monthly_income"] = income_match.group(1)
                conversation_step = "ready"
                summary = format_summary()
                return f"""✅ Perfect! Here's your complete information:{summary}

🎯 Click 'Send Data to Browser Extension' to use this data.

Type NEW to add another service."""
            return "What is your monthly income?"
        
        else:
            conversation_step = "ready"
            return f"""✅ Your data is ready!

🎯 Click 'Send Data to Browser Extension' to auto-fill forms.

Type NEW to add another service."""
    
    # ========== 就绪状态 ==========
    if conversation_step == "ready":
        summary = format_summary()
        return f"""✅ Your data is ready!{summary}

🎯 Click **'Send Data to Browser Extension'** to use this data.

📌 Type **NEW** to add another service (PTPTN/EPF/LHDN)

Type 'reset' to start over."""
    
    # 默认
    conversation_step = "asking_name"
    return "Hello! I'm GovEase AI. What is your full name?"


# ============================================================
# 数据管理函数
# ============================================================
def get_user_data():
    return user_data


def update_user_data(data):
    global user_data, collected_fields
    for key, value in data.items():
        if value and value != "Not found" and value != "null":
            # Protect full_name — never overwrite once set
            if key == "full_name" and user_data.get("full_name"):
                print(f"[DEBUG] Skipping overwrite of full_name with: '{value}'")
                continue
            user_data[key] = value
            collected_fields.add(key)
    return user_data


def clear_user_data():
    global user_data, collected_fields, current_portal, conversation_step
    user_data = {
        "full_name": None, "ic_number": None, "address": None,
        "date_of_birth": None, "email": None, "phone": None,"gender": None,
        "monthly_income": None, "employer": None,
        "parent_income": None, "degree_name": None, "university": None,
        "epf_number": None, "tax_number": None,
        "withdrawal_type": None, "bank_name": None, "bank_account": None,
        "postcode": None, "city": None, "state": None
    }
    collected_fields = set()
    current_portal = None
    conversation_step = "asking_name"


def reset_conversation():
    clear_user_data()