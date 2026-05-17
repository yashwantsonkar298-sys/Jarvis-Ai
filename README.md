# JARVIS AI Vision Controller

**Submitted by:** Group Project Team  
**Program:** B.Tech First Year  
**Section:** CSE-29  

**Current Project Clone Link:** `http://127.0.0.1:8765/group-clone` - Run `python app.py` or `python kiosk_server.py` first, then open this group clone with team members and problem statements. If port `8765` is busy, use the port printed in the terminal.  
**Quick Presentation Launcher:** Double-click `start_kiosk.bat` to start the standalone presentation server and open the group clone. If port `8765` is busy, the server opens the correct next available port automatically.

## Copyright Notice

Copyright (C) 2026 Yashwant Sonkar and Project Team. All rights reserved.

Unauthorized copying, redistribution, rebranding, resale, or submission of this project as someone else's work is strictly prohibited. If this project is copied and run without permission, the visible project pages and dashboard show the original ownership notice.

## Team Members

| Order | Name | Roll No |
| --- | --- | --- |
| 1 | Vanshika Yadav | 2503201001297 |
| 2 | Yashwant Sonkar | 2503201001359 |
| 3 | Suraj Prajapati | 2503201001201 |
| 4 | Vishal Maurya | 2503201001324 |
| 5 | Tarang Mittal | 2503201001231 |

Mode switch ab stable hai:
1 = Media Mode
2 = Navigation Mode
3 = Touch Mode
N = next mode cycle

Server mode API bhi add kiya:
http://127.0.0.1:8765/api/mode?mode=touch

## Project Summary

JARVIS AI Vision Controller is a touchless human-computer interaction system. It uses a webcam, hand tracking, face verification, voice commands, and local dashboard telemetry to control a Windows computer without touching the keyboard or mouse.

The project is built for hackathon/demo use. It includes a biometric security gate, three gesture-control modes, voice feedback, voice assistant commands, Guardian SOS mode, a live browser dashboard, and a touchless kiosk demo page.

## Problem Areas Covered

| Problem area | Project work |
| --- | --- |
| Hands-free computer access | Webcam hand tracking, hover tap, pinch shortcuts, and gesture modes let users control the computer without keyboard, mouse, or touch. |
| Secure gesture-control unlock | Face ID, eye check, and a secret index-plus-pinky hand sign prevent random users from activating OS-level controls. |
| Touchless public-service interaction | The kiosk demo, live dashboard telemetry, and Guardian SOS command center show touchless interaction for public screens and emergency workflows. |

## Main Files

| File or folder | Purpose |
| --- | --- |
| `app.py` | Main AI vision controller app. Runs camera, hand tracking, Face ID, voice assistant, dashboard, and all gesture controls. |
| `project_clone.html` | A-to-Z hackathon presentation clone page for project features, tools, controls, engines, and demo flow. |
| `project_clone_group.html` | Group project clone page with team members and problem statements. |
| `kiosk_demo.html` | Browser-based touchless kiosk demo with hospital, classroom, smart home, emergency, and information desk workflows. |
| `kiosk_server.py` | Lightweight standalone server for the project clone and kiosk demo pages. |
| `COPYRIGHT.md` | Copyright and ownership notice for the project. |
| `requirements.txt` | Python dependencies required by the project. |
| `known_faces/` | Stores local Face ID data such as the OpenCV LBPH model or optional face encoding. |
| `captures/` | Created automatically when screenshots or demo captures are saved. |
| `start_kiosk.bat` | Windows shortcut script to run the standalone kiosk server. |

## Quick Start

Use the included virtual environment if it is already present:

```powershell
.\game_env\Scripts\activate
python app.py
```

Or install dependencies into your own Python 3.11 environment:

```powershell
python -m pip install -r requirements.txt
python app.py
```

After the app starts, open these URLs in a browser:

```text
Dashboard: http://127.0.0.1:8765
Group clone: http://127.0.0.1:8765/group-clone
Kiosk demo: http://127.0.0.1:8765/kiosk
Guardian SOS page: http://127.0.0.1:8765/guardian
```

If port `8765` is busy, the app tries the next available port up to `8774`. Check the terminal output for the exact URL.

## Build Windows App

Use the included PyInstaller spec when creating the Windows app:

