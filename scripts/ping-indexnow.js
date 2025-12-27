/**
 * scripts/ping-indexnow.js
 * Postbuild: (1) génère le fichier clé IndexNow à la racine du site,
 *            (2) envoie un ping batch au bon endpoint agrégateur IndexNow.
 *
 * Netlify:
 *  - Vars requises:
 *      INDEXNOW_KEY   -> votre clé IndexNow (contenu du fichier clé)
 *  - Vars optionnelles:
 *      BASE_URL       -> URL canonique du site (def: https://avatar-video-ai.com)
 *      MODIFIED_URLS  -> liste CSV d’URLs fraîchement modifiées à prioriser
 *  - Script:
 *      "postbuild": "node scripts/ping-indexnow.js"
 *
 * Doc / exemples:
 *  - Endpoint agrégateur (batch POST JSON): https://api.indexnow.org/indexnow
 *  - Payload:
 *      {
 *        "host": "avatar-video-ai.com",
 *        "key": "XXXX",
 *        "keyLocation": "https://avatar-video-ai.com/indexnow-XXXX.txt",
 *        "urlList": ["https://avatar-video-ai.com/", "..."]
 *      }
 */

const fs = require('fs/promises');
const path = require('path');

const BASE_URL = (process.env.BASE_URL || 'https://avatar-video-ai.com').replace(/\/+$/, '');
const INDEXNOW_KEY = (process.env.INDEXNOW_KEY || '').trim();
const INDEXNOW_ENDPOINT = process.env.INDEXNOW_ENDPOINT || 'https://api.indexnow.org/indexnow';

const KEY_FILENAME = `indexnow-${INDEXNOW_KEY}.txt`;
const KEY_FILE_ABS = path.join(process.cwd(), KEY_FILENAME);
const KEY_LOCATION = `${BASE_URL}/${KEY_FILENAME}`;

// URLs minimales + pages stratégiques (ajoutez vos dernières pages modifiées via MODIFIED_URLS)
const FALLBACK_URLS = [
  '/', '/sitemap.xml',
  '/sitemap-en.xml', '/fr/sitemap-fr.xml',
  '/blog/', '/fr/blog/',
  '/blog/heygen-update-2025', '/fr/blog/mise-a-jour-heygen-2025',
  '/blog/heygen-ai-review', '/fr/blog/avis-heygen-ai',
  '/legal-notice', '/privacy-policy',
  '/fr/', '/fr/mentions-legales', '/fr/politique-de-confidentialite'
];

const MODIFIED_URLS = (process.env.MODIFIED_URLS || '')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean);

// Liste unique, absolue
const urlList = Array.from(new Set(
  [...MODIFIED_URLS, ...FALLBACK_URLS].map(u => (u.startsWith('http') ? u : `${BASE_URL}${u}`))
));

async function ensureKeyFile() {
  if (!INDEXNOW_KEY) {
    console.warn('[IndexNow] INDEXNOW_KEY manquant — génération/ping annulés.');
    return false;
  }
  try {
    await fs.writeFile(KEY_FILE_ABS, INDEXNOW_KEY + '\n', 'utf8');
    console.log(`[IndexNow] Fichier clé écrit: ${KEY_FILE_ABS}`);
    return true;
  } catch (err) {
    console.error('[IndexNow] Échec écriture fichier clé:', err);
    return false;
  }
}

async function pingIndexNow() {
  if (!INDEXNOW_KEY) return;

  const payload = {
    host: new URL(BASE_URL).host,
    key: INDEXNOW_KEY,
    keyLocation: KEY_LOCATION,
    urlList
  };

  console.log(`[IndexNow] Ping vers ${INDEXNOW_ENDPOINT} avec ${urlList.length} URL(s)…`);

  try {
    const res = await fetch(INDEXNOW_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify(payload)
    });
    const ok = res.ok;
    const text = await res.text().catch(() => '');
    if (ok) {
      console.log('[IndexNow] Ping OK:', res.status, text ? `body: ${text.slice(0,200)}` : '');
    } else {
      console.warn('[IndexNow] Ping échoué:', res.status, res.statusText, text ? `body: ${text.slice(0,200)}` : '');
    }
  } catch (err) {
    console.warn('[IndexNow] Erreur réseau:', err && err.message ? err.message : err);
  }
}

(async function main() {
  const ready = await ensureKeyFile();
  if (!ready) return;
  await pingIndexNow();
})();
