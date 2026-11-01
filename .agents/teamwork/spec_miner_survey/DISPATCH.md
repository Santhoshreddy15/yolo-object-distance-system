# Dispatch: API & Calibration Spec Miner

## 2026-11-01T05:06:31Z
You are the API & Calibration Spec Miner for the YOLO object distance estimation system survey phase.
Your working directory is: C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\spec_miner_survey
Project root: C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system

MANDATORY: You MUST read ORIGINAL_REQUEST.md before starting work:
Path: C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\ORIGINAL_REQUEST.md

Task:
1. Inspect the codebase to extract all API specifications:
   - All REST endpoints, HTTP methods, route paths.
   - Request payloads, content types supported (multipart/form-data, application/json, Base64 data URLs, raw binary, image/jpeg, image/png, image/webp).
   - Response structures, field names, data types, units of distance (meters, cm, mm).
   - Error handling: HTTP status codes, error payload format, how 0 objects, invalid coords, corrupted images, missing calibration parameters are handled.
2. Inspect the camera calibration and monocular distance estimation specification:
   - What mathematical formulas, pinhole models, focal lengths, real-world object class dimensions/priors, or calibration matrix parameters are used.
   - What reference scenes or test scenes exist, or what formulas govern ground truth distance verification.
3. Write your complete, detailed specification report to:
   C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\spec_miner_survey\analysis.md
4. Also write your handoff report to:
   C:\Users\macha\.gemini\antigravity\scratch\yolo-object-distance-system\.agents\teamwork\spec_miner_survey\handoff.md
5. When done, notify the orchestrator (conversation ID: 6bfc04fe-19d9-4c4a-8967-c21e967d520b) via send_message.
