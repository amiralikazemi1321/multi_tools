import sys
import os
import json
import random

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QListWidget, QStackedWidget, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

from openai import OpenAI


# ---------------- PATH ----------------
APP_DIR = os.path.join(os.path.expanduser("~"), ".amirali_ultra_v4")
os.makedirs(APP_DIR, exist_ok=True)

NOTES_FILE = os.path.join(APP_DIR, "notes.json")
TODO_FILE = os.path.join(APP_DIR, "todo.json")
CONFIG_FILE = os.path.join(APP_DIR, "config.json")


# ---------------- AI CORE ----------------
class AI:
    def __init__(self):
        self.client = None
        self.base_url = "https://api.gapgpt.app/v1"
        self.api_key = ""
        self.model = "gpt-4o"

    def configure(self, base_url, api_key, model):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

        if not api_key:
            self.client = None
            return

        try:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        except:
            self.client = None

    def ask(self, prompt):
        if not self.client:
            return "❌ AI غیرفعال است"

        try:
            res = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"❌ Error: {e}"


# ---------------- THEME ----------------
def dark_theme():
    p = QPalette()
    p.setColor(QPalette.Window, QColor(25, 25, 25))
    p.setColor(QPalette.WindowText, Qt.white)
    p.setColor(QPalette.Base, QColor(18, 18, 18))
    p.setColor(QPalette.Text, Qt.white)
    return p


