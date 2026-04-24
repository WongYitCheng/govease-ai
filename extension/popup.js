// popup.js - GovEase Extension Popup (No inline scripts)

// 辅助函数：更新状态显示
function updateStatus(data) {
    const statusContent = document.getElementById('statusContent')
    
    if (data && (data.full_name || data.ic_number)) {
        statusContent.innerHTML = `
            <div style="margin-bottom: 4px;">✅ <strong>Ready to fill forms!</strong></div>
            <div>📛 Name: ${escapeHtml(data.full_name || '—')}</div>
            <div>🆔 IC: ${escapeHtml(data.ic_number || '—')}</div>
            <div>📍 Address: ${escapeHtml((data.address || '—').substring(0, 40))}</div>
            <div>🎂 DOB: ${escapeHtml(data.date_of_birth || '—')}</div>
        `
    } else {
        statusContent.innerHTML = `
            <div style="margin-bottom: 4px;">⚠️ <strong>No data yet</strong></div>
            <div>Please upload your IC in the chat interface first.</div>
            <div style="margin-top: 8px; font-size: 10px; color: #666;">💡 Chat: http://localhost:5000</div>
        `
    }
}

// 辅助函数：转义 HTML 防止 XSS
function escapeHtml(str) {
    if (!str) return ''
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
}

// 从 chrome.storage 加载数据
function loadData() {
    const statusContent = document.getElementById('statusContent')
    statusContent.innerHTML = '🔄 Loading from storage...'
    
    chrome.storage.local.get(['govease_user_data', 'govEasePortal'], (result) => {
        const data = result.govease_user_data
        
        // 恢复 portal 设置
        if (result.govEasePortal) {
            const portalSelect = document.getElementById('portalSelect')
            if (portalSelect) portalSelect.value = result.govEasePortal
        }
        
        updateStatus(data)
    })
}

// 从 Flask 服务器获取数据并保存
async function fetchAndSaveData() {
    const statusContent = document.getElementById('statusContent')
    statusContent.innerHTML = '🔄 Connecting to server...'
    
    try {
        const response = await fetch('http://localhost:5000/get-data')
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
        }
        
        const data = await response.json()
        console.log('[GovEase] Fetched data:', data)
        
        if (data && (data.full_name || data.ic_number)) {
            // 保存到 chrome.storage
            chrome.storage.local.set({ 'govease_user_data': data }, () => {
                statusContent.innerHTML = `
                    <div style="margin-bottom: 4px;">✅ <strong class="success">Data saved to extension!</strong></div>
                    <div>📛 Name: ${escapeHtml(data.full_name || '—')}</div>
                    <div>🆔 IC: ${escapeHtml(data.ic_number || '—')}</div>
                    <div style="margin-top: 6px;">🚀 Now open any government portal and click the floating button!</div>
                `
                // 3 秒后恢复正常显示
                setTimeout(() => updateStatus(data), 3000)
            })
        } else {
            statusContent.innerHTML = `
                <div style="margin-bottom: 4px;">❌ <strong class="error">No data found</strong></div>
                <div>Please upload your IC in the chat interface first.</div>
                <div style="margin-top: 8px;">💡 Chat: http://localhost:5000</div>
            `
        }
    } catch (error) {
        console.error('[GovEase] Fetch error:', error)
        statusContent.innerHTML = `
            <div style="margin-bottom: 4px;">❌ <strong class="error">Cannot connect to server</strong></div>
            <div>Make sure Flask is running:</div>
            <div style="font-family: monospace; margin-top: 6px;">python app.py</div>
        `
    }
}

// 保存 portal 设置
function savePortalSetting() {
    const portalSelect = document.getElementById('portalSelect')
    if (portalSelect) {
        chrome.storage.local.set({ 'govEasePortal': portalSelect.value })
    }
}

// 初始化事件监听器
function init() {
    // 加载数据
    loadData()
    
    // 绑定按钮事件
    const reloadBtn = document.getElementById('reloadBtn')
    if (reloadBtn) {
        reloadBtn.addEventListener('click', loadData)
    }
    
    const saveBtn = document.getElementById('saveBtn')
    if (saveBtn) {
        saveBtn.addEventListener('click', fetchAndSaveData)
    }
    
    const portalSelect = document.getElementById('portalSelect')
    if (portalSelect) {
        portalSelect.addEventListener('change', savePortalSetting)
    }
}

// 等待 DOM 加载完成
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
} else {
    init()
}