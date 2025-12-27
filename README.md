# Avatar Video AI — Affiliate site (HeyGen)
**Domain:** `https://avatar-video-ai.com`  
**Locales:** EN (x-default) at root, FR under `/fr/`  
**Targets (mobile Lighthouse):** Perf ≥ 90 · SEO ≥ 95 · Accessibility ≥ 95 · Best Practices ≥ 95  
**Core Web Vitals goals:** LCP < 2.5 s · CLS < 0.05

---

## 1) Project structure

/
├─ index.html # EN (x-default)
├─ legal-notice.html # EN (notranslate: no, but legal content only)
├─ privacy-policy.html # EN (notranslate)
├─ blog/
│ ├─ index.html # EN hub
│ └─ heygen-ai-review.html # EN article
├─ fr/
│ ├─ index.html # FR
│ ├─ mentions-legales.html # FR (notranslate)
│ ├─ politique-de-confidentialite.html
│ ├─ sitemap-fr.html # human-readable
│ ├─ sitemap-fr.xml # FR urlset (new)
│ └─ blog/
│   ├─ index.html # FR hub
│   └─ avis-heygen-ai.html # FR article
├─ sitemap-en.xml
├─ sitemap.xml # index of EN/FR sitemaps
├─ robots.txt
├─ assets/
│ ├─ styles.css # source
│ ├─ styles.min.css # shipped
│ ├─ main.js # source
│ └─ main.min.js # shipped
├─ images/ # use ONLY images from provided ZIP
├─ scripts/
│ ├─ appscript-newsletter.js # Google Apps Script (Web App)
│ ├─ ping-indexnow.js # Node postbuild script
│ └─ minify.py # refresh CSS/JS bundles
├─ data/
│ └─ newsletter-template.csv
├─ netlify.toml
├─ _redirects
└─ README.md


---

## 2) Deployment (Netlify)

1. **Create site from folder** (this repo).
2. In **Site settings → Build & deploy → Build settings**:
   - **Build command:** `node scripts/ping-indexnow.js || echo 'IndexNow skipped'`
   - **Publish directory:** `.`
3. **Environment variables** (Netlify UI → Site configuration → Environment):
   - `NODE_VERSION = 18`
   - `INDEXNOW_KEY = <your-indexnow-key>` (enables postbuild ping + root key file)
   - *(Optional)* `BASE_URL = https://avatar-video-ai.com`
   - *(Optional)* `MODIFIED_URLS = https://avatar-video-ai.com/new-page.html,https://avatar-video-ai.com/blog/`
4. **Deploy**. The postbuild will:
   - Generate `/indexnow-<INDEXNOW_KEY>.txt` containing the key.
   - Ping the **IndexNow aggregator**: `https://api.indexnow.org/indexnow` with a batch of URLs.

> **No server-side language redirects.** Locale switching is manual via header/footer links and a *non-blocking* suggestion banner.
>
> CSS/JS workflow: edit `assets/styles.css` or `assets/main.js`, then run `python3 scripts/minify.py` (requires `rcssmin`/`rjsmin`, `pip install --user rcssmin rjsmin`) so the `.min.*` files served in production stay in sync.

---

## 3) Consent, Analytics & Events (GDPR / CNIL)

- **Consent Mode v2** is implemented in `/assets/main.min.js`.
- **GA4** (ID **G-VWL0HBYRC3**) **loads only after explicit opt-in** for the “Analytics” category.
- Consent is stored in `localStorage` for **13 months** (CNIL).
- **reCAPTCHA v3** is *disabled by default* until keys are provided.

### Add/verify GA4
Nothing to add: GA4 is automatically injected once consent is granted.

### Events tracked
- `affiliate_click` (label = URL or data-label)
- `cta_hero_click`
- `video_start`, `video_play`, `video_complete` (YouTube lite)
- `newsletter_submit` (status)
- `faq_toggle` (open/close)
- `scroll_50`
- `read_progress` (blog articles, 10% steps)

---

## 4) Newsletter → Google Sheets (Apps Script)

### A) Prepare Google Sheet
- Create a sheet with tab name `newsletter` *(or modify `SHEET_NAME`)*.
- Import `data/newsletter-template.csv` headers if needed.

