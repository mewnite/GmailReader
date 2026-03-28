# Gmail Watcher

Una app de escritorio en Python para vigilar Gmail desde una interfaz local y avisar cuando llega un correo de remitentes específicos. La app guarda un historial de correos detectados, muestra una preview dentro de la misma ventana y evita disparar alertas por correos viejos en el primer arranque.

## Qué hace

* Se conecta a Gmail por IMAP.
* Vigila uno o varios remitentes específicos.
* Muestra notificaciones de escritorio cuando llega un correo nuevo coincidente.
* Guarda un cursor para no volver a procesar correos viejos.
* Muestra una segunda capa de lectura con historial y preview del correo.
* Permite iniciar y detener el monitoreo desde la interfaz.

## Requisitos

* Python 3.10 o superior.
* Una cuenta de Gmail.
* IMAP habilitado en Gmail.
* 2-Step Verification activada en tu cuenta de Google.
* Una app password generada para esta aplicación.

## Instalación

1. Instalá las dependencias:

```bash
pip install plyer
```

2. Ejecutá la app:

```bash
python gmail_watcher_gui.py
```

## Configuración de Gmail

### 1) Activar IMAP

En Gmail desde la web:

1. Abrí Gmail en el navegador.
2. Entrá a **Settings**.
3. Elegí **See all settings**.
4. Abrí la pestaña **Forwarding and POP/IMAP**.
5. En la sección **IMAP access**, activá IMAP.
6. Guardá los cambios.

## Cómo obtener la contraseña de app

Google exige 2-Step Verification para crear app passwords. También puede pasar que no te aparezca la opción si tu cuenta es de trabajo/escuela, si usás solo llaves de seguridad o si tenés Advanced Protection.

### Paso a paso

1. Abrí tu **Google Account**.
2. Entrá a **Security**.
3. Activá **2-Step Verification** si todavía no la tenés.
4. Volvé a **Security** y buscá **App passwords**.
5. Generá una nueva contraseña de app.
6. Copiala y guardala: se muestra una sola vez.

### Importante

* No uses tu contraseña normal de Google en la app.
* Cada vez que cambies la contraseña de Google, las app passwords se revocan y tenés que crear una nueva.
* Si una app tiene opción de **Sign in with Google**, Google recomienda usar esa opción en lugar de una app password.

## Cómo usar la app

1. Abrí la ventana de Gmail Watcher.
2. Cargá tu correo de Gmail.
3. Cargá la app password.
4. Escribí uno o varios remitentes a vigilar, separados por coma.
5. Elegí el intervalo de revisión.
6. Hacé clic en **Iniciar**.

## Cómo funciona el primer arranque

La primera vez la app toma como referencia el estado actual del inbox para no avisarte por correos viejos que ya estaban ahí.

Eso significa que:

* No va a saltar por mails antiguos pendientes de leer.
* Solo alerta sobre correos nuevos que lleguen después de iniciar la vigilancia.

## Vista de lectura

La app tiene dos capas:

* **Alertas**: estado general, notificaciones, logs y cursor.
* **Lectura**: historial de correos detectados y preview dentro de la app.

En la pestaña de lectura podés:

* ver los correos que dispararon alerta,
* seleccionar uno,
* leer una preview corta del contenido,
* refrescar la preview si hace falta.

## Inicio automático con la PC

Podés hacer que la app arranque sola al iniciar sesión en Windows.

### Opción simple

1. Apretá `Win + R`.
2. Escribí:

```bash
shell:startup
```

3. Poné ahí un acceso directo al `.exe` o un `.bat` que ejecute el script.

### Opción recomendada

Convertí la app a `.exe` y dejala en la carpeta de inicio.

## Conversión a .exe

```bash
pip install pyinstaller
py -3.13 -m PyInstaller --onefile --noconsole gmail_watcher_gui.py
```

El ejecutable queda dentro de la carpeta `dist`.

## Seguridad

* Guardá la app password con cuidado.
* No la compartas.
* Si dejás de usar la app, revocá la app password desde tu cuenta de Google.

## Solución de problemas

### No aparecen notificaciones

* Verificá que `plyer` esté instalado.
* Probá el botón **Probar notificación**.
* Revisá la configuración de notificaciones de Windows.

### La app no conecta con Gmail

* Confirmá que IMAP esté activado.
* Confirmá que la contraseña sea una app password.
* Confirmá que 2-Step Verification esté activada.

### No veo la opción de app passwords

Puede pasar si:

* no activaste 2-Step Verification,
* tu cuenta es de trabajo, escuela u organización,
* tu cuenta usa Advanced Protection,
* tu cuenta está configurada solo con llaves de seguridad.

## Archivos principales

* `gmail_watcher_gui.py`: aplicación principal.

## Nota final

La app está pensada para vigilar correos nuevos sin volver a disparar mails viejos y para darte una vista cómoda dentro de la misma interfaz.
