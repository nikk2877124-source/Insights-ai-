# InsightAI Streamlit SaaS Frontend - TODO

## Plan confirmation
- [x] Gather backend endpoint contract (auth/datasets/cleaning/ai)
- [ ] Create Streamlit SaaS frontend skeleton matching the requested folder structure

## Core implementation
- [ ] Add `frontend/app.py` (global theme, navigation layout, auth gating)
- [ ] Implement `frontend/api/client.py` with JWT-based methods
- [ ] Implement session + auth helpers in `frontend/utils/`
- [ ] Create reusable UI components in `frontend/components/`:
  - [ ] metric cards
  - [ ] chart cards
  - [ ] AI response cards
  - [ ] loading spinner
  - [ ] sidebar + navbar

## Pages
- [ ] Dashboard page (kpi cards + recent activity)
- [ ] Upload Dataset page (drag/drop upload, progress, preview)
- [ ] Dataset Profile page (missing values, types, distributions, quality score/grade)
- [ ] AI Summary page (call /ai/dataset-summary)
- [ ] AI Cleaning page (call /ai/interpret-prompt then /cleaning/start)
- [ ] Comparison page (before/after KPIs + charts)
- [ ] Business Insights page (call /ai/business-insights)
- [ ] AI Chat page (chat UI + history via /ai/chat/history/{dataset_id})
- [ ] Downloads page (original + cleaned downloads)

## Styling
- [ ] Implement dark glassmorphism theme in `frontend/assets/styles.css`
- [ ] Wire CSS into Streamlit

## Requirements + run
- [ ] Add `frontend/requirements.txt`
- [ ] Provide run instructions
- [ ] Sanity test by running Streamlit and calling backend endpoints

