"""Χτίζει το index.html από το posts.json.
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
# Συχνές ερωτήσεις -> δομημένα δεδομένα για το Google (FAQPage), από το ίδιο το κείμενο της σελίδας
import re as _re
_faq = _re.search(r'<div class="faq[^"]*">(.*?)</div>', src, _re.S)
_qa = _re.findall(r'<summary>(.*?)</summary><p>(.*?)</p>', _faq.group(1), _re.S) if _faq else []
_strip = lambda t: html.unescape(_re.sub(r"<[^>]+>", "", t)).strip()
_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": _strip(q), "acceptedAnswer": {"@type": "Answer", "text": _strip(a_)}} for q, a_ in _qa]}
src = src.replace("<!--FAQLD-->", '<script type="application/ld+json">' + json.dumps(_ld, ensure_ascii=False) + "</script>" if _qa else "")
vdata = json.dumps(videos, ensure_ascii=False).replace("</", "<\\/")
out = src.replace("/*POSTS*/", data).replace("/*VIDEOS*/", vdata)
# Κανόνας ασφαλείας (CSP): ο browser τρέχει ΜΟΝΟ τα δικά μας scripts (με το ακριβές αποτύπωμά τους)
# και τα Turnstile/Clarity. Οτιδήποτε άλλο μπλοκάρεται. Τα αποτυπώματα ξαναϋπολογίζονται σε κάθε build.
import hashlib, base64
_hashes = sorted({"'sha256-" + base64.b64encode(hashlib.sha256(m.encode("utf-8")).digest()).decode() + "'"
                  for m in _re.findall(r"<script>(.*?)</script>", out, _re.S)})
CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' " + " ".join(_hashes) + " https://challenges.cloudflare.com https://www.clarity.ms https://scripts.clarity.ms",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https://i.ytimg.com https://*.clarity.ms https://c.bing.com",
    "font-src 'self'",
    "connect-src 'self' https://acbo-forms.cold-poetry-1424.workers.dev https://*.clarity.ms https://c.bing.com",
    "frame-src https://challenges.cloudflare.com https://www.youtube-nocookie.com",
    "object-src 'none'", "base-uri 'self'", "form-action 'self'", "upgrade-insecure-requests"])
assert "<!--CSP-->" in out
out = out.replace("<!--CSP-->", '<meta http-equiv="Content-Security-Policy" content="' + CSP + '">\n<meta name="referrer" content="strict-origin-when-cross-origin">', 1)
open(os.path.join(here, "index.html"), "w", encoding="utf-8").write(out)

def rfc822(d):
    return format_datetime(datetime.strptime(d, "%Y-%m-%d").replace(hour=9, tzinfo=timezone.utc))


print("OK:", len(posts), "άρθρα")
