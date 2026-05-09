<div align="center">

# 🔴 cPanelCVE

### CVE-2026-41940 — cPanel & WHM Authentication Bypass

**CVSS 10.0 (Critical) · Confirmed In‑The‑Wild · Auto Root Login**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Selenium](https://img.shields.io/badge/Selenium-✔-43B02A?logo=selenium&logoColor=white)](https://selenium.dev)

</div>

---

## 📖 Overview

**cPanelCVE** is a proof‑of‑concept exploit for CVE-2026-41940, a critical session‑file CRLF injection vulnerability in cPanel & WHM that allows **complete root authentication bypass** on WHM (Web Host Manager) port 2087.

Once the bypass is successful, the tool **automatically opens your browser** (Chrome or Firefox) and logs you directly into the WHM interface as **root** — no manual cookie setup, no password, no click‑throughs.

### 🧬 How It Works

The exploit runs in **4 stages**:

| Stage | Description |
|-------|-------------|
| **0 — Canonical Discovery** | Retrieves the real hostname via `/openid_connect/cpanelid` to prevent redirect loops. |
| **1 — Preauth Session** | Posts wrong credentials to `/login/?login_only=1` to obtain a `whostmgrsession` cookie. |
| **2 — CRLF Injection** | Sends a poisoned `Authorization: Basic` header that writes `hasroot=1` directly into the session file. |
| **3 — Propagate** | Triggers the `do_token_denied` internal gadget to flush the raw session into the live cache. |
| **4 — Verify** | Accesses `/json-api/version` — a 200 OK with version data confirms unrestricted **root access**. |

After Stage 4, the tool either:

- Opens Chrome/Firefox **instantly**, injects the session cookie via DevTools, and lands on the WHM dashboard (fully automatic).
- Or prints ready‑to‑use JavaScript commands for manual login.

---

## ⚡ Quick Start

### Prerequisites

- **Python 3.8+** (stdlib only for exploit core)
- **Selenium** (for auto‑browser login):
  ```bash
  pip install selenium
  pip install -r requirements.txt

## ⚡ Usage

```bash
# Auto‑login with Chrome (default)
python cpanelcve.py -u https://target.com:2087 --selenium

# Auto‑login with Firefox
python cpanelcve.py -u https://target.com:2087 --selenium --engine firefox

# Print manual browser console commands
python cpanelcve.py -u https://target.com:2087 --browser
```
<p align="center"> <sub>Made with ❤️ by @mahanOFp</sub> </p>
