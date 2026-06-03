# ⚡ GUÍA RÁPIDA DE INICIO (5 MINUTOS)

## Paso 1: Instalar 📥

```bash
pip install plyer
```

## Paso 2: Crear App Password en Google 🔑

**⏱️ 2 minutos**

1. Abre: https://myaccount.google.com/apppasswords
2. Selecciona: **Correo** → **Windows**
3. Google te dará una contraseña de 16 caracteres (ej: `pqdt kgfp kcne zfrk`)
4. **Cópiala SIN ESPACIOS**: `pqdtkgfpkcnezfrk`

> ⚠️ Si no ves "App passwords", primero habilita Verificación en 2 pasos en https://myaccount.google.com/security

## Paso 3: Configurar el Programa 🖥️

**⏱️ 1 minuto**

Abre el programa:
```bash
python gmail_watcher_gui.py
```

Llena estos campos:
```
📧 Correo Gmail:      tu@gmail.com
🔑 App password:      pqdtkgfpkcnezfrk (SIN ESPACIOS)
👁️ Vigilar:           noreply@fing.edu.uy
⏱️ Intervalo:         30 (segundos)
```

## Paso 4: ¡Listo! ▶️

Presiona **▶️ Iniciar** y listo.

Ver la magia suceder en la pestaña **📋 Alertas**

---

## Cheat Sheet Rápido

### Comandos Rápidos

```bash
# Instalar dependencias
pip install plyer

# Ejecutar programa
python gmail_watcher_gui.py

# Versión terminal (sin interfaz gráfica)
python app.py
```

### Configurar Múltiples Remitentes

En el campo "Vigilar remitentes", separa con comas:

```
noreply@fing.edu.uy, admin@trabajo.com, ventas@tienda.com
```

O solo por dominio:

```
fing.edu.uy, trabajo.com
```

### Iniciar Automáticamente en Windows

1. Crea archivo `iniciar.bat`:
```batch
@echo off
cd /d "C:\ruta\a\la\carpeta"
python gmail_watcher_gui.py
```

2. `Win + R` → escribe `shell:startup`

3. Copia `iniciar.bat` en esa carpeta

4. ¡Listo! Se inicia solo al encender Windows

---

## ¿Algo no funciona?

### ❌ "Authentication failed"
→ Verifica que copiaste App Password **SIN ESPACIOS**

### ❌ "No detecta correos"
→ Usa solo el dominio: `fing.edu.uy` en lugar de email completo

### ❌ "No hay notificaciones"
→ Presiona botón "🔔 Probar" para testear

### ❌ "Se desconecta constantemente"
→ Sube el intervalo a 60 segundos

---

## Indicadores

| Símbolo | Significado |
|---------|-------------|
| 🟢 | Vigilando - Todo OK |
| 🟡 | Conectando - Espera |
| 🔴 | Detenida - No está activo |
| ✓ | Éxito |
| ⚠️ | Advertencia |
| ❌ | Error |

---

## Archivos Importantes

- **gmail_watcher_gui.py** ← Programa principal (ábrelo con `python`)
- **gmail_watcher_config.json** ← Guarda tu configuración (se crea automático)

---

## ¿Preguntas?

1. Lee **MANUAL.md** (manual completo)
2. Revisa el **Registro** en pestaña Alertas
3. Prueba el botón **"🔔 Probar"**

---

**¡Ya está! Disfrutalo 🚀**
