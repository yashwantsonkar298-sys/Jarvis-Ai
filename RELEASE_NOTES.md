# JARVIS AI Vision Controller - Hackathon Release

## Release Status

This release is ready for local demo use on Windows with webcam, microphone, and Python dependencies installed.

## Included Features

- 2FA biometric gate with Face ID, eye check, and secret hand sign.
- MediaPipe hand tracking with optimized low-latency settings.
- Adaptive Gesture Intelligence that scales pinch thresholds from hand geometry.
- Single-finger control mapping for easier operation.
- Navigation Mode index gestures: up/down scroll and left/right slide.
- Touch Mode hover tap and pinch shortcuts.
- Voice assistant with YouTube, Google search, browser controls, media controls, app launch, typing, screenshots, and mode switching.
- Guardian SOS Mode with voice trigger, emergency command center, screenshot capture, dashboard alert state, and clear command.
- Automatic preference for noise-cancelling virtual microphones such as NVIDIA Broadcast, Krisp, Sonar, SteelSeries, and ClearCast.
- Start Menu app scanning plus built-in aliases for common apps.
- Live local dashboard with security, hand tracking, action, voice, microphone, and mode telemetry.
- Touchless kiosk demo page.
- Performance tuning: PyAutoGUI delay removed, lightweight hand model, camera buffer reduction, cached face cascades, and OpenCV optimization.

## Demo Commands

```text
youtube open karo
youtube par lo-fi music search karo
search python tutorial
notepad open karo
vs code open karo
volume up
new tab
close tab
scroll down
slide right
type hello everyone
screenshot
navigation mode
touch mode
guardian sos
clear sos
```

## Run

```powershell
python -m pip install -r requirements.txt
python app.py
```

## Demo Notes

- For best voice quality, use NVIDIA Broadcast with an RTX laptop GPU and select the NVIDIA Broadcast microphone in Windows input settings.
- For long distance voice control, use a Bluetooth headset, lapel mic, or collar mic. Software noise cancellation cannot fully replace a close microphone.
- Projector auto-connect is intentionally not included. Use Windows `Win + K` manually before the demo for reliable setup.

## Known Limits

- Voice recognition uses online Google recognition through SpeechRecognition, so internet is required.
- Arbitrary system commands are not allowed for safety. Unknown voice commands fall back to Google search.
- Some app launch commands depend on installed app paths or Start Menu shortcuts.
- Face recognition quality depends on lighting and camera quality.

## Future Features

- Offline voice recognition with Whisper or Vosk.
- Wake word support such as "Jarvis".
- Voice command confirmation for sensitive actions.
- Custom command profile editor.
- Native Windows `SendInput` engine for faster input than PyAutoGUI.
- App-specific profiles for PowerPoint, browser, media player, and games.
- Gesture calibration screen for each user.
- WebSocket dashboard updates with charts.
- Packaged `.exe` build with PyInstaller.
- Optional mobile remote dashboard.
- Guardian contact profile with opt-in SMS/call integration.
