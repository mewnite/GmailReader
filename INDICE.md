# 📑 ÍNDICE DE ARCHIVOS - Gmail Watcher Pro v2.1

## 📋 Contenido de la Carpeta

```
gmail_watcher_pro/
│
├── 🚀 ARCHIVOS EJECUTABLES
│   ├── gmail_watcher_gui.py          ← PRINCIPAL: Interfaz gráfica
│   └── app.py                        ← ALTERNATIVA: Versión terminal
│
├── 📚 DOCUMENTACIÓN PRINCIPAL
│   ├── README.md                     ← Lee primero (este archivo)
│   ├── INICIO_RAPIDO.md              ← ⏱️ 5 minutos para empezar
│   ├── MANUAL.md                     ← 📖 Manual completo
│   ├── GUIA_INICIO.html              ← 🌐 Versión web visual
│   └── INDICE.md                     ← Este archivo
│
├── 🔧 DOCUMENTACIÓN TÉCNICA
│   ├── ACTUALIZACIONES.md            ← Qué cambió en v2.1
│   ├── CAMBIOS.md                    ← Detalle de fixes
│   └── requirements.txt              ← Dependencias
│
├── 💾 CONFIGURACIÓN (se crea automático)
│   └── gmail_watcher_config.json     ← Tu configuración guardada
│
└── 📁 CARPETAS AUXILIARES
    ├── build/                        ← Compilación (ignorar)
    └── dist/                         ← Distribución (ignorar)
```

---

## 🎯 ¿POR DÓNDE EMPIEZO?

### 1️⃣ Primer Uso - Usuario Nuevo
**Recomendación: 10 minutos**

1. Lee: `README.md` (2 min)
2. Lee: `INICIO_RAPIDO.md` (3 min)
3. Abre: `GUIA_INICIO.html` en navegador (2 min)
4. Ejecuta: `python gmail_watcher_gui.py` (3 min)

✅ **Resultado:** Programa funcionando

---

### 2️⃣ Necesitas Ayuda
**Recomendación: Manual Completo**

1. Busca tu problema en: `MANUAL.md` → "Solución de Problemas"
2. Revisa: "Preguntas Frecuentes"
3. Intenta: Soluciones sugeridas
4. Si persiste: Anota error y revisa el log

---

### 3️⃣ Eres Usuario de v1.0
**Recomendación: Changelog**

1. Lee: `ACTUALIZACIONES.md` (Qué cambió)
2. Revisa: `CAMBIOS.md` (Detalles técnicos)
3. Migra: Solo reemplaza `gmail_watcher_gui.py`
4. Configuración: Se carga automáticamente

---

### 4️⃣ Quieres Entender Todo
**Recomendación: Orden Completo**

```
1. README.md (general)
   ↓
2. INICIO_RAPIDO.md (práctica)
   ↓
3. GUIA_INICIO.html (visual)
   ↓
4. MANUAL.md (referencia completa)
   ↓
5. ACTUALIZACIONES.md (cambios)
   ↓
6. CAMBIOS.md (técnica profunda)
```

---

## 📖 DESCRIPCIÓN DETALLADA DE ARCHIVOS

### Archivos Ejecutables

#### `gmail_watcher_gui.py` ⭐ PRINCIPAL
- **Descripción:** Programa con interfaz gráfica
- **Cómo usar:** `python gmail_watcher_gui.py`
- **Para:** La mayoría de usuarios
- **Características:**
  - Interfaz bonita
  - Fácil de usar
  - Historial visual
  - Notificaciones automáticas

#### `app.py` 
- **Descripción:** Versión de terminal (sin GUI)
- **Cómo usar:** `python app.py`
- **Para:** Servidores / daemon / terminal
- **Características:**
  - Muy ligero
  - Perfecto para correr en background
  - Logging en terminal

---

### Documentación General

#### `README.md` ⭐ LEE PRIMERO
- **Contenido:**
  - Resumen ejecutivo
  - Inicio rápido (2 min)
  - Características principales
  - Solución rápida de problemas
  - Links a documentación completa
- **Tiempo:** 5 minutos
- **Para:** Todos

#### `INICIO_RAPIDO.md` 
- **Contenido:**
  - Pasos en 5 minutos
  - Cheat sheet de comandos
  - Configuración múltiples remitentes
  - Autoarranque en Windows
  - Troubleshooting rápido
- **Tiempo:** 5 minutos
- **Para:** Usuarios con prisa

#### `MANUAL.md` 📖 REFERENCIA COMPLETA
- **Contenido:**
  - Introducción completa
  - Instalación paso a paso
  - Configuración detallada
  - Uso de cada función
  - 10+ soluciones de problemas
  - 15+ FAQ
  - Información técnica
  - Versiones
- **Tiempo:** 30 minutos (lectura completa)
- **Para:** Referencia y problemas complejos

#### `GUIA_INICIO.html` 🌐 VERSIÓN WEB
- **Contenido:** Versión visual bonita de INICIO_RAPIDO
- **Cómo usar:** Abre en navegador
- **Para:** Usuarios que prefieren visual
- **Ventajas:** Bonito, fácil de leer, emojis

---

### Documentación Técnica

#### `ACTUALIZACIONES.md` 🔄 CHANGELOG
- **Contenido:**
  - Qué cambió en v2.1
  - Bugs arreglados
  - Mejoras implementadas
  - Comparación antes/después
  - Tabla de compatibilidad
  - Historial completo v1.0 → v2.1
- **Tiempo:** 10 minutos
- **Para:** Usuarios de v1.0, interesados en cambios

