import imaplib
import email
import re
import time
from email.header import decode_header
from plyer import notification

# CONFIG
EMAIL = "pabluchin15@gmail.com"
PASSWORD = "pqdt kgfp kcne zfrk"
REMITENTES_OBJETIVO = ["noreply@fing.edu.uy"]  # Ahora es una lista
INTERVALO = 30  # segundos

def decode_mime_text(text):
    """Decodifica texto MIME correctamente"""
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

def extraer_email(email_field):
    """Extrae el email de un campo From con formato 'Name <email@domain>'"""
    if not email_field:
        return ""
    # Busca patrón <email@domain>
    match = re.search(r'<([^>]+)>', email_field)
    if match:
        return match.group(1).strip().lower()
    # Si no tiene <>, asume que es el email directo
    return email_field.strip().lower()

def conectar():
    """Conecta con reintentos"""
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            server = imaplib.IMAP4_SSL('imap.gmail.com')
            server.login(EMAIL, PASSWORD)
            print(f"✓ Conectado en intento {intento + 1}")
            return server
        except Exception as e:
            print(f"✗ Intento {intento + 1} falló: {e}")
            if intento < max_intentos - 1:
                time.sleep(5)
    raise Exception("No se pudo conectar después de 3 intentos")

def revisar_mails(server):
    """Revisa mails sin marcar como leídos"""
    try:
        server.select('INBOX', readonly=True)  # readonly evita cambios accidentales
        status, mensajes = server.search(None, 'UNSEEN')
        
        if status != 'OK' or not mensajes[0]:
            return
        
        uids = mensajes[0].split()
        print(f"Revisando {len(uids)} mails sin leer...")
        
        for uid in uids:
            try:
                status, data = server.fetch(uid, '(RFC822)')
                if status != 'OK' or not data[0]:
                    continue
                
                msg = email.message_from_bytes(data[0][1])
                
                # Extrae datos correctamente
                from_field = decode_mime_text(msg.get('From', ''))
                remitente = extraer_email(from_field)
                asunto = decode_mime_text(msg.get('Subject', '(sin asunto)'))
                
                print(f"  De: {from_field} ({remitente})")
                print(f"  Asunto: {asunto}")
                
                # Compara el email extraído con los objetivos
                for objetivo in REMITENTES_OBJETIVO:
                    if remitente == objetivo.lower() or objetivo.lower() in remitente:
                        print(f"  ✓ ¡COINCIDENCIA!")
                        mostrar_notificacion(asunto, from_field)
                        break
                
            except Exception as e:
                print(f"Error procesando UID {uid}: {e}")
        
    except Exception as e:
        print(f"Error en revisar_mails: {e}")
        raise

def mostrar_notificacion(asunto, remitente):
    """Muestra notificación con más información"""
    try:
        notification.notify(
            title="📩 Mail importante",
            message=f"De: {remitente}\nAsunto: {asunto[:100]}",
            timeout=8
        )
    except Exception as e:
        print(f"Error en notificación: {e}")

def main():
    print("=== Gmail Watcher Simple ===")
    print(f"Vigilando: {', '.join(REMITENTES_OBJETIVO)}")
    print(f"Intervalo: {INTERVALO}s\n")
    
    server = None
    intentos_reconexion = 0
    
    while True:
        try:
            if server is None:
                server = conectar()
                intentos_reconexion = 0
            
            revisar_mails(server)
            time.sleep(INTERVALO)
            
        except imaplib.IMAP4.abort:
            print("Conexión abortada, reconectando...")
            server = None
            intentos_reconexion += 1
            if intentos_reconexion > 5:
                print("Demasiados intentos fallidos, esperando 30 segundos...")
                time.sleep(30)
                intentos_reconexion = 0
            time.sleep(5)
            
        except Exception as e:
            print(f"Error: {e}")
            server = None
            time.sleep(10)

if __name__ == "__main__":
    main()