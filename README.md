# GovEase AI

> Your Intelligent Liaison for Seamless Malaysian Government Services

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-2.0+-red)](https://flask.palletsprojects.com)

---

# [▶️ Click Here to Watch the Pitching Video]（https://drive.google.com/file/d/1RVI-GQRoZTHifEP2_Bd41cXtZgN2faIk/view?usp=sharing）

## 📌 Overview

**GovEase AI** is an intelligent form-filling assistant that helps Malaysians navigate government portals (LHDN, PTPTN, EPF) with ease.

Instead of manually filling repetitive forms across multiple websites, users simply upload their IC or salary slip once. GovEase AI extracts the information using **ILMU GLM-5.1 (Z.AI)** , applies security watermarks, and auto-fills any government form with one click.

### 🎯 Problem Statement

Malaysians face fragmented, manual, and repetitive workflows across government portals:
- Same IC uploaded 4+ times
- Same address typed repeatedly
- Confusing jargon and complex forms
- Security concerns about document sharing

### 💡 Solution

GovEase AI closes the **Digital Bureaucracy Gap** with a 3-Agent architecture:

| Agent | Function |
|-------|----------|
| **Concierge** | Extracts data from IC/salary slip via GLM vision model |
| **Guardian** | Applies department-specific watermarks (LHDN/PTPTN/EPF) |
| **Executor** | Chrome extension that auto-fills any government form |

---

## 🏗️ System Architecture

GovEase AI uses a **3-Agent architecture**:

| Agent | Function |
|-------|----------|
| **Concierge** | Extracts data from IC/salary slip via GLM-5.1 |
| **Guardian** | Adds watermarks (LHDN/PTPTN/EPF) to documents |
| **Executor** | Chrome extension that auto-fills forms |

### Data Flow
`User → Concierge (GLM) → Guardian → Storage → Executor → Form Filled`

### Tech Stack
- Backend: Flask (Python)
- AI: ILMU GLM-5.1
- Extension: Chrome Manifest V3
- Frontend: HTML/CSS/JS

## 🔑 API Key Configuration

This project requires an ILMU GLM-5.1 API key.

### For Judges / Reviewers:

1. **Get your API key** from: https://console.ilmu.ai/dashboard
   - Sign up / Log in
   - Go to **API Keys** → **Create API Key**
   - Copy the key (starts with `sk-`)

2. **The `config.py` file is already created and ignored by Git.**
   - Open `config.py` in the project root
   - Replace with your actual API key:

```python
# config.py
ILMU_API_KEY = "sk-your-actual-api-key-here"
