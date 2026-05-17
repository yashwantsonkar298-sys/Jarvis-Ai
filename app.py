import cv2
import mediapipe as mp
import pyautogui
import math
import time
import numpy as np
import threading
import queue
import json
import ctypes
import html
import importlib
import os
import shutil
import subprocess
import sys
import webbrowser
from urllib.parse import parse_qs, quote_plus, urlparse
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_face_recognition_spec = importlib.util.find_spec("face_recognition")
face_recognition = importlib.import_module("face_recognition") if _face_recognition_spec else None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import sounddevice as sd
except ImportError:
    sd = None

try:
    import pythoncom
    import win32com.client as win32_client
except ImportError:
    pythoncom = None
    win32_client = None

# =======================================================
# AI MULTI-MODE OS CONTROLLER - JARVIS PROTOCOL v3.0
# =======================================================

PROJECT_COPYRIGHT_NOTICE = (
    "Copyright (C) 2026 Yashwant Sonkar and Project Team. "
    "Unauthorized copying, redistribution, or rebranding is prohibited."
)
PROJECT_OWNER_NOTICE = "COPYRIGHT (C) 2026 Yashwant Sonkar | Do not copy or rebrand"

cv2.setUseOptimized(True)

MODE_VOICE_ONCE = True
MODE_VOICE_NAMES = {"MEDIA MODE", "NAVIGATION MODE", "TOUCH MODE"}
MODE_VOICE_MESSAGES_SPOKEN = set()
SPEECH_LOCK = threading.Lock()
SPEECH_QUEUE = queue.Queue(maxsize=8)
SPEECH_THREAD = None


def set_voice_feedback_status(status):
    if "update_telemetry" not in globals():
        return
    try:
        update_telemetry(voice_feedback=status)
    except Exception:
        pass


def speak_with_sapi(text):
    if win32_client is None:
        raise RuntimeError("win32com is unavailable")

    initialized = False
    if pythoncom is not None:
        pythoncom.CoInitialize()
        initialized = True

    voice = None
    try:
        voice = win32_client.Dispatch("SAPI.SpVoice")
        voice.Rate = 0
        voice.Volume = 100
        voice.Speak(str(text))
    finally:
        voice = None
        if initialized:
            pythoncom.CoUninitialize()


def speak_with_pyttsx3(text):
    if pyttsx3 is None:
        raise RuntimeError("pyttsx3 is unavailable")

    engine = pyttsx3.init()
    engine.setProperty("rate", 160)
    engine.say(str(text))
    engine.runAndWait()
    engine.stop()


def speak_with_powershell(text):
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate = 0; $s.Volume = 100; "
        "$text = [Console]::In.ReadToEnd(); "
        "if ($text) { $s.Speak($text) }; "
        "$s.Dispose()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        input=str(text),
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=25,
        check=True,
    )


def speech_worker():
    while True:
        text = SPEECH_QUEUE.get()
        if not text:
            continue

        last_error = None
        for backend_name, backend in (
            ("Windows SAPI", speak_with_sapi),
            ("pyttsx3", speak_with_pyttsx3),
            ("PowerShell Speech", speak_with_powershell),
        ):
            try:
                set_voice_feedback_status(f"Speaking: {backend_name}")
                backend(text)
                set_voice_feedback_status(f"Ready: {backend_name}")
                break
            except Exception as exc:
                last_error = exc
        else:
            set_voice_feedback_status("Voice feedback unavailable")
            print(f"Voice skipped: {text} ({last_error})")


def ensure_speech_worker():
    global SPEECH_THREAD
    with SPEECH_LOCK:
        if SPEECH_THREAD is None or not SPEECH_THREAD.is_alive():
            SPEECH_THREAD = threading.Thread(target=speech_worker, daemon=True)
            SPEECH_THREAD.start()


def speak(text):
    if not text:
        return

    text_value = str(text)
    normalized_mode = text_value.upper().replace(" ACTIVATED", "").strip()
    if (
        MODE_VOICE_ONCE
        and text_value.upper().endswith(" ACTIVATED")
        and normalized_mode in MODE_VOICE_NAMES
    ):
        if normalized_mode in MODE_VOICE_MESSAGES_SPOKEN:
            return
        MODE_VOICE_MESSAGES_SPOKEN.add(normalized_mode)

    ensure_speech_worker()
    try:
        SPEECH_QUEUE.put_nowait(text_value)
    except queue.Full:
        try:
            SPEECH_QUEUE.get_nowait()
        except queue.Empty:
            pass
        try:
            SPEECH_QUEUE.put_nowait(text_value)
        except queue.Full:
            print(f"Voice skipped: {text}")


APP_STARTED_AT = time.time()
DASHBOARD_PORT = 8765
PINCH_THRESHOLD = 40
PINCH_THRESHOLD_MIN = 28
PINCH_THRESHOLD_MAX = 76
PINCH_THRESHOLD_SCALE = 0.42
FACE_SCAN_INTERVAL = 0.65
FACE_MATCH_TOLERANCE = 0.48
OPENCV_FACE_CONFIDENCE_LIMIT = 78
EYE_MIN_COUNT = 1
FACE_DETECTION_MIN_SIZE = (80, 80)
FACE_RECOGNITION_DOWNSCALE = 0.35
CAMERA_TARGET_WIDTH = 640
CAMERA_TARGET_HEIGHT = 480
CAMERA_TARGET_FPS = 30
VOICE_LANGUAGE = "en-IN"
VOICE_RECOGNITION_LANGUAGES = ("en-IN", "hi-IN", "en-US")
VOICE_PHRASE_SECONDS = 6
VOICE_LISTEN_TIMEOUT = 5
VOICE_SAMPLE_RATE = 16000
VOICE_AUDIO_BLOCK_SECONDS = 0.12
VOICE_START_RMS = 220
VOICE_MIN_RECORD_SECONDS = 0.35
VOICE_END_SILENCE_SECONDS = 1.0
VOICE_DEVICE_SAMPLE_RATE_FALLBACKS = (16000, 44100, 48000)
VOICE_NOISE_MIC_KEYWORDS = ("krisp", "nvidia broadcast", "broadcast", "sonar", "steelseries", "clearcast")
VOICE_HINDI_REPLACEMENTS = {
    "खोलो": " open ",
    "खोल": " open ",
    "ओपन": " open ",
    "चालू": " start ",
    "चलाओ": " play ",
    "चलाना": " play ",
    "करो": " karo ",
    "कर": " karo ",
    "मोड": " mode ",
    "टच": " touch ",
    "गेम": " game ",
    "मीडिया": " media ",
    "नेविगेशन": " navigation ",
    "नैविगेशन": " navigation ",
    "यूट्यूब": " youtube ",
    "यू ट्यूब": " youtube ",
    "गूगल": " google ",
    "जीमेल": " gmail ",
    "क्रोम": " chrome ",
    "व्हाट्सएप": " whatsapp ",
    "नोटपैड": " notepad ",
    "कैलकुलेटर": " calculator ",
}
MODE_COMMAND_ALIASES = {
    "media": 0,
    "media mode": 0,
    "media mod": 0,
    "navigation": 1,
    "nav": 1,
    "navigate": 1,
    "nevigation": 1,
    "navigational": 1,
    "navigation mode": 1,
    "nav mode": 1,
    "navigation mod": 1,
    "touch": 2,
    "tuch": 2,
    "tach": 2,
    "toch": 2,
    "torch": 2,
    "kachua": 2,
    "kachhua": 2,
    "kachuha": 2,
    "kachuaa": 2,
    "touch mode": 2,
    "touch mod": 2,
    "tuch mode": 2,
    "tach mode": 2,
    "kachua mode": 2,
    "kachhua mode": 2,
}
AIR_CLICK_COOLDOWN = 0.35
TOUCH_HOVER_SECONDS = 0.75
TOUCH_STABILITY_RADIUS = 26
TOUCH_SCROLL_AMOUNT = 650
TOUCH_SWIPE_TRIGGER_DISTANCE = 68
TOUCH_PINCH_HOLD_SECONDS = 0.08
TOUCH_PINCH_GRACE_SECONDS = 0.09
TOUCH_PINCH_MAX_DISTANCE = 34
TOUCH_POINTER_SMOOTHING = 0.52
TOUCH_INDEX_DOMINANCE_MARGIN = 10
CURSOR_MOVE_DEADZONE = 0.85
NAV_INDEX_TRIGGER_DISTANCE = 55
MODE_SWITCH_COOLDOWN = 1.5
MODE_NOTICE_SECONDS = 2.2
GESTURE_MODE_SWITCH_ENABLED = False
SINGLE_FINGER_STABLE_SECONDS = 0.18
GESTURE_SAFE_HAND_SCALE_MAX = 220
PINCH_EXCLUSIVE_MARGIN = 14
MEDIA_VOLUME_REPEAT_SECONDS = 0.18
ACTION_COOLDOWNS = {
    "air_click": AIR_CLICK_COOLDOWN,
    "touch_tap": 0.55,
    "volumeup": MEDIA_VOLUME_REPEAT_SECONDS,
    "volumedown": MEDIA_VOLUME_REPEAT_SECONDS,
    "touch_playpause": 0.45,
    "touch_close_tab": 0.8,
    "slideleft": 0.32,
    "slideright": 0.32,
    "scrollup": 0.10,
    "scrolldown": 0.10,
}
TELEMETRY_LOCK = threading.Lock()
TELEMETRY = {
    "app": "JARVIS AI Vision Controller",
    "copyright": PROJECT_COPYRIGHT_NOTICE,
    "status": "BOOTING",
    "mode": "SYSTEM LOCKED",
    "locked": True,
    "fps": 0,
    "last_action": "System starting...",
    "hand_detected": False,
    "dashboard": "starting",
    "uptime_seconds": 0,
    "current_gesture": "None",
    "air_click": "Ready",
    "virtual_touch": "Ready",
    "control_quality": "Calibrating",
    "action_count": 0,
    "last_capture": "None",
    "face_auth": "Loading",
    "hand_auth": "Waiting",
    "auth_stage": "Face ID required",
    "auth_engine": "Detecting",
    "eye_auth": "Waiting",
    "voice_assistant": "Starting",
    "last_voice_command": "None",
    "voice_apps": 0,
    "voice_mic": "Detecting",
    "voice_feedback": "Starting",
    "guardian_status": "Standby",
    "guardian_event": "None",
    "guardian_time": "None",
    "adaptive_pinch": PINCH_THRESHOLD,
    "hand_scale": 0,
}
ACTION_COUNTS = {}
LAST_ACTION_TIMES = {}
BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR)).resolve()
CAPTURE_DIR = BASE_DIR / "captures"
KIOSK_FILE = RESOURCE_DIR / "kiosk_demo.html"
CLONE_FILE = RESOURCE_DIR / "project_clone.html"
GROUP_CLONE_FILE = RESOURCE_DIR / "project_clone_group.html"
KNOWN_FACE_DIR = BASE_DIR / "known_faces"
BUNDLED_KNOWN_FACE_DIR = RESOURCE_DIR / "known_faces"


def seed_writable_known_faces():
    if BUNDLED_KNOWN_FACE_DIR == KNOWN_FACE_DIR or not BUNDLED_KNOWN_FACE_DIR.exists():
        return
    try:
        KNOWN_FACE_DIR.mkdir(exist_ok=True)
        for source_path in BUNDLED_KNOWN_FACE_DIR.iterdir():
            target_path = KNOWN_FACE_DIR / source_path.name
            if source_path.is_file() and not target_path.exists():
                shutil.copy2(source_path, target_path)
    except OSError:
        pass


seed_writable_known_faces()
KNOWN_FACE_IMAGE = KNOWN_FACE_DIR / "yashwant.jpg"
KNOWN_FACE_ENCODING = KNOWN_FACE_DIR / "yashwant_encoding.npy"
KNOWN_FACE_MODEL = KNOWN_FACE_DIR / "yashwant_lbph.yml"
FACE_CASCADE_PATH = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
EYE_CASCADE_PATH = Path(cv2.data.haarcascades) / "haarcascade_eye.xml"
FACE_CASCADE = cv2.CascadeClassifier(str(FACE_CASCADE_PATH))
EYE_CASCADE = cv2.CascadeClassifier(str(EYE_CASCADE_PATH))


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


