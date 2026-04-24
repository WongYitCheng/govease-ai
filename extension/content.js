// ============================================================
// GovEase AI - Content Script
// 智能表单填充，支持名/姓拆分，大小写不敏感
// ============================================================

console.log("[GovEase] Content script loaded - FINAL VERSION")

const FIELD_MAP = {
  "full_name": [
    "name", "nama", "fullname", "full_name", "penuh",
    "full name", "complete name", "nama penuh",
    "FULL NAME", "Full Name", "Nama Penuh"
  ],
  "first_name": [
    "first", "fname", "given-name", "firstname", "nama pertama",
    "first name", "given_name", "given",
    "FIRST NAME", "First Name", "Nama Pertama"
  ],
  "last_name": [
    "last", "lname", "family-name", "surname", "lastname", "nama keluarga",
    "last name", "family_name", "family",
    "LAST NAME", "Last Name", "Nama Keluarga"
  ],
  "ic_number": [
    "ic", "nric", "mykad", "no_kad", "pengenalan", "identity",
    "id_number", "no. pengenalan", "mykad number", "ic number",
    "IC", "NRIC", "MyKad", "IC Number", "Identification Number",
    "Kad Pengenalan", "NO. KAD PENGENALAN"
  ],
  "address": [
    "address", "alamat", "addr", "street", "jalan",
    "ADDRESS", "Address", "Alamat", "Street Address"
  ],
  "date_of_birth": [
    "dob", "birth", "tarikh_lahir", "birthdate", "date of birth",
    "DOB", "Date of Birth", "Tarikh Lahir", "Birth Date"
  ],
  "monthly_income": [
    "income", "salary", "pendapatan", "gaji", "monthly",
    "earnings", "INCOME", "Salary", "Pendapatan Bulanan",
    "monthly income", "Monthly Income"
  ],
  "employer": [
    "employer", "company", "majikan", "Employer", "Company Name",
    "employer name", "Employer Name"
  ],
  "tax_number": [
    "tax", "cukai", "tax number", "no. cukai", "tax reference",
    "Tax Number", "No. Cukai", "SG"
  ],
  "email": [
    "email", "e-mail", "emel", "mail",
    "EMAIL", "Email Address", "Alamat Emel"
  ],
  "phone": [
    "phone", "telephone", "mobile", "handphone", "no telepon",
    "PHONE", "Phone Number", "No Telefon", "Mobile Number"
  ],
  "postcode": [
    "postcode", "poskod", "zip", "postal", "Postcode", "Poskod"
  ],
  "city": [
    "city", "bandar", "City", "Bandar"
  ],
  "state": [
    "state", "negeri", "State", "Negeri"
  ]
}

// 拆分 full_name 为 first name 和 last name
function splitFullName(fullName) {
    if (!fullName) return { firstName: null, lastName: null }
    
    console.log("[GovEase] Splitting name:", fullName)
    
    const trimmed = fullName.trim().split(/\s+/)
    
    if (trimmed.length === 1) {
        return { firstName: trimmed[0], lastName: null }
    } else if (trimmed.length === 2) {
        return { firstName: trimmed[0], lastName: trimmed[1] }
    } else {
        // WONG YIT CHENG → firstName: WONG, lastName: YIT CHENG
        return {
            firstName: trimmed[0],
            lastName: trimmed.slice(1).join(' ')
        }
    }
}

// 清洗 IC 号码（移除连字符）
function cleanICNumber(icNumber) {
    if (!icNumber) return null
    return icNumber.toString().replace(/[-_\s]/g, '')
}

// 从地址提取 postcode
function extractPostcode(address) {
    if (!address) return null
    const match = address.match(/\b(\d{5})\b/)
    return match ? match[1] : null
}

// 从地址提取 city
function extractCity(address) {
    if (!address) return null
    const cities = ['Kuala Lumpur', 'Shah Alam', 'Petaling Jaya', 'Subang', 'Putrajaya', 
                    'Cyberjaya', 'Johor Bahru', 'Penang', 'George Town', 'Ipoh', 
                    'Kuching', 'Kota Kinabalu', 'Melaka', 'Seremban', 'Klang']
    for (let city of cities) {
        if (address.toLowerCase().includes(city.toLowerCase())) {
            return city
        }
    }
    return null
}

