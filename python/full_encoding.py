#! /usr/bin/env python3

# current things to work on
# encoding of new xml in UTF-8
# some weird xmlns declarations showing up in the finished file.
# THIS ISSUE HAS BEEN FIXED using ET.register_namespace('', 'http://www.tei-c.org/ns/1.0')
# section 1.6? we have an annotation for a section that appears not to exist

##### BIG PROBLEM - ending up with XML/HTML entities where we want unicode '<' and '>'
#
# 1.2 cotidie operibus not encoding properly - mismatch b/n basetext.txt and app-crit-test.csv
# 1.2 have in(2) as a lemma - check this - from .csv.
# use this to pick which in gets replaced
# 1.3 section.text not returning full text - possibly section.contents idk
# 1.3 ac(2) same as in(2) above
# 1.5 extra ' in rei copiam exiguam - fixed by fixing app-crit-test.csv
# 1.6 this part of text is missing
#
# clean up extraneous print statements
# remove extraneous os.system("open...") statement

# figure out how to escape angle brackets in tree.write()
# options:
# fix at the very end
# escape < > in input string to tree.write()
# how to get basetext.xml to screweduptext.txt?

import re
import os
import time
import codecs  # This is important for reading files with Unicode characters.
import csv
import xml.etree.ElementTree as ET # used to parse XML to insert <app> tags
from xml.sax.saxutils import unescape  # used to unescape some angle brackets


# Create a variable for the path to the base text.
path = '/Volumes/data/katy/PycharmProjects/DLL/automation/sources/basetext.txt'

# Open the file with utf-8 encoding.
source_file = codecs.open(path,'r','utf-8')

# Read the file.
source_text = source_file.read()

# Tell python what to search for (with thanks to https://stackoverflow.com/questions/13168761/python-use-regex-sub-multiple-times-in-1-pass).

print('Gosh, that\'s a lot of unencoded text! We\'d better get started!')
time.sleep(5)

# Handle additive emendation, since it is indicated by < >, which would be swept up by other routines below.
print('Okay, we\'ll handle editorial additions first, since their angle brackets\n might cause trouble later.')
time.sleep(4)
search_addition = re.compile(r'<([a-zA-Z]*)>')
replace0 = search_addition.sub(r'<supplied reason="lost">\1</supplied>', source_text)

# Search for numbers at beginning of paragraphs, then wrap paragraph in <p n="[number]"> </p>/
print('Done. Next up: encoding the paragraphs.')
time.sleep(5)
search_paragraph = re.compile(r'\n([0-9]*)(.*)')
replace1 = search_paragraph.sub(r'<p n="\1">\2</p>',replace0)

# Remove empty paragraphs.
print('Done. Now let\'s kill any empty paragraphs caused by line breaks in the original document.')
time.sleep(3)
search_empty_paragraph = re.compile(r'<p n="">([\s]*)</p>')
replace2 = search_empty_paragraph.sub(r'', replace1)

# Search for (number) and reformat it as <seg n="number">(number).
print('Empty paragraphs have been killed. Handling segments now.')
time.sleep(5)
search_segment = re.compile(r'\(([0-9]*)\)')
replace3 = search_segment.sub(r'<seg n="\1">',replace2)

# Add the closing </seg>.
search_add_close_seg = re.compile(r'(<seg|</p>)')
replace4 = search_add_close_seg.sub(r'</seg>\1',replace3)

# Remove the orphan </seg> at the beginning of the paragraph.
search_remove_orphan_seg = re.compile(r'\s</seg>(<seg n="1">)\s')
replace5 = search_remove_orphan_seg.sub(r'\1',replace4)

# Remove space before and after <seg> markers.
search_remove_seg_space = re.compile(r'\s</seg><seg n="([0-9]*)">\s')
replace6 = search_remove_seg_space.sub(r'</seg> <seg n="\1">',replace5)

# Handle crux.
print('Now handling special symbols. First up: †crux†.')
time.sleep(3)
search_crux = re.compile(r'†([a-zA-Z]*)†')
replace7 = search_crux.sub(r'<sic>\1</sic>',replace6)

# Handle lacuna.
print('... now *** lacunae')
time.sleep(3)
search_lacuna = re.compile(r'\*\*\*')
replace8 = search_lacuna.sub(r'<gap reason="lost"/>', replace7)

# Handle editorial deletion.
print('... now {editorial deletions}.')
time.sleep(3)
search_deletion = re.compile(r'\[([a-zA-Z]*)\]')
replace9 = search_deletion.sub(r'<surplus>\1</surplus>',replace8)