# ---------------- MAIN APP ----------------
class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ultra V4 FIXED NAV")
        self.resize(1000, 650)

        self.ai = AI()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.history = []

        self.notes = self.load_json(NOTES_FILE, {})
        self.todos = self.load_json(TODO_FILE, [])
        self.config = self.load_json(CONFIG_FILE, {
            "base_url": "https://api.gapgpt.app/v1",
            "api_key": "",
            "model": "gpt-4o"
        })

        self.ai.configure(
            self.config["base_url"],
            self.config["api_key"],
            self.config["model"]
        )

        QApplication.setPalette(dark_theme())

        self.build_ui()

    # ---------------- NAV SYSTEM (FIXED) ----------------
    def go(self, index):
        self.history.append(self.stack.currentIndex())
        self.stack.setCurrentIndex(index)

    def go_home(self):
        self.stack.setCurrentIndex(0)
        self.history.clear()

    def go_back(self):
        if self.history:
            self.stack.setCurrentIndex(self.history.pop())
        else:
            self.go_home()

    # ---------------- UI ----------------
    def build_ui(self):

        # ================= HOME =================
        home = QWidget()
        hl = QVBoxLayout(home)

        hl.addWidget(QLabel("🏠 HOME"))

        btn_ai = QPushButton("🧠 AI")
        btn_ai.clicked.connect(lambda: self.go(1))

        btn_settings = QPushButton("⚙ Settings")
        btn_settings.clicked.connect(lambda: self.go(2))

        btn_notes = QPushButton("📝 Notes")
        btn_notes.clicked.connect(lambda: self.go(3))

        btn_todo = QPushButton("✅ Todo")
        btn_todo.clicked.connect(lambda: self.go(4))

        btn_game = QPushButton("🎮 Game")
        btn_game.clicked.connect(lambda: self.go(5))

        hl.addWidget(btn_ai)
        hl.addWidget(btn_settings)
        hl.addWidget(btn_notes)
        hl.addWidget(btn_todo)
        hl.addWidget(btn_game)

        back_btn = QPushButton("⬅ Back")
        back_btn.clicked.connect(self.go_back)
        hl.addWidget(back_btn)

        self.stack.addWidget(home)

        # ================= AI =================
        ai = QWidget()
        al = QVBoxLayout(ai)

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)

        self.chat_in = QLineEdit()
        self.chat_in.returnPressed.connect(self.send_ai)

        send = QPushButton("Send")
        send.clicked.connect(self.send_ai)

        back = QPushButton("⬅ Back")
        back.clicked.connect(self.go_back)

        al.addWidget(self.chat)
        al.addWidget(self.chat_in)
        al.addWidget(send)
        al.addWidget(back)

        self.stack.addWidget(ai)

        # ================= SETTINGS =================
        st = QWidget()
        sl = QVBoxLayout(st)

        self.base_url_in = QLineEdit(self.config["base_url"])
        self.api_key_in = QLineEdit()
        self.model_box = QComboBox()
        self.model_box.addItems(["gpt-4o", "gpt-4.1-mini", "gemini-2.5-pro"])

        save = QPushButton("Save")
        save.clicked.connect(self.save_config)

        back = QPushButton("⬅ Back")
        back.clicked.connect(self.go_back)

        sl.addWidget(self.base_url_in)
        sl.addWidget(self.api_key_in)
        sl.addWidget(self.model_box)
        sl.addWidget(save)
        sl.addWidget(back)

        self.stack.addWidget(st)

        # ================= NOTES =================
        notes = QWidget()
        nl = QVBoxLayout(notes)

        self.note_title = QLineEdit()
        self.note_text = QTextEdit()
        self.note_list = QListWidget()

        save_n = QPushButton("Save Note")
        save_n.clicked.connect(self.save_note)

        self.note_list.itemClicked.connect(self.load_note)

        back = QPushButton("⬅ Back")
        back.clicked.connect(self.go_back)

        nl.addWidget(self.note_title)
        nl.addWidget(self.note_text)
        nl.addWidget(save_n)
        nl.addWidget(self.note_list)
        nl.addWidget(back)

        self.stack.addWidget(notes)
        self.refresh_notes()

        # ================= TODO =================
        todo = QWidget()
        tl = QVBoxLayout(todo)

        self.todo_in = QLineEdit()
        self.todo_list = QListWidget()

        self.todo_in.returnPressed.connect(self.add_todo)
        self.todo_list.itemClicked.connect(self.toggle_todo)

        back = QPushButton("⬅ Back")
        back.clicked.connect(self.go_back)

        tl.addWidget(self.todo_in)
        tl.addWidget(self.todo_list)
        tl.addWidget(back)

        self.stack.addWidget(todo)
        self.refresh_todo()

        # ================= GAME =================
        game = QWidget()
        gl = QVBoxLayout(game)

        self.secret = random.randint(1, 100)
        self.guess = QLineEdit()
        self.result = QLabel("Guess 1-100")

        btn = QPushButton("Try")
        btn.clicked.connect(self.check_game)

        back = QPushButton("⬅ Back")
        back.clicked.connect(self.go_back)

        gl.addWidget(self.guess)
        gl.addWidget(btn)
        gl.addWidget(self.result)
        gl.addWidget(back)

        self.stack.addWidget(game)

    # ---------------- AI ----------------
    def send_ai(self):
        msg = self.chat_in.text().strip()
        if not msg:
            return

        self.chat.append("🧑 " + msg)
        self.chat.append("🤖 ...")

        reply = self.ai.ask(msg)

        self.chat.append("🤖 " + reply + "\n")
        self.chat_in.clear()

    # ---------------- CONFIG ----------------
    def save_config(self):
        self.config = {
            "base_url": self.base_url_in.text(),
            "api_key": self.api_key_in.text().strip(),
            "model": self.model_box.currentText()
        }

        self.ai.configure(
            self.config["base_url"],
            self.config["api_key"],
            self.config["model"]
        )

        json.dump(self.config, open(CONFIG_FILE, "w"), indent=2)

    # ---------------- NOTES ----------------
    def save_note(self):
        self.notes[self.note_title.text()] = self.note_text.toPlainText()
        json.dump(self.notes, open(NOTES_FILE, "w"), indent=2)
        self.refresh_notes()

    def refresh_notes(self):
        self.note_list.clear()
        for k in self.notes:
            self.note_list.addItem(k)

    def load_note(self, item):
        k = item.text()
        self.note_title.setText(k)
        self.note_text.setText(self.notes[k])

    # ---------------- TODO ----------------
    def add_todo(self):
        self.todos.append(self.todo_in.text())
        self.todo_in.clear()
        json.dump(self.todos, open(TODO_FILE, "w"), indent=2)
        self.refresh_todo()

    def refresh_todo(self):
        self.todo_list.clear()
        for t in self.todos:
            self.todo_list.addItem(t)

    def toggle_todo(self, item):
        pass

    # ---------------- GAME ----------------
    def check_game(self):
        try:
            g = int(self.guess.text())
            if g == self.secret:
                self.result.setText("Correct 🎉")
            elif g < self.secret:
                self.result.setText("Higher ⬆️")
            else:
                self.result.setText("Lower ⬇️")
        except:
            pass

    # ---------------- JSON ----------------
    def load_json(self, p, d):
        if os.path.exists(p):
            return json.load(open(p, "r"))
        return d


# ---------------- RUN ----------------
app = QApplication(sys.argv)
w = App()
w.show()
sys.exit(app.exec())