// 从地址提取 state
function extractState(address) {
    if (!address) return null
    const states = {
        'Kuala Lumpur': ['Kuala Lumpur', 'KL'],
        'Selangor': ['Selangor', 'Shah Alam', 'Petaling Jaya', 'Subang', 'Klang'],
        'Penang': ['Penang', 'Pulau Pinang'],
        'Johor': ['Johor', 'Johor Bahru'],
        'Negeri Sembilan': ['Negeri Sembilan', 'Seremban'],
        'Perak': ['Perak', 'Ipoh'],
        'Pahang': ['Pahang', 'Kuantan'],
        'Sabah': ['Sabah', 'Kota Kinabalu'],
        'Sarawak': ['Sarawak', 'Kuching']
    }
    for (let [state, keywords] of Object.entries(states)) {
        for (let keyword of keywords) {
            if (address.toLowerCase().includes(keyword.toLowerCase())) {
                return state
            }
        }
    }
    return null
}

// 主填充函数
function fillForms(userData) {
    if (!userData) {
        console.log("[GovEase] No user data provided")
        return 0
    }
    
    console.log("[GovEase] Filling forms with data:", userData)
    
    // 获取或拆分姓名
    let firstName = userData.first_name
    let lastName = userData.last_name
    let fullName = userData.full_name
    
    // 如果没有拆分但有 full_name，自动拆分
    if ((!firstName || !lastName) && fullName) {
        const split = splitFullName(fullName)
        firstName = split.firstName
        lastName = split.lastName
        console.log(`[GovEase] Auto-split: First="${firstName}", Last="${lastName}"`)
    }
    
    // 清洗 IC
    const cleanIC = cleanICNumber(userData.ic_number)
    
    // 从地址提取信息
    const postcode = extractPostcode(userData.address)
    const city = extractCity(userData.address)
    const state = extractState(userData.address)
    
    // 获取所有输入框
    const inputs = document.querySelectorAll("input:not([type='password']):not([type='hidden']), textarea, select")
    let filled = 0
    const filledFields = []
    
    inputs.forEach(input => {
        if (input.disabled || input.readOnly) return
        
        // 获取所有标识符
        const id = (input.id || "").toLowerCase()
        const name = (input.name || "").toLowerCase()
        const placeholder = (input.placeholder || "").toLowerCase()
        const className = (input.className || "").toLowerCase()
        const ariaLabel = (input.getAttribute("aria-label") || "").toLowerCase()
        
        // 获取关联的 label
        let labelText = ""
        if (input.labels && input.labels.length > 0) {
            labelText = input.labels[0].innerText.toLowerCase()
        } else {
            const label = document.querySelector(`label[for="${input.id}"]`)
            if (label) labelText = label.innerText.toLowerCase()
        }
        
        const combined = `${id} ${name} ${placeholder} ${className} ${ariaLabel} ${labelText}`
        
        let valueToFill = null
        let fieldType = null
        
        // 1. 匹配 First Name
        if (!valueToFill && firstName) {
            for (const kw of FIELD_MAP["first_name"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = firstName
                    fieldType = "first_name"
                    break
                }
            }
        }
        
        // 2. 匹配 Last Name
        if (!valueToFill && lastName) {
            for (const kw of FIELD_MAP["last_name"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = lastName
                    fieldType = "last_name"
                    break
                }
            }
        }
        
        // 3. 匹配 Full Name
        if (!valueToFill && fullName) {
            for (const kw of FIELD_MAP["full_name"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = fullName
                    fieldType = "full_name"
                    break
                }
            }
        }
        
        // 4. 匹配 IC Number
        if (!valueToFill && cleanIC) {
            for (const kw of FIELD_MAP["ic_number"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = cleanIC
                    fieldType = "ic_number"
                    break
                }
            }
        }
        
        // 5. 匹配 Address
        if (!valueToFill && userData.address) {
            for (const kw of FIELD_MAP["address"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = userData.address
                    fieldType = "address"
                    break
                }
            }
        }
        
        // 6. 匹配 Date of Birth
        if (!valueToFill && userData.date_of_birth) {
            for (const kw of FIELD_MAP["date_of_birth"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = userData.date_of_birth
                    fieldType = "date_of_birth"
                    break
                }
            }
        }
        
        // 7. 匹配 Monthly Income
        if (!valueToFill && userData.monthly_income) {
            for (const kw of FIELD_MAP["monthly_income"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = userData.monthly_income
                    fieldType = "monthly_income"
                    break
                }
            }
        }
        
        // 8. 匹配 Employer
        if (!valueToFill && userData.employer) {
            for (const kw of FIELD_MAP["employer"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = userData.employer
                    fieldType = "employer"
                    break
                }
            }
        }
        
        // 9. 匹配 Tax Number
        if (!valueToFill && userData.tax_number) {
            for (const kw of FIELD_MAP["tax_number"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = userData.tax_number
                    fieldType = "tax_number"
                    break
                }
            }
        }
        
        // 10. 匹配 Email
        if (!valueToFill && userData.email) {
            for (const kw of FIELD_MAP["email"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = userData.email
                    fieldType = "email"
                    break
                }
            }
        }
        
        // 11. 匹配 Phone
        if (!valueToFill && userData.phone) {
            for (const kw of FIELD_MAP["phone"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = userData.phone
                    fieldType = "phone"
                    break
                }
            }
        }
        
        // 12. 匹配 Postcode (从地址提取)
        if (!valueToFill && postcode) {
            for (const kw of FIELD_MAP["postcode"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = postcode
                    fieldType = "postcode"
                    break
                }
            }
        }
        
        // 13. 匹配 City (从地址提取)
        if (!valueToFill && city) {
            for (const kw of FIELD_MAP["city"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = city
                    fieldType = "city"
                    break
                }
            }
        }
        
        // 14. 匹配 State (从地址提取)
        if (!valueToFill && state) {
            for (const kw of FIELD_MAP["state"]) {
                if (combined.includes(kw.toLowerCase())) {
                    valueToFill = state
                    fieldType = "state"
                    break
                }
            }
        }
        
        // 填充值
        if (valueToFill) {
            input.value = valueToFill
            input.dispatchEvent(new Event("input", { bubbles: true }))
            input.dispatchEvent(new Event("change", { bubbles: true }))
            input.dispatchEvent(new Event("blur", { bubbles: true }))
            input.style.backgroundColor = "#e8f8f2"
            input.style.border = "2px solid #1D9E75"
            input.style.outline = "none"
            
            filled++
            filledFields.push(`${fieldType || 'unknown'}: ${valueToFill.substring(0, 30)}`)
        }
    })
    
    console.log(`[GovEase] ✅ Filled ${filled} fields:`, filledFields)
    return filled
}

