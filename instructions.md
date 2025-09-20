# Expansi: The AI Layer for Sustainable Seas!

**Mission:**  
Detect and flag illegal, unreported, and unregulated (IUU) fishing and maritime pollution by fusing AIS, satellite, and ocean data. Deliver actionable alerts to authorities.

---

## Core Users
- **Coast Guard & Maritime Enforcement:** Operations centers, patrol units
- **NGOs & Researchers:** Monitoring IUU fishing and Marine Protected Areas (MPAs)
- **Commercial Partners:** ESG compliance, fleet risk scoring
.
---

## Problem Statement
Many vessels broadcast AIS, but offenders spoof or go dark. Reconciling declared identity and behavior with satellite observations is challenging. Laws vary by zone and fishery. Authorities need high-signal alerts, not raw data firehoses.

---

## Hackathon MVP Scope
- Ingest AIS and at least one satellite signal
- Basic vessel classification and anomaly detection
- Overlay legal zones
- Generate and log alerts with confidence scores
- Simple map UI
- Voice agent to call out alerts

---

## Key Data Sources

- **AIS:** Position, MMSI, speed/course/heading, timestamp, vessel name/type
- **Satellite:**  
  - SAR (Sentinel-1): Night/cloud, detects metal hulls  
  - Optical (Sentinel-2, Landsat): Daytime visual  
  - Nighttime lights (VIIRS): Fishing light clusters
- **Ocean/Environmental:**  
  - Bathymetry (GEBCO)  
  - Sea Surface Temperature (SST)  
  - Chlorophyll (MODIS/VIIRS)  
  - Wind/wave (ERA5, optional)
- **Geofences/Law Polygons:**  
  - Baselines, territorial sea (12nm), contiguous zone (24nm), EEZ (200nm), high seas, MPAs, seasonal closures, gear restrictions
- **Ports & Anchorages**
- **Optional:** VMS/LRIT, RFMO registries, whitelists/blacklists

---

## Features to Engineer (Model Inputs)

- **Vessel Kinematics:** Speed profile, acceleration, course changes, loitering, track gaps
- **Spatial Context:** Distance to port, EEZ/MPA membership, boundary proximity, bathymetry, SST, chlorophyll
- **Temporal:** Local time, day of week, season, closed season flags
- **Behavior Patterns:**  
  - "Fishing-like": Slow (2–5 kn), frequent heading changes  
  - Transshipment proximity  
  - Rendezvous events (two tracks within X nm for Y min)
- **Identity Integrity:** AIS on/off, MMSI reuse, callsign/name collisions, spoofing
- **Satellite Reconciliation:**  
  - SAR/optical detections overlapping dark/false AIS  
  - "Ghost" detections (no AIS nearby)

---

## ML Tasks

- **Vessel Activity Classification:** Fishing, transit, loitering, transshipment (GBDT baseline, optional LSTM/transformer)
- **Vessel Type Classification:** Trawler, longliner, purse seiner, tanker, cargo, tug, etc. (kinematics + AIS type + length estimate)
- **Anomaly Detection:** Isolation forest or deep SVDD on track features (flags dark activity, boundary hugging, odd speed/heading)
- **Fusion Model:** Match SAR/optical detections to AIS tracks (nearest neighbor in space-time, motion model, match probability)
- **Risk Scoring:** Combine activity class, anomaly score, legal-zone conflicts, fusion mismatch into a 0–100 priority score

---

## Labels & Heuristics (Hackathon)

- **Fishing-like:** Speed 1–6 kn, high heading variance ≥30 min
- **Transshipment-like:** Two vessels <1 nm, relative speed <1 kn for ≥45 min outside port
- **Dark:** AIS gap >60 min with satellite detection in gap area
- **Zone Violation:** Activity=fishing, location in closed zone

---

## System Architecture (High Level)

**Data Ingestion**
- AIS stream (websocket/Kafka) + batch backfill
- Satellite detections fetcher (prebaked CSV/GeoJSON)
- Environmental tiles (SST/chl) via raster sampling

**Processing**
- Track builder (per-MMSI, time-ordered, interpolate gaps)
- Feature service (compute features per window)
- Fusion service (associate satellite spots to tracks)
- Rules engine (legal overlays, business rules)
- Model service (activity/type/anomaly inference)

**Storage**
- MongoDB: vessels, positions, tracks, detections, alerts, reports, voice_logs, law_zones, users, roles

**API Gateway**
- Auth0-protected REST endpoints

**UI**
- 3D globe + 2D mini-map (AIS, satellite hits, zones, alerts)

**Voice Agent**
- Inbound: Watch alert stream, auto-generate call scripts
- Outbound: Simulate coast guard calls, log transcripts

**Reporting**
- Cerebras GenAI summary over last 24h/7d alerts (with reasoning/links)

**Search/Legal Context**
- Exa: Retrieve relevant regulations for zone/activity
- Gemini: Q&A over fetched regs + context graph

**Ops**
- Simple k8s or docker-compose; background workers for model inference

---

## Auth & Authorization (Auth0)

- **Roles:** viewer, analyst, operator, admin, hq_clearance
- **Resource-based access:** EEZs, fleets, /reports scoped to clearance
- **Claims:** allowed_zone_ids, allowed_fleet_ids

---

## Key API Endpoints (Sketch)