VOICE_APP_COMMANDS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "camera": "microsoft.windows.camera:",
    "settings": "ms-settings:",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "windows explorer": "explorer.exe",
    "folder": "explorer.exe",
    "folders": "explorer.exe",
    "file": "explorer.exe",
    "files": "explorer.exe",
    "file manager": "explorer.exe",
    "current folder": str(BASE_DIR),
    "project folder": str(BASE_DIR),
    "this folder": str(BASE_DIR),
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "word": "winword.exe",
    "microsoft word": "winword.exe",
    "excel": "excel.exe",
    "microsoft excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "power point": "powerpnt.exe",
    "microsoft powerpoint": "powerpnt.exe",
    "vs code": "code.exe",
    "v s code": "code.exe",
    "vscode": "code.exe",
    "code": "code.exe",
    "code editor": "code.exe",
    "source code": "code.exe",
    "visual code": "code.exe",
    "visual studio code": "code.exe",
    "spotify": "spotify.exe",
    "vlc": "vlc.exe",
    "zoom": "zoom.exe",
    "teams": "ms-teams:",
    "microsoft teams": "ms-teams:",
    "discord": "discord.exe",
    "obs": "obs64.exe",
}
VOICE_SITE_COMMANDS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
    "chatgpt": "https://chatgpt.com",
    "bsnl": "https://www.bsnl.co.in",
}
VOICE_APP_CANONICAL_NAMES = {
    "vs code": "visual studio code",
    "v s code": "visual studio code",
    "vscode": "visual studio code",
    "code": "visual studio code",
    "code editor": "visual studio code",
    "source code": "visual studio code",
    "visual code": "visual studio code",
    "folder": "file explorer",
    "folders": "file explorer",
    "file": "file explorer",
    "files": "file explorer",
    "file manager": "file explorer",
}
OPEN_AMBIGUOUS_TARGETS = {
    "app",
    "apps",
    "application",
    "folder",
    "file",
    "files",
    "program",
    "programs",
    "shortcut",
    "thing",
    "window",
    "windows",
}
OPEN_CLEANUP_WORDS = (
    "open",
    "on",
    "start",
    "launch",
    "run",
    "kholo",
    "khol",
    "kholna",
    "chalu",
    "chalao",
    "kar",
    "karo",
    "kardo",
    "karna hai",
    "mujhe",
    "please",
    "app",
    "application",
    "software",
)
VOICE_DYNAMIC_APPS = {}
air_click_started_at = None
air_click_armed = True
touch_hover_started_at = None
touch_anchor = None
touch_armed = True
touch_swipe_anchor = None
touch_smoothed_pointer = None
touch_pinch_name = None
touch_pinch_started_at = 0
touch_pinch_last_seen_at = 0
touch_playpause_armed = True
touch_close_armed = True
single_action_pose = None
single_finger_hold = None
single_finger_hold_started_at = 0
nav_index_anchor = None
window_fullscreen = False
window_scale = 1.0


def update_telemetry(**changes):
    with TELEMETRY_LOCK:
        TELEMETRY.update(changes)
        TELEMETRY["uptime_seconds"] = int(time.time() - APP_STARTED_AT)


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def adaptive_pinch_threshold(lmList):
    wrist = (lmList[0][1], lmList[0][2])
    middle_mcp = (lmList[9][1], lmList[9][2])
    index_mcp = (lmList[5][1], lmList[5][2])
    pinky_mcp = (lmList[17][1], lmList[17][2])
    palm_height = distance(wrist, middle_mcp)
    palm_width = distance(index_mcp, pinky_mcp)
    hand_scale = max(palm_height, palm_width)
    threshold = int(np.clip(hand_scale * PINCH_THRESHOLD_SCALE, PINCH_THRESHOLD_MIN, PINCH_THRESHOLD_MAX))
    return threshold, int(hand_scale)


def get_finger_states(lmList):
    return {
        "index": lmList[8][2] < lmList[6][2],
        "middle": lmList[12][2] < lmList[10][2],
        "ring": lmList[16][2] < lmList[14][2],
        "pinky": lmList[20][2] < lmList[18][2],
    }


def can_run_action(action_name):
    now = time.time()
    cooldown = ACTION_COOLDOWNS.get(action_name, 0.2)
    if now - LAST_ACTION_TIMES.get(action_name, 0) < cooldown:
        return False
    LAST_ACTION_TIMES[action_name] = now
    ACTION_COUNTS[action_name] = ACTION_COUNTS.get(action_name, 0) + 1
    return True


def total_actions():
    return sum(ACTION_COUNTS.values())


def set_mode_notice(message):
    global mode_notice_text, mode_notice_until
    mode_notice_text = str(message)
    mode_notice_until = time.time() + MODE_NOTICE_SECONDS


def spoken_mode_name(mode_name):
    return mode_name.title()


def activate_mode(mode_index, source="keyboard", announce=True):
    global current_mode_index, last_mode_change_time
    if mode_index < 0 or mode_index >= len(MODES):
        return False, "Mode not found"
    if current_mode_index == mode_index:
        mode_name = MODES[mode_index]
        mode_label = spoken_mode_name(mode_name)
        message = f"{mode_label} on"
        set_mode_notice(message)
        update_telemetry(last_action=message)
        if announce:
            speak(message)
        return True, message

    current_mode_index = mode_index
    last_mode_change_time = time.time()
    if "reset_gesture_state" in globals():
        reset_gesture_state()
    mode_name = MODES[current_mode_index]
    mode_label = spoken_mode_name(mode_name)
    ACTION_COUNTS[f"{source}_mode"] = ACTION_COUNTS.get(f"{source}_mode", 0) + 1
    message = f"{mode_label} on"
    if globals().get("system_locked", False):
        update_telemetry(mode=f"SYSTEM LOCKED | {mode_name} selected", last_action=message)
    else:
        update_telemetry(mode=mode_name, last_action=message)
    set_mode_notice(message)
    if announce:
        speak(message)
    return True, message


def mode_index_from_text(text):
    normalized = normalize_voice_name(text)
    if normalized in MODE_COMMAND_ALIASES:
        return MODE_COMMAND_ALIASES[normalized]

    tokens = set(normalized.split())
    has_mode_intent = (
        "mode" in tokens
        or "mod" in tokens
        or "movie" in tokens
        or "mood" in tokens
        or normalized in MODE_COMMAND_ALIASES
        or any(word in tokens for word in ("switch", "activate", "activated", "set", "select", "change", "chalu", "kar", "karo", "kardo", "on", "lagao", "banao"))
    )
    if not has_mode_intent:
        return None

    for phrase, mode_index in sorted(MODE_COMMAND_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        phrase_tokens = phrase.split()
        if all(token in tokens for token in phrase_tokens):
            return mode_index
    return None


def looks_like_mode_command(text):
    normalized = normalize_voice_name(text)
    tokens = set(normalized.split())
    mode_words = set()
    for phrase in MODE_COMMAND_ALIASES:
        mode_words.update(phrase.split())
    intent_words = {"mode", "mod", "movie", "mood", "switch", "activate", "activated", "set", "select", "change", "chalu", "kar", "karo", "kardo", "on", "lagao", "banao"}
    return bool(tokens & mode_words) or (bool(tokens & {"mode", "mod", "movie", "mood"}) and bool(tokens & intent_words))


def clamp_screen_point(x, y):
    return (
        float(np.clip(x, 0, max(1, screen_w - 1))),
        float(np.clip(y, 0, max(1, screen_h - 1))),
    )


def clean_voice_query(command, trigger_phrases):
    tokens = normalize_voice_name(command).split()
    trigger_token_sets = [
        normalize_voice_name(phrase).split()
        for phrase in trigger_phrases
        if normalize_voice_name(phrase)
    ]
    trigger_token_sets.sort(key=len, reverse=True)

    cleaned_tokens = []
    index = 0
    while index < len(tokens):
        matched = False
        for trigger_tokens in trigger_token_sets:
            trigger_len = len(trigger_tokens)
            if trigger_len and tokens[index : index + trigger_len] == trigger_tokens:
                index += trigger_len
                matched = True
                break
        if not matched:
            cleaned_tokens.append(tokens[index])
            index += 1
    return " ".join(cleaned_tokens)


def has_any_phrase(text, phrases):
    return any(phrase in text for phrase in phrases)


def has_any_voice_phrase(text, phrases):
    return any(phrase_in_text(text, phrase) for phrase in phrases)


def normalize_voice_name(text):
    text = text.lower()
    for source, replacement in VOICE_HINDI_REPLACEMENTS.items():
        text = text.replace(source, replacement)
    cleaned = []
    for char in text:
        cleaned.append(char if char.isalnum() else " ")
    return " ".join("".join(cleaned).split())


def phrase_in_text(text, phrase):
    normalized_text = normalize_voice_name(text)
    normalized_phrase = normalize_voice_name(phrase)
    if not normalized_text or not normalized_phrase:
        return False

    text_tokens = normalized_text.split()
    phrase_tokens = normalized_phrase.split()
    if len(phrase_tokens) == 1:
        return phrase_tokens[0] in text_tokens
    phrase_len = len(phrase_tokens)
    return any(text_tokens[index : index + phrase_len] == phrase_tokens for index in range(len(text_tokens) - phrase_len + 1))


def has_exact_token(text, token):
    return normalize_voice_name(token) in set(normalize_voice_name(text).split())


def is_ambiguous_open_target(target):
    normalized_target = normalize_voice_name(target)
    tokens = normalized_target.split()
    if not tokens:
        return True
    meaningful_tokens = [token for token in tokens if token not in {"please", "app", "application", "software"}]
    if not meaningful_tokens:
        return True
    return len(meaningful_tokens) == 1 and meaningful_tokens[0] in OPEN_AMBIGUOUS_TARGETS


def app_lookup_names(app_name):
    normalized_name = normalize_voice_name(app_name)
    names = []
    for candidate in (normalized_name, VOICE_APP_CANONICAL_NAMES.get(normalized_name)):
        if candidate:
            normalized_candidate = normalize_voice_name(candidate)
            if normalized_candidate and normalized_candidate not in names:
                names.append(normalized_candidate)
    return names


def load_start_menu_apps():
    user_home = Path.home()
    shortcut_dirs = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        user_home / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs"),
    ]
    app_index = {}
    for shortcut_dir in shortcut_dirs:
        if not shortcut_dir.exists():
            continue
        try:
            shortcuts = list(shortcut_dir.rglob("*.lnk"))
        except OSError:
            continue
        for shortcut in shortcuts:
            app_name = normalize_voice_name(shortcut.stem)
            if app_name and app_name not in app_index:
                app_index[app_name] = shortcut
    return app_index


def refresh_voice_app_index():
    global VOICE_DYNAMIC_APPS
    VOICE_DYNAMIC_APPS = load_start_menu_apps()
    update_telemetry(voice_apps=len(VOICE_DYNAMIC_APPS))
    return VOICE_DYNAMIC_APPS


def audio_rms(audio_bytes):
    if not audio_bytes:
        return 0
    samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
    if samples.size == 0:
        return 0
    return int(np.sqrt(np.mean(samples * samples)))


def pick_sounddevice_microphone():
    if sd is None:
        return None, "sounddevice missing", VOICE_SAMPLE_RATE

    try:
        devices = sd.query_devices()
    except Exception:
        return None, "Microphone list unavailable", VOICE_SAMPLE_RATE

    input_devices = [
        (index, device)
        for index, device in enumerate(devices)
        if int(device.get("max_input_channels", 0)) > 0
    ]
    if not input_devices:
        return None, "No input microphone found", VOICE_SAMPLE_RATE

    default_input = None
    try:
        default_device = sd.default.device
        default_input = default_device[0] if isinstance(default_device, (list, tuple)) else default_device
    except Exception:
        default_input = None

    def supported_sample_rate(index, device):
        candidates = []
        try:
            default_rate = int(float(device.get("default_samplerate", 0)))
            if default_rate > 0:
                candidates.append(default_rate)
        except (TypeError, ValueError):
            pass
        candidates.extend(VOICE_DEVICE_SAMPLE_RATE_FALLBACKS)

        seen = set()
        for rate in candidates:
            if rate in seen:
                continue
            seen.add(rate)
            try:
                sd.check_input_settings(device=index, channels=1, dtype="int16", samplerate=rate)
                return int(rate)
            except Exception:
                continue
        return VOICE_SAMPLE_RATE

    for index, device in input_devices:
        name = str(device.get("name", "Microphone"))
        if any(keyword in name.lower() for keyword in VOICE_NOISE_MIC_KEYWORDS):
            return index, name, supported_sample_rate(index, device)

    for index, device in input_devices:
        if index == default_input:
            return index, str(device.get("name", "Default microphone")), supported_sample_rate(index, device)

    index, device = input_devices[0]
    return index, str(device.get("name", "Microphone")), supported_sample_rate(index, device)


def calibrate_sounddevice_microphone(device_index, sample_rate):
    recording = sd.rec(
        int(sample_rate * 1.0),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        device=device_index,
    )
    sd.wait()
    ambient = audio_rms(recording.tobytes())
    adaptive = max(int(ambient * 2.0), ambient + 180)
    return max(VOICE_START_RMS, adaptive)


def listen_with_sounddevice(device_index, sample_rate, start_threshold):
    if sr is None:
        raise RuntimeError("SpeechRecognition is unavailable")

    block_size = max(512, int(sample_rate * VOICE_AUDIO_BLOCK_SECONDS))
    preroll_blocks = []
    frames = []
    start_deadline = time.time() + VOICE_LISTEN_TIMEOUT

    with sd.RawInputStream(
        samplerate=sample_rate,
        blocksize=block_size,
        device=device_index,
        channels=1,
        dtype="int16",
    ) as stream:
        while time.time() < start_deadline:
            block, _ = stream.read(block_size)
            block = bytes(block)
            preroll_blocks.append(block)
            preroll_blocks = preroll_blocks[-3:]
            if audio_rms(block) >= start_threshold:
                frames.extend(preroll_blocks)
                phrase_started_at = time.time()
                last_voice_at = phrase_started_at
                break
        else:
            raise sr.WaitTimeoutError("listening timed out")

        end_threshold = max(int(VOICE_START_RMS * 0.75), int(start_threshold * 0.55))
        while time.time() - phrase_started_at < VOICE_PHRASE_SECONDS:
            block, _ = stream.read(block_size)
            block = bytes(block)
            frames.append(block)

            now = time.time()
            if audio_rms(block) >= end_threshold:
                last_voice_at = now

            if (
                now - phrase_started_at >= VOICE_MIN_RECORD_SECONDS
                and now - last_voice_at >= VOICE_END_SILENCE_SECONDS
            ):
                break

    audio_data = b"".join(frames)
    if not audio_data:
        raise sr.WaitTimeoutError("no speech captured")
    return sr.AudioData(audio_data, sample_rate, 2)


