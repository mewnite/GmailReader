import imaplib
import email
import json
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from email.header import decode_header
from email.utils import parsedate_to_datetime

try:
    from plyer import notification
except Exception:
    notification = None

APP_NAME = "Gmail Watcher"
CONFIG_FILE = "gmail_watcher_config.json"
DEFAULT_INTERVAL = 15
IMAP_HOST = "imap.gmail.com"
MAX_HISTORY = 75
PREVIEW_BYTES = 4096
PREVIEW_CHARS = 1800


def decode_mime_text(text):
    if not text:
        return ""
    parts = decode_header(text)
    out = []
    for part, enc in parts:
        if isinstance(part, bytes):
            try:
                out.append(part.decode(enc or "utf-8", errors="ignore"))
            except Exception:
                out.append(part.decode("utf-8", errors="ignore"))
        else:
            out.append(part)
    return "".join(out)


def parse_sender_list(raw):
    items = []
    for part in raw.split(","):
        clean = part.strip().lower()
        if clean:
            items.append(clean)
    return items


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def normalize_preview(text):
    if not text:
        return "No se pudo extraer preview de este correo."
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    compact = []
    blank = False
    for line in lines:
        if not line.strip():
            if not blank:
                compact.append("")
            blank = True
        else:
            compact.append(line)
            blank = False
    result = "\n".join(compact).strip()
    if len(result) > PREVIEW_CHARS:
        result = result[:PREVIEW_CHARS].rstrip() + "\n\n[preview recortada]"
    return result or "No hay texto visible en el preview."


class GmailWatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("980x640")
        self.root.minsize(900, 580)

        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.mail = None
        self.last_uid = None
        self.history = []
        self.history_by_uid = {}

        self.config = self.load_config()

        self.email_var = tk.StringVar(value=self.config.get("email", os.getenv("GMAIL_ADDRESS", "")))
        self.password_var = tk.StringVar(value=self.config.get("password", os.getenv("GMAIL_APP_PASSWORD", "")))
        self.sender_var = tk.StringVar(value=self.config.get("watched_senders", os.getenv("WATCHED_SENDER", "")))
        self.interval_var = tk.StringVar(value=str(self.config.get("interval", DEFAULT_INTERVAL)))
        self.status_var = tk.StringVar(value="Detenida")
        self.last_mail_var = tk.StringVar(value="Ninguno")
        self.count_var = tk.StringVar(value=str(self.config.get("count", 0)))
        self.cursor_var = tk.StringVar(value="UID base: -")

        self.build_ui()
        self.restore_history_from_config()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(200, self.process_log_queue)

    def build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        top = ttk.Frame(self.root, padding=14)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Correo Gmail").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(top, textvariable=self.email_var).grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(top, text="App password").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(top, textvariable=self.password_var, show="*").grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(top, text="Remitentes a vigilar").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(top, textvariable=self.sender_var).grid(row=2, column=1, sticky="ew", pady=6)
        ttk.Label(top, text="Separá varios con coma").grid(row=2, column=2, sticky="w", padx=(10, 0), pady=6)

        ttk.Label(top, text="Intervalo (seg)").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(top, textvariable=self.interval_var, width=10).grid(row=3, column=1, sticky="w", pady=6)

        button_row = ttk.Frame(top)
        button_row.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        self.start_button = ttk.Button(button_row, text="Iniciar", command=self.start_watching)
        self.start_button.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.stop_button = ttk.Button(button_row, text="Detener", command=self.stop_watching, state="disabled")
        self.stop_button.grid(row=0, column=1, sticky="w")

        self.test_button = ttk.Button(button_row, text="Probar notificación", command=self.test_notification)
        self.test_button.grid(row=0, column=2, sticky="w", padx=(8, 0))

        self.refresh_button = ttk.Button(button_row, text="Refrescar lectura", command=self.refresh_reading_layer)
        self.refresh_button.grid(row=0, column=3, sticky="w", padx=(8, 0))

        notebook = ttk.Notebook(self.root)
        notebook.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))

        alerts_tab = ttk.Frame(notebook, padding=12)
        read_tab = ttk.Frame(notebook, padding=12)
        notebook.add(alerts_tab, text="Alertas")
        notebook.add(read_tab, text="Lectura")

        alerts_tab.columnconfigure(0, weight=1)
        alerts_tab.rowconfigure(1, weight=1)

        stats = ttk.Frame(alerts_tab)
        stats.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        stats.columnconfigure(1, weight=1)
        ttk.Label(stats, text="Estado:").grid(row=0, column=0, sticky="w")
        ttk.Label(stats, textvariable=self.status_var).grid(row=0, column=1, sticky="w")
        ttk.Label(stats, text="Último mail:").grid(row=1, column=0, sticky="w")
        ttk.Label(stats, textvariable=self.last_mail_var).grid(row=1, column=1, sticky="w")
        ttk.Label(stats, text="Alertas enviadas:").grid(row=2, column=0, sticky="w")
        ttk.Label(stats, textvariable=self.count_var).grid(row=2, column=1, sticky="w")
        ttk.Label(stats, text="Cursor:").grid(row=3, column=0, sticky="w")
        ttk.Label(stats, textvariable=self.cursor_var).grid(row=3, column=1, sticky="w")

        self.log = scrolledtext.ScrolledText(alerts_tab, wrap=tk.WORD, height=18, state="disabled")
        self.log.grid(row=1, column=0, sticky="nsew")

        read_tab.columnconfigure(0, weight=1)
        read_tab.columnconfigure(1, weight=2)
        read_tab.rowconfigure(1, weight=1)

        ttk.Label(read_tab, text="Correos detectados").grid(row=0, column=0, sticky="w")
        ttk.Label(read_tab, text="Preview").grid(row=0, column=1, sticky="w")

        left_frame = ttk.Frame(read_tab)
        right_frame = ttk.Frame(read_tab)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        right_frame.grid(row=1, column=1, sticky="nsew")
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        self.history_list = tk.Listbox(left_frame, height=20, activestyle="dotbox")
        self.history_list.grid(row=0, column=0, sticky="nsew")
        self.history_list.bind("<<ListboxSelect>>", self.on_history_select)

        left_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.history_list.yview)
        self.history_list.configure(yscrollcommand=left_scroll.set)
        left_scroll.grid(row=0, column=1, sticky="ns")

        self.preview_box = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, state="disabled")
        self.preview_box.grid(row=0, column=0, sticky="nsew")

        footer = ttk.Frame(self.root, padding=(14, 0, 14, 14))
        footer.grid(row=2, column=0, sticky="ew")
        ttk.Label(
            footer,
            text="La primera vez toma como base el inbox actual para evitar alertas viejas. La preview se baja solo cuando la seleccionás.",
        ).grid(row=0, column=0, sticky="w")

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return {}
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_config(self):
        data = {
            "email": self.email_var.get().strip(),
            "password": self.password_var.get().strip(),
            "watched_senders": self.sender_var.get().strip(),
            "interval": self.get_interval(),
            "last_uid": self.last_uid,
            "count": safe_int(self.count_var.get(), 0),
            "history": self.history[-MAX_HISTORY:],
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.append_log(f"No se pudo guardar configuración: {e}")

    def restore_history_from_config(self):
        stored_history = self.config.get("history", [])
        if not isinstance(stored_history, list):
            return
        for item in stored_history:
            if not isinstance(item, dict):
                continue
            uid = item.get("uid")
            if uid is None:
                continue
            entry = {
                "uid": safe_int(uid, 0),
                "from": item.get("from", ""),
                "subject": item.get("subject", "(sin asunto)"),
                "date": item.get("date", ""),
                "snippet": item.get("snippet", ""),
            }
            self.add_history_entry(entry, from_restore=True)

    def get_interval(self):
        try:
            value = int(self.interval_var.get().strip())
            return max(5, value)
        except Exception:
            return DEFAULT_INTERVAL

    def append_log(self, text):
        timestamp = time.strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert(tk.END, f"[{timestamp}] {text}\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def process_log_queue(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                kind = item.get("kind")
                if kind == "log":
                    self.append_log(item["text"])
                elif kind == "status":
                    self.status_var.set(item["text"])
                elif kind == "last_mail":
                    self.last_mail_var.set(item["text"])
                elif kind == "count":
                    self.count_var.set(str(item["text"]))
                elif kind == "cursor":
                    self.cursor_var.set(item["text"])
                elif kind == "history":
                    self.add_history_entry(item["entry"])
                elif kind == "preview":
                    self.set_preview(item["text"])
        except queue.Empty:
            pass
        self.root.after(200, self.process_log_queue)

    def set_status(self, text):
        self.log_queue.put({"kind": "status", "text": text})

    def set_last_mail(self, text):
        self.log_queue.put({"kind": "last_mail", "text": text})

    def set_count(self, value):
        self.log_queue.put({"kind": "count", "text": value})

    def set_cursor(self, uid):
        self.log_queue.put({"kind": "cursor", "text": f"UID base: {uid}"})

    def log_message(self, text):
        self.log_queue.put({"kind": "log", "text": text})

    def test_notification(self):
        self.show_notification("Prueba", "La notificación está funcionando.")
        self.append_log("Notificación de prueba enviada.")

    def show_notification(self, title, message):
        if notification is not None:
            try:
                notification.notify(title=title, message=message[:240], timeout=6)
                return
            except Exception:
                pass
        self.root.bell()
        self.append_log(f"{title}: {message}")

    def connect(self):
        email_addr = self.email_var.get().strip()
        password = self.password_var.get().strip()
        if not email_addr or not password:
            raise ValueError("Falta correo o app password.")

        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(email_addr, password)
        return mail

    def get_highest_uid(self, mail):
        mail.select("inbox")
        _, data = mail.search(None, "ALL")
        ids = data[0].split() if data and data[0] else []
        if not ids:
            return 0
        return int(ids[-1])

    def fetch_message_header(self, mail, uid):
        _, data = mail.fetch(str(uid), "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID)] RFC822.SIZE)")
        if not data or data[0] is None:
            return None
        raw = data[0][1]
        msg = email.message_from_bytes(raw)
        sender = decode_mime_text(msg.get("From", ""))
        subject = decode_mime_text(msg.get("Subject", "(sin asunto)"))
        date = decode_mime_text(msg.get("Date", ""))
        message_id = decode_mime_text(msg.get("Message-ID", ""))
        return {"from": sender, "subject": subject, "date": date, "message_id": message_id}

    def fetch_message_preview(self, mail, uid):
        try:
            typ, data = mail.fetch(str(uid), f"(BODY.PEEK[TEXT]<0.{PREVIEW_BYTES}>)")
            if typ != "OK" or not data or not data[0] or len(data[0]) < 2:
                return "No se pudo obtener la preview por IMAP parcial."
            raw = data[0][1]
            if not raw:
                return "No hay texto visible en la preview."
            try:
                text = raw.decode("utf-8", errors="ignore")
            except Exception:
                text = raw.decode(errors="ignore")
            return normalize_preview(text)
        except Exception as e:
            return f"No se pudo obtener preview: {e}"

    def sender_matches(self, sender_header, watched_senders):
        sender_header_lower = sender_header.lower()
        for watched in watched_senders:
            if watched and watched in sender_header_lower:
                return True
        return False

    def initialize_cursor(self):
        self.mail = self.connect()
        self.mail.select("inbox")

        saved_uid = self.config.get("last_uid")
        if saved_uid:
            self.last_uid = int(saved_uid)
            self.log_message(f"Cursor restaurado en UID {self.last_uid}.")
        else:
            self.last_uid = self.get_highest_uid(self.mail)
            self.log_message(f"Cursor inicial creado en UID {self.last_uid}. No se alertará correo viejo.")

        self.set_cursor(self.last_uid)
        self.set_last_mail("Ninguno")
        self.set_count(self.config.get("count", 0))
        self.save_config()

    def add_history_entry(self, entry, from_restore=False):
        if not isinstance(entry, dict):
            return

        uid = safe_int(entry.get("uid"), 0)
        if uid <= 0:
            return

        if uid in self.history_by_uid:
            return

        clean = {
            "uid": uid,
            "from": entry.get("from", ""),
            "subject": entry.get("subject", "(sin asunto)"),
            "date": entry.get("date", ""),
            "snippet": entry.get("snippet", ""),
        }

        self.history.append(clean)
        self.history_by_uid[uid] = clean
        self.history.sort(key=lambda x: x["uid"])
        self.history = self.history[-MAX_HISTORY:]
        if len(self.history_by_uid) > MAX_HISTORY * 2:
            self.history_by_uid = {item["uid"]: item for item in self.history}

        display = f"{clean['uid']} | {clean['subject'][:45]}"
        self.history_list.insert(tk.END, display)
        if not from_restore:
            self.persist_history_async()

    def persist_history_async(self):
        self.save_config()

    def refresh_history_list(self):
        self.history_list.delete(0, tk.END)
        for item in self.history:
            self.history_list.insert(tk.END, f"{item['uid']} | {item['subject'][:45]}")

    def on_history_select(self, _event=None):
        selection = self.history_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index < 0 or index >= len(self.history):
            return
        item = self.history[index]
        preview_text = self.build_preview_text(item)
        self.set_preview(preview_text)

    def set_preview(self, text):
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", tk.END)
        self.preview_box.insert(tk.END, text)
        self.preview_box.configure(state="disabled")

    def build_preview_text(self, item):
        lines = [
            f"UID: {item.get('uid', '')}",
            f"De: {item.get('from', '')}",
            f"Asunto: {item.get('subject', '')}",
            f"Fecha: {item.get('date', '')}",
            "",
        ]
        snippet = item.get("snippet")
        if snippet:
            lines.append(snippet)
        else:
            lines.append("Sin preview guardada todavía. Podés refrescar la lectura o volver a detectar el mail.")
        return "\n".join(lines)

    def refresh_reading_layer(self):
        if self.mail is None:
            messagebox.showinfo("Lectura", "Primero iniciá el monitoreo para conectarse a Gmail.")
            return
        selection = self.history_list.curselection()
        if not selection:
            messagebox.showinfo("Lectura", "Seleccioná un correo detectado para refrescar su preview.")
            return
        index = selection[0]
        if index < 0 or index >= len(self.history):
            return
        item = self.history[index]
        uid = item.get("uid")
        if not uid:
            return
        try:
            preview = self.fetch_message_preview(self.mail, uid)
            item["snippet"] = preview
            self.set_preview(self.build_preview_text(item))
            self.save_config()
            self.append_log(f"Preview refrescada para UID {uid}.")
        except Exception as e:
            self.append_log(f"No se pudo refrescar preview: {e}")

    def poll_once(self):
        if self.mail is None:
            self.mail = self.connect()

        self.mail.select("inbox")
        _, data = self.mail.search(None, "ALL")
        ids = data[0].split() if data and data[0] else []
        if not ids:
            return

        highest_uid = int(ids[-1])
        if self.last_uid is None:
            self.last_uid = highest_uid
            self.save_config()
            return

        if highest_uid <= self.last_uid:
            return

        watched = parse_sender_list(self.sender_var.get())
        if not watched:
            return

        new_uids = [int(uid) for uid in ids if int(uid) > int(self.last_uid)]
        new_uids.sort()

        for uid in new_uids:
            header = self.fetch_message_header(self.mail, uid)
            if not header:
                continue

            sender = header["from"]
            subject = header["subject"]
            date = header["date"]

            if self.sender_matches(sender, watched):
                preview = self.fetch_message_preview(self.mail, uid)
                current = safe_int(self.count_var.get(), 0) + 1
                self.set_count(current)
                self.set_last_mail(f"UID {uid} | {subject}")
                self.show_notification("Nuevo Gmail detectado", f"De: {sender}\nAsunto: {subject}")
                self.log_message(f"Coincidencia: {sender} | {subject} | {date}")
                self.log_queue.put(
                    {
                        "kind": "history",
                        "entry": {
                            "uid": uid,
                            "from": sender,
                            "subject": subject,
                            "date": date,
                            "snippet": preview,
                        },
                    }
                )
                self.log_queue.put({"kind": "preview", "text": self.build_preview_text({"uid": uid, "from": sender, "subject": subject, "date": date, "snippet": preview})})
            else:
                self.log_message(f"Ignorado: {sender} | {subject}")

            self.last_uid = uid
            self.save_config()
            self.set_cursor(self.last_uid)

    def worker(self):
        try:
            self.set_status("Conectando")
            self.initialize_cursor()
            self.set_status("Vigilando")
            interval = self.get_interval()
            self.log_message("Monitor iniciado.")

            while not self.stop_event.is_set():
                try:
                    self.poll_once()
                except imaplib.IMAP4.abort:
                    self.log_message("La sesión IMAP se cortó. Reintentando conexión.")
                    try:
                        if self.mail:
                            try:
                                self.mail.logout()
                            except Exception:
                                pass
                        self.mail = self.connect()
                    except Exception as e:
                        self.log_message(f"Reintento falló: {e}")
                except Exception as e:
                    self.log_message(f"Error en revisión: {e}")

                for _ in range(interval * 10):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)

        except Exception as e:
            self.log_message(str(e))
            self.set_status("Error")
            self.root.after(0, lambda: self.start_button.configure(state="normal"))
            self.root.after(0, lambda: self.stop_button.configure(state="disabled"))
        finally:
            try:
                if self.mail is not None:
                    self.mail.logout()
            except Exception:
                pass
            self.mail = None
            if not self.stop_event.is_set():
                self.set_status("Detenida")

    def start_watching(self):
        if self.worker_thread and self.worker_thread.is_alive():
            return

        if not self.email_var.get().strip() or not self.password_var.get().strip() or not self.sender_var.get().strip():
            messagebox.showwarning("Faltan datos", "Completá correo, app password y al menos un remitente.")
            return

        self.stop_event.clear()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.worker_thread = threading.Thread(target=self.worker, daemon=True)
        self.worker_thread.start()

    def stop_watching(self):
        self.stop_event.set()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.set_status("Deteniendo")
        self.save_config()
        self.log_message("Monitor detenido por el usuario.")

    def on_close(self):
        self.stop_event.set()
        self.save_config()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass
    app = GmailWatcherApp(root)
    app.refresh_history_list()
    root.mainloop()


if __name__ == "__main__":
    main()