- `POST /ingest/ais` — [{mmsi, lat, lon, sog, cog, ts, heading, name, type}]
- `POST /ingest/sat` — [{det_id, lat, lon, ts, sensor, rcs, conf}]
- `GET /vessels/:mmsi` — Profile, latest pos, risk_score
- `GET /vessels/:mmsi/tracks?start=…&end=…`
- `GET /zones` — Polygons, metadata
- `GET /classify/activity?mmsi=…&start=…&end=…` — Class timeline
- `POST /fuse` — {det_id, candidate_mmsis:[…]} → best match + prob
- `GET /alerts?zone=…&since=…&min_score=…`
- `POST /alerts/ack` — {alert_id, note}
- `POST /voice/call` — {alert_id, callee}
- `GET /reports/daily` — HTML/PDF summary

---

## MongoDB Schema (Rough)

- **vessels:**  
  `{_id: mmsi, name, ais_type, length_est, flags: [...], last_pos: {lat, lon, ts}, risk_score, history_refs}`
- **positions:**  
  `{_id, mmsi, lat, lon, sog, cog, heading, ts, src: "AIS"}`
- **tracks:**  
  `{_id, mmsi, start_ts, end_ts, feature_summaries: {...}, segments: [{t0, t1, centroid, stats}]}`
- **detections:**  
  `{_id: det_id, lat, lon, ts, sensor, attrs: {rcs, cloud}, matched_mmsi, match_prob}`
- **alerts:**  
  `{_id, type: [...], mmsi, ts, zone_id, details: {...}, priority, acknowledged: boolean}`
- **law_zones:**  
  `{_id: zone_id, name, type: [...], polygon, rules: {...}}`
- **voice_logs:**  
  `{_id, alert_id, ts, transcript, audio_uri, callee, outcome}`
- **reports:**  
  `{_id, ts_range, html_uri, author, clearance}`

---

## Map UI (Hackathon)

- **Left panel:** Filters (zone, time, min risk), legend toggle
- **Center:** 3D globe (Cesium/deck.gl) with AIS tracks, satellite hits, zone overlays
- **Mini 2D inset:** Local tile map for precise clicking
- **Click a spot:** Vessel card (mmsi, type, length, flag state, last 24h track, risk, top reasons)
- **Alert feed:** Rolling list (score, type, sparkline timeline)
- **/reports page:** Rendered Cerebras summaries, export to PDF

---

## Model Details (Minimal Viable)

- **Activity Classifier v0:**  
  - Inputs: 30-min rolling window [mean_sog, std_heading, turn_rate, stop_ratio, nighttime_flag, distance_to_boundary, bathy, sst, chl]  
  - Model: XGBoost  
  - Output: Probabilities for fishing/transit/loiter/transship

- **Fusion Matcher v0:**  
  - Predict vessel position at sat timestamp (last AIS + motion model)  
  - Compute great-circle distance to detection  
  - Logistic regression on distance, speed, heading consistency  
  - Output: match_prob

- **Anomaly Score v0:**  
  - Isolation forest over [gap_duration, boundary_hug, speed_outlier, zigzag_index]  
  - Output: 0–1 score

- **Risk Score:**  
  - `risk = w1*P(fishing_in_restricted) + w2*anomaly + w3*dark_overlap + w4*transshipment_prob`  
  - Weights calibrated by grid search on small labeled set

---

## Satellite Pre-processing (Hackathon Shortcuts)

- Use prebaked CSV of "detections" (lat/lon/ts, confidence) for SAR
- Optical: Use detections from visible boat finder or synthetic points
- Nighttime lights: Simple cluster centroids as "light detections"

---

## Length Estimation

- From AIS static data if present
- From satellite bbox length (if optical sample available)
- Otherwise, infer from speed + sea state heuristics (rough)

---

## Legal Reasoning Flow (Exa + Gemini)

- Use alert context: zone_id, activity, time, gear (if known)
- Exa search:  
  `"site:rfmo.org OR site:fao.org [zone/RFMO name] [activity] fishing regulation"`
- Store top 5 URLs/snippets with timestamps
- Gemini prompt: Build short "legal note" citing zone and rule text
- Attach legal note to alert details and /reports

---

## AI Voice Agent

- Trigger on new high-priority alert
- Draft script: who we are, vessel name/mmsi/position, suspected activity, zone rule, requested action, callback
- TTS to audio file, log transcript in MongoDB
- For demo: Simulate call or use webhook to softphone sandbox; log outcome

---

## Security & Privacy

- Auth0 access tokens required on all endpoints
- Row-level filtering by allowed_zone_ids and clearance
- Redact PII (e.g., phone numbers) in logs
- Signed URLs for report exports

---

## Observability

- Structured logs per alert with trace ID
- Metrics: alerts/day, precision@k, fusion match precision, mean alert-to-ack time, false positive rate by type
- Dashboards: lag, ingest rates, queue depths

---

## Evaluation & Baselines

- **Fishing vs Transit:** Target >0.8 AUROC on small labeled set
- **Fusion Match:** Aim for 90% correct match within 2nm if AIS present in last 20min
- **Dark Detection:** Measure precision against synthetic positives
- **Zone Violation:** Rule-based, measure correctness on handcrafted scenarios

---

## MVP Demo Script

1. Log in as "hq_clearance" via Auth0
2. Globe shows East Pacific; turn on "MPAs" and "dark detections"
3. Click alert "dark_fishing" near MPA boundary; show vessel card, track gap, sat overlap, chlorophyll/SST context
4. Open legal note tab; show reg snippet from Exa+Gemini
5. Hit "notify" to generate voice script/audio; show voice log saved
6. Open /reports and show Cerebras-generated daily summary