### B) Create Apps Script Web App
1. Go to [script.google.com](https://script.google.com) → **New project**.
2. Paste **`scripts/appscript-newsletter.js`** (replace content).
3. **Deploy → New deployment → Web app**  
   - *Execute as:* Me  
   - *Who has access:* Anyone (or Anyone with the link)  
   - Copy the **Web App URL**.

### C) Wire the form
- In **`/blog/index.html`** and **`/fr/blog/index.html`** forms, set attributes:
  ```html
  data-apps-script-url="https://script.google.com/macros/s/AKfycbx.../exec"
  data-sheet-id="YOUR_GOOGLE_SHEET_ID"

Without those values, the form runs in graceful mode (no external calls, friendly message, console log).

D) Test with cURL (optional)

curl -X POST "https://script.google.com/macros/s/AKfycbx.../exec" \
  -H "Content-Type: application/json" \
  -d '{
    "sheetId":"YOUR_SHEET_ID",
    "record":{
      "timestamp":"2025-09-28T12:00:00.000Z",
      "email":"tester@example.com",
      "page":"/blog/heygen-ai-review.html",
      "lang":"en",
      "utm":{"utm_source":"test"},
      "consent":"newsletter"
    }
  }'

CSP note: When you activate your Apps Script, its domain is already whitelisted in netlify.toml (script.google.com & script.googleusercontent.com). If you proxy or change domains, add the exact origin to connect-src.

5) IndexNow (fast indexing)

Script: scripts/ping-indexnow.js

Endpoint: https://api.indexnow.org/indexnow (aggregator)

Root key file generated: /indexnow-<INDEXNOW_KEY>.txt

Add recently modified URLs via MODIFIED_URLS env var (CSV).

6) SEO & i18n

Unique titles/descriptions per page & language; one H1 per page.

hreflang on every page (EN↔FR + x-default to EN).

Canonical: self-referential.

Sitemaps:

/sitemap.xml → index of /sitemap-en.xml and /fr/sitemap-fr.xml

Open Graph / Twitter localized: en_US / fr_FR.

JSON-LD:

Organization (publisher = Avatar Video AI)

FAQPage (content provided in EN/FR)

BreadcrumbList (all except home)

Article (blog posts)

Robots: robots.txt provided; UTM & click IDs normalized (Yandex Clean-param).

7) Performance & Accessibility

LCP: hero <picture> with fixed width/height + fetchpriority="high".

All images use <picture> / img with loading="lazy", decoding="async", explicit dimensions.

YouTube Lite: click-to-load, privacy youtube-nocookie.com, no CLS.

Keyboard: visible focus rings, skip link, burger accessible.

Reduced motion respected.

Contrast AA via theme; text sizes responsive; no layout shifts.

8) Security (headers / CSP)

Configured in netlify.toml:

HSTS, Referrer-Policy: strict-origin-when-cross-origin

X-Content-Type-Options: nosniff, X-Frame-Options: DENY

CSP minimal allowlist:

script-src: self, GA4, Translate (for potential future use), Google (reCAPTCHA), Apps Script

connect-src: self, GA/GTAG, Apps Script endpoints

frame-src: https://www.youtube-nocookie.com, https://www.google.com/recaptcha/

img-src: self, data, https, https://i.ytimg.com

media-src: self, blob, https

If you later enable reCAPTCHA v3, add your exact site key domain as needed.

9) Affiliate compliance (HeyGen)

CTA URLs (ALL):
https://www.heygen.com/?sid=rewardful&via=rayzvideoai
with target="_blank" rel="noopener nofollow sponsored".

Program reminders:

20% recurring up to 12 months (Creator/Team)

60-day cookie

Enterprise not commissioned

Payout threshold: $100

Strictly no brand bidding (keywords “HeyGen”, “heygen.com”, etc.). Add negatives if PPC is ever used.

Logos/marks: Do not use official HeyGen logos without written permission. Use only your own logo in /images/.

10) Images & assets

Use only images from /images (provided ZIP).

Pick a Hero (LCP) image with good compression and neutral background.

Provide alt attributes with descriptive text; keep captions short and clear.

11) Language suggestion banner

Non-blocking UI rendered at the top if navigator.language ≠ page language.

Links to the alternate URL; does not auto-redirect.

12) Quick edit points

Update dates (Last updated) in legal pages when policies change.

Replace newsletter Apps Script URL & Sheet ID to activate the form.

If you add more posts, remember:

BreadcrumbList, Article JSON-LD, FAQ (if any), hreflang pair.

Add new URLs to the proper sitemap (or let your generator update it).

Consider adding to MODIFIED_URLS for a stronger IndexNow ping.

13) Final checklist (pre-launch)

 All CTAs → affiliate link with rel="noopener nofollow sponsored".

 hreflang EN/FR + x-default everywhere.

 Consent Mode v2 OK; GA4 fires only after opt-in.

 Breadcrumb visible + JSON-LD on all but home.

 Sitemaps & robots.txt valid; 0 broken links.

 YouTube Lite OK; 0 CLS; LCP < 2.5 s.

 Newsletter→Sheets graceful without keys; works with keys.

 IndexNow: INDEXNOW_KEY set; postbuild ping OK.

 Header/Footer unified; no unapproved HeyGen logos.

 Lighthouse (mobile, 4G): Perf ≥ 90 | SEO ≥ 95 | A11y ≥ 95 | BP ≥ 95.

14) Local testing tips

Open index.html in a local server (to avoid CORS/file URL quirks):

npx http-server . -p 8080
# or
python3 -m http.server 8080


Test consent flow in Incognito; clear localStorage keys:

avai_consent_v2, avai_utm, avai_lang_suggest_dismissed_v2.

Chrome DevTools → Lighthouse → Mobile → Throttling: “Simulated Fast 3G/4G”.

Author: Avatar Video AI (E-Com Shop, SASU — SIREN 934 934 308)
Contact: contact.ecomshopfrance@gmail.com

::contentReference[oaicite:0]{index=0}


