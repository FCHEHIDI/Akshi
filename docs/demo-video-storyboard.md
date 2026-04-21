# 🎞️ Demo Video — "The Sentinel's Watch"
> Style : Film muet 1910 · Noir & Blanc · Intertitres victoriens

---

## Workflow de production

1. **Capture écran** → OBS Studio (1920×1080, MP4, une scène à la fois)
2. **Filtre vintage N&B** → RenderForest (template *Vintage Film*) ou DaVinci Resolve
3. **Slides intertitres** → Canva / PowerPoint — fond noir, texte blanc, police **IM Fell English** ou **Playfair Display**, ornements victoriens
4. **Montage final** → DaVinci Resolve — intercaler `[Intertitre] → [Scène] → ...`
5. **Musique** → [incompetech.com](https://incompetech.com) — *"Cinematic Paleo"* de Kevin MacLeod (CC, gratuit) à ~20% de volume

---

## Storyboard (~3 min)

| # | Titre | Intertitre | Action à l'écran | Durée |
|---|-------|-----------|-----------------|-------|
| 0 | Carton d'ouverture | *"Anno Domini MMXXVI — Une époque où les machines veillent sur les machines"* | Fond noir, texte centré, ornements | 0:00–0:10 |
| 1 | The Threat | *"Vos services périssent dans l'obscurité — et nul ne vous en avertit"* | Écran noir → fondu vers login | 0:10–0:20 |
| 2 | The Threshold | *"L'Accès aux Chambres du Contrôle"* | Page login → saisie lente → entrée dashboard | 0:20–0:35 |
| 3 | The Observatory | *"D'un seul regard — l'état de l'Empire tout entier"* + *"Quatre vérités : Services · Santé · Incidents · Vélocité"* | Dashboard — panoramique sur KPI cards + grille services | 0:35–1:05 |
| 4 | The Subjects | *"Trois automates sous surveillance permanente"* + *"L'un d'eux est... peu fiable"* | Page `/services` — zoom sur flaky-service | 1:05–1:25 |
| 5 | The Vigil | *"Chaque trente secondes — l'automate sonde, mesure, juge"* | Page `/checks` — badge rouge d'un check échoué | 1:25–1:50 |
| 6 | The Alarm | *"L'Incident — né dans l'ombre, révélé sans délai"* + *"Un homme se lève — 'J'en prends connaissance'"* | Page `/incidents` filtrée open → clic Acknowledge | 1:50–2:25 |
| 7 | The Resolution | *"L'ordre est restauré — l'incident scellé dans les archives"* + *"L'Empire respire de nouveau"* | Clic Resolve → liste vide → retour dashboard tout vert | 2:25–2:45 |
| 8 | Carton de fin | *"SentinelOps — Gardien des services modernes — Django · Celery · Next.js — Disponible sous peu — en nuage"* | Fond noir, fondu final | 2:45–3:00 |

---

## Checklist avant tournage

- [ ] `docker compose --env-file .env.docker up --build` — stack principale
- [ ] `docker compose -f demo/docker-compose.yml up` — 3 services démo
- [ ] Attendre ~1 min que le flaky-service génère des incidents
- [ ] Vérifier que des incidents *open* sont visibles dans `/incidents`
- [ ] OBS configuré en 1920×1080 MP4
- [ ] Fond d'écran du bureau neutre (noir de préférence)
