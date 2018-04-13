#! /usr/bin/env python3

# clean up extra print statements

import re
import os
import time
import codecs  # This is important for reading files with Unicode characters.
import csv
import lxml.etree as ET # used to parse XML to insert <app> tags
# we are now using LXML in order to avoid the parser removing our comments

pwd_path = '/Volumes/data/katy/PycharmProjects/DLL/automation/DemosPresentations/'

def replace_with_xml(text, pattern, new_entries, index):
    # avoid replacing the ones that are in comments or xml:id attributes
    if re.search("\<\!--(.)*" + pattern + "[\s\w]*--\>(.)*" + pattern, text):
        index += 1
        if re.search("xml\:id\=\"(.)" + pattern, text):
            index += 1

    beg, end = [(x.start(), x.end()) for x in re.finditer(pattern, text, flags=re.IGNORECASE)][index]

    return "{0}{1}{2}".format(text[:beg], new_entries, text[end:])


def make_lem_tag(p, s, lem, wit, source, note):

    if lem == '':
           lem = '<!-- NO LEMMA -->'

    # this block deals with editorial additions, which have <> in the lemma
    # deal with lemmas of the form '<word> some other words'
    # NB this won't work for <sua> acies right now because there's still a text/lem mismatch

    if (re.match('<\w+>(\s)*\w+', lem)):
        newLem = '<supplied reason="lost">' + lem.split('>')[0].replace('<', '') + '</supplied>' + \
                 lem.split('>')[1]
        # we use a separate variable to contain the lemma we want to search for
        # because of the text-retrieval function we use
        idLem = lem.replace('<', '').replace('>', '') + " addition"
        searchLem = newLem
        lem = newLem

    # now deal with lemmas of the form '<word>'
    elif (re.match('<\w+>', lem)):
        searchLem = lem.replace('<', '').replace('>', '')
        idLem = searchLem + " addition"
        searchLem = '<supplied reason="lost">' + searchLem + '</supplied>'
        # we use a separate variable to contain the lemma we want to search for
        # because of the text-retrieval function we use
        lem = searchLem

    else:
        searchLem = lem
        idLem = lem

    # A function for creating the xml:id value like lem-1.1-vicit.
    def lem_xmlid():
        # Handle lemmas with multiple words so that they are joined with "-"
        split = idLem.split(' ')
        joined = '-'.join(split)
        joined = joined.replace("gap-reason=”lost”", "lacuna")
        return 'xml:id="lem-' + str(row[0]) + '.' + str(row[1]) + '-' + joined + '"'

    lem_xmlid = str(lem_xmlid())
    puncRE = re.compile('[,;\'<>()/]')
    lem_xmlid = puncRE.sub('', lem_xmlid)

    # A function for creating the xml:id as the value for @target.
    def lem_target():
        split = idLem.split(' ')
        joined = '-'.join(split)
        joined = joined.replace("gap-reason=”lost”", "lacuna")
        return "lem-" + str(p) + '.' + str(s) + '-' + joined

    lem_target = str(lem_target())

    # A function for wrapping the witness(es) for a lemma in the correct XML.
    def lem_wit():
        if wit == '':
            return ['wit="None"', '']
        else:
            # List the sigla, putting # before each one. Space will be added below.
            detailTags = ''
            split = wit.split(' ')
            for s in split:
                # handle original corrections
                if re.match('[A-Z]ac', s):
                    # witDetail for correction-original
                    detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + lem_target + "\" type=\"correction-original\"/>"

                elif re.match('[A-Z]c', s):
                    # witDetail for correction-altered
                    detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + lem_target + "\" type=\"correction-altered\"/>"

                elif re.match('[A-Z]spl', s):
                    # witDetail for supra lineam
                    detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + lem_target + "\">supra lineam</witDetail>"

                elif re.match('[A-Z]sbl', s):
                    # witDetail for sub lineam
                    detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + lem_target + "\">sub lineam</witDetail>"
                else:
                    pass

            joined = '#'.join(split)
            # This produces A#B#C. We need some space:
            search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
            spaced_wit = search_wit.sub(r' \1', joined)
            # Now we have A #B #C. Let's put # on that first one.
            search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
            first_wit = search_joined.sub(r'#\1', spaced_wit)
            return ['wit="' + str(first_wit) + '"', detailTags]

    lemwit = lem_wit()

    # A function for wrapping the source(s) for a lemma in the correct XML.
    def lemsrc():
        if not source:
            return 'source="None"'
        else:
            # return 'source="'+row[4]+'"'
            # List the sigla, putting # before each one. Space will be added below.
            split = source.split(' ')
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
        witDets = ''
        noteTags = ''
        if not note:
            return '<!-- NO LEMMA ANNOTATION -->'
        else:
            try:
                split = note.split(";")

                for s in split:
                    if re.search("\[", s):
                        # encode a wit detail
                        s = s.replace("[", '').replace("]", '')
                        wit = s.split(" ")[0]
                        message = s.replace(wit, "")

                        witDets += ("<witDetail wit=\"#" + wit + "\" target=\"#" + lem_target + \
                                    "\">" + message + "</witDetail>")

                    else:
                        # this is a normal note not a wit detail
                        noteTags += ('<note target="' + lem_target + '">' + note + '</note>')

                return witDets + noteTags
            except:
                return '<note target="' + lem_target + '">' + note + '</note>'

    lemnote = str(lemnote())

    return [searchLem, '<lem ' + lemwit[0] + ' ' + lemsrc + ' ' + lem_xmlid + '>' \
            + lem + '</lem>' + lemwit[1] + lemnote]