# Go back and fix the first paragraph, for some reason.
search_first_p = re.compile(r'1<seg(.*)<p n="2"')
replace10 = search_first_p.sub(r'<p n="1"><seg\1</seg></p>\n\n<p n="2"',replace9)

# Write the TEI header.
print('Adding the TEI header and footer, just to show off.')
time.sleep(2)

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
      <div type="edition" xml:id="edition-text">
            <div type="textpart" n="1" xml:id="part1">'''

# Write the footer
footer = '''</div></div></body>
      <back>
         <!--
The content of the back matter will be determined in consultation between
        the editor and the staff of the DLL. Because LDLT editions are encoded, the
        matter traditionally found in the back of a printed critical edition may be
        generated by applications instead of having to be entered manually.
        Nevertheless, there is space here for notes, indices, and other kinds of
        information.
-->
      </back>
   </text>
</TEI>'''


# Combine all of the ingredients into one.
TEI = header + replace10 + footer

# Tell the script where to write the new file.
print('Making a new file ...')
time.sleep(2)
new_path = '/Volumes/data/katy/PycharmProjects/DLL/automation/sources/basetext.xml'

# Open the new file.
new_source = codecs.open(new_path,'w','utf-8')

# Write the contents of altered source_text to new_source.
print('Writing the XML to the new file ...')
time.sleep(2)
new_source.write(str(TEI))

# Close the old and new source files.
print('Cleaning up our workspace...')
time.sleep(2)
source_file.close()

os.system("open "+ new_path)

print('Wow! That saved a lot of time!')
time.sleep(3)

print('Now that the base text is encoded, we\'ll start on the app. crit.')
time.sleep(2)


print('We\'re going to encode the notes one-by-one. <app> tags will appear as they are encoded.')
time.sleep(2)

tree = ET.parse('/Volumes/data/katy/PycharmProjects/DLL/automation/sources/basetext.xml')
root = tree.getroot()
ET.register_namespace('', 'http://www.tei-c.org/ns/1.0')

with open('/Volumes/data/katy/PycharmProjects/DLL/automation/sources/app-crit-test.csv', encoding='utf-8') as appFile:
    readApp = csv.reader(appFile, delimiter=',')
    for row in readApp:
        if row[0] == "Paragraph":
            continue
            # skip the first row, which contains column labels
        # Defining the lemma.
        def lem():
            if not row[2]:
                return '<!-- NO LEMMA -->'
            else:
                return row[2]


        lem = str(lem())


        # A function for creating the xml:id value like lem-1.1-vicit.
        def lem_xmlid():
            # Handle lemmas with multiple words so that they are joined with "-"
            split = row[2].split(' ')
            joined = '-'.join(split)
            return 'xml:id="lem-' + str(row[0]) + '.' + str(row[1]) + '-' + joined + '"'


        lem_xmlid = str(lem_xmlid())


        # A function for creating the xml:id as the value for @target.
        def lem_target():
            split = row[2].split(' ')
            joined = '-'.join(split)
            return str(row[0]) + '.' + str(row[1]) + '-' + joined


        lem_target = str(lem_target())


        # A function for wrapping the witness(es) for a lemma in the correct XML.
        def lemwit():
            if not row[3]:
                return 'wit="None"'
            else:
                # List the sigla, putting # before each one. Space will be added below.
                split = row[3].split(' ')
                joined = '#'.join(split)
                # This produces A#B#C. We need some space:
                search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
                spaced_wit = search_wit.sub(r' \1', joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1', spaced_wit)
                return 'wit="' + str(first_wit) + '"'


        lemwit = str(lemwit())


        # A function for wrapping the source(s) for a lemma in the correct XML.
        def lemsrc():
            if not row[4]:
                return 'source="None"'
            else:
                # return 'source="'+row[4]+'"'
                # List the sigla, putting # before each one. Space will be added below.
                split = row[4].split(' ')
                joined = '#'.join(split)
                # This produces A#B#C. We need some space:
                search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
                spaced_wit = search_wit.sub(r' \1', joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1', spaced_wit)
                return 'source="' + str(first_wit) + '"'


        lemsrc = str(lemsrc())


        # A function for encoding any annotation on the lemma as a <note>.
        def lemnote():
            if not row[5]:
                return '<!-- NO LEMMA ANNOTATION -->'
            else:
                return '<note target="' + lem_target + '">' + row[5] + '</note>'


        lemnote = str(lemnote())


        # Handling the first reading
        def rdg1():
            if not row[6]:
                return '<!-- NO READING 1 -->'
            else:
                return


        rdg1 = str(rdg1())


        # Handling the witness(es) for the first reading
        def rdg1wit():
            if not row[7]:
                return 'wit="None"'
            else:
                # List the sigla, putting # before each one. Space will be added below.
                split = row[7].split(' ')
                joined = '#'.join(split)
                # This produces A#B#C. We need some space:
                search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
                spaced_wit = search_wit.sub(r' \1', joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1', spaced_wit)
                return 'wit="' + str(first_wit) + '"'


        rdg1wit = str(rdg1wit())


        # Handling the source(s) for the first reading
        def rdg1src():
            if not row[8]:
                return 'source="None"'
            else:
                # List the sigla, putting # before each one. Space will be added below.
                split = row[8].split(' ')
                joined = '#'.join(split)
                # This produces A#B#C. We need some space:
                search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
                spaced_wit = search_wit.sub(r' \1', joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1', spaced_wit)
                return 'source="' + str(first_wit) + '"'


        rdg1src = str(rdg1src())


        # Handling the xml:id for the first reading
        def rdg1_xmlid():
            # Handle readings with multiple words so that they are joined with "-"
            split = row[6].split(' ')
            joined = '-'.join(split)
            return 'xml:id="rdg-' + str(row[0]) + '.' + str(row[1]) + '-' + joined + '"'


        rdg1_xmlid = str(rdg1_xmlid())


        # Target for rdg1
        def rdg1_target():
            split = row[2].split(' ')
            joined = '-'.join(split)
            return 'rdg' + str(row[0]) + '.' + str(row[1]) + '-' + joined


        rdg1_target = str(rdg1_target())


        # Note for rdg1
        def rdg1_note():
            if not row[9]:
                return '<!-- NO READING ANNOTATION -->'
            else:
                return '<note target="' + rdg1_target + '">' + row[9] + '</note>'


        rdg1_note = str(rdg1_note())


        # Handling the second reading
        def rdg2():
            if not row[10]:
                return '<!-- NO READING 2 -->'
            else:
                return


        rdg2 = str(rdg2())


        # Handling the witness(es) for the second reading
        def rdg2wit():
            if not row[11]:
                return 'wit="None"'
            else:
                # List the sigla, putting # before each one. Space will be added below.
                split = row[11].split(' ')
                joined = '#'.join(split)
                # This produces A#B#C. We need some space:
                search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
                spaced_wit = search_wit.sub(r' \1', joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1', spaced_wit)
                return 'wit="' + str(first_wit) + '"'


        rdg2wit = str(rdg2wit())


        # Handling the source(s) for the second reading
        def rdg2src():
            if not row[12]:
                return 'source="None"'
            else:
                # List the sigla, putting # before each one. Space will be added below.
                split = row[12].split(' ')
                joined = '#'.join(split)
                # This produces A#B#C. We need some space:
                search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
                spaced_wit = search_wit.sub(r' \1', joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1', spaced_wit)
                return 'source="' + str(first_wit) + '"'


        rdg2src = str(rdg2src())


        # Handling the xml:id for the second reading
        def rdg2_xmlid():
            # Handle readings with multiple words so that they are joined with "-"
            split = row[10].split(' ')
            joined = '-'.join(split)
            return 'xml:id="rdg-' + str(row[0]) + '.' + str(row[1]) + '-' + joined + '"'


        rdg2_xmlid = str(rdg2_xmlid())


        # Target for rdg2
        def rdg2_target():
            split = row[10].split(' ')
            joined = '-'.join(split)
            return 'rdg-' + str(row[0]) + '.' + str(row[1]) + '-' + joined


        rdg2_target = str(rdg2_target())


        # Note for rdg2
        def rdg2_note():
            if not row[13]:
                return '<!-- NO READING ANNOTATION -->'
            else:
                return '<note target="' + rdg1_target + '">' + row[13] + '</note>'


        rdg2_note = str(rdg2_note())

        entries = '<!-- App entry for ' + str(row[0]) + '.' + str(row[1]) + ': ' + lem + ' -->' + \
                  '<app><lem ' + lemwit + ' ' + lemsrc + ' ' + lem_xmlid + '>' \
                  + lem + '</lem>' + \
                  lemnote + \
                  '<rdg ' + rdg1wit + ' ' + rdg1src + ' ' + rdg1_xmlid + '>' + rdg1 + '</rdg>' + \
                  rdg1_note + \
                  '<rdg ' + rdg2wit + ' ' + rdg2src + ' ' + rdg2_xmlid + '>' + rdg2 + '</rdg>' + \
                  rdg2_note + \
                  '</app>\n'

        # Cleaning up some issues with the app. crit. entries.
        # Remove empty readings.
        search_no_ann = re.compile(r'<!-- NO ([A-Z]*) ANNOTATION -->')
        no_ann_replace = search_no_ann.sub('', entries)

        search_empty_readings = re.compile(
            r'<rdg wit="None" source="None" xml:id="rdg-([0-9]*).([0-9]*)-([.]*)"><!-- ([A-Z(\s)?]*([\d])?) --></rdg>')
        empty_readings_replace = search_empty_readings.sub('', no_ann_replace)

        # Remove empty witnesses
        search_wit = re.compile(r'wit="None"')
        wit_replace = search_wit.sub(r'', empty_readings_replace)

        # Remove empty sources
        search_src = re.compile(r'source="None"')
        src_replace = search_src.sub(r'', wit_replace)

        # Turn empty readings into self-closing tags.
        search_none_rdg = re.compile(r'>None</rdg>')
        none_rdg_replace = search_none_rdg.sub('/>', src_replace)

        # Remove extra white space between attributes.
        search_ws = re.compile(r'\s\s')
        ws_replace = search_ws.sub(r' ', none_rdg_replace)

        # Dealing with conventional symbols in critical editions.
        # Brackets for an addtion, first as a value of <lem> or <rdg>
        search_addition = re.compile(r'<([a-zA-Z]*)>([\sa-zA-Z]*)?(</rdg>|</lem>)')
        replace_addition1 = search_addition.sub(r'"><supplied reason="lost">\1</supplied>\2\3', ws_replace)

        # Now as part of an xml:id, where <> are not allowed.
        search_addition1 = re.compile(r'(?<=-)<([a-zA-Z]*(-[a-zA-Z])?)>')
        replace_addition2 = search_addition1.sub(r'\1-addition', replace_addition1)

        # †Crux†, first as a value of an element.
        search_crux1 = re.compile(r'†([a-zA-Z(\s)?]*)†([\sa-zA-Z]*)?(</rdg>|</lem>)')
        replace_crux1 = search_crux1.sub(r'"><sic>\1</sic>\2\3', replace_addition2)

        # Now a crux as a value of an attribute, which is not allowed.
        search_crux2 = re.compile(r'(?<=-)†([a-zA-Z(\-)?]*)†')
        replace_crux2 = search_crux2.sub(r'\1-crux', replace_crux1)

        # Lacuna *** as a value of an element.
        search_lacuna1 = re.compile(r'\*\*\*([\sa-zA-Z]*)?(</rdg>|</lem>)')
        replace_lacuna1 = search_lacuna1.sub(r'<gap reason="lost"/>\1\2', replace_crux2)

        # Lacuna *** as a value of an attribute.
        search_lacuna2 = re.compile(r'(?<=-)\*\*\*([\sa-zA-Z]*)?')
        replace_lacuna2 = search_lacuna2.sub(r'lacuna\1', replace_lacuna1)

        # Editorial deletion with brackets [] as a value of an element
        search_deletion1 = re.compile(r'\[([a-zA-Z]*)\]?(</rdg>|</lem>)')
        replace_deletion1 = search_deletion1.sub(r'<surplus>\1</surplus>\2', replace_lacuna2)

        # Editorial deletion with brackets [] as a value of an attribute
        search_deletion2 = re.compile(r'(?<=-)\[([a-zA-Z]*)\]')
        replace_deletion2 = search_deletion2.sub(r'\1-surplus', replace_deletion1)

        new_entries = replace_deletion2

        pNum = row[0]
        segNum = row[1]
        print("Now encoding note for section " + pNum + "." + segNum)
        print(new_entries + "\n")

        xpathstr = ".//tei:p[@n='" + str(pNum) + "']/tei:seg[@n='" + str(segNum) + "']"
        # possible issue: xml namespaces - default ns for this document is http://www.tei-c.org/ns/1.0
        # xpathstr = ".//p[@n='" + str(pNum) + "']/seg[@n='" + str(segNum) + "']"
        section = root.find(xpathstr,
                     namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})  # check this

        if section is None:
            print("There seems to be a problem with section " + pNum + "." + segNum)
            print("We will skip this for now.")
            continue

        text = "".join(section.itertext())

        searchLemma = re.compile(lem + "\s | " + lem + "[.,;:!?] | " + lem + " ")
        newtext = searchLemma.sub(new_entries + " ", text)

        print(newtext + "\n")
        tree.write('/Volumes/data/katy/PycharmProjects/DLL/automation/sources/basetext.xml',
                   encoding='utf-8', xml_declaration=True, default_namespace=None)
        # need to look at some of the parameters on this method ^^



os.system("open "+ new_path)
