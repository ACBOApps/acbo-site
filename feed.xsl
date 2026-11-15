<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" encoding="UTF-8" indent="yes"/>
<xsl:template match="/rss/channel">
<html lang="el"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ACBO – Νέα &amp; ενημερώσεις (RSS)</title>
<style>
body{margin:0;background:#383840;color:#F2F2F6;font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:720px;margin:0 auto;padding:28px 18px 60px}
h1{font-size:28px;line-height:1.2;margin:0 0 8px}
.box{background:#45454F;border:1px solid #585865;border-radius:16px;padding:16px 18px;margin:18px 0 28px;color:#C3C3CE;font-size:15px}
.box code{display:block;margin-top:8px;padding:8px 10px;border-radius:8px;background:#2f2f37;color:#CFC6F0;word-break:break-all;font-size:13.5px}
a{color:#B3A7E0}
article{border-top:1px solid #585865;padding:16px 0}
article h2{font-size:19px;line-height:1.35;margin:0 0 4px}
article h2 a{color:#F2F2F6;text-decoration:none}
small{color:#C3C3CE}
p{margin:6px 0 0;color:#C3C3CE}
</style></head><body><main>
<h1>ACBO – Νέα &amp; ενημερώσεις</h1>
<p><xsl:value-of select="description"/></p>
<div class="box">Αυτή είναι η ροή RSS του site. Για να λαμβάνετε αυτόματα τα νέα μας, αντιγράψτε τη διεύθυνση παρακάτω σε μια εφαρμογή ανάγνωσης RSS (π.χ. Feedly). Αν δεν χρησιμοποιείτε RSS, δείτε τα άρθρα στο <a href="https://www.acbo.gr/#nea">site</a>.<code>https://www.acbo.gr/feed.xml</code></div>
<xsl:for-each select="item">
<article><h2><a href="{link}"><xsl:value-of select="title"/></a></h2>
<small><xsl:value-of select="substring(pubDate,6,11)"/> · <xsl:value-of select="category"/></small>
<p><xsl:value-of select="description"/></p></article>
</xsl:for-each>
</main></body></html>
</xsl:template>
</xsl:stylesheet>
