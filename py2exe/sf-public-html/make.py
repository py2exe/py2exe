from StructuredText import html_with_references


file = open("htdocs\\py2exe.html", "w")

print >>file, "<html><head>"
print >>file, '<LINK REL="STYLESHEET" HREF="py2exe.css">'
print >>file, "</head><title>py2exe</title></head><body>"
file.write(str(html_with_references(open("py2exe.stx").read())))

footer = """
<!--WEBBOT bot="HTMLMarkup" startspan ALT="Site Meter" -->
<script type="text/javascript" language="JavaScript">var site="sm5py2exe"</script>
<script type="text/javascript" language="JavaScript1.2" src="http://sm5.sitemeter.com/js/counter.js?site=sm5py2exe">
</script>
<noscript>
<a href="http://sm5.sitemeter.com/stats.asp?site=sm5py2exe" target="_top">
<img src="http://sm5.sitemeter.com/meter.asp?site=sm5py2exe" alt="Site Meter" border=0></a>
</noscript>
<!-- Copyright (c)2000 Site Meter -->
<!--WEBBOT bot="HTMLMarkup" Endspan -->
<A href="http://sourceforge.net"> 
<IMG src="http://sourceforge.net/sflogo.php?group_id=11628&amp;type=1" width="88" height="31" border="0" alt="SourceForge Logo"> </A>
"""
print >>file, footer

print >>file, "</body></html>"