```powershell
.\build_app.ps1
```

The finished executable is:

```text
output\app\app.exe
```

Important: build with `app.spec` or `build_app.ps1`. A basic auto-py-to-exe/PyInstaller build can miss MediaPipe runtime resources like `hand_landmark_tracking_cpu.binarypb` and `palm_detection_lite.tflite`, which causes `FileNotFoundError: The path does not exist` when the app starts.

## Full Feature List

| Feature | What it does | How to use it |
| --- | --- | --- |
| Biometric gate | Hides the raw camera feed behind a scanner screen until identity is verified. | Start `python app.py`, look at the camera, then show the secret hand sign. |
| Face ID | Verifies the authorized user before gestures can control the system. | Press `E` to enroll your face if needed. Existing local profile is loaded from `known_faces/`. |
| Eye check | Confirms eyes are visible before allowing unlock. | Keep your face clearly visible with good lighting. |
| Secret hand sign | Second factor after Face ID. | Raise index and pinky fingers, fold middle and ring fingers. |
| MediaPipe hand tracking | Detects 21 hand landmarks in real time. | Keep one hand clearly visible inside the camera frame. |
| Adaptive pinch intelligence | Automatically adjusts pinch threshold based on hand size/distance from camera. | No manual setup needed. Move your hand naturally closer or farther. |
| Smooth cursor control | Maps index finger movement to screen cursor movement. | Use Touch Mode and move your index finger. |
| Stable keyboard mode control | Prevents accidental mode changes when the hand is too close to the camera. | Press `1`, `2`, or `3` to select a mode directly. |
| Media Mode | Gesture controls for system volume. | Middle raises volume, ring lowers volume. |
| Navigation Mode | Gesture controls for slide navigation and finger-based scrolling. | Move index left/right to change slides; use middle/ring for scroll. |
| Touch Mode | Gesture controls for kiosk/buttons/web pages. | Move cursor with index finger, swipe left/right to slide, use hover tap or pinch shortcuts. |
| Touch pinch shortcuts | Uses strict thumb-finger contact for media/tab actions. | Thumb + index toggles video play/pause; thumb + middle closes the current YouTube/browser tab. |
| Virtual touch | Taps a screen target after a steady hover. | In Touch Mode, hold index finger steady over a button for about `0.75s`. |
| Single-finger controls | Uses single raised fingers for easier demo operation. | Raise only the required finger for the current mode. |
| Legacy pinch fallback | Keeps older thumb + finger pinch gestures working. | Pinch thumb with index/middle/ring/pinky depending on action. |
| Voice assistant | Opens websites, apps, searches, controls tabs, types text, and changes modes. | Speak commands such as `youtube open karo`, `search python tutorial`, or `touch mode`. |
| Voice feedback | Speaks important events like unlock and mode switch. | Works automatically through Windows SAPI, `pyttsx3`, or PowerShell speech fallback. |
| Guardian SOS Mode | Demo emergency workflow with screenshot, dashboard alert, and command center page. | Say `guardian sos`, `emergency`, or `help me`. Clear with `clear sos`. |
| Live dashboard | Shows mode, FPS, lock state, hand detection, gesture, voice status, and SOS state. | Open `http://127.0.0.1:8765`. |
| Touchless kiosk demo | Real browser demo surface for public-service touchless interaction. | Open `/kiosk`, switch to Touch or Navigation Mode, and click buttons with gestures. |
| Demo capture | Saves current camera/HUD frame. | Press `S`. Files are saved in `captures/`. |
| Manual presenter controls | Helps during live presentation. | Use `L`, `N`, `F`, `M`, `+`, `-`, `R`, `Q`, or `Esc`. |
| Safe shutdown | Releases camera and closes windows cleanly. | Press `Q`, `Esc`, or close the OpenCV window. |

## How To Use The Main App

1. Connect a webcam and microphone.
2. Run `python app.py`.
3. Wait for the JARVIS scanner window.
4. Open the dashboard URL shown in the terminal.
5. Face the camera until Face ID is verified.
6. Show the secret hand sign: index and pinky up, middle and ring folded.
7. After unlock, use gestures or voice commands.
8. Press `1`, `2`, or `3` to select a mode directly. Press `N` only if you want to cycle modes.
9. Press `L` to relock the system during a demo.
10. Press `Q` or `Esc` to exit.

