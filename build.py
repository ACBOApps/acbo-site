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
open(os.path.join(here, "index.html"), "w", encoding="utf-8").write(
    src.replace("/*POSTS*/", data).replace("/*VIDEOS*/", vdata))

def rfc822(d):
    return format_datetime(datetime.strptime(d, "%Y-%m-%d").replace(hour=9, tzinfo=timezone.utc))


print("OK:", len(posts), "άρθρα")
