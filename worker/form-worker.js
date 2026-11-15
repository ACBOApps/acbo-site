/*
 * ACBO – Φόρμα επικοινωνίας του site.
 * Cloudflare Worker: ελέγχει Turnstile, μπλοκάρει spam και στέλνει email στο info@acbo.gr μέσω Microsoft 365 (Graph).
 * Τα μυστικά (secrets) ΔΕΝ μπαίνουν ποτέ στον κώδικα ή στο GitHub: ορίζονται στο Cloudflare.
 */
const DEFAULT_ORIGINS = ['https://acbo.gr', 'https://www.acbo.gr', 'https://acboapps.github.io'];
const PHONES = 'Καλέστε μας: 210 49 49 109 / 2310 664 960.';

const json = (body, status, origin) => new Response(JSON.stringify(body), {
  status,
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
    'X-Content-Type-Options': 'nosniff',
    'Cache-Control': 'no-store',
    ...(origin ? { 'Access-Control-Allow-Origin': origin, 'Vary': 'Origin' } : {}),
  },
});

const clean = (v, max = 200) => String(v ?? '').replace(/<[^>]*>/g, '').replace(/[\r\n]+/g, ' ').trim().slice(0, max);
const digits = (v) => String(v ?? '').replace(/\D/g, '');
const validEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v) && v.length <= 120;

async function turnstileOk(env, token, ip) {
  const body = new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: token || '' });
  if (ip) body.set('remoteip', ip);
  try {
    const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body });
    return !!(await r.json()).success;
  } catch { return false; }
}

async function graphToken(env) {
  const tr = await fetch(`https://login.microsoftonline.com/${env.MS_TENANT_ID}/oauth2/v2.0/token`, {
    method: 'POST',
    body: new URLSearchParams({
      client_id: env.MS_CLIENT_ID, client_secret: env.MS_CLIENT_SECRET,
      scope: 'https://graph.microsoft.com/.default', grant_type: 'client_credentials',
    }),
  });
  const tok = tr.ok ? (await tr.json()).access_token : null;
  if (!tok) console.log('ACBO form: token', tr.status);
  return tok;
}

/* Ημερήσιος έλεγχος υγείας: ελέγχει κλειδιά, δικαίωμα και πολιτική της Microsoft ΧΩΡΙΣ να στείλει email.
   Στέλνει μήνυμα χωρίς παραλήπτη: αν η Microsoft απαντήσει «λάθος παραλήπτης» (400), η πρόσβαση είναι εντάξει.
   Αν απαντήσει 401/403, κάτι χάλασε (π.χ. έληξε το κλειδί ή άλλαξε η πολιτική). */
let lastHealth = null;
async function health(env) {
  if (lastHealth && Date.now() - lastHealth.t < 10 * 60 * 1000) return lastHealth.ok;
  let ok = false;
  try {
    const tok = await graphToken(env);
    if (tok) {
      const r = await fetch(`https://graph.microsoft.com/v1.0/users/${encodeURIComponent(env.MAIL_FROM)}/sendMail`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${tok}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: { subject: 'health', body: { contentType: 'Text', content: '-' }, toRecipients: [] }, saveToSentItems: false }),
      });
      ok = r.status === 400;
      if (!ok) console.log('ACBO form: health', r.status, (await r.text()).slice(0, 300));
    }
  } catch (e) { console.log('ACBO form: health error', String(e)); }
  lastHealth = { t: Date.now(), ok };
  return ok;
}

async function graphSend(env, subject, text, replyTo) {
  const tok = await graphToken(env);
  if (!tok) return false;
  const message = {
    subject,
    body: { contentType: 'Text', content: text },
    toRecipients: [{ emailAddress: { address: env.MAIL_TO } }],
  };
  if (replyTo) message.replyTo = [{ emailAddress: { address: replyTo } }];
  const r = await fetch(`https://graph.microsoft.com/v1.0/users/${encodeURIComponent(env.MAIL_FROM)}/sendMail`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${tok}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, saveToSentItems: false }),
  });
  if (r.status !== 202) console.log('ACBO form: sendMail', r.status, (await r.text()).slice(0, 300));
  return r.status === 202;
}

