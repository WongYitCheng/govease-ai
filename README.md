# GovEase AI

> Your Intelligent Liaison for Seamless Malaysian Government Services

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-2.0+-red)](https://flask.palletsprojects.com)

---

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
