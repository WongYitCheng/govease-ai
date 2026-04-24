const FIELD_MAP = {
  "ic_number":    ["ic", "nric", "identity", "mykad", "no_kad", 
                   "driver", "license", "social"],
  "full_name":    ["name", "nama", "fullname", "full_name", 
                   "first", "last", "card_user"],
  "address":      ["address", "alamat", "addr", "zip", "postal"],
  "date_of_birth":["dob", "birth", "tarikh_lahir", "birthdate"],
  "dob_day":      ["day"],
  "dob_month":    ["month"],
  "dob_year":     ["year"],
  "monthly_income":["income", "salary", "pendapatan"]
}

function fillForms(userData) {
  const inputs = document.querySelectorAll("input, select, textarea")
  let filled = 0

  inputs.forEach(input => {
    const id    = (input.id || "").toLowerCase()
    const name  = (input.name || "").toLowerCase()
    const placeholder = (input.placeholder || "").toLowerCase()
    const combined = `${id} ${name} ${placeholder}`

    for (const [dataKey, keywords] of Object.entries(FIELD_MAP)) {
      if (keywords.some(kw => combined.includes(kw))) {
        if (userData[dataKey]) {
          input.value = userData[dataKey]
          input.dispatchEvent(new Event("input", { bubbles: true }))
          input.dispatchEvent(new Event("change", { bubbles: true }))
          input.style.backgroundColor = "#e8f8f2"
          filled++
        }
      }
    }
  })
  return filled
}

function showButton(userData) {
  const btn = document.createElement("div")
  btn.id = "govease-btn"
  btn.innerHTML = `
    <div style="
      position:fixed; bottom:24px; right:24px; z-index:99999;
      background:#1D9E75; color:white; padding:12px 20px;
      border-radius:12px; cursor:pointer; font-family:sans-serif;
      font-size:14px; font-weight:600; box-shadow:0 4px 16px rgba(0,0,0,0.2);
    ">
      GovEase AI — Fill Form
    </div>
  `
  btn.onclick = () => {
    const count = fillForms(userData)
    btn.querySelector("div").innerHTML = 
      `GovEase AI — Filled ${count} fields!`
    btn.querySelector("div").style.background = "#155f48"
    setTimeout(() => btn.remove(), 3000)
  }
  document.body.appendChild(btn)
}

chrome.storage.local.get("govease_user_data", (result) => {
  if (result.govease_user_data) {
    showButton(result.govease_user_data)
  }
})
// Run immediately on any page
fetch("http://localhost:5000/get-data")
  .then(res => res.json())
  .then(data => {
    if (data && (data.full_name || data.ic_number)) {
      showButton(data)
    }
  })
  .catch(err => {
    console.log("GovEase: Flask not running or no data yet")
  })