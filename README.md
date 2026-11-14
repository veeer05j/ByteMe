---
title: DayWeave Clinic Portal
sdk: streamlit
app_file: app.py
pinned: false
---

# DayWeave Clinic Portal

# DayWeave

**Life Powered by Tech — Middlesex University Mauritius**
**Theme 3: Powered to Live Better**

DayWeave is an offline-first health and wellbeing app built for Mauritius. It runs in
the browser, installs on Android as a real APK, and talks to a Groq-hosted AI coach.
No React, no build step, no bundler — plain HTML, CSS and JavaScript.

---

## Features

| Area | What it does |
|---|---|
| Health log | Weight, water, sleep and steps. Saves to `localStorage`. Seven-entry Chart.js trend with sleep on a second axis. |
| Breathing | 4-7-8 guided breathing with an animated circle and phase labels. |
| Medicine reminders | Daily or one-time. Fires a 880 Hz tone, a vibration pattern, a full-screen dialog and a browser notification. Alert history kept. One-time doses are removed after they fire. |
| Appointments | Book against 106 real Mauritian facilities. Stored locally, editable, deletable. |
| Map | Leaflet map of real hospitals, private clinics, Area Health Centres and pharmacies. Opening and closing times, nearest-first sorting, `Nearby (10 km)` and `Across Mauritius` scopes, live 100 m GPS arrival banner. |
| Proximity alerts | If an appointment is close and you are far from the facility, a popup appears with the distance and a mini map. |
| Routines | Daily checklist with a progress bar. Resets automatically at midnight using a local date key, not UTC. |
| Squat counter | Live camera, MediaPipe Pose Landmarker, knee-angle rep detection, sets every ten reps. GPU delegate with CPU fallback. |
| Step counter | Phone accelerometer and gyroscope, noise filtering, batched writes to `localStorage`. |
| AI Coach | Its own tab. Sends the last ten messages to Groq `openai/gpt-oss-20b` through a serverless function. Falls back to a local rule-based reply if the network or the API is unavailable. |

Budgeting is deliberately out of scope.

---

## Tech stack

- HTML5, CSS3, vanilla JavaScript (ES2020)
- [Chart.js 4.4.1](https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js) — health trend
- [Leaflet 1.9.4](https://unpkg.com/leaflet@1.9.4/dist/leaflet.js) — map, OpenStreetMap tiles
- [MediaPipe tasks-vision 0.10.14](https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs) — pose landmarker lite
- [Groq API](https://console.groq.com) — `openai/gpt-oss-20b`
- Vercel — static hosting plus one serverless function
- PWABuilder — Trusted Web Activity packaging

---

## Project structure