## Biometric Unlock Flow

| Step | Requirement | Status shown |
| --- | --- | --- |
| 1 | App starts locked | `SYSTEM LOCKED` |
| 2 | Face is detected | `Face ID required` |
| 3 | Authorized face matches | `Yashwant verified` |
| 4 | Eyes are visible | `Eye check pass` |
| 5 | Secret hand sign is shown | `Identity verified` |
| 6 | Control modes activate | `MEDIA MODE`, `NAVIGATION MODE`, or `TOUCH MODE` |

If Face ID is not enrolled, press `E` while your face and eyes are visible. The app saves a local Face ID profile in `known_faces/`.

## Gesture Controls

### Global Gestures

| Gesture | Action |
| --- | --- |
| Face match + eye check + index/pinky hand sign | Unlock system |
| `1` / `2` / `3` keys | Select Media / Navigation / Touch Mode directly |
| Voice command `media`, `navigation`, or `touch` | Select the spoken mode directly |
| Pinky mode switch | Disabled by default for hackathon stability |
| Index finger movement in Touch Mode | Move mouse cursor |
| `Q` or `Esc` key | Exit app |

### Media Mode

| Gesture | Action |
| --- | --- |
| Middle finger only | Volume up |
| Ring finger only | Volume down |
| Thumb + middle pinch | Volume up fallback |
| Thumb + ring pinch | Volume down fallback |

### Navigation Mode

| Gesture | Action |
| --- | --- |
| Index finger moves left | Previous slide / left arrow |
| Index finger moves right | Next slide / right arrow |
| Middle finger only | Scroll up |
| Ring finger only | Scroll down |
| Thumb + middle pinch | Scroll up fallback |
| Thumb + ring pinch | Scroll down fallback |

### Touch Mode

| Gesture | Action |
| --- | --- |
| Index finger movement | Move mouse cursor |
| Index finger swipe left/right | Previous/next slide or left/right arrow. |
| Steady index hover | Virtual touch tap |
| Thumb + index pinch | Video play / pause |
| Thumb + middle pinch | Close current YouTube/browser tab |

## Keyboard Demo Controls

| Key | Action |
| --- | --- |
| `1` | Select Media Mode. |
| `2` | Select Navigation Mode. |
| `3` | Select Touch Mode. |
| `S` | Save demo screenshot/HUD frame into `captures/`. |
| `E` | Enroll or re-enroll Face ID. |
| `L` | Relock the security system. |
| `N` | Cycle to the next mode manually. |
| `F` | Toggle fullscreen scanner window. |
| `M` | Minimize scanner window. |
| `+` / `=` | Increase scanner window size. |
| `-` / `_` | Decrease scanner window size. |
| `R` | Restore scanner window size. |
| `Q` or `Esc` | Exit safely. |

## Voice Commands

Voice input uses Hindi-English friendly commands with `en-IN`, `hi-IN`, and `en-US` recognition. Search/open style commands can become Google searches; unmatched commands are rejected instead of running arbitrary shell commands.

### Website And Search Commands

| Example command | Action |
| --- | --- |
| `youtube open karo` | Opens YouTube. |
| `youtube par lo-fi music search karo` | Searches YouTube. |
| `arijit song chalao` | Searches YouTube for the requested song/music. |
| `lo-fi music bajao` | Searches YouTube for the requested music. |
| `search python tutorial` | Searches Google. |
| `mujhe weather today search karna hai` | Searches Google. |
| `gmail open karo` | Opens Gmail. |
| `google open karo` | Opens Google. |
| `github open karo` | Opens GitHub. |
| `whatsapp open karo` | Opens WhatsApp Web. |
| `chatgpt open karo` | Opens ChatGPT. |

### App Launch Commands

