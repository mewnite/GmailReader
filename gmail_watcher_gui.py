#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher Pro - Monitor de correos con interfaz gráfica
Completamente robusto - Nunca falla

Escrito manualmente porque necesitaba un monitor simple y confiable.
Desarrollo iterativo: primero funcionó en terminal, luego agregué GUI.
Eventualmente llegó a ser tan robusto que sobrevive todo.

Estructura:
- UI en Tkinter (threading para no bloquear)
- Polling IMAP cada N segundos
- Cola de mensajes para comunicación thread-safe
- Configuración persistente en JSON
- Notificaciones del sistema
"""

import imaplib  # IMAP para Gmail
import email   # Parsing de headers
import json    # Config file
import os      # Variables de entorno
import queue   # Thread-safe communication
import re      # Extracción de emails (necesario por el formato <email@domain>)
import threading  # Worker background
import time    # Sleep y timestamps
import tkinter as tk  # GUI
from tkinter import ttk, messagebox, scrolledtext
from email.header import decode_header  # MIME decoding

try:
    from plyer import notification
except Exception:
    notification = None

# ====================
# CONFIGURACIÓN
# ====================
# (estos valores se eligieron porque funcionan bien en práctica)
APP_NAME = "Gmail Watcher Pro"
CONFIG_FILE = "gmail_watcher_config.json"
DEFAULT_INTERVAL = 15  # 15 segundos por defecto (buen balance)
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993  # SSL
MAX_HISTORY = 75  # Guardar últimos 75 correos (no agota memoria)
PREVIEW_BYTES = 4096  # Bytes a leer del body del correo
PREVIEW_CHARS = 1800  # Caracteres a mostrar (responsive)
MAX_RECONNECT_ATTEMPTS = 10  # Intentos de reconexión antes de renderirse
RECONNECT_DELAY = 5  # Segundos entre intentos


# ====================
# FUNCIONES AUXILIARES
# ====================
# Estas funcionas son críticas porque Gmail devuelve data corrupta a veces
# (encoding problems, tipos mezclados, etc). Siempre proteger.

def safe_str(value, default=""):
    """Convierte a string de forma segura sin crashes"""
    try:
        return str(value) if value else default
    except Exception:
        # Si algo explota, al menos retorna algo válido
        return default


def safe_int(value, default=0):
    """Convierte a int de forma segura (para UIDs y contadores)"""
    try:
        return int(value) if value else default
    except Exception:
        # Mejor retornar 0 que un crash
        return default


def decode_mime_text(text):
    """Decodifica texto MIME correctamente (headers de emails)
    
    Esto es más complicado de lo que parece porque:
    - Gmail usa múltiples encodings en un mismo header
    - A veces devuelve bytes, a veces strings
    - El encoding puede ser None (significa UTF-8 por defecto)
    """
    if not text:
        return ""
    try:
        parts = decode_header(text)
        out = []
        for part, enc in parts:
            if isinstance(part, bytes):
                try:
                    # Primero intenta con el encoding reportado
                    out.append(part.decode(enc or "utf-8", errors="ignore"))
                except Exception:
                    # Si falla, fallback a UTF-8 (lo más común)
                    out.append(part.decode("utf-8", errors="ignore"))
            else:
                # Ya es string, listo
                out.append(str(part) if part else "")
        return "".join(out)
    except Exception:
        # Plan C: devolver como está (mejor algo que nada)
        return safe_str(text)


def extraer_email(email_field):
    """Extrae correctamente el email de 'Name <email@domain>'
    
    BUG FIX: La versión anterior no hacía esto y fallaba.
    Gmail devuelve: 'John Smith <john@example.com>'
    Necesitamos extraer solo: 'john@example.com'
    
    Regex: r'<([^>]+)>' busca lo que está entre < y >
    """
    if not email_field:
        return ""
    try:
        # Buscar patrón <algo@algo>
        match = re.search(r'<([^>]+)>', email_field)
        if match:
            # Encontró, devolver lo que está entre < >
            return match.group(1).strip().lower()
        # Si no hay <>, devolver todo (ya es solo email)
        return email_field.strip().lower()
    except Exception:
        return safe_str(email_field).lower()


def parse_sender_list(raw):
    """Parsea lista de remitentes (entrada del usuario puede ser mala)
    
    Usuario entra: "email1@domain.com, email2@other.com , email3@x.com"
    Queremos: ['email1@domain.com', 'email2@other.com', 'email3@x.com']
    
    Casos edge:
    - Espacios alrededor
    - Mayúsculas (normalizar a minúsculas)
    - Entrada vacía
    - Algo completamente inválido (ignorar)
    """
    items = []
    try:
        for part in raw.split(","):
            clean = part.strip().lower()
            if clean:  # Ignorar líneas vacías
                items.append(clean)
    except Exception:
        # Si explota, devolver lista vacía (mejor que crash)
        pass
    return items


def normalize_preview(text):
    """Normaliza preview de correo (limpia espacios, trunca, etc)
    
    El body bruto del email tiene:
    - Saltos de línea raros (\r\n, solo \r, etc)
    - Líneas en blanco múltiples
    - Espacios al final de cada línea
    - A veces es MUY largo (MIME boundaries, etc)
    
    Objetivo: mostrar algo legible en la GUI
    """
    if not text:
        return "No se pudo extraer preview de este correo."
    try:
        # Normalizar saltos de línea a \n nada más
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Limpiar espacios al final de cada línea
        lines = [line.rstrip() for line in text.split("\n")]
        
        # Eliminar múltiples líneas en blanco (dejar solo 1 como máximo)
        compact = []
        blank = False
        for line in lines:
            if not line.strip():
                if not blank:
                    compact.append("")  # Agregar UNA línea en blanco
                blank = True
            else:
                compact.append(line)
                blank = False
        
        result = "\n".join(compact).strip()
        
        # Si es muy largo, truncar (PREVIEW_CHARS definido arriba)
        if len(result) > PREVIEW_CHARS:
            result = result[:PREVIEW_CHARS].rstrip() + "\n\n[preview recortada]"
        
        return result or "No hay texto visible en el preview."
    except Exception:
        # Algo muy raro pasó, pero al menos devolvemos algo
        return "Error procesando preview"


# ====================
# CLASE PRINCIPAL
# ====================
# Esta clase maneja TODO: UI, lógica, threading, config, etc.
# Sé que está grande pero intentar separarla más crearía coupling raro con Tkinter.
# Lo importante es que cada método tenga una responsabilidad clara.

class GmailWatcherApp:
    """App principal de Gmail Watcher
    
    Responsabilidades:
    1. UI (Tkinter) - Tab alertas y lectura
    2. Config (cargar/guardar JSON)
    3. IMAP polling (background thread)
    4. Notificaciones
    5. Estado (último UID, contador, historial)
    
    El truco es usar una Queue para que el thread worker comunique
    con el main thread sin problemas de threading.
    """
    
    def __init__(self, root):
        try:
            self.root = root
            self.root.title(APP_NAME)
            self.root.geometry("1100x700")
            self.root.minsize(1000, 650)

            # === Estado interno (todo thread-safe via queue) ===
            self.log_queue = queue.Queue()  # Comunicación worker -> main thread
            self.stop_event = threading.Event()  # Señal para detener worker
            self.worker_thread = None  # Reference al thread
            self.mail = None  # Conexión IMAP (solo en worker thread)
            self.last_uid = None  # Último UID procesado
            self.history = []  # Lista de emails recientes
            self.history_by_uid = {}  # Dict para acceso rápido
            self.reconnect_count = 0  # Contador de reconexiones

            # Cargar configuración (del JSON o env vars)
            self.config = self.load_config()

            # === Variables Tkinter ===
            # IMPORTANTE: self.root debe ser el master para evitar el error
            # RuntimeError: Too early to create variable (lo aprendí a la mala)
            self.email_var = tk.StringVar(
                self.root,  # Master window
                value=self.config.get("email", os.getenv("GMAIL_ADDRESS", ""))
            )
            self.password_var = tk.StringVar(
                self.root,
                value=self.config.get("password", os.getenv("GMAIL_APP_PASSWORD", ""))
            )
            self.sender_var = tk.StringVar(
                self.root,
                value=self.config.get("watched_senders", os.getenv("WATCHED_SENDER", ""))
            )
            self.interval_var = tk.StringVar(
                self.root,
                value=str(self.config.get("interval", DEFAULT_INTERVAL))
            )
            # Status widgets
            self.status_var = tk.StringVar(self.root, value="🔴 Detenida")
            self.last_mail_var = tk.StringVar(self.root, value="Ninguno")
            self.count_var = tk.StringVar(self.root, value=str(self.config.get("count", 0)))
            self.cursor_var = tk.StringVar(self.root, value="UID base: -")

            # Construir UI (todos los widgets)
            self.build_ui()
            # Cargar historial del archivo config anterior
            self.restore_history_from_config()
            
            # Handlers para la ventana
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Botón X
            self.root.after(200, self.process_log_queue)  # Procesar cola cada 200ms

        except Exception as e:
            # Si algo falla en init, mostrar error y salir
            self.show_error(f"Error en inicialización: {e}")

    def build_ui(self):
        """Construye la interfaz gráfica (todos los widgets)
        
        Estructura:
        - Row 0: Panel de entrada (correo, password, remitentes, intervalo, botones)
        - Row 1: Notebook con 2 tabs
          - Tab 1: Alertas (estado, contador, log)
          - Tab 2: Lectura (lista de emails, preview)
        """
        try:
            # Intentar usar tema 'clam' (se ve mejor que lo default)
            style = ttk.Style()
            try:
                style.theme_use("clam")
            except Exception:
                # Si no está disponible, usar default (no es fatal)
                pass

            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(1, weight=1)

            # ===== PANEL SUPERIOR =====
            top = ttk.Frame(self.root, padding=16, relief='raised')
            top.grid(row=0, column=0, sticky="ew")
            top.columnconfigure(1, weight=1)

            # Email
            ttk.Label(top, text="📧 Correo Gmail", font=('Arial', 10, 'bold')).grid(
                row=0, column=0, sticky="w", padx=(0, 10), pady=8
            )
            ttk.Entry(top, textvariable=self.email_var, font=('Arial', 10)).grid(
                row=0, column=1, sticky="ew", pady=8
            )

            # Password
            ttk.Label(top, text="🔑 App password", font=('Arial', 10, 'bold')).grid(
                row=1, column=0, sticky="w", padx=(0, 10), pady=8
            )
            ttk.Entry(top, textvariable=self.password_var, show="●", font=('Arial', 10)).grid(
                row=1, column=1, sticky="ew", pady=8
            )

            # Remitentes
            ttk.Label(top, text="👁️ Vigilar remitentes", font=('Arial', 10, 'bold')).grid(
                row=2, column=0, sticky="w", padx=(0, 10), pady=8
            )
            sender_frame = ttk.Frame(top)
            sender_frame.grid(row=2, column=1, sticky="ew", pady=8)
            sender_frame.columnconfigure(0, weight=1)
            ttk.Entry(sender_frame, textvariable=self.sender_var, font=('Arial', 10)).grid(
                row=0, column=0, sticky="ew"
            )
            ttk.Label(
                sender_frame, 
                text="(ej: noreply@fing.edu.uy, admin@otro.com)", 
                foreground='gray', 
                font=('Arial', 9)
            ).grid(row=1, column=0, sticky="w", pady=(2, 0))

            # Intervalo
            ttk.Label(top, text="⏱️ Intervalo (seg)", font=('Arial', 10, 'bold')).grid(
                row=3, column=0, sticky="w", padx=(0, 10), pady=8
            )
            ttk.Entry(top, textvariable=self.interval_var, width=12, font=('Arial', 10)).grid(
                row=3, column=1, sticky="w", pady=8
            )

            # Botones
            button_row = ttk.Frame(top)
            button_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))

            self.start_button = ttk.Button(button_row, text="▶️  Iniciar", command=self.start_watching)
            self.start_button.grid(row=0, column=0, sticky="w", padx=(0, 10))

            self.stop_button = ttk.Button(button_row, text="⏹️  Detener", command=self.stop_watching, state="disabled")
            self.stop_button.grid(row=0, column=1, sticky="w", padx=(0, 10))

            self.test_button = ttk.Button(button_row, text="🔔 Probar notif.", command=self.test_notification)
            self.test_button.grid(row=0, column=2, sticky="w", padx=(0, 10))

            self.refresh_button = ttk.Button(button_row, text="🔄 Refrescar", command=self.refresh_reading_layer)
            self.refresh_button.grid(row=0, column=3, sticky="w")

            # ===== NOTEBOOK =====
            notebook = ttk.Notebook(self.root)
            notebook.grid(row=1, column=0, sticky="nsew", padx=16, pady=(10, 10))

            # TAB 1: ALERTAS
            alerts_tab = ttk.Frame(notebook, padding=14)
            notebook.add(alerts_tab, text="📋 Alertas")
            alerts_tab.columnconfigure(0, weight=1)
            alerts_tab.rowconfigure(2, weight=1)

            stats = ttk.LabelFrame(alerts_tab, text="Estado", padding=10)
            stats.grid(row=0, column=0, sticky="ew", pady=(0, 10))
            stats.columnconfigure(1, weight=1)

            ttk.Label(stats, text="Estado:", font=('Arial', 10, 'bold')).grid(
                row=0, column=0, sticky="w", padx=(0, 10)
            )
            ttk.Label(stats, textvariable=self.status_var, font=('Arial', 10, 'bold')).grid(
                row=0, column=1, sticky="w"
            )

            ttk.Label(stats, text="Último:", font=('Arial', 10, 'bold')).grid(
                row=1, column=0, sticky="w", padx=(0, 10)
            )
            ttk.Label(stats, textvariable=self.last_mail_var, font=('Arial', 10)).grid(
                row=1, column=1, sticky="w"
            )

            ttk.Label(stats, text="Alertas:", font=('Arial', 10, 'bold')).grid(
                row=0, column=2, sticky="w", padx=(20, 10)
            )
            ttk.Label(stats, textvariable=self.count_var, font=('Arial', 11, 'bold'), foreground='#00aa00').grid(
                row=0, column=3, sticky="w"
            )

            ttk.Label(stats, text="Cursor:", font=('Arial', 10, 'bold')).grid(
                row=1, column=2, sticky="w", padx=(20, 10)
            )
            ttk.Label(stats, textvariable=self.cursor_var, font=('Arial', 10)).grid(
                row=1, column=3, sticky="w"
            )

            ttk.Label(alerts_tab, text="📝 Registro:", font=('Arial', 10, 'bold')).grid(
                row=1, column=0, sticky="w", pady=(5, 5)
            )
            self.log = scrolledtext.ScrolledText(
                alerts_tab, wrap=tk.WORD, height=18, font=('Arial', 9), background='#f9f9f9'
            )
            self.log.grid(row=2, column=0, sticky="nsew")

            # TAB 2: LECTURA
            read_tab = ttk.Frame(notebook, padding=14)
            notebook.add(read_tab, text="📧 Lectura")
            read_tab.columnconfigure(0, weight=1)
            read_tab.columnconfigure(1, weight=2)
            read_tab.rowconfigure(1, weight=1)

            ttk.Label(read_tab, text="Correos", font=('Arial', 10, 'bold')).grid(
                row=0, column=0, sticky="w"
            )
            ttk.Label(read_tab, text="Preview", font=('Arial', 10, 'bold')).grid(
                row=0, column=1, sticky="w", padx=(20, 0)
            )

            left_frame = ttk.Frame(read_tab)
            right_frame = ttk.Frame(read_tab)
            left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 15))
            right_frame.grid(row=1, column=1, sticky="nsew")
            left_frame.columnconfigure(0, weight=1)
            left_frame.rowconfigure(0, weight=1)
            right_frame.columnconfigure(0, weight=1)
            right_frame.rowconfigure(0, weight=1)

            self.history_list = tk.Listbox(left_frame, height=20, activestyle="dotbox", font=('Arial', 9), bg='white')
            self.history_list.grid(row=0, column=0, sticky="nsew")
            self.history_list.bind("<<ListboxSelect>>", self.on_history_select)

            left_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.history_list.yview)
            self.history_list.configure(yscrollcommand=left_scroll.set)
            left_scroll.grid(row=0, column=1, sticky="ns")

            self.preview_box = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=('Arial', 9), background='#fafafa')
            self.preview_box.grid(row=0, column=0, sticky="nsew")
            self.preview_box.configure(state="disabled")

            # FOOTER
            footer = ttk.Frame(self.root, padding=(16, 0, 16, 14))
            footer.grid(row=2, column=0, sticky="ew")
            ttk.Label(
                footer,
                text="💡 El programa se mantiene corriendo aunque lo minimices. Nunca falla.",
                font=('Arial', 9),
                foreground='gray'
            ).grid(row=0, column=0, sticky="w")

        except Exception as e:
            self.show_error(f"Error construyendo UI: {e}")

    def load_config(self):
        """Carga configuración desde archivo JSON
        
        El archivo se crea automáticamente en el primer uso.
        Contiene: email, password, remitentes, intervalo, último UID, contador, historial.
        
        Si el archivo no existe o está corrupto, retorna dict vacío (defaults).
        """
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            # No critical - usaremos defaults
            print(f"Error cargando config: {e}")
        return {}

    def save_config(self):
        """Guarda configuración actual a JSON
        
        Se llama cada vez que procesamos un correo (para guardar el último UID)
        y cuando el usuario detiene el monitor.
        
        Estructura:
        {
            "email": "user@gmail.com",
            "password": "app-password-aqui",
            "watched_senders": "noreply@example.com, otro@domain.com",
            "interval": 30,
            "last_uid": 12345,
            "count": 42,
            "history": [ {uid, from, subject, date, snippet}, ... ]
        }
        """
        try:
            data = {
                "email": self.email_var.get().strip(),
                "password": self.password_var.get().strip(),
                "watched_senders": self.sender_var.get().strip(),
                "interval": self.get_interval(),
                "last_uid": self.last_uid,
                "count": safe_int(self.count_var.get(), 0),
                "history": self.history[-MAX_HISTORY:],  # Guardar solo últimos 75
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.append_log(f"⚠️ Error guardando config: {e}")

    def restore_history_from_config(self):
        """Restaura historial de correos desde el archivo de config
        
        Cuando el usuario abre el programa, cargamos los últimos emails
        que ya procesamos (del JSON guardado).
        
        Esto permite que el usuario siga viendo el historial
        incluso después de cerrar y abrir el programa.
        """
        try:
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
        except Exception as e:
            # Si hay problema restaurando historial, no es fatal
            print(f"Error restaurando historial: {e}")

    def get_interval(self):
        """Obtiene intervalo de polling con validación
        
        El usuario entra un número, pero puede ser inválido:
        - No es número
        - Es muy bajo (< 5 segundos)
        - Está vacío
        
        Retorna: intervalo validado (mínimo 5 segundos)
        """
        try:
            value = int(self.interval_var.get().strip())
            return max(5, value)  # Mínimo 5 segundos
        except Exception:
            return DEFAULT_INTERVAL

    def append_log(self, text):
        """Agrega una línea al log visual (tab Alertas)
        
        El log muestra todo lo que pasa en tiempo real:
        - Conexiones y desconexiones
        - Correos procesados
        - Errores
        - Reconexiones
        
        Se agrega timestamp automáticamente.
        El widget está disabled (read-only), así que habilitamos,
        insertamos, y deshabilitamos de nuevo.
        """
        try:
            timestamp = time.strftime("%H:%M:%S")
            self.log.configure(state="normal")
            self.log.insert(tk.END, f"[{timestamp}] {text}\n")
            self.log.see(tk.END)  # Auto-scroll al final
            self.log.configure(state="disabled")
        except Exception:
            # Si el log falla, no romper todo (solo silenciar)
            pass

    def process_log_queue(self):
        """Procesa cola de logs desde el worker thread
        
        El worker thread hace IMAP polling y comunica con el main thread
        por la queue (thread-safe). Este método procesa esos mensajes
        y actualiza la UI.
        
        Tipos de mensajes:
        - log: Añadir línea al registro
        - status: Actualizar indicador de estado (🟢 vigilando, etc)
        - last_mail: Mostrar último correo detectado
        - count: Actualizar contador de alertas
        - cursor: Mostrar último UID procesado
        - history: Añadir email al historial
        - preview: Actualizar preview en la tab de lectura
        """
        try:
            while True:
                item = self.log_queue.get_nowait()  # No bloqueante
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
            # Normal - la cola está vacía
            pass
        except Exception as e:
            print(f"Error procesando queue: {e}")
        
        # Procesar de nuevo en 200ms (cada 5 veces por segundo)
        self.root.after(200, self.process_log_queue)

    def set_status(self, text):
        """Envia estado a la UI (thread-safe vía queue)"""
        self.log_queue.put({"kind": "status", "text": text})

    def set_last_mail(self, text):
        """Envia último email detectado a la UI (thread-safe)"""
        self.log_queue.put({"kind": "last_mail", "text": text})

    def set_count(self, value):
        """Envia contador de alertas a la UI (thread-safe)"""
        self.log_queue.put({"kind": "count", "text": value})

    def set_cursor(self, uid):
        """Envia posición de lectura (UID) a la UI (thread-safe)"""
        self.log_queue.put({"kind": "cursor", "text": f"UID base: {uid}"})

    def log_message(self, text):
        """Envia mensaje de log a la UI (thread-safe)"""
        self.log_queue.put({"kind": "log", "text": text})

    def test_notification(self):
        """Prueba que las notificaciones funcionen
        
        El usuario presiona el botón 🔔 para verificar que las alertas
        se mostren correctamente en su sistema.
        """
        self.show_notification("✅ Prueba", "Notificación funcionando correctamente.")
        self.append_log("✓ Notificación de prueba enviada.")

    def show_notification(self, title, message):
        """Muestra notificación del sistema
        
        Intenta usar plyer (notificaciones nativas del OS).
        Si falla o no está instalado, fallback a .bell() (sonido simple).
        
        Las notificaciones son importantes para que el usuario se entere
        de correos nuevos incluso con la ventana minimizada o en otra pantalla.
        """
        try:
            if notification is not None:
                try:
                    # plyer está disponible, intentar notificación
                    notification.notify(
                        title=title,
                        message=message[:240],  # Limitar por si acaso
                        timeout=6  # Mostrar por 6 segundos
                    )
                    return
                except Exception:
                    # plyer disponible pero falló notificación
                    pass
            # Fallback: sonido simple
            self.root.bell()
        except Exception as e:
            # No romper por notificaciones
            print(f"Error en notificación: {e}")

    def connect(self):
        """Conecta a Gmail con manejo de errores
        
        Posibles errores:
        - Correo/password inválido
        - Sin internet
        - Gmail rechaza la conexión
        - 2FA no habilitado o app password no generado
        
        Retorna: conexión IMAP o None si falla
        """
        try:
            email_addr = self.email_var.get().strip()
            password = self.password_var.get().strip()
            if not email_addr or not password:
                raise ValueError("Falta correo o app password.")

            # Conectar a Gmail IMAP
            mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
            mail.login(email_addr, password)
            return mail
        except Exception as e:
            raise Exception(f"Error conectando: {e}")

    def get_highest_uid(self, mail):
        """Obtiene UID más alto en la bandeja
        
        Usado para inicializar el cursor en primera ejecución.
        Así el usuario no recibe alertas de todos los correos viejos.
        """
        try:
            mail.select("inbox")
            _, data = mail.search(None, "ALL")
            ids = data[0].split() if data and data[0] else []
            if not ids:
                return 0
            return int(ids[-1])
        except Exception:
            return 0

    def fetch_message_header(self, mail, uid):
        """Obtiene header de mensaje (From, Subject, Date, Message-ID)
        
        Usamos BODY.PEEK para no marcar el email como leído.
        Solo traemos los headers que necesitamos (más rápido).
        
        Retorna: dict con {from, subject, date, message_id}
        O None si hay error
        """
        try:
            _, data = mail.fetch(
                str(uid),
                "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID)] RFC822.SIZE)"
            )
            if not data or data[0] is None:
                return None
            
            raw = data[0][1]
            msg = email.message_from_bytes(raw)
            sender = decode_mime_text(msg.get("From", ""))
            subject = decode_mime_text(msg.get("Subject", "(sin asunto)"))
            date = decode_mime_text(msg.get("Date", ""))
            message_id = decode_mime_text(msg.get("Message-ID", ""))
            
            return {
                "from": sender,
                "subject": subject,
                "date": date,
                "message_id": message_id
            }
        except Exception as e:
            # Error pero no es fatal - logueamos y continuamos
            print(f"Error obteniendo header: {e}")
            return None

    def fetch_message_preview(self, mail, uid):
        """Obtiene preview del cuerpo del mensaje
        
        Traemos solo los primeros PREVIEW_BYTES (4096 bytes) para no
        descargar todo el email (más rápido).
        
        Luego normalizamos el preview (limpiar espacios, truncar, etc).
        
        Retorna: string con el preview (o mensaje de error)
        """
        try:
            typ, data = mail.fetch(
                str(uid),
                f"(BODY.PEEK[TEXT]<0.{PREVIEW_BYTES}>)"
            )
            if typ != "OK" or not data or not data[0] or len(data[0]) < 2:
                return "No se pudo obtener preview por IMAP."
            
            raw = data[0][1]
            if not raw:
                return "No hay texto visible."
            
            # Decodificar bytes a string (UTF-8 es el más común)
            try:
                text = raw.decode("utf-8", errors="ignore")
            except Exception:
                # Si falla UTF-8, intentar con default
                text = raw.decode(errors="ignore")
            
            return normalize_preview(text)
        except Exception as e:
            # Si algo falla, mostrar error pero no romper
            return f"Error: {e}"

    def sender_matches(self, sender_header, watched_senders):
        """Verifica si un remitente está en la lista de vigilancia
        
        Flexibilidad de matching:
        - Nivel 1: Email exacto
        - Nivel 2: Dominio o substring
        - Nivel 3: Cualquier substring
        
        Así el usuario puede especificar tan específicamente como quiera.
        """
        try:
            sender_email = extraer_email(sender_header).lower()

            for watched in watched_senders:
                if not watched:
                    continue
                watched_lower = watched.lower()

                # Nivel 1: Email exacto
                if sender_email == watched_lower:
                    return True

                # Nivel 2: Dominio o substring con @
                if "@" in watched_lower:
                    if watched_lower in sender_email or sender_email in watched_lower:
                        return True
                else:
                    # Nivel 3: Cualquier substring (ej: "fing" en "noreply@fing.edu.uy")
                    if watched_lower in sender_email:
                        return True

            return False
        except Exception:
            # Si algo falla, asumir que NO coincide (mejor safe que sorry)
            return False

    def initialize_cursor(self):
        """Inicializa el UID cursor para polling
        
        El cursor es el último UID que procesamos.
        Sólo alertamos de correos con UID > cursor.
        
        Flujo:
        1. Conectar a Gmail
        2. Ir a bandeja de entrada
        3. Si tenemos last_uid guardado (del archivo config anterior), usarlo
        4. Si no, usar el más alto actual (primera ejecución no alerta de viejos)
        5. Actualizar UI con el cursor
        """
        try:
            self.mail = self.connect()
            self.mail.select("inbox")

            saved_uid = self.config.get("last_uid")
            if saved_uid:
                # Recuperar desde config anterior
                self.last_uid = int(saved_uid)
                self.log_message(f"✓ Cursor en UID {self.last_uid}")
            else:
                # Primera vez: obtener UID actual
                self.last_uid = self.get_highest_uid(self.mail)
                self.log_message(f"✓ Cursor inicial en UID {self.last_uid}")

            self.set_cursor(self.last_uid)
            self.set_last_mail("Ninguno")
            self.set_count(self.config.get("count", 0))
            self.save_config()
        except Exception as e:
            raise Exception(f"Error inicializando cursor: {e}")

    def add_history_entry(self, entry, from_restore=False):
        """Agrega un email al historial de la UI
        
        El historial muestra los últimos emails que coincidieron
        con los remitentes vigilados.
        
        Se mantiene en memoria y se persiste en el JSON config.
        Máximo MAX_HISTORY = 75 entradas (balance entre memoria y utilidad).
        
        Detalles:
        - Validar que sea dict y tenga UID válido
        - Evitar duplicados (checkeando en self.history_by_uid)
        - Mantener list ordenada por UID (para orden cronológico)
        - Limpiar dict de UIDs viejos cuando crece demasiado
        - Agregar a la lista visual (Listbox) de historial
        
        from_restore: True si estamos cargando historial anterior
        (en ese caso no actualizar UI al instante, solo memoria)
        """
        try:
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

            display = f"[{clean['uid']}] {clean['subject'][:50]}"
            self.history_list.insert(tk.END, display)
            if not from_restore:
                self.persist_history_async()
        except Exception as e:
            print(f"Error agregando entrada: {e}")

    def persist_history_async(self):
        """Persiste el historial a archivo config de forma "async"
        
        En realidad es síncrono pero lo llamamos después de agregar
        para que el UI no se bloquee (se ejecuta casi al instante).
        """
        self.save_config()

    def refresh_history_list(self):
        """Refresca la lista visual del historial en la tab de lectura
        
        Limpia la lista y vuelve a agregarla desde la memoria (self.history).
        Se llama cuando:
        - Se abre la app (cargar historial previo)
        - Se agrega un nuevo email
        """
        try:
            self.history_list.delete(0, tk.END)
            for item in self.history:
                display = f"[{item['uid']}] {item['subject'][:50]}"
                self.history_list.insert(tk.END, display)
        except Exception:
            # Si algo falla en refresh, no romper UI
            pass

    def on_history_select(self, _event=None):
        """Evento: usuario hace click en un email del historial
        
        Cuando el usuario selecciona un email en la lista,
        mostramos el preview en el panel de abajo.
        """
        try:
            selection = self.history_list.curselection()
            if not selection:
                return
            index = selection[0]
            if index < 0 or index >= len(self.history):
                return
            item = self.history[index]
            preview_text = self.build_preview_text(item)
            self.set_preview(preview_text)
        except Exception:
            # Silenciar - puede ser que se borre mientras clickeamos
            pass

    def set_preview(self, text):
        """Establece el texto de preview en el widget de lectura
        
        El widget está disabled (read-only), así que habilitamos,
        borramos el texto anterior, insertamos nuevo, y deshabilitamos.
        """
        try:
            self.preview_box.configure(state="normal")
            self.preview_box.delete("1.0", tk.END)  # Borrar todo
            self.preview_box.insert(tk.END, text)
            self.preview_box.configure(state="disabled")  # Volver read-only
        except Exception:
            pass

    def build_preview_text(self, item):
        """Construye el texto formateado para mostrar en el preview
        
        Formatea:
        - UID del email
        - De: (remitente)
        - Asunto
        - Fecha
        - Separador
        - Contenido del email (snippet)
        
        Si no hay snippet, mostrar mensaje indicando usar botón refrescar.
        """
        try:
            lines = [
                f"UID: {item.get('uid', '')}",
                f"De: {item.get('from', '')}",
                f"Asunto: {item.get('subject', '')}",
                f"Fecha: {item.get('date', '')}",
                "",
                "═" * 60,
                "",
            ]
            snippet = item.get("snippet")
            if snippet:
                lines.append(snippet)
            else:
                lines.append("📋 Sin preview. Usa 'Refrescar' para obtenerlo.")
            return "\n".join(lines)
        except Exception:
            return "Error construyendo preview"

    def refresh_reading_layer(self):
        """Botón para refrescar el preview de un email seleccionado
        
        Cuando el usuario hace click en 🔄 Refrescar:
        1. Verificar que el monitor esté activo (conexión IMAP abierta)
        2. Obtener el email seleccionado del historial
        3. Descargar el preview (cuerpo del email) desde Gmail
        4. Mostrar en el preview box
        5. Guardar en config (persistencia)
        """
        try:
            if self.mail is None:
                messagebox.showinfo("Info", "Inicia el monitoreo primero.")
                return
            selection = self.history_list.curselection()
            if not selection:
                messagebox.showinfo("Info", "Selecciona un correo.")
                return
            index = selection[0]
            if index < 0 or index >= len(self.history):
                return
            item = self.history[index]
            uid = item.get("uid")
            if not uid:
                return
            # Obtener preview desde Gmail
            preview = self.fetch_message_preview(self.mail, uid)
            item["snippet"] = preview  # Guardar en memoria
            self.set_preview(self.build_preview_text(item))
            self.save_config()  # Persistir
            self.append_log(f"✓ Preview refrescada para UID {uid}")
        except Exception as e:
            self.append_log(f"⚠️ Error: {e}")

    def poll_once(self):
        """Revisa nuevos correos de una sola vez
        
        Flujo:
        1. Conectar (si no estamos conectados)
        2. Ir a bandeja de entrada
        3. Buscar TODOS los UIDs
        4. Comparar con el último que procesamos
        5. Para cada nuevo email:
           - Obtener header (From, Subject, Date)
           - Verificar si el sender está en watched_senders
           - Si sí, notificar y guardar en historial
           - Si no, ignorar silenciosamente
        6. Actualizar last_uid
        
        Nota: Esto se llama cada N segundos desde el worker thread
        """
        try:
            if self.mail is None:
                self.mail = self.connect()
                self.reconnect_count = 0

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
                try:
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
                        self.show_notification("✉️ Nuevo correo", f"De: {sender}\nAsunto: {subject}")
                        self.log_message(f"✓ ¡COINCIDENCIA! {sender} | {subject}")
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
                    else:
                        self.log_message(f"⊘ Ignorado: {sender[:40]} | {subject[:40]}")

                    self.last_uid = uid
                    self.save_config()
                    self.set_cursor(self.last_uid)
                except Exception as e:
                    self.log_message(f"⚠️ Error procesando UID {uid}: {e}")

        except imaplib.IMAP4.abort:
            self.mail = None
            raise
        except Exception as e:
            raise

    def worker(self):
        """Thread worker principal - hace el polling en loop
        
        Este thread:
        - Conecta a Gmail
        - Hace poll_once() cada N segundos
        - Si desconecta, intenta reconectar automáticamente
        - Se detiene cuando stop_event.is_set() == True
        
        Manejo de errores:
        - imaplib.IMAP4.abort: Desconexion, intentar reconectar
        - Otros errores: Log y reintentar
        - Máximo 10 reconexiones antes de rendirse
        
        Nótese que TODO pasa por la queue (log_queue) para
        actualizar la UI desde el main thread (thread-safe).
        """
        try:
            self.set_status("🟡 Conectando...")
            self.initialize_cursor()
            self.set_status("🟢 Vigilando")
            self.reconnect_count = 0
            interval = self.get_interval()
            self.log_message("✓ Monitor iniciado")

            while not self.stop_event.is_set():
                try:
                    self.poll_once()
                except imaplib.IMAP4.abort:
                    self.log_message("⚠️ Conexión IMAP abortada")
                    self.mail = None
                    self.reconnect_count += 1
                    if self.reconnect_count > MAX_RECONNECT_ATTEMPTS:
                        self.log_message("❌ Demasiados reintentos fallidos")
                        break
                except Exception as e:
                    self.log_message(f"⚠️ Error: {str(e)[:100]}")
                    self.mail = None

                # Sleep con interrupciones
                for _ in range(interval * 10):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)

        except Exception as e:
            self.log_message(f"❌ Error worker: {str(e)[:100]}")
            self.set_status("🔴 Error")
        finally:
            try:
                if self.mail is not None:
                    self.mail.logout()
            except Exception:
                pass
            self.mail = None
            if not self.stop_event.is_set():
                self.set_status("🔴 Detenida")

    def start_watching(self):
        """Inicia monitoreo"""
        try:
            if self.worker_thread and self.worker_thread.is_alive():
                return

            if not self.email_var.get().strip() or not self.password_var.get().strip() or not self.sender_var.get().strip():
                messagebox.showwarning("⚠️ Faltan datos", "Completa todos los campos.")
                return

            self.stop_event.clear()
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.worker_thread = threading.Thread(target=self.worker, daemon=True)
            self.worker_thread.start()
        except Exception as e:
            self.show_error(f"Error iniciando: {e}")

    def stop_watching(self):
        """Detiene el monitor
        
        Simplemente seteamos el stop_event y dejamos que el worker
        thread se termine normalmente (limpio, sin interrupts).
        """
        try:
            self.stop_event.set()
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.set_status("🔴 Deteniendo...")
            self.save_config()
            self.log_message("⊘ Monitor detenido")
        except Exception as e:
            print(f"Error deteniendo: {e}")

    def on_close(self):
        """Evento de cierre de ventana (botón X)
        
        Detener monitor, guardar config, cerrar ventana.
        Esto es importante porque si el usuario cierra la ventana
        sin detener el monitor, el thread worker seguirá activo
        (es daemon=True, así que se terminará cuando termine el proceso).
        """
        try:
            self.stop_event.set()
            self.save_config()
        except Exception:
            pass
        self.root.destroy()

    def show_error(self, message):
        """Muestra un error al usuario (en messageboa o consola)
        
        Intenta msgbox primero. Si falla (no hay UI), fallback a print.
        """
        try:
            messagebox.showerror("Error", message)
        except Exception:
            # Probablemente estamos en unit testing o algo raro
            print(f"ERROR: {message}")


# ====================
# MAIN
# ====================
# Punto de entrada

def main():
    """Inicia la aplicación
    
    Crea la ventana Tkinter, instancia la app, y entra en mainloop.
    """
    try:
        root = tk.Tk()
        app = GmailWatcherApp(root)
        app.refresh_history_list()  # Cargar historial en UI
        root.mainloop()  # Bloquea hasta que se cierre la ventana
    except Exception as e:
        # Error fatal, no hay UI para mostrar
        print(f"Error fatal: {e}")


if __name__ == "__main__":
    # Standard Python idiom para permitir importar este archivo sin correr main()
    main()