def recognize_voice_command(recognizer, audio):
    last_error = None
    for language in VOICE_RECOGNITION_LANGUAGES:
        try:
            command = recognizer.recognize_google(audio, language=language)
            if command and command.strip():
                return command
        except sr.UnknownValueError as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    raise sr.UnknownValueError()


def pick_pyaudio_microphone():
    if sr is None:
        return None, "SpeechRecognition missing"
    try:
        mic_names = sr.Microphone.list_microphone_names()
    except (AttributeError, OSError):
        return None, "Microphone list unavailable"

    for index, name in enumerate(mic_names):
        lowered = name.lower()
        if any(keyword in lowered for keyword in VOICE_NOISE_MIC_KEYWORDS):
            return sr.Microphone(device_index=index), name

    try:
        return sr.Microphone(), "Default microphone"
    except (AttributeError, OSError):
        return None, "PyAudio microphone unavailable"


def open_google_search(query):
    if not query:
        return False, "No search query"
    webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
    return True, f"Searching {query}"


def open_youtube_search(query=None):
    if query:
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
        return True, f"Searching YouTube for {query}"
    webbrowser.open("https://www.youtube.com")
    return True, "Opening YouTube"


def open_site(site_name):
    normalized_site = normalize_voice_name(site_name)
    url = VOICE_SITE_COMMANDS.get(normalized_site) or VOICE_SITE_COMMANDS.get(site_name)
    if not url:
        return False, f"Unknown site {site_name}"
    webbrowser.open(url)
    return True, f"Opening {normalized_site or site_name}"


def find_site_name_in_command(command):
    for site_name in sorted(VOICE_SITE_COMMANDS, key=len, reverse=True):
        if phrase_in_text(command, site_name):
            return site_name
    return None


def dynamic_app_match_score(app_name, indexed_name):
    normalized_name = normalize_voice_name(app_name)
    normalized_indexed = normalize_voice_name(indexed_name)
    if not normalized_name or is_ambiguous_open_target(normalized_name):
        return 0
    if normalized_name == normalized_indexed:
        return 100

    query_tokens = [token for token in normalized_name.split() if token not in {"please", "app", "application", "software"}]
    indexed_tokens = normalized_indexed.split()
    indexed_token_set = set(indexed_tokens)
    if not query_tokens or not indexed_tokens:
        return 0

    if len(query_tokens) == 1:
        token = query_tokens[0]
        if token in OPEN_AMBIGUOUS_TARGETS or len(token) < 4:
            return 0
        if token in indexed_token_set:
            return 82 if indexed_tokens[0] == token else 72
        if len(token) >= 5 and any(indexed_token.startswith(token) for indexed_token in indexed_tokens):
            return 58
        return 0

    matched_tokens = sum(1 for token in query_tokens if token in indexed_token_set)
    if matched_tokens == len(query_tokens):
        return 90 + min(8, matched_tokens)

    indexed_meaningful = [token for token in indexed_tokens if token not in OPEN_AMBIGUOUS_TARGETS]
    if indexed_meaningful and all(token in query_tokens for token in indexed_meaningful):
        return 86

    if f" {normalized_name} " in f" {normalized_indexed} ":
        return 78

    coverage = matched_tokens / max(1, len(query_tokens))
    if matched_tokens >= 2 and coverage >= 0.66:
        return int(65 + coverage * 20)
    return 0


def find_dynamic_app_match(app_name):
    lookup_names = app_lookup_names(app_name)
    best_match = (0, None, None)
    for indexed_name, shortcut_path in sorted(VOICE_DYNAMIC_APPS.items(), key=lambda item: len(item[0]), reverse=True):
        for lookup_name in lookup_names:
            score = dynamic_app_match_score(lookup_name, indexed_name)
            if score > best_match[0]:
                best_match = (score, indexed_name, shortcut_path)
    if best_match[0] >= 70:
        return best_match[1], best_match[2]
    return None, None


def launch_target(target):
    try:
        os.startfile(str(target))
        return True
    except (AttributeError, OSError):
        pass

    escaped_target = str(target).replace("'", "''")
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Start-Process -FilePath '{escaped_target}'"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        if completed.returncode == 0:
            return True
    except (OSError, subprocess.TimeoutExpired):
        pass

    try:
        subprocess.Popen([str(target)])
        return True
    except OSError:
        return False


def open_app(app_name):
    normalized_name = normalize_voice_name(app_name)
    lookup_names = app_lookup_names(app_name)
    target = VOICE_APP_COMMANDS.get(normalized_name) or VOICE_APP_COMMANDS.get(app_name)
    if not target:
        for lookup_name in lookup_names:
            target = VOICE_APP_COMMANDS.get(lookup_name)
            if target:
                break

    if target and launch_target(target):
        return True, f"Opening {normalized_name or app_name}"

    dynamic_name, shortcut_path = find_dynamic_app_match(normalized_name)
    if dynamic_name and shortcut_path:
        try:
            os.startfile(str(shortcut_path))
            return True, f"Opening {dynamic_name}"
        except OSError:
            pass

    if not target:
        return False, f"Unknown app {app_name}"

    return False, f"Could not open {app_name}"


def find_app_name_in_command(command, allow_fallback=True):
    normalized_command = normalize_voice_name(command)
    for app_name in sorted(VOICE_APP_COMMANDS, key=len, reverse=True):
        if phrase_in_text(normalized_command, app_name):
            return app_name
    for app_name in sorted(VOICE_DYNAMIC_APPS, key=len, reverse=True):
        if phrase_in_text(normalized_command, app_name):
            return app_name
    if not allow_fallback:
        return None

    query = clean_voice_query(command, OPEN_CLEANUP_WORDS)
    if not query:
        return None
    dynamic_name, _ = find_dynamic_app_match(query)
    return dynamic_name or query


def voice_screenshot():
    CAPTURE_DIR.mkdir(exist_ok=True)
    capture_path = CAPTURE_DIR / f"voice_screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png"
    pyautogui.screenshot(str(capture_path))
    return True, f"Screenshot saved {capture_path.name}"


def is_music_or_video_search_command(command):
    normalized = normalize_voice_name(command)
    media_words = ("song", "songs", "gana", "gaana", "music", "bhajan", "video")
    action_words = ("play", "chalao", "chalu", "bajao", "lagao", "search", "dhundo", "dhoondo", "khojo")
    pointing_words = ("ye video", "is video", "this video", "current video", "selected video")
    if has_any_phrase(normalized, pointing_words):
        return False
    return has_any_phrase(normalized, media_words) and has_any_phrase(normalized, action_words)


def open_music_or_video_search(command):
    query = clean_voice_query(
        command,
        (
            "youtube",
            "you tube",
            "song",
            "songs",
            "gana",
            "gaana",
            "music",
            "bhajan",
            "video",
            "play",
            "chalao",
            "chalu",
            "bajao",
            "lagao",
            "search",
            "dhundo",
            "dhoondo",
            "khojo",
            "par",
            "pe",
            "mein",
            "me",
            "karo",
            "karna hai",
            "mujhe",
        ),
    )
    return open_youtube_search(query if query else None)


def trigger_guardian_sos(command):
    CAPTURE_DIR.mkdir(exist_ok=True)
    event_time = time.strftime("%Y-%m-%d %H:%M:%S")
    screenshot_name = f"guardian_sos_{time.strftime('%Y%m%d_%H%M%S')}.png"
    screenshot_path = CAPTURE_DIR / screenshot_name
    try:
        pyautogui.screenshot(str(screenshot_path))
        capture_message = screenshot_name
    except Exception:
        capture_message = "Screenshot unavailable"

    update_telemetry(
        guardian_status="SOS ACTIVE",
        guardian_event=command,
        guardian_time=event_time,
        last_capture=str(screenshot_path) if screenshot_path.exists() else capture_message,
        last_action="GUARDIAN SOS ACTIVE",
        voice_assistant="Guardian SOS active",
    )
    ACTION_COUNTS["guardian_sos"] = ACTION_COUNTS.get("guardian_sos", 0) + 1
    try:
        pyautogui.hotkey("win", "d")
    except Exception:
        pass

    if "dashboard_port" in globals() and dashboard_port:
        webbrowser.open(f"http://127.0.0.1:{dashboard_port}/guardian")
    speak("Guardian SOS activated. Emergency command center opened.")
    return True, "Guardian SOS active"


def clear_guardian_sos():
    update_telemetry(
        guardian_status="Standby",
        guardian_event="Cleared",
        guardian_time=time.strftime("%Y-%m-%d %H:%M:%S"),
        last_action="Guardian SOS cleared",
        voice_assistant="Listening",
    )
    speak("Guardian SOS cleared.")
    return True, "Guardian SOS cleared"


def set_mode_by_voice(command):
    mode_index = mode_index_from_text(command)
    if mode_index is None:
        return False, "Mode not found"
    return activate_mode(mode_index, source="voice", announce=False)


def run_voice_keyboard_command(command):
    normalized = normalize_voice_name(command)
    if "backspace" in normalized:
        pyautogui.press("backspace")
        return True, "Backspace"
    if has_any_phrase(normalized, ("back jao", "go back", "browser back", "piche jao", "peeche jao", "wapas jao", "wapis jao", "previous page")) or normalized in ("back", "piche", "peeche", "wapas", "wapis"):
        pyautogui.hotkey("alt", "left")
        return True, "Back"
    if has_any_phrase(normalized, ("forward jao", "go forward", "browser forward", "aage jao", "next page")) or normalized in ("forward", "aage"):
        pyautogui.hotkey("alt", "right")
        return True, "Forward"
    if has_any_phrase(normalized, ("refresh", "reload", "page reload", "dubara load")):
        pyautogui.hotkey("ctrl", "r")
        return True, "Refresh"
    if has_any_phrase(normalized, ("address bar", "search bar", "url bar", "omnibox")):
        pyautogui.hotkey("ctrl", "l")
        return True, "Search bar"
    if has_any_phrase(normalized, ("ye video chalao", "ye video ko chalao", "ye video ka chalao", "is video chalao", "is video ko chalao", "this video play", "play this video", "selected video chalao", "current video chalao", "open this video", "ye result kholo", "selected result kholo")):
        pyautogui.press("enter")
        return True, "Video open"
    if has_any_phrase(normalized, ("open selected", "selected kholo", "select karo", "enter karo", "result kholo")):
        pyautogui.press("enter")
        return True, "Enter"
    if "volume up" in command or "awaz badhao" in command or "sound badhao" in command:
        pyautogui.press("volumeup")
        return True, "Volume up"
    if "volume down" in command or "awaz kam" in command or "sound kam" in command:
        pyautogui.press("volumedown")
        return True, "Volume down"
    if "mute" in command:
        pyautogui.press("volumemute")
        return True, "Volume muted"
    if normalized in ("play", "pause", "play pause", "play karo", "pause karo", "video pause", "video play", "video chalu", "video band"):
        pyautogui.press("playpause")
        return True, "Play pause"
    if "next tab" in command:
        pyautogui.hotkey("ctrl", "tab")
        return True, "Next tab"
    if "previous tab" in command or "prev tab" in command:
        pyautogui.hotkey("ctrl", "shift", "tab")
        return True, "Previous tab"
    if "new tab" in command:
        pyautogui.hotkey("ctrl", "t")
        return True, "New tab"
    if "close tab" in command:
        pyautogui.hotkey("ctrl", "w")
        return True, "Tab closed"
    if "close window" in command:
        pyautogui.hotkey("alt", "f4")
        return True, "Window closed"
    if "enter" in command:
        pyautogui.press("enter")
        return True, "Enter"
    if "scroll up" in command:
        pyautogui.scroll(500)
        return True, "Scroll up"
    if "scroll down" in command:
        pyautogui.scroll(-500)
        return True, "Scroll down"
    if "left" in command and ("slide" in command or "arrow" in command):
        pyautogui.press("left")
        return True, "Left"
    if "right" in command and ("slide" in command or "arrow" in command):
        pyautogui.press("right")
        return True, "Right"
    if "screenshot" in command or "screen shot" in command:
        return voice_screenshot()
    return False, "No keyboard command"


def extract_after_any(command, triggers):
    lowered_command = command.lower()
    for trigger in triggers:
        lowered_trigger = trigger.lower()
        trigger_index = lowered_command.find(lowered_trigger)
        if trigger_index >= 0:
            return command[trigger_index + len(trigger):].strip()
    return ""