| Example command | Action |
| --- | --- |
| `notepad open karo` | Opens Notepad. |
| `calculator open karo` | Opens Calculator. |
| `paint open karo` | Opens Paint. |
| `camera open karo` | Opens Windows Camera. |
| `settings open karo` | Opens Windows Settings. |
| `explorer open karo` | Opens File Explorer. |
| `file explorer open karo` | Opens File Explorer. |
| `cmd open karo` | Opens Command Prompt. |
| `command prompt open karo` | Opens Command Prompt. |
| `powershell open karo` | Opens PowerShell. |
| `chrome open karo` | Opens Chrome if installed. |
| `edge open karo` | Opens Microsoft Edge. |
| `word open karo` | Opens Microsoft Word if installed. |
| `microsoft word open karo` | Opens Microsoft Word if installed. |
| `excel open karo` | Opens Microsoft Excel if installed. |
| `microsoft excel open karo` | Opens Microsoft Excel if installed. |
| `powerpoint open karo` | Opens Microsoft PowerPoint if installed. |
| `power point open karo` | Opens Microsoft PowerPoint if installed. |
| `vs code open karo` | Opens Visual Studio Code if installed. |
| `visual studio code open karo` | Opens Visual Studio Code if installed. |
| `spotify open karo` | Opens Spotify if installed. |
| `vlc open karo` | Opens VLC if installed. |
| `zoom open karo` | Opens Zoom if installed. |
| `teams open karo` | Opens Microsoft Teams if installed. |
| `microsoft teams open karo` | Opens Microsoft Teams if installed. |
| `discord open karo` | Opens Discord if installed. |
| `obs open karo` | Opens OBS if installed. |

The app also scans Windows Start Menu shortcuts, so many installed apps can open even if they are not in the built-in alias list.

### Keyboard And Browser Voice Commands

| Example command | Action |
| --- | --- |
| `volume up` | Presses system volume up. |
| `awaz badhao` / `sound badhao` | Presses system volume up. |
| `volume down` | Presses system volume down. |
| `awaz kam` / `sound kam` | Presses system volume down. |
| `mute` | Toggles mute. |
| `play` / `pause` | Toggles play/pause. |
| `ye video chalao` | Opens the selected/current video or result by pressing Enter. |
| `selected result kholo` | Opens the currently selected result by pressing Enter. |
| `new tab` | Opens new browser tab. |
| `close tab` | Closes current browser tab. |
| `next tab` | Switches to next browser tab. |
| `previous tab` | Switches to previous browser tab. |
| `back jao` / `piche jao` | Goes back in the browser with `Alt + Left`. |
| `forward jao` / `aage jao` | Goes forward in the browser with `Alt + Right`. |
| `refresh` / `reload` | Reloads the page. |
| `search bar` / `address bar` | Focuses the browser search/address bar. |
| `close window` | Sends `Alt + F4`. |
| `enter` | Presses Enter. |
| `backspace` | Presses Backspace. |
| `scroll up` | Scrolls up. |
| `scroll down` | Scrolls down. |
| `slide left` | Presses left arrow. |
| `slide right` | Presses right arrow. |
| `left arrow` | Presses left arrow. |
| `right arrow` | Presses right arrow. |
| `screenshot` | Saves screenshot in `captures/`. |
| `type hello world` | Types `hello world` into the active field. |
| `write hello world` | Types `hello world` into the active field. |

### Mode Voice Commands

| Command | Action |
| --- | --- |
| `media` | Switches to Media Mode. |
| `media mode` | Switches to Media Mode. |
| `navigation` / `nav` | Switches to Navigation Mode. |
| `navigation mode` | Switches to Navigation Mode. |
| `touch` | Switches to Touch Mode. |
| `touch mode` | Switches to Touch Mode. |

### Guardian SOS Voice Commands

| Command | Action |
| --- | --- |
| `guardian sos` | Activates Guardian SOS. |
| `emergency` | Activates Guardian SOS. |
| `help me` | Activates Guardian SOS. |
| `bachao` | Activates Guardian SOS. |
| `madad` | Activates Guardian SOS. |
| `medical help` | Activates Guardian SOS. |
| `clear sos` | Clears SOS state. |
| `cancel sos` | Clears SOS state. |
| `stop sos` | Clears SOS state. |

## Guardian SOS Mode

Guardian SOS Mode is a demo-ready accessibility and safety workflow. It does not call real emergency services automatically.

When activated, it:

- Saves an emergency screenshot in `captures/`.
- Opens the local command center at `/guardian`.
- Updates dashboard telemetry to `SOS ACTIVE`.
- Stores trigger phrase, time, selected mic, and capture path.
- Announces the alert using text-to-speech.

Use `clear sos` to return the dashboard to standby state.

