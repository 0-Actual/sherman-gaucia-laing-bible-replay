# Q6 Bible Math Merge Web Build V1

Author: Sherman G. Laing  
Generated UTC: 2026-05-03T15:49:26+00:00

## What this package is

This is a runnable local web build around the uploaded `app.js` runtime. The uploaded runtime expects `window.Q6_DATA`, a canvas, controls, node lists, verse selectors, search panels, instrument toggles, and reference image slots. This package supplies those missing parts.

## What is included

- `index.html` — local launch file.
- `scripts/app.js` — uploaded runtime preserved unchanged.
- `scripts/q6_data.js` — Creation Week Q6 data payload for Genesis 1:1–2:3 using WEB text.
- `q6_data.json` — same payload as JSON for inspection.
- `styles/style.css` — responsive visual shell.
- `assets/*.jpg` — local placeholder reference images required by the runtime.
- `manifest.json` — file inventory, hashes, and source-status gates.
- `validation_report.json` — static validation results.

## Source-status truth gate

- Official `Tanach.xml.zip` byte-exact possession is **not claimed** inside this package.
- The official page was observed to list `Tanach.xml.zip` as length `2365002` bytes and SHA-256 `1bc6e006f43d3b18f2f718cefa3aa4774cac2c54092c28d173dd61996c43a050`.
- The runtime payload here uses Creation Week WEB text to make the Q6 interface runnable while the source-critical Hebrew XML gate remains separate.

## Android use

1. Extract the ZIP.
2. Tap `index.html` and open it in Chrome or another browser.
3. Audio requires a user tap on a Play button; browsers block autoplay by design.

## Desktop use

Open `index.html`, or serve the folder locally with any static server.