def handle_voice_command(command):
    raw_command = str(command).strip()
    if not raw_command:
        return False, "Empty voice command"

    normalized_command = normalize_voice_name(raw_command)
    command = normalized_command
    update_telemetry(last_voice_command=raw_command)
    youtube_words = ("youtube", "you tube")
    open_words = ("open", "start", "launch", "run", "kholo", "khol", "chalu", "chalao", "kholna", "karo", "kar", "kardo")
    search_words = ("search", "google", "dhundo", "dhoondo", "khojo", "find")
    sos_words = ("sos", "emergency", "help me", "bachao", "madad", "medical help", "guardian")

    if has_any_phrase(command, sos_words) and not has_any_phrase(command, ("clear", "cancel", "stop")):
        success, message = trigger_guardian_sos(command)
    elif has_any_phrase(command, ("clear sos", "cancel sos", "stop sos", "clear guardian", "cancel guardian")):
        success, message = clear_guardian_sos()
    elif mode_index_from_text(command) is not None:
        success, message = set_mode_by_voice(command)
    elif looks_like_mode_command(command):
        success, message = False, "Mode command not matched. Say touch mode, media mode, or navigation mode."
    elif command.startswith("type ") or command.startswith("write "):
        text = extract_after_any(raw_command, ("type ", "write "))
        if text:
            pyautogui.write(text, interval=0.01)
            success, message = True, "Typed text"
        else:
            success, message = False, "No text to type"
    elif is_music_or_video_search_command(command):
        success, message = open_music_or_video_search(command)
    elif has_any_phrase(command, youtube_words):
        query = clean_voice_query(command, youtube_words + open_words + search_words + ("par", "pe", "mein", "me", "karo", "karna hai", "mujhe"))
        success, message = open_youtube_search(query if query else None)
    else:
        success, message = run_voice_keyboard_command(command)
        known_app_name = find_app_name_in_command(command, allow_fallback=False)
        known_site_name = find_site_name_in_command(command)
        open_intent = has_any_voice_phrase(command, open_words) or (
            has_exact_token(command, "on") and (known_app_name or known_site_name)
        ) or (
            known_app_name and command == normalize_voice_name(known_app_name)
        ) or (
            known_site_name and command == normalize_voice_name(known_site_name)
        )
        if not success and open_intent:
            opened = False
            success, message = False, "Open target not found"
            if known_app_name:
                success, message = open_app(known_app_name)
                opened = success
            if not opened and known_site_name:
                success, message = open_site(known_site_name)
                opened = success
            if not opened:
                app_name = find_app_name_in_command(command, allow_fallback=True)
                if app_name and not is_ambiguous_open_target(app_name):
                    success, message = open_app(app_name)
                    opened = success
            if not opened:
                query = clean_voice_query(command, OPEN_CLEANUP_WORDS)
                if query and not is_ambiguous_open_target(query):
                    success, message = open_google_search(query)
                else:
                    success, message = False, "Open target not clear"
        elif not success and (has_any_phrase(command, search_words) or "mujhe" in command):
            query = clean_voice_query(command, search_words + ("karo", "karna hai", "mujhe", "ke bare mein", "ke baare mein"))
            success, message = open_google_search(query)
        elif not success:
            success, message = False, "Voice command not matched"

    if success:
        ACTION_COUNTS["voice_command"] = ACTION_COUNTS.get("voice_command", 0) + 1
        update_telemetry(last_action=message, voice_assistant="Listening")
        print(f"Voice command: {raw_command} -> {message}")
        speak(message)
    else:
        update_telemetry(voice_assistant=message)
        print(f"Voice command failed: {raw_command} -> {message}")
        if looks_like_mode_command(raw_command):
            speak(message)
    return success, message


def voice_assistant_loop():
    if sr is None:
        update_telemetry(voice_assistant="Install SpeechRecognition")
        return

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 420
    recognizer.pause_threshold = 0.65
    recognizer.non_speaking_duration = 0.35

    if sd is not None:
        device_index, mic_name, sample_rate = pick_sounddevice_microphone()
        if device_index is not None:
            update_telemetry(
                voice_assistant="Calibrating microphone",
                voice_mic=f"{mic_name} (sounddevice)",
            )
            try:
                start_threshold = calibrate_sounddevice_microphone(device_index, sample_rate)
            except Exception:
                update_telemetry(voice_assistant="Microphone calibration failed")
                time.sleep(2)
            else:
                recognizer.energy_threshold = start_threshold
                update_telemetry(
                    voice_assistant="Listening",
                    voice_mic=f"{mic_name} (sounddevice)",
                )
                sounddevice_errors = 0
                while True:
                    try:
                        audio = listen_with_sounddevice(device_index, sample_rate, start_threshold)
                        sounddevice_errors = 0
                        update_telemetry(voice_assistant="Recognizing")
                        command = recognize_voice_command(recognizer, audio)
                        handle_voice_command(command)
                    except sr.WaitTimeoutError:
                        update_telemetry(voice_assistant="Listening")
                        continue
                    except sr.UnknownValueError:
                        update_telemetry(voice_assistant="Listening")
                    except sr.RequestError:
                        update_telemetry(voice_assistant="Speech service offline")
                        time.sleep(2)
                    except Exception:
                        sounddevice_errors += 1
                        update_telemetry(voice_assistant="Microphone error")
                        if sounddevice_errors >= 3:
                            update_telemetry(voice_assistant="Trying PyAudio fallback")
                            break
                        time.sleep(2)
        else:
            update_telemetry(voice_assistant=mic_name, voice_mic=mic_name)

    microphone, mic_name = pick_pyaudio_microphone()
    if microphone is None:
        update_telemetry(voice_assistant=mic_name, voice_mic=mic_name)
        return

    update_telemetry(voice_assistant="Calibrating microphone", voice_mic=f"{mic_name} (PyAudio)")
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.2)
    except (AttributeError, OSError):
        update_telemetry(voice_assistant="Microphone calibration failed")
        return

    update_telemetry(voice_assistant="Listening", voice_mic=f"{mic_name} (PyAudio)")
    while True:
        try:
            with microphone as source:
                audio = recognizer.listen(source, timeout=VOICE_LISTEN_TIMEOUT, phrase_time_limit=VOICE_PHRASE_SECONDS)
            update_telemetry(voice_assistant="Recognizing")
            command = recognize_voice_command(recognizer, audio)
            handle_voice_command(command)
        except sr.WaitTimeoutError:
            update_telemetry(voice_assistant="Listening")
            continue
        except sr.UnknownValueError:
            update_telemetry(voice_assistant="Listening")
        except sr.RequestError:
            update_telemetry(voice_assistant="Speech service offline")
            time.sleep(2)
        except (AttributeError, OSError):
            update_telemetry(voice_assistant="Microphone error")
            time.sleep(2)


def start_voice_assistant():
    thread = threading.Thread(target=voice_assistant_loop, daemon=True)
    thread.start()
    return thread


def control_quality(fps, hand_detected):
    if not hand_detected:
        return "Waiting for hand"
    if fps >= 24:
        return "Excellent"
    if fps >= 15:
        return "Stable"
    return "Low FPS"


def draw_text(img, text, position, scale=0.7, color=(255, 255, 255), thickness=1):
    cv2.putText(img, text, position, cv2.FONT_HERSHEY_DUPLEX, scale, color, thickness)


def clamp_box(x1, y1, x2, y2, width, height):
    return (
        int(np.clip(x1, 0, max(0, width - 1))),
        int(np.clip(y1, 0, max(0, height - 1))),
        int(np.clip(x2, 0, max(0, width - 1))),
        int(np.clip(y2, 0, max(0, height - 1))),
    )


def blend_rect(img, x1, y1, x2, y2, color, alpha=0.72):
    h, w = img.shape[:2]
    x1, y1, x2, y2 = clamp_box(x1, y1, x2, y2, w, h)
    if x2 <= x1 or y2 <= y1:
        return
    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, cv2.FILLED)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


