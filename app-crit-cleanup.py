#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 28 13:17:04 2017

@author: sjhuskey
"""
import codecs, os, re

path = '/Users/sjhuskey/Dropbox/DLL/Technical/Automate/automation/app-crit-entries.txt'

# Open the file with utf-8 encoding.
source_file = codecs.open(path,'r','utf-8')

# Read the file.
source_text = source_file.read()


# Cleaning up some issues with the app. crit. entries.
# Remove empty readings.
search_no_ann = re.compile(r'<!-- NO ([A-Z]*) ANNOTATION -->')
no_ann_replace = search_no_ann.sub('',source_text)

search_empty_readings = re.compile(r'<rdg wit="None" source="None" xml:id="rdg-([0-9]*).([0-9]*)-([.]*)"><!-- ([A-Z(\s)?]*([\d])?) --></rdg>')
empty_readings_replace = search_empty_readings.sub('',no_ann_replace)

# Remove empty witnesses        
search_wit = re.compile(r'wit="None"')
wit_replace = search_wit.sub(r'',empty_readings_replace)

# Remove empty sources   
search_src = re.compile(r'source="None"')
src_replace = search_src.sub(r'',wit_replace)


# Turn empty readings into self-closing tags.
search_none_rdg = re.compile(r'>None</rdg>')
none_rdg_replace = search_none_rdg.sub('/>',src_replace)
        
#Remove extra white space between attributes.
search_ws = re.compile(r'\s\s')
ws_replace = search_ws.sub(r' ',none_rdg_replace)

# Dealing with conventional symbols in critical editions.
# Brackets for an addtion, first as a value of <lem> or <rdg>
search_addition = re.compile(r'<([a-zA-Z]*)>([\sa-zA-Z]*)?(</rdg>|</lem>)')
replace_addition1 = search_addition.sub(r'"><supplied reason="lost">\1</supplied>\2\3', ws_replace)

# Now as part of an xml:id, where <> are not allowed.
search_addition1 = re.compile(r'(?<=-)<([a-zA-Z]*(-[a-zA-Z])?)>')
replace_addition2 = search_addition1.sub(r'\1-addition',replace_addition1)

# †Crux†, first as a value of an element.
search_crux1 = re.compile(r'†([a-zA-Z(\s)?]*)†([\sa-zA-Z]*)?(</rdg>|</lem>)')
replace_crux1 = search_crux1.sub(r'"><sic>\1</sic>\2\3',replace_addition2)

# Now a crux as a value of an attribute, which is not allowed.
search_crux2 = re.compile(r'(?<=-)†([a-zA-Z(\-)?]*)†')
replace_crux2 = search_crux2.sub(r'\1-crux',replace_crux1)

# Lacuna *** as a value of an element.
search_lacuna1 = re.compile(r'\*\*\*([\sa-zA-Z]*)?(</rdg>|</lem>)')
replace_lacuna1 = search_lacuna1.sub(r'<gap reason="lost"/>\1\2', replace_crux2)

# Lacuna *** as a value of an attribute.
search_lacuna2 = re.compile(r'(?<=-)\*\*\*([\sa-zA-Z]*)?')
replace_lacuna2 = search_lacuna2.sub(r'lacuna\1', replace_lacuna1)

# Editorial deletion with brackets [] as a value of an element
search_deletion1 = re.compile(r'\[([a-zA-Z]*)\]?(</rdg>|</lem>)')
replace_deletion1 = search_deletion1.sub(r'<surplus>\1</surplus>\2',replace_lacuna2)

# Editorial deletion with brackets [] as a value of an attribute
search_deletion2 = re.compile(r'(?<=-)\[([a-zA-Z]*)\]')
replace_deletion2 = search_deletion2.sub(r'\1-surplus',replace_deletion1)


new_entries = replace_deletion2

header = '''<?xml-model
href="https://digitallatin.github.io/guidelines/critical-editions.rng" type="application/xml" 
  schematypens="http://relaxng.org/ns/structure/1.0"?>
<?xml-model
href="https://digitallatin.github.io/guidelines/critical-editions.rng" type="application/xml"
	schematypens="http://purl.oclc.org/dsdl/schematron"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
   <teiHeader>
      <fileDesc>
         <titleStmt>
            <title>Title</title>
         </titleStmt>
         <publicationStmt>
            <p>Publication Information</p>
         </publicationStmt>
         <sourceDesc>
            <p>Information about the source</p>
         </sourceDesc>
      </fileDesc>
   </teiHeader>
   <text>
      <body>
      <listApp>'''

# Write the footer
footer = '''</listApp
   </text>
</TEI>'''

TEI = header + new_entries + footer

new_path = '/Users/sjhuskey/Dropbox/DLL/Technical/Automate/automation/new-app-crit-entries.xml'

# Open the new file.
new_source = codecs.open(new_path,'w','utf-8')

new_source.write(str(TEI))

source_file.close()
new_source.close()
os.system("open "+ new_path)