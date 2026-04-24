const FIELD_MAP = {
  "ic_number":    ["ic", "nric", "identity", "mykad", "no_kad", "pengenalan",
                   "no_pengenalan", "mykad", "driver", "license", "social"],
  "full_name":    ["name", "nama", "fullname", "full_name", "penuh",
                   "first", "last", "card_user"],
  "address":      ["address", "alamat", "addr", "zip", "postal", "jalan"],
  "date_of_birth":["dob", "birth", "tarikh_lahir", "birthdate", "lahir"],
  "dob_day":      ["day", "hari"],
  "dob_month":    ["month", "bulan"],
  "dob_year":     ["year", "tahun"],
  "monthly_income":["income", "salary", "pendapatan", "gaji"]
}

// 清洗 IC 号码：只保留数字
function cleanICNumber(value) {
  if (!value) return value
  // 移除所有非数字字符（连字符、空格、字母等）
  return value.toString().replace(/\D/g, '')
}

function fillForms(userData) {
  const inputs = document.querySelectorAll("input, select, textarea")
  let filled = 0

  inputs.forEach(input => {
    // Skip password fields and hidden fields
    if (input.type === "password" || input.type === "hidden") return
    
    const id    = (input.id || "").toLowerCase()
    const name  = (input.name || "").toLowerCase()
    const placeholder = (input.placeholder || "").toLowerCase()
    const className = (input.className || "").toLowerCase()
    const combined = `${id} ${name} ${placeholder} ${className}`

    for (const [dataKey, keywords] of Object.entries(FIELD_MAP)) {
      if (keywords.some(kw => combined.includes(kw))) {
        if (userData[dataKey]) {
          let value = userData[dataKey]
          
          // 🔧 IC 号码：移除连字符和空格
          if (dataKey === "ic_number") {
            const originalValue = value
            value = cleanICNumber(value)
            console.log(`[GovEase] IC cleaned: "${originalValue}" → "${value}"`)
          }
          
          input.value = value
          input.dispatchEvent(new Event("input", { bubbles: true }))
          input.dispatchEvent(new Event("change", { bubbles: true }))
          input.dispatchEvent(new Event("blur", { bubbles: true }))
          input.style.backgroundColor = "#e8f8f2"
          input.style.border = "2px solid #1D9E75"
          filled++
          
          console.log(`[GovEase] Filled ${dataKey} = ${value}`)
        }
      }
    }
  })
  
  console.log(`[GovEase] Total filled: ${filled} fields`)
  return filled
}

function showButton(userData) {
  // Remove existing button if any
  const existing = document.getElementById("govease-btn")
  if (existing) existing.remove()
  
  const btn = document.createElement("div")
  btn.id = "govease-btn"
  btn.innerHTML = `
    <div style="
      position:fixed; bottom:24px; right:24px; z-index:99999;
      background:#1D9E75; color:white; padding:12px 20px;
      border-radius:12px; cursor:pointer; font-family:sans-serif;
      font-size:14px; font-weight:600; box-shadow:0 4px 16px rgba(0,0,0,0.2);
      transition: all 0.2s ease;
    ">
      🤖 GovEase AI — Fill Form
    </div>
  `
  btn.onclick = () => {
    const count = fillForms(userData)
    const btnDiv = btn.querySelector("div")
    btnDiv.innerHTML = `✅ GovEase AI — Filled ${count} fields!`
    btnDiv.style.background = "#155f48"
    setTimeout(() => btn.remove(), 3000)
  }
  document.body.appendChild(btn)
}

// Try to get data from chrome.storage first
chrome.storage.local.get("govease_user_data", (result) => {
  if (result.govease_user_data) {
    console.log("[GovEase] Data loaded from chrome.storage")
    console.log("[GovEase] IC before cleaning:", result.govease_user_data.ic_number)
    // Test cleaning
    const cleaned = cleanICNumber(result.govease_user_data.ic_number)
    console.log("[GovEase] IC after cleaning:", cleaned)
    showButton(result.govease_user_data)
  }
})

// Also try to fetch from Flask backend
fetch("http://localhost:5000/get-data")
  .then(res => res.json())
  .then(data => {
    if (data && (data.full_name || data.ic_number)) {
      console.log("[GovEase] Data loaded from Flask:", data)
      chrome.storage.local.set({ "govease_user_data": data })
      showButton(data)
    }
  })
  .catch(err => {
    console.log("[GovEase] Flask not running or no data yet")
  })

// Log that content script is loaded
console.log("[GovEase] Content script loaded")