## Live Dashboard

The app starts a local dashboard server using Python's built-in HTTP server.

| URL | Purpose |
| --- | --- |
| `/` or `/dashboard` | Main JARVIS live dashboard. |
| `/api/status` | JSON telemetry endpoint. |
| `/api/mode?mode=touch` | Server mode-control endpoint. Replace `touch` with `media` or `navigation`. |
| `/group-clone` or `/project_clone_group.html` | Group project clone page with team members and problem statements. |
| `/kiosk` or `/kiosk_demo.html` | Touchless kiosk demo page. |
| `/guardian` | Guardian SOS command center. |

Dashboard panels show:

- Current mode
- Lock/unlock state
- FPS
- Last action
- Hand detected or waiting
- Current gesture
- Pinch/action status
- Virtual touch state
- Control quality
- Action count
- Adaptive pinch value
- Hand scale
- Last capture path
- Face ID status
- Eye check status
- Hand sign status
- Active Face ID engine
- Voice assistant state
- Voice mic
- Voice feedback state
- Guardian SOS state

## Touchless Kiosk Demo

The kiosk demo is designed to show a real-world use case for the AI Vision Controller.

Kiosk sections:

| Section | Demo actions |
| --- | --- |
| Hospital Help | Call nurse, emergency help, medicine schedule, doctor timing. |
| Classroom Control | Next slide, previous slide, play/pause lecture, start quiz. |
| Smart Home | Toggle lights, increase fan speed, toggle door lock, adjust AC temperature. |
| Emergency Alert | Activate SOS, call security, open fire safety, reset alert. |
| Information Desk | Campus directions, help desk, event schedule, accessibility services. |

How to demo the kiosk:

1. Run `python app.py`.
2. Open the kiosk URL printed in terminal.
3. Unlock with Face ID plus the secret index+pinky hand sign.
4. Switch to Touch Mode or Navigation Mode.
5. Move the cursor over a kiosk button.
6. Use steady index hover in Touch Mode to tap kiosk buttons.
7. Show the live dashboard updating side-by-side.

To run the project clone and kiosk page without the full AI controller:

```powershell
python kiosk_server.py
```

Then open:

```text
http://127.0.0.1:8765/kiosk
http://127.0.0.1:8765/group-clone
```

## Software And Engines Used

| Software / engine | Where used | How it works in this project |
| --- | --- | --- |
| Python 3.11 | Entire project | Main programming language used to connect camera, AI models, OS input, voice, and local web server. |
| OpenCV | Camera, image processing, HUD, Face ID fallback | Reads webcam frames, flips/resizes images, draws the scanner/HUD, detects face/eyes using Haar cascades, and runs LBPH Face Recognizer when optional `face_recognition` is unavailable. |
| OpenCV Contrib Face Recognizer | Face ID fallback | Uses `cv2.face.LBPHFaceRecognizer_create()` to train a local authorized-user face model from camera frames. |
| MediaPipe Hands | Hand tracking | Detects 21 hand landmarks per frame. The app reads finger tip and joint positions to identify raised fingers, pinches, movement direction, and secret hand sign. |
| NumPy | Math and coordinate processing | Calculates interpolation, clipping, arrays, thresholds, hand scale, and face training labels. |
| PyAutoGUI | OS control | Moves the mouse, clicks, scrolls, presses media keys, types text, sends hotkeys, and saves screenshots. |
| SpeechRecognition | Speech-to-text | Converts captured microphone audio into text using Google recognition with `en-IN` language. |
| sounddevice | Microphone capture | Records raw microphone audio without requiring PyAudio. It also lets the app prefer noise-cancelling virtual microphones. |
| pyttsx3 | Voice output fallback | Speaks status messages such as mode changes if Windows SAPI direct access is unavailable. |
| pywin32 / Windows SAPI | Voice output primary path | Uses Windows `SAPI.SpVoice` for reliable text-to-speech on Windows. |
| PowerShell Speech | Voice output final fallback | Uses `.NET System.Speech` through PowerShell if SAPI and `pyttsx3` fail. |
| Protobuf | MediaPipe dependency | Helps MediaPipe store and exchange model/config data internally. |
| Python `http.server` | Dashboard and kiosk server | Runs a local server on `127.0.0.1` to serve dashboard HTML, kiosk HTML, Guardian page, and JSON telemetry. |
| Python `threading` and `queue` | Background workers | Keeps voice feedback, voice listening, and dashboard serving from blocking the camera loop. |
| Python `webbrowser`, `subprocess`, and `os` | App and website launching | Opens supported websites, launches whitelisted apps, and scans Start Menu shortcuts. |
| HTML/CSS/JavaScript | Dashboard and kiosk UI | Builds responsive browser pages and kiosk button interactions. |
| Optional `face_recognition` | Face ID optional engine | If installed, the app uses face embeddings and distance matching. If not installed, it automatically falls back to OpenCV LBPH. |

