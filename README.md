# [L]inx C2 


![status](https://img.shields.io/badge/status-active-brightgreen)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![license](https://img.shields.io/badge/license-MIT-green)

---

## Sobre este proyecto

Llevo **3 años** con este proyecto. Con altibajos, frustraciones y mucha procrastinación, ahora que se como funciona el malware básico y no me considero un skid, lo subo para que los skids hagan cosas de skids.

No es un producto realmente, es un cuaderno de aprendizaje con esteroides. Hay cosas que no van y ya no lo voy a corregir ni a hacer otra versión.

El código ha sido depurado y reescrito por IA, porque había mucho spagetti y funciones repetidas.

---

## ¿Qué es esto?

Un bot de Discord que actúa como **servidor de comando y control** (C2) para máquinas Windows. Se conecta, se identifica, crea su propio canal categorizado por región y queda a la espera de comandos.

No es una herramienta profesional, deja mucha trazabilidad y realmente no sirve para mucho mas que para larpear así que **No lo ejecutes en máquinas que no sean tuyas.**

---

## Características

- Reverse shell persistente por canal de Discord
- Extracción de credenciales de Chrome, Edge, Brave, Opera, Vivaldi y Firefox
- Historial de navegación multi-perfil y multi-usuario
- Tokens de Discord de clientes instalados y navegadores
- WiFi guardadas (SSID + contraseña)
- Keylogger por polling de GetAsyncKeyState (sin dependencias)
- Captura de pantalla simple y multi-monitor
- Webcam vía OpenCV
- Portapapeles en vivo
- Persistencia múltiple: HKCU Run, HKLM Run, Startup VBS, Scheduled Task, Service
- Anti-sandbox / anti-debug básico (Peb->BeingDebugged, MAC de VM, RAM, disco)
- Ejecución de código Python remota
- Tareas en background con IDs y polling de salida
- Deshabilitar Defender (requiere admin)
- UAC bypass vía fodhelper (legacy, W10)
- Fake BSOD multi-monitor con QR
- BSOD real vía NtRaiseHardError
- Download / Upload de archivos entre host y Discord
- Heartbeat con reconexión automática

---

## Estructura del proyecto

```
linx-c2/
  src/
    linx.py              # bot principal, todo en uno
  .env.example           # plantilla de variables
  SECURITY.md            # política de seguridad y disclaimer
  LICENSE                # MIT
  README.md
```

---

## Comandos

Referencia completa en docs/COMMANDS.md. Resumen:

| Categoría | Comandos |
|-----------|----------|
| Shell | !shell, !exitshell, !exec, !bg, !bgoutput, !bglist |
| Info | !sysinfo, !ip, !geo, !status, !uptime, !tasklist, !netstat |
| Captura | !screenshot, !screenshotall, !webcam, !paperclip, !keylog, !keylogstart, !keylogstop |
| Datos | !passwords, !history, !token, !wifi |
| Archivos | !ls, !cd, !pwd, !rm, !mkdir, !download, !sendfile, !getfile |
| Privilegios | !admincheck, !uacbypass, !elevate, !disableantivirus |
| Persistencia | !persistence, !unpersistence, !persistcheck |
| Diversion | !fakebluescreen, !bluescreen, !windowspassword |
| Control | !py, !shutdown, !exit |

---

## Instalación

lo clonas/descargas, metes las variables y lo ejecutas, si tienes dudas igual este proyecto no es para tí.

---

## Dependencias

Obligatorias:

```
discord.py>=2.3.0
```

Opcionales (cada una activa una capacidad):

| Paquete | Habilita |
|---------|----------|
| pycryptodome | descifrado de credenciales Chromium/Firefox |
| pywin32 | DPAPI (master key v10) |
| psutil | sysinfo detallado, detección de sandbox |
| pyautogui | screenshots |
| Pillow | screenshots fallback + QR en BSOD |
| pyperclip | portapapeles |
| requests | descargas, geolocalización |
| aiohttp | categorización por región async |
| opencv-python | webcam |
| qrcode | QR en fake BSOD |
| screeninfo | multi-monitor BSOD |

El bot degrada con gracia si falta cualquiera de las opcionales.

---

## Estado del proyecto

- Estable: shell, persistencia, extracción, captura
- En revisión: bypass UAC (deprecado en W11, se queda como referencia histórica)
- Roto / pendiente: App-Bound encryption de Chrome 127+ (v20/v21 de Local State)

---



## Descargo de responsabilidad

**Este software se distribuye exclusivamente con fines educativos, de investigación en seguridad ofensiva y de aprendizaje personal.**

El autor **no se hace responsable** del uso que terceros hagan de este código. Ejecutarlo sobre sistemas que no son de tu propiedad, o sobre los que no tienes autorización explícita por escrito, es **ilegal** en prácticamente toda jurisdicción. Las consecuencias legales, penales o civiles derivadas del uso indebido recaen **única y exclusivamente sobre quien lo ejecuta**.

Este repositorio no incluye, promueve ni facilita actividad delictiva. Es un cuaderno de aprendizaje publicado para que otros puedan estudiar cómo se construyen herramientas ofensivas, cómo funcionan por dentro los mecanismos de persistencia de Windows, cómo se extraen credenciales de navegadores usando DPAPI, y cómo se diseña un C2 sobre un canal no convencional (Discord).

Si no entiendes las implicaciones éticas y legales de ejecutar esto, **no lo ejecutes**.

---

## Licencia

MIT. Haz lo que quieras con el código, pero no me vengas a buscar si te metes en un lío.

---

Escrito con café, muchas IA de dudosa procedencia, errores de sintaxis y muchas ganas de entender cómo funcionan las cosas por dentro.