def make_rdg_tag(p, s, reading, wit, source, note):
# Handling a reading
        def rdg():
            if not reading:
                return '<!-- NO READING -->'
            else:
                return reading


        reading = str(rdg())
        if reading == '<!-- NO READING -->':
            return ''
        else:
            pass

        # this block deals with editorial additions, which have <> in the lemma
        # deal with lemmas of the form '<word> some other words'

        if (re.match('<\w+>(\s)*\w+ | \w+(\s)*<\w+> | <\w+(\s)*<gap reason="lost"/>(\s)*\w+>\w+', reading)):
            reading = '<supplied reason="lost">' + reading.split('>')[0].replace('<', '') + '</supplied>' + \
                        reading.split('>')[1]
            # we use a separate variable to contain the lemma we want to search for
            # because of the text-retrieval function we use
            idRdg = reading.replace('<', '').replace('>', '').replace('supplied', '').replace('reason="lost"', '') + " addition"

            print(idRdg)


            # now deal with lemmas of the form '<word>'
        elif (re.match('<\w+>', reading)):
            reading = reading.replace('<', '').replace('>', '')
            idRdg = reading + " addition"
            reading = '<supplied reason="lost">' + reading + '</supplied>'
            # we use a separate variable to contain the lemma we want to search for
            # because of the text-retrieval function we use
        else:
            idRdg = reading

        # Handling the source(s) for the first reading
        def rdgsrc():
            if not source:
                return 'source="None"'
            else:
                # List the sigla, putting # before each one. Space will be added below.
                split = source.split(' ')
                joined = '#'.join(split)
                # This produces A#B#C. We need some space:
                search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
                spaced_wit = search_wit.sub(r' \1', joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1', spaced_wit)
                return 'source="' + str(first_wit) + '"'


        source = str(rdgsrc())


        # Handling the xml:id for the reading
        def rdg_xmlid():
            # Handle readings with multiple words so that they are joined with "-"
            split = idRdg.split(' ')
            joined = '-'.join(split).replace("\"", '')
            joined = joined.replace("gap-reason=”lost”", "lacuna")
            return 'xml:id="rdg-' + str(p) + '.' + str(s) + '-' + joined + '"'

        # remove punctuation that would make @xml:id invalid
        rdg_xmlid = str(rdg_xmlid())
        puncRE = re.compile('[,;\'<>()/]')
        rdg_xmlid = puncRE.sub('', rdg_xmlid)

        # Target for rdg
        def rdg_target():
            split = idRdg.split(' ')
            joined = '-'.join(split)
            joined = joined.replace("gap-reason=”lost”", "lacuna")
            return 'rdg-' + str(p) + '.' + str(s) + '-' + joined


        rdg_target = str(rdg_target())

        # A function for wrapping the witness(es) for a lemma in the correct XML.
        def rdg_wit():
            if wit == '':
                return ['wit="None"', '']
            else:
                # List the sigla, putting # before each one. Space will be added below.
                detailTags = ''
                split = wit.split(' ')
                for s in split:
                    # handle original corrections
                    if re.match('[A-Z]ac', s):
                        #witDetail for correction-original
                        detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + rdg_target + "\" type=\"correction-original\"/>"

                    elif re.match('[A-Z]c', s):
                        #witDetail for correction-altered
                        detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + rdg_target + "\" type=\"correction-altered\"/>"

                    elif re.match('[A-Z]spl', s):
                    # witDetail for supra lineam
                        detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + rdg_target + "\">supra lineam</witDetail>"

                    elif re.match('[A-Z]sbl', s):
                    # witDetail for sub lineam
                        detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + rdg_target + "\">sub lineam</witDetail>"
                    else:
                        pass

                joined = '#'.join(split)
                # This produces A#B#C. We need some space:
                search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
                spaced_wit = search_wit.sub(r' \1', joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1', spaced_wit)
                return ['wit="' + str(first_wit) + '"', detailTags]

        wit = rdg_wit()

        # Notes for rdg
        def rdg_notes():
            witDets = ''
            noteTags = ''
            beforeTags = ''
            if not note:
                return ['', '']
            else:
                try:
                    split = note.split(";")

                    for s in split:
                        if re.search("\[", s):
                            # encode a wit detail
                            s = s.replace("[", '').replace("]", '')
                            wit = s.split(" ")[0]
                            message = s.replace(wit, "")

                            witDets += ("<witDetail wit=\"#" + wit + "\" target=\"#" + rdg_target + \
                                        "\">" + message + "</witDetail>")

                        elif (s == "an" or s == "vel"):
                            # this note goes before the reading (e.g. an or vel)
                            beforeTags += ('<note target="' + rdg_target + '">' + s + '</note>')

                        else:
                            # this is a normal note not a wit detail
                            noteTags += ('<note target="' + rdg_target + '">' + s + '</note>')

                    return [beforeTags, witDets + noteTags]
                except:
                    return [beforeTags, '<note target="' + rdg_target + '">' + note + '</note>']

        notes = rdg_notes()
        return notes[0] + '<rdg ' + wit[0] + ' ' + source + ' ' \
                + rdg_xmlid + '>' + reading + '</rdg>' + wit[1] + notes[1]

def cleanup_tag(entries):
    # Cleaning up some issues with the app. crit. entries.
    # Remove empty readings.
    search_no_ann = re.compile(r'<!-- NO ([A-Z]*) ANNOTATION -->')
    no_ann_replace = search_no_ann.sub('', entries)

    search_empty_readings = re.compile(
        r'<rdg wit="None" source="None" xml:id="rdg-([0-9]*).([0-9]*)-([.]*)"><!-- ([A-Z(\s)?]*([\d])?) --></rdg>')
    empty_readings_replace = search_empty_readings.sub('', no_ann_replace)

    search_empty_readings2 = re.compile(
        r'<rdg xml:id="rdg-([0-9]*).([0-9]*)-"></rdg>')
    empty_readings_replace2 = search_empty_readings2.sub('', empty_readings_replace)

    # Remove empty witnesses
    search_wit = re.compile(r'wit="None"')
    wit_replace = search_wit.sub(r'', empty_readings_replace2)

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

    # deal with <rdg>om.</rdg>
    search_omission = re.compile(r'>om\.</rdg>')
    replace_omission = search_omission.sub(r'/>', replace_deletion2)
    # pretty sure this works?

    new_entries = replace_omission
    return new_entries

# custom parser that won't remove comments
parser = ET.XMLParser(remove_comments=False)

# Create a variable for the path to the base text.
path = pwd_path + 'basetext.txt'

# Open the file with utf-8 encoding.
source_file = codecs.open(path,'r','utf-8')

# Read the file.
source_text = source_file.read()

# Tell python what to search for (with thanks to https://stackoverflow.com/questions/13168761/python-use-regex-sub-multiple-times-in-1-pass).

print('O di immortales! That\'s a lot of unencoded text!')
time.sleep(1)

# Handle additive emendation, since it is indicated by < >, which would be swept up by other routines below.
print('Okay, we\'ll handle editorial additions first, since their angle brackets\n might cause trouble later.')
time.sleep(1)
search_addition = re.compile(r'<([a-zA-Z]*)>')
replace0 = search_addition.sub(r'&lt;supplied reason="lost"&gt;\1&lt;/supplied&gt;', source_text)
# this will make allow us to retrieve section text without duplicating it.
# the XML entities are replaced with <> at the very end.

# Search for numbers at beginning of paragraphs, then wrap paragraph in <p n="[number]"> </p>/
print('Done. Next up: encoding the paragraphs.')
time.sleep(1)
search_paragraph = re.compile(r'\n([0-9]*)(.*)')
replace1 = search_paragraph.sub(r'<p n="\1">\2</p>',replace0)

# Remove empty paragraphs.
print('Done. Now let\'s kill any empty paragraphs caused by line breaks in the original document.')
time.sleep(1)
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
replace7 = search_crux.sub(r'&lt;sic&gt;\1&lt;/sic&gt;',replace6)

# Handle lacuna.
print('... now *** lacunae')
time.sleep(3)
search_lacuna = re.compile(r'\*\*\*')
replace8 = search_lacuna.sub(r'&lt;gap reason="lost"/&gt; ', replace7)

# Handle editorial deletion.
print('... now {editorial deletions}.')
time.sleep(3)
search_deletion = re.compile(r'\[([a-zA-Z]*)\]')
replace9 = search_deletion.sub(r'&lt;surplus&gt;\1&lt;/surplus&gt;',replace8)

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
new_path = pwd_path + 'RB-demo.xml'

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

print('Wow! That saved a lot of time!')
time.sleep(3)

print('Now that the base text is encoded, we\'ll start on the app. crit.')
time.sleep(2)


print('We\'re going to encode the notes one-by-one. <app> tags will appear as they are encoded.')
time.sleep(2)

# tree is an instance of ElementTree
# root is an instance of Element
tree = ET.parse(new_path, parser=parser)
root = tree.getroot()
# the following statement is necessary to avoid having 'ns0' as a prefix for every tag in the doc.
# the TEI namespace (default ns for this doc) is found at: http://www.tei-c.org/ns/1.0
ET.register_namespace('tei', 'http://www.tei-c.org/ns/1.0')

with open(pwd_path + 'RB-app-test.csv', encoding='utf-8') as appFile:
    readApp = csv.reader(appFile, delimiter=',')
    for row in readApp:
        if row[0] == "Paragraph":
            continue
            # skip the first row, which contains column labels
        try:
            time.sleep(.5)
            pNum = row[0]
            sNum = row[1]
            l = len(row)

            # Defining the lemma.
            lemReturn = make_lem_tag(pNum, sNum, row[2], row[3], row[4], row[5])
            searchLem = lemReturn[0]
            lemtag = lemReturn[1].strip()

            if row[6] == '':
                commenttag = ''
            else:
                commenttag = "<note>" + row[6] + "</note>"

            i = 7
            rdgTags = ''

            while (i < (l - 1)):
                rdgTags += make_rdg_tag(pNum, sNum, row[i], row[i + 1], row[i + 2], row[i + 3])
                i += 4

            # ideas: making 4-tuples first, then iterating through those
            # pros: probably easier to avoid an infinite loop
            # cons: lots of extra steps, potential for off by one errors

            # other idea: iterating over col in row, removing extra tags as we go.
            # use make_rdg_tag(p, s, row[n], row[n+1]...
            # pros: no tedious tuple-making
            # cons: syntactically challenging, higher probability of infinite loop



            entries = '<!-- App entry for ' + str(row[0]) + '.' + str(row[1]) + ': ' + searchLem + ' -->' + \
                      '<app>' + lemtag + rdgTags + commenttag + '</app>'

            new_entries = cleanup_tag(entries)

            # code above this point written by Samuel Huskey with minor edits by Katy Felkner
            # code below this point written by Katy Felkner

            print("Now encoding note for section " + pNum + "." + sNum)

            print("Using XPath to find the section!....")
            xpathstr = ".//tei:p[@n='" + str(pNum) + "']/tei:seg[@n='" + str(sNum) + "']"
            section = root.find(xpathstr,
                                namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})  # check this

            text = "".join(section.itertext())

            print("Replacing lemma instances with the proper <app> tag...")
            if re.search("\([0-9]+\)", searchLem):
                # this lemma does not apply to the first instance of the lemma text

                # break up the lemma(#) thing
                lemNum = searchLem.split('(')[1].replace(')', '')
                lemNum = int(lemNum)  # we were having type mismatch problems
                newLem = searchLem.split('(')[0]

                # update the tag with the new lemma text
                new_entries = new_entries.replace(searchLem, newLem)

                searchLem = newLem  # for simplicity

            else:
                lemNum = 1


            replacePattern = "(?<![a-zA-Z-])" + searchLem + "(?![a-zA-Z-])"
            # custom function defined above
            newtext = replace_with_xml(text, replacePattern, new_entries, (lemNum - 1))

            section.text = newtext

        except:
            print("**** problem with encoding section " + pNum + "." + sNum)
            print("this is probably due to a text/csv mismatch")



# we're done with the csv file now
appFile.close()

bigstr = ET.tostring(root, encoding="unicode").replace("&gt;", ">").replace("&lt;", "<").replace("”", "\"")

print("Writing to a .xml file....")
time.sleep(2)

newRoot = ET.fromstring(bigstr)

tree._setroot(newRoot)
tree.write(pwd_path + 'RB-demo.xml',
           encoding='utf-8', xml_declaration=True)

print("Valid XML coming your way!")
time.sleep(2)

#openstring = 'open ' + pwd_path + 'RB-demo.xml'
#os.system(openstring)