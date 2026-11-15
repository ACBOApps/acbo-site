"""Χτίζει το index.html και το feed.xml από το posts.json.
Για νέο άρθρο: προσθέστε μια εγγραφή στην αρχή του posts.json και τρέξτε: python3 build.py
"""
import json, html, os
from datetime import datetime, timezone
from email.utils import format_datetime

SITE = "https://www.acbo.gr"
here = os.path.dirname(os.path.abspath(__file__))
posts = json.load(open(os.path.join(here, "posts.json"), encoding="utf-8"))
posts.sort(key=lambda p: p["date"], reverse=True)

src = open(os.path.join(here, "index.src.html"), encoding="utf-8").read()
data = json.dumps(posts, ensure_ascii=False).replace("</", "<\\/")
videos = json.load(open(os.path.join(here, "videos.json"), encoding="utf-8"))
vdata = json.dumps(videos, ensure_ascii=False).replace("</", "<\\/")
open(os.path.join(here, "index.html"), "w", encoding="utf-8").write(
    src.replace("/*POSTS*/", data).replace("/*VIDEOS*/", vdata))

def rfc822(d):
    return format_datetime(datetime.strptime(d, "%Y-%m-%d").replace(hour=9, tzinfo=timezone.utc))

items = []
for p in posts:
    link = f"{SITE}/#nea-{p['slug']}"
    items.append(f"""    <item>
      <title>{html.escape(p['title'])}</title>
      <link>{link}</link>
      <guid isPermaLink="false">acbo-{p['slug']}</guid>
      <pubDate>{rfc822(p['date'])}</pubDate>
      <category>{html.escape(p['tag'])}</category>
      <description>{html.escape(p['summary'])}</description>
      <content:encoded><![CDATA[{p['body']}]]></content:encoded>
    </item>""")

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="feed.xsl"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>ACBO – Νέα &amp; ενημερώσεις</title>
    <link>{SITE}/#nea</link>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Λογιστικά, φορολογικά και myDATA σε απλά λόγια, από την ACBO &amp; TAXExpert.</description>
    <language>el</language>
    <lastBuildDate>{rfc822(posts[0]['date'])}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""
open(os.path.join(here, "feed.xml"), "w", encoding="utf-8").write(feed)

# ---- calendar.ics: οι ίδιοι κανόνες με τη σελίδα «Προθεσμίες» (14 μήνες μπροστά) ----
from datetime import date, timedelta
from dateutil.easter import easter, EASTER_ORTHODOX
import calendar as _cal

def holidays(y):
    E = easter(y, EASTER_ORTHODOX)
    return {date(y,1,1), date(y,1,6), E-timedelta(48), date(y,3,25), E-timedelta(2), E+timedelta(1),
            date(y,5,1), E+timedelta(50), date(y,8,15), date(y,10,28), date(y,12,25), date(y,12,26)}

def last_work(y, m):
    d = date(y, m, _cal.monthrange(y, m)[1])
    while d.weekday() >= 5 or d in holidays(y):
        d -= timedelta(1)
    return d

NOM = ['Ιανουάριος','Φεβρουάριος','Μάρτιος','Απρίλιος','Μάιος','Ιούνιος','Ιούλιος','Αύγουστος','Σεπτέμβριος','Οκτώβριος','Νοέμβριος','Δεκέμβριος']
RULES = [('vat_m','Δήλωση ΦΠΑ (μηνιαία)','m'),('vat_q','Δήλωση ΦΠΑ (τριμηνιαία)','q'),
         ('fmy','Απόδοση παρακρατούμενων φόρων','m'),('apd','ΑΠΔ & εργοδοτικές εισφορές','m'),
         ('efka','Εισφορές ΕΦΚΑ μη μισθωτών','m')]
today = date.today()
ev = []
for i in range(14):
    y, m = today.year + (today.month - 1 + i) // 12, (today.month - 1 + i) % 12 + 1
    due = last_work(y, m)
    py, pm = (y, m - 1) if m > 1 else (y - 1, 12)
    for rid, title, per in RULES:
        if per == 'q' and m not in (1, 4, 7, 10):
            continue
        period = f"{(pm-1)//3+1}ο τρίμηνο {py}" if per == 'q' else f"{NOM[pm-1]} {py}"
        ev.append((due, rid, f"{title} · {period}"))
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ACBO//Prothesmies//EL", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         "X-WR-CALNAME:ACBO · Προθεσμίες", "X-WR-TIMEZONE:Europe/Athens", "REFRESH-INTERVAL;VALUE=DURATION:P1D"]
for d, rid, summ in ev:
    lines += ["BEGIN:VEVENT", f"UID:{rid}-{d:%Y%m%d}@acbo.gr", f"DTSTAMP:{stamp}",
              f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d+timedelta(1):%Y%m%d}",
              f"SUMMARY:{summ}", "DESCRIPTION:Ενδεικτική προθεσμία. Πληροφορίες: ACBO 210 49 49 109 / 2310 664 960",
              "TRANSP:TRANSPARENT", "BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{summ}", "TRIGGER:-P3D", "END:VALARM", "END:VEVENT"]
lines.append("END:VCALENDAR")
open(os.path.join(here, "calendar.ics"), "w", encoding="utf-8", newline="\r\n").write("\n".join(lines) + "\n")
print("OK:", len(posts), "άρθρα,", len(ev), "προθεσμίες στο calendar.ics")
