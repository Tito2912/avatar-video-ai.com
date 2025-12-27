/** Google Apps Script — Newsletter collector (Web App)
 * Usage:
 * 1) Apps Script > New project. Paste this file.
 * 2) Replace SHEET_NAME if needed. Create a Google Sheet and note its ID.
 * 3) Deploy > "New deployment" > Type: Web app
 *    - Execute as: Me
 *    - Who has access: Anyone (or Anyone with the link)
 *    - Copy the Web App URL (use it as data-apps-script-url in the form)
 * 4) In the website form, set:
 *      data-apps-script-url="<YOUR_WEB_APP_URL>"
 *      data-sheet-id="<YOUR_SHEET_ID>"
 *
 * Expected POST JSON body from site:
 *   {
 *     "sheetId": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
 *     "record": {
 *        "timestamp": "2025-09-28T10:00:00.000Z",
 *        "email": "you@example.com",
 *        "page": "/blog/heygen-ai-review.html",
 *        "lang": "en",
 *        "utm": {"utm_source":"newsletter", ...},
 *        "consent": "newsletter"
 *     }
 *   }
 *
 * Response:
 *   200 OK { ok: true } on success
 *   400/500 with { ok:false, error: "..."} on errors
 */

const SHEET_NAME = 'newsletter';
const HEADERS = ['timestamp','email','page','lang','utm_source','consent'];

function doPost(e) {
  try {
    const { data, error } = parseBody_(e);
    if (error) return json_(400, { ok:false, error });

    const { sheetId, record } = data;
    if (!sheetId || !record || !record.email) {
      return json_(400, { ok:false, error:'Missing sheetId or record.email' });
    }

    // Basic server-side validations
    if (!isValidEmail_(record.email)) {
      return json_(400, { ok:false, error:'Invalid email' });
    }

    const lock = LockService.getScriptLock();
    lock.tryLock(5000);

    const ss = SpreadsheetApp.openById(sheetId);
    let sh = ss.getSheetByName(SHEET_NAME);
    if (!sh) {
      sh = ss.insertSheet(SHEET_NAME);
      sh.appendRow(HEADERS);
    }

    // Compose row
    const utm_source = record.utm && record.utm.utm_source ? String(record.utm.utm_source) : '';
    const row = [
      record.timestamp || new Date().toISOString(),
      String(record.email).trim().toLowerCase(),
      String(record.page || ''),
      String(record.lang || ''),
      utm_source,
      String(record.consent || 'newsletter')
    ];

    // Append
    sh.appendRow(row);

    // Optional: lightweight dedupe by email+lang (keep first)
    // dedupeBy_(sh, [1,3]); // columns index starting at 0: timestamp=0,email=1,page=2,lang=3,utm=4,consent=5

    return json_(200, { ok:true });
  } catch (err) {
    return json_(500, { ok:false, error: String(err && err.message || err) });
  } finally {
    try { LockService.getScriptLock().releaseLock(); } catch (_){}
  }
}

/* ---------- Helpers ---------- */
function parseBody_(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) return { error:'Empty body' };
    const ct = (e.postData.type || '').toLowerCase();
    if (ct.indexOf('application/json') === -1) return { error:'Content-Type must be application/json' };
    const data = JSON.parse(e.postData.contents);
    return { data };
  } catch (err) {
    return { error:'Invalid JSON: ' + err };
  }
}

function json_(status, obj) {
  const out = ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
  const res = {
    statusCode: status,
    headers: corsHeaders_()
  };
  return HtmlService.createHtmlOutput()
    .setContent(JSON.stringify({ __json: true, ...obj })) // workaround: Apps Script lacks direct status control
    .setTitle('Newsletter API')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DENY); // defense-in-depth
}

function doOptions(e) { // CORS preflight
  return ContentService.createTextOutput('')
    .setMimeType(ContentService.MimeType.TEXT);
}

function corsHeaders_() {
  return {
    'Access-Control-Allow-Origin': '*',            // TIP: restrict to your domain when ready
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Vary': 'Origin'
  };
}

function isValidEmail_(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email || ''));
}

/* Optional: simple deduper by columns (0-based indexes)
function dedupeBy_(sh, keyCols) {
  const last = sh.getLastRow();
  if (last <= 1) return;
  const vals = sh.getRange(2,1,last-1,sh.getLastColumn()).getValues();
  const seen = new Set();
  const keep = [];
  vals.forEach((row, idx) => {
    const key = keyCols.map(i => String(row[i] || '')).join('||');
    if (seen.has(key)) return; // skip dup
    seen.add(key);
    keep.push(row);
  });
  // Rewrite (keep header)
  sh.getRange(2,1,last-1,sh.getLastColumn()).clearContent();
  if (keep.length) sh.getRange(2,1,keep.length,keep[0].length).setValues(keep);
}
*/