## Engine Details

### Camera Engine

The app opens webcam index `0` with OpenCV:

- Target resolution: `640x480`
- Target FPS: `30`
- Camera buffer: `1` frame for lower latency

Each frame is flipped horizontally so hand movement feels like a mirror.

### Hand Tracking Engine

MediaPipe gives 21 landmarks for the detected hand. The app checks important points:

- Index tip and joints
- Middle tip and joints
- Ring tip and joints
- Pinky tip and joints
- Thumb tip
- Wrist and palm points

Finger state is calculated by comparing fingertip height with finger joint height. For example, index finger is considered raised when the index tip is above the index joint in the camera frame.

### Adaptive Pinch Engine

The app measures palm size using wrist, middle MCP, index MCP, and pinky MCP points. It then scales pinch threshold between:

```text
Minimum: 28 px
Default reference: 40 px
Maximum: 76 px
Scale factor: 0.42
```

This helps pinches work even when the hand is closer or farther from the camera.

### Action Cooldown Engine

Each repeated action has a cooldown to prevent accidental multiple triggers.

Examples:

| Action | Cooldown |
| --- | --- |
| Touch tap | `0.55s` |
| Touch-mode play/pause | `0.45s` |
| Touch-mode tab close | `0.80s` |
| Volume up/down | `0.18s` |
| Slide left/right | `0.32s` |

### Face ID Engine

The app supports two Face ID paths:

1. **Optional `face_recognition` engine:** Uses face embeddings saved in `known_faces/yashwant_encoding.npy`.
2. **OpenCV LBPH fallback:** Uses `known_faces/yashwant_lbph.yml`.

The current project already includes an OpenCV LBPH profile file. If a new profile is needed, press `E` while your face and eyes are visible.

### Eye Check Engine

OpenCV Haar cascades detect eyes inside the upper face region. The app requires at least one visible eye before enrollment or verification continues.

### Voice Assistant Engine

The voice assistant:

1. Picks a microphone.
2. Prefers microphones containing names like `Krisp`, `NVIDIA Broadcast`, `Broadcast`, `Sonar`, `SteelSeries`, or `ClearCast`.
3. Calibrates ambient noise.
4. Records a phrase.
5. Sends audio to SpeechRecognition's Google recognizer.
6. Matches the text against a safe command list.
7. Runs the matching browser/app/keyboard/search action.

Search/open style commands can become Google searches. Other unmatched commands are rejected, not run as shell commands.

### Voice Feedback Engine

The app tries speech output in this order:

1. Windows SAPI through `pywin32`
2. `pyttsx3`
3. PowerShell `.NET System.Speech`

Speech runs in a background queue so the main camera loop does not freeze.

### Dashboard Telemetry Engine

The app stores status in a thread-safe `TELEMETRY` dictionary. The dashboard calls `/api/status` every `700ms` and updates the browser UI.

### Input Control Engine

PyAutoGUI is used for:

- Mouse movement
- Left click
- Scroll
- Keyboard keys
- Browser tab hotkeys
- System media keys
- Screenshot capture
- Typing dictated text

For demo speed, PyAutoGUI pause and minimum sleep are set to zero.

## Requirements

From `requirements.txt`:

```text
opencv-contrib-python==4.13.0.92
mediapipe==0.10.5
pyautogui==0.9.54
pyttsx3==2.99
SpeechRecognition==3.16.1
sounddevice==0.5.5
pywin32==311
protobuf==3.20.3
numpy==2.4.4
pyinstaller==6.20.0
```

Recommended system:

