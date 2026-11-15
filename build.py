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

print("OK:", len(posts), "άρθρα")