#### `CAMBIOS.md` 🔧 DETALLES TÉCNICOS
- **Contenido:**
  - Bugs específicos solucionados
  - Cambios en lógica de programa
  - Mejoras de interfaz
  - Cambios técnicos internos
  - Información de dependencias
- **Tiempo:** 15 minutos
- **Para:** Desarrolladores, usuarios técnicos

#### `requirements.txt`
- **Contenido:** Lista de librerías necesarias
- **Cómo usar:** `pip install -r requirements.txt`
- **Contiene:** 
  - plyer >= 2.1.0 (notificaciones)
- **Tamaño:** Muy pequeño

---

### Archivos de Configuración

#### `gmail_watcher_config.json`
- **Descripción:** Archivo de configuración guardada
- **Creado automáticamente:** Al cerrar el programa
- **Contiene:**
  - Email de Gmail
  - App Password
  - Remitentes vigilados
  - Intervalo
  - Historial (últimos 75 correos)
  - Cursor (UID)
  - Contador de alertas
- **Ubicación:** Misma carpeta del programa
- **Tamaño:** ~5KB típicamente

---

## 🗂️ CÓMO ORGANIZAR TU CARPETA

### Opción 1: Simple
```
mi_proyecto/
├── gmail_watcher_gui.py
└── requirements.txt
```
Suficiente para usar el programa.

### Opción 2: Completo (Recomendado)
```
mi_proyecto/
├── gmail_watcher_gui.py
├── app.py
├── requirements.txt
├── README.md
├── INICIO_RAPIDO.md
├── MANUAL.md
├── GUIA_INICIO.html
└── docs/
    ├── ACTUALIZACIONES.md
    ├── CAMBIOS.md
    └── INDICE.md
```
Mejor organización y fácil de mantener.

---

## 📊 TABLA RÁPIDA

| Archivo | Tipo | Propósito | Lectura | Frecuencia |
|---------|------|----------|---------|-----------|
| gmail_watcher_gui.py | Código | Programa principal | - | Siempre |
| app.py | Código | Alternativa CLI | - | Opcional |
| README.md | Doc | Primer contacto | 5 min | Una vez |
| INICIO_RAPIDO.md | Doc | Primeros pasos | 5 min | Una vez |
| MANUAL.md | Doc | Referencia | 30 min | Consulta |
| GUIA_INICIO.html | Doc | Visual | 5 min | Una vez |
| ACTUALIZACIONES.md | Doc | Cambios | 10 min | Si updatea |
| CAMBIOS.md | Doc | Técnica | 15 min | Si interesa |
| requirements.txt | Config | Dependencias | 1 min | Una vez |
| gmail_watcher_config.json | Config | Tu config | - | Automático |

---

## 🚀 ACCIONES RÁPIDAS

### Para empezar ahora
```bash
pip install plyer
python gmail_watcher_gui.py
```

### Para leer documentación
1. `README.md` - Visión general
2. `INICIO_RAPIDO.md` - Guía rápida
3. `MANUAL.md` - Referencia completa

### Para resolver problemas
→ Busca en `MANUAL.md` → sección "Solución de Problemas"

### Para entender cambios
→ Lee `ACTUALIZACIONES.md` (cambios principales)
→ Lee `CAMBIOS.md` (detalles técnicos)

---

## 🎯 PRÓXIMAS ACCIONES

### Ahora (5 minutos)
- [ ] Lee `README.md`
- [ ] Lee `INICIO_RAPIDO.md`
- [ ] Instala dependencias: `pip install plyer`

### Hoy (10 minutos)
- [ ] Obtén App Password de Google
- [ ] Ejecuta: `python gmail_watcher_gui.py`
- [ ] Completa configuración
- [ ] Presiona "▶️ Iniciar"

### Si algo no funciona
- [ ] Revisa `MANUAL.md`
- [ ] Mira el Registro (pestaña Alertas)
- [ ] Prueba botón "🔔 Probar"

---

## 📝 NOTAS IMPORTANTES

### Estructura de Carpetas
- El programa crea `gmail_watcher_config.json` automáticamente
- NO elimines archivos .md (son documentación)
- `build/` y `dist/` se pueden ignorar/eliminar

### Actualizaciones
- Solo necesitas reemplazar `gmail_watcher_gui.py`
- Tu configuración se carga automáticamente
- El historial se conserva

### Respaldo
- Haz backup de `gmail_watcher_config.json` si la config es importante
- Tu App Password está guardado en ese archivo (seguro, pero personal)

---

## 🆘 AYUDA RÁPIDA

| Pregunta | Respuesta |
|----------|-----------|
| ¿Por dónde empiezo? | Lee `README.md` |
| ¿Cómo instalo? | Lee `INICIO_RAPIDO.md` |
| ¿Algo no funciona? | Busca en `MANUAL.md` |
| ¿Qué cambió? | Lee `ACTUALIZACIONES.md` |
| ¿Es técnica mi duda? | Mira `CAMBIOS.md` |
| ¿Necesito ayuda visual? | Abre `GUIA_INICIO.html` |

---

## 📞 CONTACTO/SOPORTE

**Si tienes dudas:**
1. Busca en documentación
2. Revisa Registro de actividad
3. Prueba notificación
4. Verifica credenciales

**Documentación disponible:**
- ✅ 6 archivos .md
- ✅ 1 archivo .html
- ✅ FAQs integradas
- ✅ Troubleshooting

---

**¡Todo lo que necesitas está aquí! 🎉**

*Índice completo de Gmail Watcher Pro v2.1*
*Actualizado: Junio 2026*