export default {
  async fetch(req, env) {
    const allowed = env.ALLOWED_ORIGINS ? env.ALLOWED_ORIGINS.split(',').map((s) => s.trim()) : DEFAULT_ORIGINS;
    const origin = req.headers.get('Origin') || '';
    const okOrigin = allowed.includes(origin) ? origin : '';

    if (req.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: okOrigin ? {
        'Access-Control-Allow-Origin': okOrigin, 'Access-Control-Allow-Methods': 'POST', 'Access-Control-Max-Age': '86400', 'Vary': 'Origin',
      } : {} });
    }
    if (req.method === 'GET' && new URL(req.url).pathname === '/health') {
      const ok = await health(env);
      return json({ ok }, ok ? 200 : 503, '');
    }
    if (req.method !== 'POST') return json({ ok: false, error: 'Μη αποδεκτό αίτημα.' }, 405, okOrigin);
    if (!okOrigin) return json({ ok: false, error: 'Μη αποδεκτό αίτημα.' }, 403, '');

    for (const k of ['TURNSTILE_SECRET', 'MAIL_TO', 'MAIL_FROM', 'MS_TENANT_ID', 'MS_CLIENT_ID', 'MS_CLIENT_SECRET']) {
      if (!env[k]) return json({ ok: false, error: `Η φόρμα δεν είναι ακόμη ενεργή. ${PHONES}` }, 503, okOrigin);
    }

    let f;
    try { f = await req.formData(); } catch { return json({ ok: false, error: 'Μη αποδεκτό αίτημα.' }, 400, okOrigin); }
    const get = (k) => f.get(k) ?? '';

    if (get('website')) return json({ ok: true }, 200, okOrigin);               // bot: σιωπηλή «επιτυχία»
    if ((parseInt(get('elapsed'), 10) || 0) < 3000) return json({ ok: false, error: 'Η φόρμα στάλθηκε πολύ γρήγορα. Δοκιμάστε ξανά.' }, 400, okOrigin);

    const ip = req.headers.get('CF-Connecting-IP') || '';
    if (!(await turnstileOk(env, String(get('cf_token')), ip))) {
      return json({ ok: false, error: 'Ο έλεγχος ασφαλείας απέτυχε. Ανανεώστε τη σελίδα και δοκιμάστε ξανά.' }, 400, okOrigin);
    }

    const form = String(get('form'));
    const when = new Date().toLocaleString('el-GR', { timeZone: 'Europe/Athens' });
    let subject, text, replyTo = '';

    if (form === 'contact') {
      const name = clean(get('name')), phone = clean(get('phone'), 30);
      let email = clean(get('email'), 120);
      const office = clean(get('office'), 40), type = clean(get('type'), 60);
      const message = String(get('message')).replace(/<[^>]*>/g, '').trim().slice(0, 3000);
      if (!name || digits(phone).length < 10) return json({ ok: false, error: 'Συμπληρώστε ονοματεπώνυμο και τηλέφωνο.' }, 400, okOrigin);
      if (email && !validEmail(email)) email = '';
      subject = `Νέο αίτημα από το site: ${type} (${office})`;
      text = `Νέο μήνυμα από τη φόρμα επικοινωνίας του acbo.gr\n\nΟνοματεπώνυμο: ${name}\nΤηλέφωνο: ${phone}\nEmail: ${email || '-'}\nΓραφείο: ${office}\nΘέμα: ${type}\n\nΜήνυμα:\n${message || '-'}\n\n---\nΗμερομηνία: ${when}`;
      replyTo = email;
    } else {
      return json({ ok: false, error: 'Μη αποδεκτό αίτημα.' }, 400, okOrigin);
    }

    const sent = await graphSend(env, subject, text, replyTo);
    return sent ? json({ ok: true }, 200, okOrigin)
                : json({ ok: false, error: `Δεν ήταν δυνατή η αποστολή. ${PHONES}` }, 500, okOrigin);
  },
};