// 显示浮动按钮
function showButton(userData) {
    const existing = document.getElementById("govease-btn")
    if (existing) existing.remove()
    
    const btn = document.createElement("div")
    btn.id = "govease-btn"
    btn.innerHTML = `
        <div style="
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 999999;
            background: linear-gradient(135deg, #1D9E75 0%, #158a63 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 40px;
            cursor: pointer;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            border: none;
        ">
            <span>🤖</span> GovEase AI — Fill Form
        </div>
    `
    
    btn.onclick = () => {
        const count = fillForms(userData)
        const btnDiv = btn.querySelector("div")
        if (count > 0) {
            btnDiv.innerHTML = `<span>✅</span> GovEase AI — Filled ${count} fields!`
            btnDiv.style.background = "#0d5c45"
        } else {
            btnDiv.innerHTML = `<span>⚠️</span> No fields matched!`
            btnDiv.style.background = "#e67e22"
            setTimeout(() => {
                btnDiv.innerHTML = `<span>🤖</span> GovEase AI — Fill Form`
                btnDiv.style.background = "linear-gradient(135deg, #1D9E75 0%, #158a63 100%)"
            }, 2000)
        }
        setTimeout(() => btn.remove(), 3000)
    }
    
    document.body.appendChild(btn)
    console.log("[GovEase] Button added to page")
}

// ============================================================
// 数据获取逻辑
// ============================================================

// 优先从 chrome.storage 获取数据
chrome.storage.local.get("govease_user_data", (result) => {
    if (result.govease_user_data) {
        console.log("[GovEase] Data loaded from chrome.storage")
        const data = result.govease_user_data
        if (data.full_name || data.ic_number) {
            showButton(data)
        }
    }
})

// 从 Flask 获取数据并同步
fetch("http://localhost:5000/get-data")
    .then(res => {
        if (!res.ok) throw new Error("Flask not running")
        return res.json()
    })
    .then(data => {
        if (data && (data.full_name || data.ic_number)) {
            console.log("[GovEase] Data loaded from Flask:", data)
            chrome.storage.local.set({ "govease_user_data": data })
            showButton(data)
        }
    })
    .catch(err => {
        console.log("[GovEase] Flask not running or no data yet:", err.message)
    })

// 监听来自网页的消息 (用于 Save to Extension 按钮)
window.addEventListener("message", (event) => {
    if (event.data.type === "GOVEASE_SAVE_DATA") {
        console.log("[GovEase] Received data from webpage:", event.data.data)
        chrome.storage.local.set({ "govease_user_data": event.data.data }, () => {
            console.log("[GovEase] Data saved to chrome.storage")
            showButton(event.data.data)
        })
    }
})

// 监听自定义事件 (用于 mock portal)
window.addEventListener("govEaseFillForm", () => {
    console.log("[GovEase] Received govEaseFillForm event")
    chrome.storage.local.get("govease_user_data", (result) => {
        if (result.govease_user_data) {
            fillForms(result.govease_user_data)
        } else {
            console.log("[GovEase] No data available to fill")
        }
    })
})

console.log("[GovEase] Content script loaded and ready")