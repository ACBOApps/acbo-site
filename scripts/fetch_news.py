"""Κατεβάζει τα RSS του Taxheaven και γράφει το news.json (μόνο τίτλος, σύντομη περίληψη, σύνδεσμος).
Δεν αντιγράφεται το πλήρες περιεχόμενο, σύμφωνα με τους όρους του Taxheaven.
Τρέχει αυτόματα από το GitHub Actions. Αν ένα feed αποτύχει, κρατιούνται τα προηγούμενα στοιχεία του."""
import json, re, sys, html, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime

BASE = "https://www.taxheaven.gr/bibliothiki/soft/xml/"
FEEDS = [("new", "Νέα & Ειδήσεις", "soft_new.xml"),
         ("law", "Αποφάσεις & Εγκύκλιοι", "soft_law.xml"),
         ("dat", "Φορολογικό ημερολόγιο", "soft_dat.xml")]
PER_FEED = 5
OUT = "news.json"

def clean(t, n):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > n:
        t = t[:n].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
    return t

def to_iso(s):
    s = (s or "").strip()
    try:
        return parsedate_to_datetime(s).date().isoformat()
    except Exception:
        pass
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:19] if "T" in f else s[:10], f).date().isoformat()
        except Exception:
            pass
    return datetime.utcnow().date().isoformat()

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ACBO-site-news/1.0; +https://www.acbo.gr)"})
    return urllib.request.urlopen(req, timeout=30).read()

try:
    old = json.load(open(OUT, encoding="utf-8")).get("items", [])
except Exception:
    old = []

DL_OUT = "deadlines.json"

def write_deadlines(root):
    """Όλες οι προσεχείς προθεσμίες του φορολογικού ημερολογίου: μόνο τίτλος, ημερομηνία, σύνδεσμος."""
    today = datetime.utcnow().date().isoformat()
    dl, seen = [], set()
    for it in root.iter("item"):
        title = clean(it.findtext("title"), 160)
        link = (it.findtext("link") or "").strip()
        date = to_iso(it.findtext("pubDate") or it.findtext("date"))
        if not title or not link.startswith("https://www.taxheaven.gr/") or date < today or link in seen:
            continue
        seen.add(link)
        dl.append({"title": title, "date": date, "link": link})
    dl.sort(key=lambda i: (i["date"], i["title"]))
    dl = dl[:80]
    if not dl:
        print("deadlines: κανένα προσεχές, κρατιέται το παλιό αρχείο")
        return
    try:
        same = json.load(open(DL_OUT, encoding="utf-8")).get("items") == dl
    except Exception:
        same = False
    if not same:
        json.dump({"source": "Taxheaven.gr – Φορολογικό ημερολόγιο", "items": dl,
                   "updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")},
                  open(DL_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("deadlines:", len(dl))

items = []
for key, label, fn in FEEDS:
    try:
        root = ET.fromstring(fetch(BASE + fn))
        got = []
        for it in root.iter("item"):
            title = clean(it.findtext("title"), 150)
            link = (it.findtext("link") or "").strip()
            if not title or not link.startswith("https://"):
                continue
            got.append({"feed": key, "source": label, "title": title,
                        "summary": clean(it.findtext("description"), 140),
                        "link": link, "date": to_iso(it.findtext("pubDate") or it.findtext("date"))})
            if len(got) >= PER_FEED:
                break
        if not got:
            raise ValueError("κενό feed")
        if key == "dat":
            write_deadlines(root)
        items += got
        print("OK", fn, len(got))
    except Exception as e:
        print("ΑΠΟΤΥΧΙΑ", fn, e, file=sys.stderr)
        items += [i for i in old if i.get("feed") == key]

items.sort(key=lambda i: i["date"], reverse=True)
new = {"source": "Taxheaven.gr", "items": items}
try:
    same = json.load(open(OUT, encoding="utf-8")).get("items") == items
except Exception:
    same = False
if not same:
    json.dump({**new, "updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("γράφτηκε", OUT, len(items))
else:
    print("καμία αλλαγή")
