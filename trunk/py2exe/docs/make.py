from StructuredText import html_with_references

file = open("index.html", "w")

print >>file, "<html><head>"
print >>file, '<LINK REL="STYLESHEET" HREF="py2exe.css">'
print >>file, "</head><title>py2exe</title></head><body>"
file.write(str(html_with_references(open("py2exe.stx").read())))
print >>file, "</body></html>"
