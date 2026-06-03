# 📚 MANUAL DE USUARIO - Gmail Watcher Pro

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Instalación](#instalación)
3. [Configuración Inicial](#configuración-inicial)
4. [Uso de la Aplicación](#uso-de-la-aplicación)
5. [Solución de Problemas](#solución-de-problemas)
6. [Preguntas Frecuentes](#preguntas-frecuentes)
7. [Información Técnica](#información-técnica)

---

## Introducción

**Gmail Watcher Pro** es una aplicación que monitorea tu bandeja de entrada de Gmail en tiempo real y te notifica automáticamente cuando recibes correos de remitentes específicos.

### Características Principales

✅ **Monitor en Tiempo Real** - Revisa nuevos correos automáticamente cada 15-60 segundos
✅ **Notificaciones del Sistema** - Alertas popup con sonido
✅ **Historial Completo** - Guarda todos los correos detectados
✅ **Preview de Correos** - Lee el contenido sin abrir Gmail
✅ **Configuración Flexible** - Vigila múltiples remitentes
✅ **100% Confiable** - Nunca falla, manejo de errores integrado

---

## Instalación

### Requisitos
- Python 3.7 o superior
- Cuenta de Gmail activa
- Conexión a internet

### Paso 1: Instalar Python
Si no tienes Python instalado, descárgalo desde [python.org](https://www.python.org)

### Paso 2: Instalar Dependencias

Abre una terminal en la carpeta del programa y ejecuta:

```bash
pip install -r requirements.txt
```

O instala manualmente:

```bash
pip install plyer
```

### Paso 3: Configurar Gmail

Este es el paso más importante. Necesitas crear una "App Password" especial para que el programa acceda a tu Gmail.

#### 3.1 Habilitar Autenticación de 2 Factores

1. Abre [Google Account](https://myaccount.google.com)
2. En el panel izquierdo, busca **"Seguridad"**
3. Verifica que tengas **"Verificación en 2 pasos"** habilitada
   - Si no está habilitada, actívala primero

#### 3.2 Crear App Password

1. Vuelve a [Google Account → Seguridad](https://myaccount.google.com/security)
2. Desplázate hacia abajo hasta encontrar **"Contraseñas de aplicación"**
3. Si no la ves, primero completa estos pasos:
   - Verifica que hayas habilitado "Verificación en 2 pasos"
   - Espera unos minutos y recarga la página
4. Selecciona:
   - **Aplicación:** Correo
   - **Dispositivo:** Windows
5. Google te generará una contraseña de 16 caracteres (con espacios)
6. **Cópiala (sin espacios)** - Este es tu App Password

---

## Configuración Inicial

### Primer Uso

1. **Abre el programa:**
   ```bash
   python gmail_watcher_gui.py
   ```

2. **Completa los campos:**

   | Campo | Ejemplo | Notas |
   |-------|---------|-------|
   | 📧 Correo Gmail | `tu@gmail.com` | Tu correo de Gmail completo |
   | 🔑 App password | `pqdt kgfp kcne zfrk` | Sin espacios: `pqdtkgfpkcnezfrk` |
   | 👁️ Vigilar remitentes | `noreply@fing.edu.uy` | Puedes agregar varios separados por coma |
   | ⏱️ Intervalo | `15` | Segundos entre revisiones (mínimo 5) |

3. **Ejemplo completo:**
   ```
   Correo: mimail@gmail.com
   Password: pqdtkgfpkcnezfrk
   Remitentes: noreply@fing.edu.uy, admin@trabajo.com, ventas@tienda.com
   Intervalo: 30
   ```

---

## Uso de la Aplicación

### Interfaz Principal

```
┌─────────────────────────────────────────────────────────┐
│ 📧 Correo Gmail: mimail@gmail.com                        │
│ 🔑 App password: ●●●●●●●●●●●●●●●●                      │
│ 👁️ Vigilar remitentes: noreply@fing.edu.uy              │
│ ⏱️ Intervalo: 30 seg                                     │
│                                                          │
│ [▶️ Iniciar] [⏹️ Detener] [🔔 Probar] [🔄 Refrescar]    │
└─────────────────────────────────────────────────────────┘
```

### Pestañas

#### 📋 Pestaña "Alertas"

Muestra:
- **Estado:** 🔴 Detenida | 🟡 Conectando | 🟢 Vigilando
- **Último mail:** El último correo detectado
- **Alertas:** Contador de correos identificados
- **Cursor:** Posición en el inbox (para evitar duplicados)
- **Registro:** Log detallado de actividad

#### 📧 Pestaña "Lectura"

- **Lado izquierdo:** Lista de todos los correos detectados
- **Lado derecho:** Preview completo del correo seleccionado
- Usa **"Refrescar"** para descargar el contenido completo

### Botones

| Botón | Función | Cuándo usar |
|-------|---------|-------------|
| ▶️ Iniciar | Comienza a monitorear | Al empezar |
| ⏹️ Detener | Pausa el monitoreo | Cuando quieras pausar |
| 🔔 Probar | Envía notificación de prueba | Para verificar que funciona |
| 🔄 Refrescar | Descarga preview del correo | Selecciona un correo primero |

### Indicadores de Estado

| Símbolo | Significado | Acción |
|---------|-------------|--------|
| 🟢 Vigilando | Funcionando correctamente | Ninguna |
| 🟡 Conectando | Iniciando conexión | Espera |
| 🔴 Detenida | No está activo | Presiona "Iniciar" |
| ⚠️ | Advertencia leve | Revisa el log |
| ❌ | Error grave | Reinicia el programa |

---

## Solución de Problemas

### "Authentication failed"

**Síntoma:** Error al intentar conectar

**Posibles causas:**
1. App Password incorrecto o mal copiado
2. Correo de Gmail incorrecto
3. 2FA no habilitado

**Solución:**
1. Verifica que hayas copiado el App Password **SIN ESPACIOS**
2. Confirma que es tu correo de Gmail (no otro email)
3. Ve a [Google Account](https://myaccount.google.com) y verifica 2FA
4. Si nada funciona, crea un nuevo App Password

---

### "No detecta mis correos"

**Síntoma:** El programa corre pero no detecta correos que debería

**Posibles causas:**
1. Los remitentes no coinciden exactamente
2. El formato no es correcto
3. Los correos ya fueron marcados como leídos

**Soluciones:**

1. **Verifica el remitente:**
   - En Gmail, abre un correo del remitente
   - Mira exactamente qué dice en "De:"
   - Cópialo exactamente en "Vigilar remitentes"

2. **Intenta variaciones:**
   ```
   ❌ Mal:  "Nombre Completo <email@domain>"
   ✅ Bien: "email@domain"
   ✅ También: "domain" (vigila todo el dominio)
   ```

3. **Vigila solo el dominio:**
   ```
   En lugar de: noreply@fing.edu.uy
   Prueba con: fing.edu.uy
   ```

4. **Marca como no leído:**
   - En Gmail, abre el correo
   - Presiona "Marcar como no leído"
   - El programa lo detectará en la próxima revisión

---

### "Se desconecta constantemente"

**Síntoma:** Aparecen mensajes de reconexión frecuentes

**Posibles causas:**
1. Intervalo muy bajo
2. Conexión a internet inestable
3. Límite de conexiones de Gmail alcanzado

**Soluciones:**

1. **Aumenta el intervalo:**
   - Prueba con 30-60 segundos en lugar de 15
   - Esto reduce carga en la red

2. **Cierra otras sesiones de Gmail:**
   - En navegador: cierra Gmail o desconéctate
   - En otros dispositivos: cierra la app de Gmail

3. **Verifica conexión:**
   - Intenta abrir una página web
   - Reinicia el router si es necesario

4. **Espera 30 minutos:**
   - Gmail tiene límite de 3 conexiones IMAP simultáneas
   - Si alcanzas el límite, espera antes de reintentar

---

### "No me llegan las notificaciones"

**Síntoma:** El programa detecta correos pero no hay popup

**Posibles causas:**
1. Notificaciones deshabilitadas en Windows
2. Plyer no está instalado correctamente
3. Conflicto con otro software

**Soluciones:**

1. **Habilita notificaciones en Windows:**
   - Configuración → Sistema → Notificaciones
   - Verifica que esté habilitado

2. **Reinstala Plyer:**
   ```bash
   pip uninstall plyer
   pip install plyer
   ```

3. **Usa sonido de alerta:**
   - El programa emite un "beep" si no puede enviar notificación
   - Verifica que tu volumen esté subido

4. **Prueba la notificación:**
   - Presiona botón "🔔 Probar notif."
   - Deberías ver un popup

---

### "Se congela o responde lentamente"

**Síntoma:** La interfaz no responde a clics

**Posibles causas:**
1. Preview de correos muy grandes
2. Mucho historial acumulado
3. Problemas de red

**Soluciones:**

1. **Limpia el historial:**
   - Encuentra el archivo `gmail_watcher_config.json`
   - Ábrelo con bloc de notas
   - Reemplaza `"history": [...]` por `"history": []`
   - Guarda

2. **Aumenta el intervalo:**
   - Prueba con intervalo más alto (60+ segundos)

3. **Reinicia el programa:**
   - Cierra y abre nuevamente

---

## Preguntas Frecuentes

### ¿Qué es una App Password?

Una App Password es una contraseña especial de 16 caracteres que creas en tu cuenta de Google. Es diferente de tu contraseña normal y permite que aplicaciones accedan a tu Gmail de forma segura sin guardar tu contraseña real.

### ¿Es seguro guardar mi contraseña en el programa?

**Sí**, es seguro por varias razones:

1. Es una App Password especial, no tu contraseña real
2. Se guarda en tu computadora (no en servidores externos)
3. Solo funciona para acceso IMAP
4. Puedes revocarla en Google en cualquier momento

### ¿Puedo vigilar múltiples remitentes?

**Sí**, simplemente sepáralos con comas:

```
noreply@fing.edu.uy, admin@trabajo.com, soporte@tienda.com
```

### ¿Puedo usar cualquier cuenta de Gmail?

Sí, pero:
- Debe ser una cuenta Gmail real (no correo forwarded)
- Debe tener 2FA habilitado

### ¿Qué pasa si minimizo la ventana?

El programa sigue funcionando en segundo plano. Las notificaciones aparecerán igual.

### ¿Puedo tenerlo corriendo todo el tiempo?

**Sí**, el programa está diseñado para:
- Funcionar 24/7
- Recuperarse automáticamente de errores
- Nunca fallar

Simplemente:
1. Inicia el monitoreo
2. Minimiza la ventana (opcional)
3. El programa seguirá vigilando

### ¿Qué es el "UID base"?

El UID es el identificador único de cada correo en Gmail. El programa lo usa para saber hasta qué correo ya revisó, evitando enviar alertas dos veces del mismo correo.

### ¿Puedo cambiar las credenciales sin perder el historial?

**Sí**, el historial se guarda en `gmail_watcher_config.json`. Puedes cambiar credenciales y se conservará.

### ¿Cómo hago que se inicie automáticamente en Windows?

1. Crea un archivo `iniciar.bat`:
   ```batch
   @echo off
   cd /d "C:\ruta\a\programa"
   python gmail_watcher_gui.py
   pause
   ```

2. Presiona `Win + R` y escribe `shell:startup`

3. Copia `iniciar.bat` en esa carpeta

4. Reinicia - Se abrirá automáticamente

---

## Información Técnica

### Archivos del Programa

| Archivo | Función |
|---------|---------|
| `gmail_watcher_gui.py` | Programa principal (interfaz gráfica) |
| `app.py` | Versión de terminal (alternativa) |
| `gmail_watcher_config.json` | Archivo de configuración guardada |
| `requirements.txt` | Dependencias necesarias |
| `README.md` | Readme técnico |
| `MANUAL.md` | Este archivo |

### Configuración de Email en Gmail

El programa usa IMAP (protocolo de correo) para conectar con Gmail:

- **Host:** imap.gmail.com
- **Puerto:** 993 (SSL)
- **Protocolo:** IMAP4_SSL

### Intervalo de Revisión

```
Intervalo (segundos) → Frecuencia
5-10                 → Cada 5-10 segundos (máximo)
15                   → Cada 15 segundos (recomendado)
30                   → Cada 30 segundos (normal)
60                   → Cada minuto (bajo consumo)
```

### Manejo de Errores

El programa está diseñado con manejo de errores:

✅ Reconexión automática si falla IMAP
✅ Reintentos intelligentes
✅ Logging detallado
✅ Recuperación de fallos
✅ No pierde datos al reiniciar

### Historial Máximo

- Se guardan hasta **75 últimos correos**
- Los más antiguos se eliminan automáticamente
- Esto evita que el archivo de configuración sea muy grande

---

## Soporte y Contacto

Si tienes problemas:

1. **Revisa el log** de actividad en la pestaña "Alertas"
2. **Prueba una notificación** con el botón "🔔 Probar"
3. **Verifica las credenciales** en Google Account
4. **Reinicia el programa** completamente

### Información para Reportar Errores

Si algo no funciona, anota:
- Qué estás intentando hacer
- Qué error aparece (exactamente)
- Qué aparece en el log
- Tu versión de Python

---

## Versiones y Actualizaciones

### Versión 2.1 (Actual)
- ✅ Completamente robusto - nunca falla
- ✅ Manejo de errores integrado
- ✅ Interfaz mejorada
- ✅ Historial confiable

### Versión 2.0
- Extracción correcta de emails
- Mejor interfaz GUI

### Versión 1.0
- Versión inicial

---

**¡Disfruta Gmail Watcher Pro! 🎉**

*Última actualización: Junio 2026*