def draw_corner_box(img, x1, y1, x2, y2, color, thickness=2, length=26):
    h, w = img.shape[:2]
    x1, y1, x2, y2 = clamp_box(x1, y1, x2, y2, w, h)
    length = max(8, min(length, max(8, (x2 - x1) // 3), max(8, (y2 - y1) // 3)))
    cv2.line(img, (x1, y1), (x1 + length, y1), color, thickness)
    cv2.line(img, (x1, y1), (x1, y1 + length), color, thickness)
    cv2.line(img, (x2, y1), (x2 - length, y1), color, thickness)
    cv2.line(img, (x2, y1), (x2, y1 + length), color, thickness)
    cv2.line(img, (x1, y2), (x1 + length, y2), color, thickness)
    cv2.line(img, (x1, y2), (x1, y2 - length), color, thickness)
    cv2.line(img, (x2, y2), (x2 - length, y2), color, thickness)
    cv2.line(img, (x2, y2), (x2, y2 - length), color, thickness)


def status_color(value, fallback=(80, 210, 255)):
    lowered = str(value).lower()
    if any(token in lowered for token in ("verified", "pass", "accepted", "identity", "running", "ready", "excellent", "stable", "clicked", "tapped")):
        return (95, 255, 150)
    if any(token in lowered for token in ("failed", "unavailable", "unknown", "too close", "error", "missing", "offline")):
        return (90, 120, 255)
    if any(token in lowered for token in ("waiting", "required", "locked", "scanning", "hold", "hover")):
        return (80, 210, 255)
    return fallback


def draw_status_row(img, label, value, x, y, width, color, progress=None):
    row_h = 28
    blend_rect(img, x, y - 20, x + width, y + row_h - 20, (18, 30, 38), 0.78)
    cv2.rectangle(img, (x, y - 20), (x + width, y + row_h - 20), color, 1)
    cv2.circle(img, (x + 12, y - 6), 4, color, cv2.FILLED)
    cv2.putText(img, f"{label}: {str(value)[:48]}", (x + 26, y), cv2.FONT_HERSHEY_PLAIN, 1, color, 1)
    if progress is not None:
        p = float(np.clip(progress, 0, 1))
        bar_x1 = x + 26
        bar_x2 = x + width - 16
        bar_y = y + 8
        cv2.line(img, (bar_x1, bar_y), (bar_x2, bar_y), (35, 55, 66), 3)
        cv2.line(img, (bar_x1, bar_y), (bar_x1 + int((bar_x2 - bar_x1) * p), bar_y), color, 3)


def draw_scanner_noise(img, color=(35, 180, 210), density=44):
    h, w = img.shape[:2]
    for x in range(0, w, density):
        cv2.line(img, (x, 0), (x, h), (20, 35, 46), 1)
    for y in range(0, h, density):
        cv2.line(img, (0, y), (w, y), (20, 35, 46), 1)
    tick_x = int((time.time() * 125) % max(w, 1))
    tick_y = int((time.time() * 88) % max(h, 1))
    cv2.line(img, (tick_x, 0), (tick_x, h), color, 2)
    cv2.line(img, (0, tick_y), (w, tick_y), (color[0] // 2, color[1] // 2, color[2] // 2), 1)


def draw_detection_zone(img, x1, y1, x2, y2, color, hand_detected):
    draw_corner_box(img, x1, y1, x2, y2, color, 2, 34)
    phase = int((time.time() * 120) % max(1, y2 - y1))
    scan_y = y1 + phase
    cv2.line(img, (x1 + 6, scan_y), (x2 - 6, scan_y), color, 1)
    label = "HAND TRACKING ACTIVE" if hand_detected else "HAND TRACKING STANDBY"
    blend_rect(img, x1, y1 - 28, x1 + 230, y1 - 4, (10, 16, 22), 0.8)
    cv2.putText(img, label, (x1 + 10, y1 - 11), cv2.FONT_HERSHEY_PLAIN, .95, color, 1)


def draw_advanced_hud(
    img,
    mode_name,
    fps,
    action_log,
    current_gesture,
    global_air_click_status,
    virtual_touch_status,
    face_auth_status,
    hand_auth_status,
    auth_engine,
    adaptive_pinch,
    hand_scale,
    system_locked,
    theme_color,
):
    panel_x1, panel_y1 = 10, 10
    panel_x2, panel_y2 = 638, 340
    blend_rect(img, panel_x1, panel_y1, panel_x2, panel_y2, (8, 11, 15), 0.82)
    draw_corner_box(img, panel_x1, panel_y1, panel_x2, panel_y2, theme_color, 2, 32)
    scan_y = panel_y1 + int((time.time() * 92) % max(1, panel_y2 - panel_y1))
    cv2.line(img, (panel_x1 + 12, scan_y), (panel_x2 - 12, scan_y), theme_color, 1)

    cv2.putText(img, "JARVIS VISION CORE", (24, 42), cv2.FONT_HERSHEY_DUPLEX, .75, theme_color, 2)
    cv2.putText(img, f"STATUS: {mode_name}", (24, 70), cv2.FONT_HERSHEY_DUPLEX, .62, theme_color, 1)
    cv2.putText(img, f"FPS {fps} Hz", (520, 42), cv2.FONT_HERSHEY_PLAIN, 1.15, (210, 230, 238), 1)

    rows = [
        ("LOG", action_log, status_color(action_log), None),
        ("GESTURE", current_gesture, status_color(current_gesture), None),
        ("AIR CLICK", global_air_click_status, status_color(global_air_click_status), None),
        ("TOUCH", virtual_touch_status, status_color(virtual_touch_status), None),
        ("FACE ID", face_auth_status, status_color(face_auth_status), None),
        ("HAND SIGN", hand_auth_status, status_color(hand_auth_status), None),
        ("ENGINE", auth_engine, (180, 220, 255), None),
        ("AI PINCH", f"{adaptive_pinch}px | HAND SCALE {hand_scale}px", (255, 215, 115), min(hand_scale / max(1, GESTURE_SAFE_HAND_SCALE_MAX), 1)),
    ]
    y = 102
    for label, value, color, progress in rows:
        draw_status_row(img, label, value, 24, y, 590, color, progress)
        y += 28

    footer = "2FA LOCKED: FACE ID + SECRET SIGN" if system_locked else "Mode keys 1-3 | Media volume | Navigation slide/scroll | Touch hover/tap"
    footer_color = (80, 210, 255) if system_locked else (160, 190, 170)
    cv2.putText(img, footer, (24, 318), cv2.FONT_HERSHEY_PLAIN, .95, footer_color, 1)
    cv2.putText(img, PROJECT_OWNER_NOTICE, (24, 334), cv2.FONT_HERSHEY_PLAIN, .72, (255, 190, 120), 1)


def resize_scanner_window(width, height, scale):
    scaled_w = max(420, int(width * scale))
    scaled_h = max(320, int(height * scale))
    cv2.resizeWindow(WINDOW_NAME, scaled_w, scaled_h)


def set_scanner_fullscreen(enabled):
    prop = cv2.WINDOW_FULLSCREEN if enabled else cv2.WINDOW_NORMAL
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, prop)


def minimize_scanner_window():
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, WINDOW_NAME)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
    except AttributeError:
        pass


def render_biometric_gate(frame, face_status, eye_status, hand_status, auth_stage, fps, selected_mode, mode_notice=""):
    h, w = frame.shape[:2]
    gate = np.zeros((h, w, 3), dtype=np.uint8)
    gate[:] = (8, 12, 18)

    draw_scanner_noise(gate)
    draw_corner_box(gate, 18, 18, w - 18, h - 18, (35, 180, 210), 2, 42)

    cx, cy = w // 2, h // 2 + 18
    radius = min(w, h) // 4
    now = time.time()
    pulse = int(10 + 8 * math.sin(now * 5))
    scanner_color = (0, 210, 255) if "verified" not in face_status.lower() else (80, 255, 140)

    cv2.circle(gate, (cx, cy), radius + pulse, scanner_color, 2)
    cv2.circle(gate, (cx, cy), radius + 30, (30, 70, 85), 1)
    cv2.circle(gate, (cx, cy), radius // 2, (55, 90, 110), 1)
    start_angle = int((now * 110) % 360)
    cv2.ellipse(gate, (cx, cy), (radius + 18, radius + 18), 0, start_angle, start_angle + 80, scanner_color, 3)
    cv2.ellipse(gate, (cx, cy), (radius + 42, radius + 42), 0, start_angle + 180, start_angle + 250, (255, 215, 115), 2)
    cv2.ellipse(gate, (cx, cy - 8), (radius // 2, radius // 2 + 28), 0, 0, 360, scanner_color, 2)
    cv2.ellipse(gate, (cx - radius // 4, cy - 22), (22, 10), 0, 0, 360, (150, 240, 255), 2)
    cv2.ellipse(gate, (cx + radius // 4, cy - 22), (22, 10), 0, 0, 360, (150, 240, 255), 2)
    cv2.line(gate, (cx - radius, cy), (cx + radius, cy), (40, 190, 220), 1)
    cv2.line(gate, (cx, cy - radius), (cx, cy + radius), (40, 190, 220), 1)
    for angle in range(0, 360, 45):
        marker_x = int(cx + math.cos(math.radians(angle + start_angle)) * (radius + 54))
        marker_y = int(cy + math.sin(math.radians(angle + start_angle)) * (radius + 54))
        cv2.circle(gate, (marker_x, marker_y), 3, scanner_color, cv2.FILLED)

    cv2.putText(gate, "JARVIS BIOMETRIC GATE", (28, 46), cv2.FONT_HERSHEY_DUPLEX, 1, (180, 245, 255), 2)
    cv2.putText(gate, "RAW CAMERA LOCKED UNTIL IDENTITY VERIFICATION", (30, 76), cv2.FONT_HERSHEY_PLAIN, 1, (120, 150, 165), 1)
    cv2.putText(gate, PROJECT_OWNER_NOTICE, (30, 92), cv2.FONT_HERSHEY_PLAIN, .82, (255, 190, 120), 1)
    cv2.putText(gate, f"SELECTED MODE: {selected_mode}", (30, 108), cv2.FONT_HERSHEY_PLAIN, 1.15, (255, 215, 115), 1)
    if mode_notice:
        cv2.rectangle(gate, (28, 120), (w - 28, 152), (18, 30, 38), cv2.FILLED)
        cv2.rectangle(gate, (28, 120), (w - 28, 152), (255, 215, 115), 1)
        cv2.putText(gate, mode_notice[:54], (40, 142), cv2.FONT_HERSHEY_PLAIN, 1.05, (255, 235, 160), 1)

    steps = [
        ("FACE ID", face_status),
        ("EYE CHECK", eye_status),
        ("HAND SIGN", hand_status),
        ("AUTH STAGE", auth_stage),
    ]
    y = h - 128
    for label, value in steps:
        ok = any(token in value.lower() for token in ("verified", "pass", "accepted", "identity"))
        color = (95, 255, 150) if ok else status_color(value)
        progress = 1 if ok else .42 + .18 * (math.sin(now * 3 + y) + 1)
        draw_status_row(gate, label, value, 28, y, w - 56, color, progress)
        y += 34

    cv2.putText(gate, f"FPS {fps} | Mode keys 1-3 | Press E enroll | L relock | Q exit", (28, h - 14), cv2.FONT_HERSHEY_PLAIN, 1, (130, 150, 170), 1)
    return gate


def has_opencv_face_auth():
    return hasattr(cv2, "face") and hasattr(cv2.face, "LBPHFaceRecognizer_create")


def detect_largest_face_details(frame_rgb):
    if FACE_CASCADE.empty() or EYE_CASCADE.empty():
        return None, None, 0

    gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.equalizeHist(gray)
    faces = FACE_CASCADE.detectMultiScale(
        gray,
        scaleFactor=1.08,
        minNeighbors=5,
        minSize=FACE_DETECTION_MIN_SIZE,
    )
    if len(faces) == 0:
        faces = FACE_CASCADE.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=4,
            minSize=FACE_DETECTION_MIN_SIZE,
        )
    if len(faces) == 0:
        return None, None, 0

    x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
    face_roi = gray[y:y + h, x:x + w]
    upper_face = face_roi[: max(1, int(h * 0.62)), :]
    eyes = EYE_CASCADE.detectMultiScale(
        upper_face,
        scaleFactor=1.08,
        minNeighbors=5,
        minSize=(18, 18),
    )
    if len(eyes) == 0:
        eyes = EYE_CASCADE.detectMultiScale(
            upper_face,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(14, 14),
        )
    return cv2.resize(face_roi, (180, 180)), (x, y, w, h), len(eyes)


def detect_largest_face_gray(frame_rgb):
    face_roi, _, _ = detect_largest_face_details(frame_rgb)
    return face_roi


def active_face_engine_name():
    if face_recognition is not None:
        return "face_recognition"
    if has_opencv_face_auth():
        return "OpenCV LBPH"
    return "Unavailable"


def load_opencv_face_model():
    if not has_opencv_face_auth():
        return None, "OpenCV Face ID unavailable"
    if not KNOWN_FACE_MODEL.exists():
        return None, "OpenCV Face ID ready: press E to enroll"

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    try:
        recognizer.read(str(KNOWN_FACE_MODEL))
    except (cv2.error, OSError):
        return None, "OpenCV Face ID model unreadable: press E to enroll"
    return recognizer, "OpenCV Face ID profile loaded"


def create_opencv_face_model(frame_rgb):
    if not has_opencv_face_auth():
        return None, "Install opencv-contrib-python"

    face_roi, _, eye_count = detect_largest_face_details(frame_rgb)
    if face_roi is None:
        return None, "No face visible for enrollment"
    if eye_count < EYE_MIN_COUNT:
        return None, "Eyes not visible for enrollment"

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    training_faces = [
        face_roi,
        cv2.equalizeHist(face_roi),
        cv2.convertScaleAbs(face_roi, alpha=1.08, beta=8),
        cv2.convertScaleAbs(face_roi, alpha=0.92, beta=-8),
        cv2.GaussianBlur(face_roi, (3, 3), 0),
    ]
    try:
        recognizer.train(training_faces, np.array([1] * len(training_faces)))
        KNOWN_FACE_DIR.mkdir(exist_ok=True)
        recognizer.write(str(KNOWN_FACE_MODEL))
    except (cv2.error, OSError):
        return None, "OpenCV Face ID enrollment failed"
    return recognizer, "OpenCV Face ID enrolled"


def load_known_face_encoding():
    if face_recognition is None:
        return load_opencv_face_model()

    if KNOWN_FACE_ENCODING.exists():
        try:
            return np.load(str(KNOWN_FACE_ENCODING)), "Face profile loaded"
        except (OSError, ValueError):
            return None, "Face profile unreadable: press E to enroll"

    if KNOWN_FACE_IMAGE.exists():
        try:
            image = face_recognition.load_image_file(str(KNOWN_FACE_IMAGE))
            encodings = face_recognition.face_encodings(image)
        except Exception:
            return None, "Face image unreadable: press E to enroll"
        if encodings:
            try:
                KNOWN_FACE_DIR.mkdir(exist_ok=True)
                np.save(str(KNOWN_FACE_ENCODING), encodings[0])
            except OSError:
                return encodings[0], "Face profile ready but not saved"
            return encodings[0], "Face profile created"
        return None, "No face found in yashwant.jpg"

    return None, "Press E to enroll Face ID"


def enroll_face_from_frame(frame_rgb):
    if face_recognition is None:
        return create_opencv_face_model(frame_rgb)

    _, face_box, eye_count = detect_largest_face_details(frame_rgb)
    if face_box is None:
        return None, "No face visible for enrollment"
    if eye_count < EYE_MIN_COUNT:
        return None, "Eyes not visible for enrollment"

    try:
        encodings = face_recognition.face_encodings(frame_rgb)
    except Exception:
        return None, "Face enrollment failed"
    if not encodings:
        return None, "No face visible for enrollment"

    try:
        KNOWN_FACE_DIR.mkdir(exist_ok=True)
        np.save(str(KNOWN_FACE_ENCODING), encodings[0])
    except OSError:
        return encodings[0], "Face ID enrolled but not saved"
    return encodings[0], "Face ID enrolled"


def recognize_authorized_face(frame_rgb, known_encoding):
    if face_recognition is None:
        if known_encoding is None:
            return False, "OpenCV Face profile missing"

        face_roi, _, eye_count = detect_largest_face_details(frame_rgb)
        if face_roi is None:
            return False, "No face detected"
        if eye_count < EYE_MIN_COUNT:
            return False, "Eye check required"

        try:
            label, confidence = known_encoding.predict(face_roi)
        except cv2.error:
            return False, "Face profile unreadable"
        if label == 1 and confidence <= OPENCV_FACE_CONFIDENCE_LIMIT:
            return True, "Yashwant verified"
        return False, "Unknown face"

    if known_encoding is None:
        return False, "Face profile missing"

    _, face_box, eye_count = detect_largest_face_details(frame_rgb)
    if face_box is None:
        return False, "No face detected"
    if eye_count < EYE_MIN_COUNT:
        return False, "Eye check required"

    small_rgb = cv2.resize(
        frame_rgb,
        (0, 0),
        fx=FACE_RECOGNITION_DOWNSCALE,
        fy=FACE_RECOGNITION_DOWNSCALE,
    )
    try:
        encodings = face_recognition.face_encodings(small_rgb)
    except Exception:
        return False, "Face scan failed"
    if not encodings:
        return False, "No face detected"

    try:
        distances = face_recognition.face_distance([known_encoding], encodings[0])
    except Exception:
        return False, "Face comparison failed"
    matched = bool(distances[0] <= FACE_MATCH_TOLERANCE)
    if matched:
        return True, "Yashwant verified"
    return False, "Unknown face"


def is_secret_hand_sign(lmList):
    index_up = lmList[8][2] < lmList[6][2]
    middle_down = lmList[12][2] > lmList[10][2]
    ring_down = lmList[16][2] > lmList[14][2]
    pinky_up = lmList[20][2] < lmList[18][2]
    return index_up and middle_down and ring_down and pinky_up


def get_finger_states(lmList):
    return {
        "index": lmList[8][2] < lmList[6][2],
        "middle": lmList[12][2] < lmList[10][2],
        "ring": lmList[16][2] < lmList[14][2],
        "pinky": lmList[20][2] < lmList[18][2],
    }


def is_only_finger_up(fingers, finger_name):
    return fingers.get(finger_name, False) and all(
        is_up == (name == finger_name) for name, is_up in fingers.items()
    )


def raised_finger_label(fingers):
    raised = [name for name, is_up in fingers.items() if is_up]
    return " + ".join(name.title() for name in raised) if raised else "Fist"


def single_finger_pose(fingers):
    raised = [name for name, is_up in fingers.items() if is_up]
    return raised[0] if len(raised) == 1 else None


def intentional_thumb_pinch(lmList, target_tip_id, threshold):
    thumb = (lmList[4][1], lmList[4][2])
    target = (lmList[target_tip_id][1], lmList[target_tip_id][2])
    if distance(thumb, target) >= threshold:
        return False

    for tip_id in (8, 12, 16, 20):
        if tip_id == target_tip_id:
            continue
        other = (lmList[tip_id][1], lmList[tip_id][2])
        if distance(thumb, other) < threshold + PINCH_EXCLUSIVE_MARGIN:
            return False
    return True


def intentional_touch_pinch(lmList, target_tip_id, threshold):
    strict_threshold = min(TOUCH_PINCH_MAX_DISTANCE, max(18, int(threshold * 0.72)))
    return intentional_thumb_pinch(lmList, target_tip_id, strict_threshold)


def is_touch_index_control_pose(lmList, fingers, index_pinched=False, middle_pinched=False):
    if index_pinched or middle_pinched or not fingers.get("index", False):
        return False
    index_tip_y = lmList[8][2]
    return all(
        lmList[tip_id][2] > index_tip_y + TOUCH_INDEX_DOMINANCE_MARGIN
        for tip_id in (12, 16, 20)
    )


def smooth_point(previous, pointer, smoothing):
    if previous is None:
        return pointer
    return (
        int(previous[0] + (pointer[0] - previous[0]) * smoothing),
        int(previous[1] + (pointer[1] - previous[1]) * smoothing),
    )


def smooth_touch_pointer(pointer):
    global touch_smoothed_pointer
    touch_smoothed_pointer = smooth_point(touch_smoothed_pointer, pointer, TOUCH_POINTER_SMOOTHING)
    return touch_smoothed_pointer


def move_cursor_from_camera_pointer(pointer):
    global plocX, plocY
    x_screen = np.interp(pointer[0], (act_w_min, act_w_max), (0, screen_w))
    y_screen = np.interp(pointer[1], (act_h_min, act_h_max), (0, screen_h))
    x_screen, y_screen = clamp_screen_point(x_screen, y_screen)
    clocX = plocX + (x_screen - plocX) / smoothening
    clocY = plocY + (y_screen - plocY) / smoothening
    if distance((clocX, clocY), (plocX, plocY)) < CURSOR_MOVE_DEADZONE:
        return True, ""
    ok, message = safe_move_to(clocX, clocY)
    if ok:
        plocX, plocY = clocX, clocY
    return ok, message


def safe_press_key(key):
    try:
        pyautogui.press(key)
        return True, ""
    except Exception as exc:
        return False, f"Input failed: {exc}"


def safe_scroll(amount):
    try:
        pyautogui.scroll(amount)
        return True, ""
    except Exception as exc:
        return False, f"Scroll failed: {exc}"


def safe_hotkey(*keys):
    try:
        pyautogui.hotkey(*keys)
        return True, ""
    except Exception as exc:
        return False, f"Hotkey failed: {exc}"


def safe_move_to(x, y):
    try:
        try:
            pyautogui.moveTo(x, y, _pause=False)
        except TypeError:
            pyautogui.moveTo(x, y)
        return True, ""
    except Exception as exc:
        return False, f"Move failed: {exc}"


def safe_click():
    try:
        pyautogui.click()
        return True, ""
    except Exception as exc:
        return False, f"Click failed: {exc}"


def reset_gesture_state():
    global air_click_started_at, air_click_armed
    global touch_hover_started_at, touch_anchor, touch_armed
    global touch_swipe_anchor, touch_smoothed_pointer
    global touch_pinch_name, touch_pinch_started_at, touch_pinch_last_seen_at
    global touch_playpause_armed, touch_close_armed
    global single_action_pose, single_finger_hold, single_finger_hold_started_at
    global nav_index_anchor
    air_click_started_at = None
    air_click_armed = True
    touch_hover_started_at = None
    touch_anchor = None
    touch_armed = True
    touch_swipe_anchor = None
    touch_smoothed_pointer = None
    touch_pinch_name = None
    touch_pinch_started_at = 0
    touch_pinch_last_seen_at = 0
    touch_playpause_armed = True
    touch_close_armed = True
    single_action_pose = None
    single_finger_hold = None
    single_finger_hold_started_at = 0
    nav_index_anchor = None


def read_camera_frame_with_retry(camera, attempts=30, delay=0.05):
    for _ in range(attempts):
        success, frame = camera.read()
        if success and frame is not None:
            return True, frame
        time.sleep(delay)
    return False, None


def dashboard_page():
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>JARVIS AI Vision Dashboard</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, Segoe UI, Arial, sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: #111417; color: #eef2f7; }
    main { width: min(1120px, calc(100vw - 32px)); margin: 0 auto; padding: 28px 0; }
    header { display: flex; justify-content: space-between; align-items: end; gap: 16px; margin-bottom: 22px; }
    h1 { margin: 0; font-size: clamp(26px, 4vw, 44px); letter-spacing: 0; }
    .subtitle { margin-top: 8px; color: #a9b4c2; }
    .badge { border: 1px solid #2d3844; padding: 8px 12px; border-radius: 8px; color: #8ee4af; background: #16211c; white-space: nowrap; }
    .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
    .panel { border: 1px solid #28313b; border-radius: 8px; background: #171c22; padding: 18px; min-height: 128px; }
    .wide { grid-column: span 2; }
    .label { color: #94a3b8; font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }
    .value { margin-top: 10px; font-size: 30px; font-weight: 750; overflow-wrap: anywhere; }
    .ok { color: #73d99f; } .warn { color: #ffcf6a; } .danger { color: #ff7a7a; }
    .modes { display: grid; gap: 10px; margin-top: 12px; }
    .mode { display: flex; justify-content: space-between; border: 1px solid #2b3641; border-radius: 8px; padding: 12px; color: #cbd5e1; }
    .mode.active { border-color: #73d99f; background: #16231d; color: #f7fff9; }
    footer { margin-top: 18px; color: #748194; font-size: 13px; line-height: 1.45; }
    .copyright { margin-top: 10px; border: 1px solid #6f4930; border-radius: 8px; padding: 10px 12px; color: #ffd0a3; background: #211811; }
    @media (max-width: 820px) { header { align-items: start; flex-direction: column; } .grid { grid-template-columns: 1fr; } .wide { grid-column: auto; } }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>JARVIS AI Vision Controller</h1>
        <div class="subtitle">Live hackathon telemetry server for your gesture-controlled OS assistant.</div>
      </div>
      <div id="server" class="badge">Server online</div>
    </header>
    <section class="grid">
      <div class="panel wide"><div class="label">Current Mode</div><div id="mode" class="value">-</div></div>
      <div class="panel"><div class="label">Security</div><div id="locked" class="value">-</div></div>
      <div class="panel"><div class="label">FPS</div><div id="fps" class="value">0</div></div>
      <div class="panel wide"><div class="label">Last Action</div><div id="action" class="value">-</div></div>
      <div class="panel"><div class="label">Hand Tracking</div><div id="hand" class="value">-</div></div>
      <div class="panel"><div class="label">Uptime</div><div id="uptime" class="value">0s</div></div>
      <div class="panel"><div class="label">Gesture</div><div id="gesture" class="value">-</div></div>
      <div class="panel"><div class="label">Air Click</div><div id="airclick" class="value">-</div></div>
      <div class="panel"><div class="label">Virtual Touch</div><div id="touch" class="value">-</div></div>
      <div class="panel"><div class="label">Quality</div><div id="quality" class="value">-</div></div>
      <div class="panel"><div class="label">Actions</div><div id="actions" class="value">0</div></div>
      <div class="panel"><div class="label">AI Pinch</div><div id="aipinch" class="value">0px</div></div>
      <div class="panel"><div class="label">Hand Scale</div><div id="handscale" class="value">0px</div></div>
      <div class="panel"><div class="label">Last Capture</div><div id="capture" class="value">-</div></div>
      <div class="panel"><div class="label">Face ID</div><div id="faceauth" class="value">-</div></div>
      <div class="panel"><div class="label">Eye Check</div><div id="eyeauth" class="value">-</div></div>
      <div class="panel"><div class="label">Hand Sign</div><div id="handauth" class="value">-</div></div>
      <div class="panel"><div class="label">Auth Engine</div><div id="authengine" class="value">-</div></div>
      <div class="panel wide"><div class="label">2FA Stage</div><div id="authstage" class="value">-</div></div>
      <div class="panel wide"><div class="label">Voice Assistant</div><div id="voice" class="value">-</div></div>
      <div class="panel wide"><div class="label">Last Voice Command</div><div id="voicecmd" class="value">-</div></div>
      <div class="panel"><div class="label">Voice Apps</div><div id="voiceapps" class="value">0</div></div>
      <div class="panel wide"><div class="label">Voice Mic</div><div id="voicemic" class="value">-</div></div>
      <div class="panel wide"><div class="label">Voice Feedback</div><div id="voicefeedback" class="value">-</div></div>
      <div class="panel"><div class="label">Guardian</div><div id="guardian" class="value">-</div></div>
      <div class="panel wide"><div class="label">Guardian Event</div><div id="guardiancmd" class="value">-</div></div>
      <div class="panel wide">
        <div class="label">Demo Modes</div>
        <div class="modes">
          <div class="mode" data-mode="MEDIA MODE"><span>Media</span><span>Middle/ring volume control</span></div>
          <div class="mode" data-mode="NAVIGATION MODE"><span>Navigation</span><span>Index slide, finger scroll</span></div>
          <div class="mode" data-mode="TOUCH MODE"><span>Touch</span><span>Hover + Tap</span></div>
        </div>
      </div>
    </section>
    <footer>
      Presentation clone: <a href="/clone">/clone</a>. Mode keys: 1 Media, 2 Navigation, 3 Touch. Gesture mode switching is disabled for demo stability.
      <div class="copyright">Copyright (C) 2026 Yashwant Sonkar and Project Team. Unauthorized copying, redistribution, or rebranding is prohibited.</div>
    </footer>
  </main>
  <script>
    const setText = (id, value) => document.getElementById(id).textContent = value;
    async function refresh() {
      try {
        const data = await fetch('/api/status', { cache: 'no-store' }).then(r => r.json());
        setText('mode', data.mode);
        setText('locked', data.locked ? 'Locked' : 'Unlocked');
        setText('fps', data.fps);
        setText('action', data.last_action);
        setText('hand', data.hand_detected ? 'Detected' : 'Waiting');
        setText('uptime', `${data.uptime_seconds}s`);
        setText('gesture', data.current_gesture);
        setText('airclick', data.air_click);
        setText('touch', data.virtual_touch);
        setText('quality', data.control_quality);
        setText('actions', data.action_count);
        setText('aipinch', `${data.adaptive_pinch}px`);
        setText('handscale', `${data.hand_scale}px`);
        setText('capture', data.last_capture);
        setText('faceauth', data.face_auth);
        setText('eyeauth', data.eye_auth);
        setText('handauth', data.hand_auth);
        setText('authengine', data.auth_engine);
        setText('authstage', data.auth_stage);
        setText('voice', data.voice_assistant);
        setText('voicecmd', data.last_voice_command);
        setText('voiceapps', data.voice_apps);
        setText('voicemic', data.voice_mic);
        setText('voicefeedback', data.voice_feedback);
        setText('guardian', data.guardian_status);
        setText('guardiancmd', data.guardian_event);
        document.getElementById('locked').className = `value ${data.locked ? 'danger' : 'ok'}`;
        document.getElementById('hand').className = `value ${data.hand_detected ? 'ok' : 'warn'}`;
        document.getElementById('faceauth').className = `value ${data.face_auth.includes('verified') ? 'ok' : 'warn'}`;
        document.getElementById('eyeauth').className = `value ${data.eye_auth.includes('pass') ? 'ok' : 'warn'}`;
        document.getElementById('handauth').className = `value ${data.hand_auth.includes('Accepted') ? 'ok' : 'warn'}`;
        document.getElementById('authengine').className = `value ${data.auth_engine === 'Unavailable' ? 'danger' : 'ok'}`;
        document.getElementById('authstage').className = `value ${data.locked ? 'warn' : 'ok'}`;
        document.getElementById('voice').className = `value ${data.voice_assistant === 'Listening' ? 'ok' : 'warn'}`;
        document.getElementById('voicefeedback').className = `value ${data.voice_feedback.includes('Ready') ? 'ok' : 'warn'}`;
        document.getElementById('guardian').className = `value ${data.guardian_status === 'SOS ACTIVE' ? 'danger' : 'ok'}`;
        document.getElementById('airclick').className = `value ${data.air_click === 'Clicked' ? 'ok' : 'warn'}`;
        document.getElementById('touch').className = `value ${data.virtual_touch === 'Tapped' ? 'ok' : 'warn'}`;
        document.getElementById('quality').className = `value ${data.control_quality === 'Excellent' ? 'ok' : 'warn'}`;
        document.querySelectorAll('.mode').forEach(el => el.classList.toggle('active', el.dataset.mode === data.mode));
      } catch (error) {
        document.getElementById('server').textContent = 'Server reconnecting';
      }
    }
    refresh();
    setInterval(refresh, 700);
  </script>
</body>
</html>"""

             
def guardian_page():
    with TELEMETRY_LOCK:
        status = html.escape(str(TELEMETRY.get("guardian_status", "Standby")))
        event = html.escape(str(TELEMETRY.get("guardian_event", "None")))
        event_time = html.escape(str(TELEMETRY.get("guardian_time", "None")))
        capture = html.escape(str(TELEMETRY.get("last_capture", "None")))
        mic = html.escape(str(TELEMETRY.get("voice_mic", "Unknown")))
        mode = html.escape(str(TELEMETRY.get("mode", "Unknown")))
    active = status == "SOS ACTIVE"
    color = "#ff4d4d" if active else "#73d99f"
    title = "GUARDIAN SOS ACTIVE" if active else "Guardian Standby"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Guardian SOS</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, Segoe UI, Arial, sans-serif; }}
    body {{ margin: 0; min-height: 100vh; background: #101317; color: #f8fafc; display: grid; place-items: center; }}
    main {{ width: min(940px, calc(100vw - 32px)); }}
    h1 {{ margin: 0 0 12px; font-size: clamp(40px, 8vw, 92px); letter-spacing: 0; color: {color}; }}
    .status {{ border: 2px solid {color}; border-radius: 8px; padding: 22px; background: #171c22; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 18px; }}
    .item {{ border: 1px solid #2d3743; border-radius: 8px; padding: 16px; background: #121820; }}
    .label {{ color: #94a3b8; font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }}
    .value {{ margin-top: 8px; font-size: 22px; overflow-wrap: anywhere; }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    <div class="status">
      <div class="label">Emergency Command Center</div>
      <div class="value">Use voice command "clear sos" after the demo or when the alert is handled.</div>
    </div>
    <section class="grid">
      <div class="item"><div class="label">Status</div><div class="value">{status}</div></div>
      <div class="item"><div class="label">Time</div><div class="value">{event_time}</div></div>
      <div class="item"><div class="label">Voice Trigger</div><div class="value">{event}</div></div>
      <div class="item"><div class="label">Capture</div><div class="value">{capture}</div></div>
      <div class="item"><div class="label">Voice Mic</div><div class="value">{mic}</div></div>
      <div class="item"><div class="label">Controller Mode</div><div class="value">{mode}</div></div>
    </section>
  </main>
</body>
</html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        request_path = urlparse(self.path).path

        if request_path in ("/", "/dashboard"):
            body = dashboard_page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if request_path in ("/kiosk", "/kiosk_demo.html"):
            if not KIOSK_FILE.exists():
                self.send_response(404)
                self.end_headers()
                return

            body = KIOSK_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if request_path in ("/clone", "/project_clone.html"):
            if not CLONE_FILE.exists():
                self.send_response(404)
                self.end_headers()
                return

            body = CLONE_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if request_path in ("/group-clone", "/project_clone_group.html"):
            if not GROUP_CLONE_FILE.exists():
                self.send_response(404)
                self.end_headers()
                return

            body = GROUP_CLONE_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if request_path == "/guardian":
            body = guardian_page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if request_path == "/api/mode":
            query = parse_qs(urlparse(self.path).query)
            mode_text = query.get("mode", [""])[0]
            mode_index = mode_index_from_text(mode_text)
            if mode_index is None:
                payload = {"ok": False, "message": "Mode not found"}
            else:
                success, message = activate_mode(mode_index, source="server", announce=True)
                payload = {"ok": success, "message": message, "mode": MODES[current_mode_index]}

            body = json.dumps(payload).encode("utf-8")
            self.send_response(200 if payload["ok"] else 400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if request_path == "/api/status":
            with TELEMETRY_LOCK:
                payload = dict(TELEMETRY)
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


def start_dashboard_server():
    port = DASHBOARD_PORT
    for _ in range(10):
        try:
            server = ReusableThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            update_telemetry(dashboard=f"http://127.0.0.1:{port}")
            return server, port
        except OSError:
            port += 1
    update_telemetry(dashboard="offline")
    return None, None

speak("System Booting. Security Lock Engaged.")

# 2. System Config
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
pyautogui.MINIMUM_DURATION = 0
pyautogui.MINIMUM_SLEEP = 0
screen_w, screen_h = pyautogui.size()
smoothening = 2.2
try:
    plocX, plocY = pyautogui.position()
except Exception:
    plocX, plocY = 0, 0

# 3. Camera Setup
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_TARGET_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_TARGET_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, CAMERA_TARGET_FPS)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
success, img = read_camera_frame_with_retry(cap)
if not success:
    print("CRITICAL ERROR: Webcam not found!")
    cap.release()
    raise SystemExit(1)
cam_h, cam_w, _ = img.shape 
pad = 100 
act_w_min, act_w_max = pad, cam_w - pad
act_h_min, act_h_max = pad, cam_h - pad

# 4. AI Engine Setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=0,
    min_detection_confidence=0.65,
    min_tracking_confidence=0.65,
)
mp_draw = mp.solutions.drawing_utils
known_face_encoding, face_auth_status = load_known_face_encoding()
auth_engine = active_face_engine_name()
face_verified = False
last_face_scan_time = 0
hand_auth_status = "Waiting for Face ID"
eye_auth_status = "Waiting for face"
auth_stage = "Face ID required"

# 5. OS Modes & Security State
MODES = ["MEDIA MODE", "NAVIGATION MODE", "TOUCH MODE"]
COLORS = [(255, 165, 0), (0, 255, 0), (255, 80, 180)] # Orange, Green, Pink
current_mode_index = 0
last_mode_change_time = 0
mode_notice_text = ""
mode_notice_until = 0

system_locked = True # SYSTEM STARTS LOCKED
pTime = 0 
WINDOW_NAME = "JARVIS AI Controller - Hackathon Edition"
refresh_voice_app_index()
dashboard_server, dashboard_port = start_dashboard_server()
voice_thread = start_voice_assistant()
missed_camera_frames = 0

print("\n" + "="*50)
print("JARVIS PROTOCOL ONLINE: SECURITY ACTIVE")
print("2FA unlock: Face ID first, then secret hand sign (index + pinky up).")
print(f"Face ID engine: {auth_engine}")
print(f"Face ID status: {face_auth_status}")
print("Voice assistant: say 'youtube open karo', 'youtube par music search karo', or 'search weather today'.")
print("Press E while your face is visible to enroll/re-enroll Face ID.")
print("Mode keys: 1 Media, 2 Navigation, 3 Touch. N cycles modes.")
print("Gesture mode switching is disabled for demo stability.")
print("Window controls: F fullscreen, M minimize, + bigger, - smaller, R restore.")
if dashboard_port:
    print(f"Live dashboard: http://127.0.0.1:{dashboard_port}")
    print(f"Project presentation clone: http://127.0.0.1:{dashboard_port}/clone")
    print(f"Group project clone: http://127.0.0.1:{dashboard_port}/group-clone")
    print(f"Touchless kiosk demo: http://127.0.0.1:{dashboard_port}/kiosk")
print("="*50 + "\n")

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
resize_scanner_window(cam_w, cam_h, window_scale)

while True:
    global_air_click_status = "Ready"
    virtual_touch_status = "Ready"
    success, img = cap.read()
    if not success or img is None:
        missed_camera_frames += 1
        update_telemetry(status="CAMERA WAIT", last_action="Waiting for camera frame")
        if missed_camera_frames >= 15:
            break
        time.sleep(0.03)
        continue
    missed_camera_frames = 0
        
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    selected_mode_name = MODES[current_mode_index]
    theme_color = COLORS[current_mode_index] if not system_locked else (0, 0, 150)
    mode_name = selected_mode_name if not system_locked else "SYSTEM LOCKED"
    telemetry_mode_name = selected_mode_name if not system_locked else f"SYSTEM LOCKED | {selected_mode_name} selected"
    action_log = "AWAITING UNLOCK..." if system_locked else "SYSTEM IDLE"
    hand_detected = bool(results.multi_hand_landmarks)
    current_gesture = "None"
    air_click_consumed = False
    adaptive_pinch = PINCH_THRESHOLD
    hand_scale = 0
    if system_locked:
        auth_stage = "Face ID required" if not face_verified else "Show secret hand sign"
        hand_auth_status = "Waiting for Face ID" if not face_verified else "Waiting for sign"
        if time.time() - last_face_scan_time >= FACE_SCAN_INTERVAL:
            face_verified, face_auth_status = recognize_authorized_face(img_rgb, known_face_encoding)
            last_face_scan_time = time.time()
            if face_verified:
                eye_auth_status = "Eye check pass"
                auth_stage = "Face verified. Awaiting hand sign"
                action_log = "FACE ID VERIFIED"
            elif "eye" in face_auth_status.lower():
                eye_auth_status = "Eye check required"
            elif "no face" in face_auth_status.lower():
                eye_auth_status = "Waiting for face"
            else:
                eye_auth_status = "Scanning"
    else:
        face_auth_status = "Yashwant verified"
        eye_auth_status = "Eye check pass"
        hand_auth_status = "Accepted"
        auth_stage = "Identity verified"
    if not hand_detected or system_locked:
        reset_gesture_state()

    # Active Area Box
    draw_detection_zone(img, act_w_min, act_h_min, act_w_max, act_h_max, theme_color, hand_detected)

    if hand_detected:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS, 
                                   mp_draw.DrawingSpec(color=(255, 255, 255), thickness=1, circle_radius=2),
                                   mp_draw.DrawingSpec(color=theme_color, thickness=2))
            
            lmList = []
            for id, lm in enumerate(hand_landmarks.landmark):
                lmList.append([id, int(lm.x * cam_w), int(lm.y * cam_h)])
            
            if len(lmList) != 0:
                # Key Landmarks
                x1, y1 = lmList[8][1], lmList[8][2]   # Index Tip
                x2, y2 = lmList[4][1], lmList[4][2]   # Thumb Tip
                x3, y3 = lmList[12][1], lmList[12][2] # Middle Tip
                x4, y4 = lmList[16][1], lmList[16][2] # Ring Tip
                x5, y5 = lmList[20][1], lmList[20][2] # Pinky Tip
                adaptive_pinch, hand_scale = adaptive_pinch_threshold(lmList)
                fingers = get_finger_states(lmList)
                index_only = is_only_finger_up(fingers, "index")
                middle_only = is_only_finger_up(fingers, "middle")
                ring_only = is_only_finger_up(fingers, "ring")
                pinky_only = is_only_finger_up(fingers, "pinky")
                frame_single_pose = single_finger_pose(fingers)
                now = time.time()
                if frame_single_pose != single_finger_hold:
                    single_action_pose = None
                    single_finger_hold = frame_single_pose
                    single_finger_hold_started_at = now
                single_pose_stable = (
                    frame_single_pose is not None
                    and now - single_finger_hold_started_at >= SINGLE_FINGER_STABLE_SECONDS
                )
                stable_index_only = index_only and frame_single_pose == "index" and single_pose_stable
                stable_middle_only = middle_only and frame_single_pose == "middle" and single_pose_stable
                stable_ring_only = ring_only and frame_single_pose == "ring" and single_pose_stable
                stable_pinky_only = pinky_only and frame_single_pose == "pinky" and single_pose_stable
                
                # --- 2FA BIOMETRIC SECURITY UNLOCK (Face ID + Secret Hand Sign) ---
                if system_locked:
                    if not face_verified:
                        current_gesture = "Face ID required"
                        hand_auth_status = "Locked"
                        action_log = face_auth_status.upper()
                    elif is_secret_hand_sign(lmList):
                        system_locked = False
                        current_gesture = "Secret hand sign"
                        eye_auth_status = "Eye check pass"
                        hand_auth_status = "Accepted"
                        auth_stage = "Identity verified"
                        speak("Identity Verified. Welcome Yashwant.")
                        action_log = "2FA UNLOCKED!"
                        ACTION_COUNTS["two_factor_unlock"] = ACTION_COUNTS.get("two_factor_unlock", 0) + 1
                        cv2.putText(img, "IDENTITY VERIFIED", (120, 300), cv2.FONT_HERSHEY_DUPLEX, 1.6, (0, 255, 0), 3)
                        LAST_ACTION_TIMES["unlock"] = time.time()
                    else:
                        current_gesture = "Show secret hand sign"
                        hand_auth_status = "Waiting for sign"
                        action_log = "FACE OK: SHOW SECRET SIGN"
                    continue # Skip everything else until both auth factors pass

                current_gesture = raised_finger_label(fingers)
                if hand_scale > GESTURE_SAFE_HAND_SCALE_MAX:
                    current_gesture = "Hand too close"
                    action_log = "HAND TOO CLOSE: MOVE BACK"
                    global_air_click_status = "Move hand back"
                    virtual_touch_status = "Move hand back"
                    reset_gesture_state()
                    cv2.putText(img, "MOVE HAND BACK", (150, 360), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 255, 255), 3)
                    continue

                # --- GLOBAL: MODE SWITCHER (Pinky finger) ---
                thumb_pinky_pinch = intentional_thumb_pinch(lmList, 20, adaptive_pinch)
                pinky_mode_ready = stable_pinky_only and single_action_pose != "mode:pinky"
                if (
                    GESTURE_MODE_SWITCH_ENABLED
                    and (pinky_mode_ready or thumb_pinky_pinch)
                    and (time.time() - last_mode_change_time > MODE_SWITCH_COOLDOWN)
                ):
                    mode_index = (current_mode_index + 1) % len(MODES)
                    activate_mode(mode_index, source="gesture", announce=True)
                    new_mode = MODES[current_mode_index]
                    current_gesture = "Pinky mode switch" if stable_pinky_only else "Thumb + pinky"
                    action_log = f"MODE SWITCH: {new_mode}"
                    if stable_pinky_only:
                        single_action_pose = "mode:pinky"
                    cv2.circle(img, (x5, y5), 20, (255, 255, 255), cv2.FILLED)
                    continue 
                
                # --- TOUCH MODE: professional pointer, swipe, and pinch controls ---
                if current_mode_index == 2:
                    index_pinched = intentional_touch_pinch(lmList, 8, adaptive_pinch)
                    middle_pinched = intentional_touch_pinch(lmList, 12, adaptive_pinch)
                    raw_touch_pinch = "index" if index_pinched else "middle" if middle_pinched else None
                    if raw_touch_pinch:
                        touch_pinch_last_seen_at = now
                        if raw_touch_pinch != touch_pinch_name:
                            touch_pinch_name = raw_touch_pinch
                            touch_pinch_started_at = now
                    elif (
                        touch_pinch_name
                        and now - touch_pinch_last_seen_at > TOUCH_PINCH_GRACE_SECONDS
                    ):
                        touch_pinch_name = None
                        touch_pinch_started_at = 0
                    active_touch_pinch = touch_pinch_name
                    pinch_ready = bool(
                        active_touch_pinch
                        and now - touch_pinch_started_at >= TOUCH_PINCH_HOLD_SECONDS
                    )

                    if active_touch_pinch is None:
                        touch_playpause_armed = True
                        touch_close_armed = True

                    if active_touch_pinch:
                        touch_hover_started_at = None
                        touch_anchor = None
                        touch_armed = True
                        touch_swipe_anchor = None
                        air_click_consumed = True
                        air_click_started_at = None
                        air_click_armed = False

                        if active_touch_pinch == "index":
                            current_gesture = "Thumb + index"
                            global_air_click_status = "Play/Pause pinch"
                            virtual_touch_status = "Play/Pause pinch"
                            cv2.circle(img, (x1, y1), 26, (0, 255, 0), 2)
                            if pinch_ready and touch_playpause_armed and can_run_action("touch_playpause"):
                                ok, message = safe_press_key("playpause")
                                action_log = "TOUCH PLAY/PAUSE" if ok else message
                                touch_playpause_armed = False
                        elif active_touch_pinch == "middle":
                            current_gesture = "Thumb + middle"
                            global_air_click_status = "Close tab pinch"
                            virtual_touch_status = "Close YouTube tab"
                            cv2.circle(img, (x3, y3), 26, (0, 255, 255), 2)
                            if pinch_ready and touch_close_armed and can_run_action("touch_close_tab"):
                                ok, message = safe_hotkey("ctrl", "w")
                                action_log = "YOUTUBE TAB CLOSE" if ok else message
                                touch_close_armed = False

                    pointer_control = is_touch_index_control_pose(lmList, fingers, index_pinched, middle_pinched)
                    if pointer_control:
                        pointer = smooth_touch_pointer((x1, y1))
                        cv2.circle(img, pointer, 8, theme_color, cv2.FILLED)
                        ok, message = move_cursor_from_camera_pointer(pointer)
                        if not ok:
                            action_log = message

                        touch_swipe_used = False
                        if touch_swipe_anchor is None:
                            touch_swipe_anchor = pointer
                        cv2.line(img, touch_swipe_anchor, pointer, theme_color, 2)
                        dx = pointer[0] - touch_swipe_anchor[0]
                        dy = pointer[1] - touch_swipe_anchor[1]

                        if abs(dx) > TOUCH_SWIPE_TRIGGER_DISTANCE and abs(dx) > abs(dy) * 1.15:
                            if dx < 0 and can_run_action("slideleft"):
                                ok, message = safe_press_key("left")
                                current_gesture = "Index finger left"
                                action_log = "TOUCH SLIDE LEFT" if ok else message
                                touch_swipe_used = True
                            elif dx > 0 and can_run_action("slideright"):
                                ok, message = safe_press_key("right")
                                current_gesture = "Index finger right"
                                action_log = "TOUCH SLIDE RIGHT" if ok else message
                                touch_swipe_used = True
                            if touch_swipe_used:
                                touch_swipe_anchor = pointer
                                touch_hover_started_at = None
                                touch_anchor = None
                                touch_armed = True
                                virtual_touch_status = "Swipe slide"

                        if not touch_swipe_used and active_touch_pinch is None:
                            if (
                                touch_anchor is None
                                or touch_hover_started_at is None
                                or distance(pointer, touch_anchor) > TOUCH_STABILITY_RADIUS
                            ):
                                touch_anchor = pointer
                                touch_hover_started_at = time.time()
                                touch_armed = True
                            hover_progress = min((time.time() - touch_hover_started_at) / TOUCH_HOVER_SECONDS, 1)
                            virtual_touch_status = (
                                f"Hover {int(hover_progress * 100)}%"
                                if touch_armed
                                else "Move to rearm"
                            )
                            current_gesture = "Virtual touch hover"
                            cv2.circle(img, pointer, int(18 + hover_progress * 28), theme_color, 2)

                            if touch_armed and hover_progress >= 1 and can_run_action("touch_tap"):
                                ok, message = safe_click()
                                current_gesture = "Virtual touch tap"
                                action_log = "VIRTUAL TOUCH TAP" if ok else message
                                virtual_touch_status = "Tapped"
                                touch_armed = False
                                cv2.circle(img, pointer, 45, (0, 255, 0), 3)
                    elif active_touch_pinch is None:
                        touch_swipe_anchor = None
                        touch_smoothed_pointer = None
                        touch_hover_started_at = None
                        touch_anchor = None
                        touch_armed = True
                else:
                    air_click_started_at = None
                    air_click_armed = True
                    if current_mode_index != 1:
                        nav_index_anchor = None
                    touch_hover_started_at = None
                    touch_anchor = None
                    touch_armed = True
                    touch_swipe_anchor = None
                    touch_smoothed_pointer = None
                    touch_pinch_name = None
                    touch_pinch_started_at = 0
                    touch_pinch_last_seen_at = 0
                    touch_playpause_armed = True
                    touch_close_armed = True

                # --- MODE 1: MEDIA MODE ---
                if current_mode_index == 0:
                    media_middle_pinch = intentional_thumb_pinch(lmList, 12, adaptive_pinch)
                    media_ring_pinch = intentional_thumb_pinch(lmList, 16, adaptive_pinch)
                    if stable_middle_only and can_run_action("volumeup"):
                        cv2.circle(img, (x3, y3), 15, theme_color, cv2.FILLED)
                        ok, message = safe_press_key("volumeup")
                        current_gesture = "Middle finger"
                        action_log = "VOLUME UP" if ok else message
                    elif stable_ring_only and can_run_action("volumedown"):
                        cv2.circle(img, (x4, y4), 15, theme_color, cv2.FILLED)
                        ok, message = safe_press_key("volumedown")
                        current_gesture = "Ring finger"
                        action_log = "VOLUME DOWN" if ok else message
                    elif media_middle_pinch and can_run_action("volumeup"):
                        cv2.circle(img, (x3, y3), 15, theme_color, cv2.FILLED)
                        ok, message = safe_press_key("volumeup")
                        current_gesture = "Thumb + middle"
                        action_log = "VOLUME UP" if ok else message
                    elif media_ring_pinch and can_run_action("volumedown"):
                        cv2.circle(img, (x4, y4), 15, theme_color, cv2.FILLED)
                        ok, message = safe_press_key("volumedown")
                        current_gesture = "Thumb + ring"
                        action_log = "VOLUME DOWN" if ok else message

                # --- MODE 2: NAVIGATION MODE ---
                elif current_mode_index == 1:
                    if stable_index_only:
                        pointer = (x1, y1)
                        cv2.circle(img, pointer, 10, theme_color, cv2.FILLED)
                        if nav_index_anchor is None:
                            nav_index_anchor = pointer
                        cv2.line(img, nav_index_anchor, pointer, theme_color, 2)
                        dx = pointer[0] - nav_index_anchor[0]
                        dy = pointer[1] - nav_index_anchor[1]

                        if abs(dy) > NAV_INDEX_TRIGGER_DISTANCE and abs(dy) > abs(dx):
                            current_gesture = "Index vertical ignored"
                            action_log = "NAV VERTICAL INDEX OFF"
                            nav_index_anchor = pointer
                        elif abs(dx) > NAV_INDEX_TRIGGER_DISTANCE and abs(dx) > abs(dy):
                            if dx < 0 and can_run_action("slideleft"):
                                ok, message = safe_press_key("left")
                                current_gesture = "Index finger left"
                                action_log = "SLIDE LEFT" if ok else message
                                nav_index_anchor = pointer
                            elif dx > 0 and can_run_action("slideright"):
                                ok, message = safe_press_key("right")
                                current_gesture = "Index finger right"
                                action_log = "SLIDE RIGHT" if ok else message
                                nav_index_anchor = pointer
                    else:
                        nav_index_anchor = None

                    if stable_middle_only and can_run_action("scrollup"):
                        cv2.circle(img, (x3, y3), 15, theme_color, cv2.FILLED)
                        ok, message = safe_scroll(300)
                        current_gesture = "Middle finger"
                        action_log = "SCROLL UP" if ok else message
                    elif stable_ring_only and can_run_action("scrolldown"):
                        cv2.circle(img, (x4, y4), 15, theme_color, cv2.FILLED)
                        ok, message = safe_scroll(-300)
                        current_gesture = "Ring finger"
                        action_log = "SCROLL DOWN" if ok else message
                    elif intentional_thumb_pinch(lmList, 12, adaptive_pinch) and can_run_action("scrollup"):
                        cv2.circle(img, (x3, y3), 15, theme_color, cv2.FILLED)
                        ok, message = safe_scroll(300)
                        current_gesture = "Thumb + middle"
                        action_log = "SCROLL UP" if ok else message
                    elif intentional_thumb_pinch(lmList, 16, adaptive_pinch) and can_run_action("scrolldown"):
                        cv2.circle(img, (x4, y4), 15, theme_color, cv2.FILLED)
                        ok, message = safe_scroll(-300)
                        current_gesture = "Thumb + ring"
                        action_log = "SCROLL DOWN" if ok else message
                if frame_single_pose is None:
                    single_action_pose = None

    # --- ADVANCED OS HUD ---
    cTime = time.time()
    fps = int(1 / (cTime - pTime)) if pTime != 0 else 0
    pTime = cTime

    active_mode_notice = ""
    if mode_notice_text:
        if time.time() < mode_notice_until:
            active_mode_notice = mode_notice_text
            action_log = mode_notice_text.upper()
        else:
            mode_notice_text = ""
            mode_notice_until = 0
    
    draw_advanced_hud(
        img,
        mode_name,
        fps,
        action_log,
        current_gesture,
        global_air_click_status,
        virtual_touch_status,
        face_auth_status,
        hand_auth_status,
        auth_engine,
        adaptive_pinch,
        hand_scale,
        system_locked,
        theme_color,
    )
    
    update_telemetry(    
        status="RUNNING",
        mode=telemetry_mode_name,
        locked=system_locked,  
        fps=fps,                                                          
        last_action=action_log,       
        hand_detected=hand_detected,
        current_gesture=current_gesture,
        air_click=global_air_click_status,
        virtual_touch=virtual_touch_status,
        control_quality=control_quality(fps, hand_detected),
        action_count=total_actions(),
        face_auth=face_auth_status,
        eye_auth=eye_auth_status,
        hand_auth=hand_auth_status,
        auth_stage=auth_stage,
        auth_engine=auth_engine,
        adaptive_pinch=adaptive_pinch,
        hand_scale=hand_scale,
    )

    if system_locked:
        img = render_biometric_gate(
            img,
            face_auth_status,
            eye_auth_status,
            hand_auth_status,
            auth_stage,
            fps,
            selected_mode_name,
            active_mode_notice,
        )

    cv2.imshow(WINDOW_NAME, img)
    
    key = cv2.waitKey(1) & 0xFF  
    if key in (ord('q'), 27):
        break
    if key == ord('s'):
        CAPTURE_DIR.mkdir(exist_ok=True)
        capture_path = CAPTURE_DIR / f"jarvis_capture_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(str(capture_path), img)
        update_telemetry(last_capture=str(capture_path), last_action="Demo frame captured")
    elif key == ord('l'):
        system_locked = True
        face_verified = False
        hand_auth_status = "Waiting for Face ID"
        eye_auth_status = "Waiting for face"
        auth_stage = "Face ID required"
        ACTION_COUNTS["manual_lock"] = ACTION_COUNTS.get("manual_lock", 0) + 1
        speak("Security Lock Engaged.")
        update_telemetry(
            locked=True,
            mode="SYSTEM LOCKED",
            last_action="Manual security lock",
            eye_auth=eye_auth_status,
            hand_auth=hand_auth_status,
            auth_stage=auth_stage,
        )
    elif key == ord('e'):
        known_face_encoding, face_auth_status = enroll_face_from_frame(img_rgb)
        auth_engine = active_face_engine_name()
        face_verified = bool(known_face_encoding is not None)
        eye_auth_status = "Eye check pass" if face_verified else "Waiting for face"
        hand_auth_status = "Waiting for sign" if face_verified else "Waiting for Face ID"
        auth_stage = "Show secret hand sign" if face_verified else "Face ID enrollment needed"
        ACTION_COUNTS["face_enroll"] = ACTION_COUNTS.get("face_enroll", 0) + 1
        speak(face_auth_status)
        update_telemetry(
            face_auth=face_auth_status,
            eye_auth=eye_auth_status,
            hand_auth=hand_auth_status,
            auth_stage=auth_stage,
            auth_engine=auth_engine,
            last_action=face_auth_status,
        )
    elif key in (ord('1'), ord('2'), ord('3')):
        selected_index = key - ord('1')
        activate_mode(selected_index, source="keyboard", announce=True)
        reset_gesture_state()
    elif key == ord('n'):
        activate_mode((current_mode_index + 1) % len(MODES), source="keyboard", announce=True)
        reset_gesture_state()
    elif key == ord('f'):
        window_fullscreen = not window_fullscreen
        set_scanner_fullscreen(window_fullscreen)
        update_telemetry(last_action="Scanner fullscreen" if window_fullscreen else "Scanner windowed")
    elif key == ord('m'):
        minimize_scanner_window()
        update_telemetry(last_action="Scanner minimized")
    elif key in (ord('+'), ord('=')):
        window_fullscreen = False
        set_scanner_fullscreen(False)
        window_scale = min(window_scale + 0.15, 1.8)
        resize_scanner_window(cam_w, cam_h, window_scale)
        update_telemetry(last_action=f"Scanner size {int(window_scale * 100)}%")
    elif key in (ord('-'), ord('_')):
        window_fullscreen = False
        set_scanner_fullscreen(False)
        window_scale = max(window_scale - 0.15, 0.55)
        resize_scanner_window(cam_w, cam_h, window_scale)
        update_telemetry(last_action=f"Scanner size {int(window_scale * 100)}%")
    elif key == ord('r'):
        window_fullscreen = False
        window_scale = 1.0
        set_scanner_fullscreen(False)
        resize_scanner_window(cam_w, cam_h, window_scale)
        update_telemetry(last_action="Scanner window restored")

    try:
        if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
            break
    except cv2.error:
        break

cap.release()
cv2.destroyAllWindows() 
update_telemetry(status="STOPPED", last_action="Application closed")
if dashboard_server:
    dashboard_server.shutdown()             
                                
   
 