- Windows 10 or Windows 11
- Python 3.11
- Webcam
- Microphone
- Browser
- Good front lighting for Face ID
- Optional noise-cancelling virtual mic software such as NVIDIA Broadcast, Krisp, SteelSeries Sonar, or ClearCast

## Face ID Setup

Use any one method:

1. Press `E` in the scanner window while your face and eyes are visible.
2. Keep the existing `known_faces/yashwant_lbph.yml` file.
3. Optional advanced path: install `face_recognition`, place `known_faces/yashwant.jpg`, and let the app create `known_faces/yashwant_encoding.npy`.

Optional `face_recognition` requires `dlib`. On Windows, `dlib` may need Visual Studio Build Tools with Desktop development with C++.

```powershell
python -m pip install face_recognition
```

If this fails, keep using the OpenCV LBPH fallback. The project works without `face_recognition`.

## Noise Cancellation Setup

For better voice control during a live demo:

1. Install NVIDIA Broadcast, Krisp, SteelSeries Sonar, or another virtual noise-cancelling microphone.
2. Enable the cleaned microphone in Windows input settings.
3. Run `python app.py`.
4. Check the dashboard `Voice Mic` panel.
5. Speak close to the mic for best recognition.

Voice recognition uses the online Google recognizer through `SpeechRecognition`, so internet access is needed for voice-to-text.

## Hackathon Demo Flow

1. Start `python app.py`.
2. Open the project clone, dashboard, and kiosk URLs.
3. Show the dashboard locked state.
4. Face the camera and show the biometric scanner.
5. Unlock with Face ID plus secret hand sign.
6. Show direct mode switching with keys `1`, `2`, `3` and voice commands such as `touch` or `media`.
7. In Media Mode, show volume up and volume down gestures.
8. In Navigation Mode, switch slides with index left/right and scroll with middle/ring gestures.
9. In Touch Mode, show smooth index movement, left/right slide, thumb+index play/pause, and thumb+middle tab close.
10. Say `youtube open karo` or `search python tutorial`.
11. Say `guardian sos` and show the Guardian command center.
12. Say `clear sos`.
13. Press `S` to save a demo capture.
14. Press `L` to relock.
15. Press `Q` or `Esc` to exit.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Webcam not found | Close other camera apps, check camera permission, reconnect webcam, then restart `python app.py`. |
| Face ID not verifying | Improve lighting, face the camera directly, press `E` to re-enroll. |
| Eye check failing | Keep eyes visible, remove dark glasses, improve lighting. |
| Gesture not detected | Keep one hand inside frame, avoid busy background, keep fingers clearly separated. |
| All gesture nodes appear active together | Move your hand back from the camera. The app blocks actions when hand scale is too large and gesture-based mode switching is disabled by default. |
| Click triggers too often | Use slower gestures; cooldowns are built in but fast repeated poses can still trigger after cooldown. |
| Voice not listening | Check Windows microphone permissions and dashboard `Voice Mic` panel. |
| Voice commands fail | Check internet connection because Google recognition is online. |
| App launch command fails | Make sure the target app is installed or has a Start Menu shortcut. |
| Dashboard not opening | Check terminal for the actual port. It may be `8766`, `8767`, etc. |
| Kiosk page not found | Make sure `kiosk_demo.html` exists in the project folder. |
| `face_recognition` install fails | Use the built-in OpenCV LBPH fallback or install Visual Studio Build Tools first. |

## Safety Notes

- Guardian SOS is a demonstration workflow. It does not call real emergency services.
- Unmatched voice commands are rejected instead of being executed as system commands.
- The app disables PyAutoGUI failsafe for smoother gesture control, so use `Q`, `Esc`, or close the OpenCV window to stop safely.
- Voice typing writes into the active focused field. Click the correct field before using `type ...` commands.

## Current Tested Status

Local smoke checks passed:

- Python syntax compile for `app.py` and `kiosk_server.py`.
- Dependency check with `pip check`.
- Core imports for OpenCV, MediaPipe, PyAutoGUI, NumPy, speech, mic, and Windows voice modules.
- Webcam opened and returned a `640x480` frame.
- Dashboard endpoint returned HTTP `200`.
- Kiosk endpoint returned HTTP `200`.
- Guardian endpoint returned HTTP `200`.
- Full app telemetry reached `RUNNING` with locked state and live FPS.
