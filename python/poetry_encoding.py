import re  # operations for regular expressions, i.e. very powerful text matching
import os  # 'operating system' - used for file input/output and automatically opening the finished file
import time  # used to add time between output statements
import codecs  # This is important for reading files with Unicode characters.
import csv  # used for processing CSV (comma separated values) input files containing app. crit. entries.
import lxml.etree as ET # used to parse XML to insert <app> tags

# this script was written by Katy Felkner (katy.felkner@ou.edu, GitHub: @katyfelkner)
# advisor: Samuel Huskey

def replace_with_xml(text, pattern, new_entries, index):
    """replaces a lemma instance within the text with its associated <app> tag.

    Arguments:
        text - the section text before replacement
        pattern - the regex match pattern for finding the lemma
            - consists of the searchLem (lemma with markup to match the text)
            - and negative lookbehind/lookahead statements to make sure the lemma is not appearing in another word
        new_entries - the <app> tag with which to replace the lemma
        index - the number of the lemma instance we are trying to replace
            - defaults to 0 (first instance) unless otherwise specified

    returns a string containing the text with <app> inserted
    """

    # counter for how many non-replacable lemma instances we have
    # i.e. we don't want to replace instances appearing within attributes or comments
    inc = 0

    #store whether the repeated text is in a lemma
    inLemma = False

    # avoid replacing lemma instances that are in comments
    if re.search("\<\!--(.)*" + pattern + "[\s\w\,]*--\>", text):
        inc += 1
    # avoid replacing lemma instances in lem @xml:id attributes
    if re.search("<lem[^<>]*?xml\:id\=\"[\w\-\.0-9]*?" + pattern + ".*?</lem>", text):
        inc += 1
        inLemma = True
    # avoid replacing lemma instances in rdg @xml:id attributes
    if re.search("<rdg[^<>]*?xml\:id\=\"[\w\-\.0-9]*?" + pattern + ".*?</rdg>", text):
        if (inLemma):
            # this is 2 b/c we need to skip both the instance in the lemma id and the reading id
            inc += 2
        else:
            inc += 1

    # find updated indices if necessary
    beg, end = [(x.start(), x.end()) for x in re.finditer(pattern, text, flags=re.IGNORECASE)][index + inc]

    # return the text with the <app> tag inserted in the proper place
    return "{0}{1}{2}".format(text[:beg], new_entries, text[end:])

def checkXML(tag):
    """checks a generated XML tag for correct syntax

    Arguments:
            tag - the tag to be checked

    returns True if syntactically valid, False otherwise
        """
    try:
        ET.fromstring(tag)
        return True
    except:
        return False


def xmlid(lr, input, p, s):
    """A function for creating the xml:id value like rdg-1.1-vicit.
        this is defined outside of make_rdg_tag() because we need to use it to make @copyOf attributes

    Arguments:
        lr - must be either "lem" or "rdg"
        input -  the text from which to make an identifier
        p - paragraph or poem number
        l - sentence or line number
        """

    # Handle readings with multiple words so that they are joined with "-"
    split = input.split(' ')
    joined = '-'.join(split)

    # deal with lacunae
    lacunaRE = re.compile("<gap-reason=[”\"]lost[”\"].*?/>")
    joined = lacunaRE.sub("-lacuna-", joined).replace("\"", '')

    # remove punctuation that would make @xml:id invalid
    puncRE = re.compile('[,;\'<>()/]')
    xmlid = 'xml:id="' + lr + '-' + str(p) + '.' + str(s) + '-' + joined + '"'

    # return the finished xml:id attribute
    return puncRE.sub('', xmlid)


def make_lem_tag(p, s, lem, wit, source, note):
    """makes a <lem> tag for one lemma.

        Arguments:
            p - paragraph number
            s - section number
            lem - the lemma as it appears in the spreadsheet
            wit - lemma witnesses as one string, separated by spaces (e.g. "A B Cac D")
            source - lemma source(s), separated by spaces (e.g. "Name OtherName ThirdName")
            note - lemma notes as one string. Multiple notes should be separated with the forward slash /
                - e.g. "This is a note / this is another note"
                - forward slash / is used as a delimiter for multiple notes, because Unicode snowman ☃ was rejected

    returns a <lem> tag with attributes properly formatted, and the correct text inside
    """

    # idLem is a version of the lemma used to make the @xml:id attribute
    # searchLem is a version of the lemma used to search the main text

    # deal with an empty lemma
    if lem == '':
           lem = '<!-- NO LEMMA -->'
           searchLem = ''

    # deal with a lemma which is a speaker
    elif re.match("\(\w+\.*\)", lem):
        searchLem = lem.replace("(", "").replace(")", "")
        idLem = searchLem + " speaker"
        lem = "<label type=\"speaker\">" + searchLem + "</label>"

    # this block deals with editorial additions, which have <> in the lemma

    # deal with lemmas of the form '<word> some other words'
    elif (re.match('<\w+>(\s)*\w+', lem)):
        newLem = '<supplied reason="lost">' + lem.split('>')[0].replace('<', '') + '</supplied>' + \
                 lem.split('>')[1]

        # a copy of the lemma with <> removed to use in xml:id attributes
        idLem = lem.replace('<', '').replace('>', '') + " addition"

        # in this case, the searchLem (used to match the base text) is the same as the marked up lemma
        searchLem = newLem
        lem = newLem

    # now deal with lemmas of the form '<word>'
    elif (re.match('<\w+>', lem)):
        searchLem = lem.replace('<', '').replace('>', '')

        # a copy of the lemma with <> removed to use in xml:id attributes
        idLem = searchLem + " addition"

        # add <supplied> tags and set searchLem
        searchLem = '<supplied reason="lost">' + searchLem + '</supplied>'
        lem = searchLem

    # initialize searchLem and idLem for all other lemmas (i.e. those that don't contain editorial additions)
    else:
        searchLem = lem
        idLem = lem

    # make the xml identifier for this lemma
    lem_xmlid = xmlid("lem", idLem, p, s)

    # modify the identifier to be used as an @target attribute
    lem_target = str(lem_xmlid.replace('xml:id=', '').replace('"', ''))

    def lem_wit(wit):
        """A function for wrapping the witness(es) for a lemma in the correct XML.

            this function returns a tuple containing:
            at index 0 - the @wit attribute of the <lem> tag
            at index 1 - a string containing relevant <witDetail> tags
        """

        if wit == '':
            # if no witnesses, return wit=None (will be cleaned up later) and no <witDetail> tags
            return ['wit="None"', '']
        else:
            detailTags = ''
            wit = wit.strip()
            split = wit.split(' ')

            # iterate through witnesses and check if each has ac, c, spl, sbl, inmg, ir
            # could add other markup here as needed
            # the regex used to match sigla will match upper and lowercase Latin letters A-Z and upper and lowercase Greek letters

            # this holds the witness sigla with markup removed
            newsplit = []
            for s in split:
                # avoid putting spreadsheet markup in witDetail tags
                if '(' in s:
                    strippedWit = s.split("(")[0]
                else:
                    strippedWit = s
                # handle original corrections
                if re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(ac\)', s):
                    # witDetail for correction-original
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + lem_target + "\" type=\"correction-original\"/>"
                    newsplit.append(s.replace("(ac)", ""))
                # matches both c and pc to maintain backwards compatibility as much as possible
                # only pc is correct. our guidelines and specs reflect this.
                elif re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(c\)', s) or re.match(
                        u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(pc\)', s):
                    # witDetail for correction-altered
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + lem_target + "\" type=\"correction-altered\"/>"
                    newsplit.append(s.replace("(c)", "").replace("(pc)", ""))
                # supra lineam
                elif re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(spl\)', s):
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + lem_target + "\">supra lineam</witDetail>"
                    newsplit.append(s.replace("(spl)", ""))
                # sub lineam
                elif re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(sbl\)', s):
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + lem_target + "\">sub lineam</witDetail>"
                    newsplit.append(s.replace("(sbl)", ""))
                # in margin
                elif re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(inmg\)', s):
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + lem_target + "\">in margin</witDetail>"
                    newsplit.append(s.replace("(inmg)", ""))
                # in rasura
                elif re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(ir\)', s):
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + lem_target + "\">in rasura</witDetail>"
                    newsplit.append(s.replace("(ir)", ""))
                # if the siglum doesn't have an annotation, it doesn't need a <witDetail>
                else:
                    newsplit.append(s)


            joined = '#'.join(newsplit)
            # This produces A#B#C. We need some space:
            search_wit = re.compile(r'(#[a-zA-Z\u0391-\u03A9\u03B1-\u03C9(a-z)?])')
            spaced_wit = search_wit.sub(r' \1', joined)
            # Now we have A #B #C. Let's put # on that first one.
            search_joined = re.compile(r'((?<!#)^[a-zA-Z\u0391-\u03A9\u03B1-\u03C9(a-z)?\s])')
            first_wit = search_joined.sub(r'#\1', spaced_wit)

            # return a tuple containing: [the @wit of the <lem> tag as a str, str containing relevant <witDetail> tags]
            return ['wit="' + str(first_wit) + '"', detailTags]

    # n.b. lemwit is a tuple not a string
    lemwit = lem_wit(wit)


    def lemsrc(source):
        """A function for wrapping the source(s) for a lemma in the correct XML.

        returns a str containing the @source attribute of the <lem> tag
        """
        if not source:
            return 'source="None"'
        else:
            # List the sigla, putting # before each one. Space will be added below.
            source = source.strip()
            split = source.split(' ')
            joined = '#'.join(split)
            # This produces A#B#C. We need some space:
            search_src = re.compile(r'(#[a-zA-Z(a-z)?])')
            spaced_src = search_src.sub(r' \1', joined)
            # Now we have A #B #C. Let's put # on that first one.
            search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
            first_src = search_joined.sub(r'#\1', spaced_src)
            return 'source="' + str(first_src) + '"'

    lemsrc = str(lemsrc(source))

    def lemnote():
        """A function for encoding any annotation on the lemma as a <note>.

        returns all note tags in a single string, e.g. "<note>this is a note</note><note>this is another note</note>"

        forward slash / is used as a delimiter for multiple notes, because Unicode snowman ☃ was rejected
        """

        noteTags = ''
        if not note:
            return '<!-- NO LEMMA ANNOTATION -->'
        else:
            if "/" in note:
                # there are multiple notes
                split = note.split("/")

                for s in split:
                    if (re.match("vulgo", s)):
                        # add the ad hoc <wit> tag for vulgo. as a witness
                        noteTags += ('<wit target="' + lem_target + '">' + s + '</wit')
                    else:
                        # wrap each note in a tag
                        noteTags += ('<note target="' + lem_target + '">' + note + '</note>')

                return noteTags
            else:
                # if only one note, wrap it in a <note> tag and return
                return '<note target="' + lem_target + '">' + note + '</note>'

    lemnote = str(lemnote())

    # return a tuple with the cleaned up lemma for searching and the full <lem> tag as a string
    return [searchLem, '<lem ' + lemwit[0] + ' ' + lemsrc + ' ' + lem_xmlid + '>' \
            + lem + '</lem>' + lemwit[1] + lemnote]


def make_rdg_tag(p, s, reading, wit, source, note):
    """makes a <rdg> tag for one reading.

        Arguments:
            p - paragraph number
            s - section number
            reading - the reading as it appears in the spreadsheet
            wit - reading witnesses as one string, separated by spaces (e.g. "A B Cac D")
            source - reading source(s), separated by spaces (e.g. "Name OtherName ThirdName")
            note - reading notes as one string. Multiple notes should be separated with the forward slash /
                - e.g. "This is a note / this is another note"
    """

    # deal with an empty reading with no notes
    # empty readings with notes are handled below
    if reading == '' and note == '':
        return ''

    elif reading == '' and re.match("copy\(", note):
        # this reading is a copyOf another reading
        # syntax for that: copy("rdg"/"lem", the full reading it's a copy of, poem number, line number)
        # if the reading in question is in this app. crit., we can process into an XML ID here
        r = note.split("(")[1].replace(")", "")
        split = r.split(",")
        other_id = xmlid(split[0], split[1].strip(), split[2].strip(), split[3].strip()).replace("xml:id=", "").replace("\"", "")
        return '<rdg copyOf="' + other_id + '"/>'

    # deal with a reading which is a speaker
    if re.match("\(\w+\.*\)", reading):
        idRdg = reading + " speaker"
        reading = "<label type=\"speaker\">" + reading.replace("(", "").replace(")", "") + "</label>"

    # this block deals with editorial additions, which have <> in the reading

    # deal with a <supplied> tag which only includes part of a word
    elif (re.search('\<\w+\s*\<gap reason=”lost”/>\s*\w+\>\w+', reading)):
        # deal with a lacuna in the middle of a word
        # this was written to deal with 13.5 but can be generalized as necessary
        reading = '<supplied reason="lost">' + reading.split('>')[0].replace('<', '', 1) + ">" +reading.split('>')[1] + '</supplied>' + reading.split('>')[2]
        # we use a separate variable to contain a version of the reading to use in xml:id
        idRdg = reading.replace('<', '').replace('>', '').replace('supplied', '').replace('reason="lost"', '') + " addition"

    # deal with readings of the form '<word> some other words' or 'some words <word>'
    elif (re.search('\<\w+\>(\s)*\w+ | \w+(\s)*\<\w+\>', reading)):
        reading = '<supplied reason="lost">' + reading.split('>')[0].replace('<', '') + '</supplied>' + \
                        reading.split('>')[1]
        # we use a separate variable to contain a version of the reading to use in xml:id
        idRdg = reading.replace('<', '').replace('>', '').replace('supplied', '').replace('reason="lost"', '') + " addition"

    # now deal with readings of the form '<word>'
    elif (re.search('<\w+>', reading)):
        reading = reading.replace('<', '').replace('>', '')
        idRdg = reading + " addition"
        reading = '<supplied reason="lost">' + reading + '</supplied>'

    # if there are no editorial addtions, initialize idRdg
    else:
        idRdg = reading

    # Handling the source(s) for the first reading
    def rdgsrc(source):
        """A function for wrapping the source(s) for a reading in the correct XML.

        returns a str containing the @source attribute of the <rdg> tag
        """
        if not source:
            return 'source="None"'
        else:
            # List the sigla, putting # before each one. Space will be added below.
            source = source.strip()
            split = source.split(' ')
            joined = '#'.join(split)
            # This produces A#B#C. We need some space:
            search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
            spaced_wit = search_wit.sub(r' \1', joined)
            # Now we have A #B #C. Let's put # on that first one.
            search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
            first_wit = search_joined.sub(r'#\1', spaced_wit)
            return 'source="' + str(first_wit) + '"'

    source = str(rdgsrc(source))

    # Handle the @xml:id and @target attributes for the reading
    rdg_xmlid = str(xmlid("rdg", idRdg, p, s))
    rdg_target = rdg_xmlid.replace("xml:id=", '').replace("\"", '')

    def rdg_wit(wit):
        """A function for wrapping the witness(es) for a reading in the correct XML.

        this function returns a tuple containing:
        at index 0 - the @wit attribute of the <rdg> tag
        at index 1 - a string containing relevant <witDetail> tags
        """

        if wit == '':
            return ['wit="None"', '']
        else:
            # List the sigla, putting # before each one. Space will be added below.
            detailTags = ''
            wit = wit.strip()
            split = wit.split(' ')
            newsplit = []
            # iterate through witnesses and check if each has ac, c, spl, sbl
            # could add other markup here as needed
            # the regex used to match sigla will match upper and lowercase Latin letters A-Z and upper and lowercase Greek letters
            for s in split:
                # avoid putting spreadsheet markup in witDetail tags
                if '(' in s:
                    strippedWit = s.split("(")[0]
                else:
                    strippedWit = s
                # handle original corrections
                if re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(ac\)', s):
                    # witDetail for correction-original
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + rdg_target + "\" type=\"correction-original\"/>"
                    newsplit.append(s.replace("(ac)", ""))
                # matches both c and pc to maintain backwards compatibility as much as possible
                # only pc is correct. our guidelines and specs reflect this.
                elif re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(c\)', s) or re.match(
                        u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(pc\)', s):
                    # witDetail for correction-altered
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + rdg_target + "\" type=\"correction-altered\"/>"
                    newsplit.append(s.replace("(c)", "").replace("(pc)", ""))
                # supra lineam
                elif re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(spl\)', s):
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + rdg_target + "\">supra lineam</witDetail>"
                    newsplit.append(s.replace("(spl)", ""))
                # sub lineam
                elif re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(sbl\)', s):
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + rdg_target + "\">sub lineam</witDetail>"
                    newsplit.append(s.replace("(sbl)", ""))
                # in margin
                elif re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(inmg\)', s):
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + rdg_target + "\">in margin</witDetail>"
                    newsplit.append(s.replace("(inmg)", ""))
                # in rasura
                elif re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(ir\)', s):
                    detailTags += "<witDetail wit=\"#" + strippedWit + "\" target=\"#" + rdg_target + "\">in rasura</witDetail>"
                    newsplit.append(s.replace("(ir)", ""))
                # if the siglum doesn't have an annotation, it doesn't need a <witDetail>
                else:
                    newsplit.append(s)

            joined = '#'.join(newsplit)
            # This produces A#B#C. We need some space:
            search_wit = re.compile(r'(#[a-zA-Z\u0391-\u03A9\u03B1-\u03C9(a-z)?])')
            spaced_wit = search_wit.sub(r' \1', joined)
            # Now we have A #B #C. Let's put # on that first one.
            search_joined = re.compile(r'((?<!#)^[a-zA-Z\u0391-\u03A9\u03B1-\u03C9(a-z)?\s])')
            first_wit = search_joined.sub(r'#\1', spaced_wit)
            return ['wit="' + str(first_wit) + '"', detailTags]

    # n.b. wit is a tuple not a string
    wit = rdg_wit(wit)

    # Notes for rdg
    def rdg_notes():
        """A function for encoding any annotation on the reading as a <note>.

        returns a tuple containing:
        at index 0 - a string containing all <note> tags that should go before the reading
        at index 1 - a string containing all <note> tags that should go after the reading

        forward slash / is used as a delimiter for multiple notes, because Unicode snowman ☃ was rejected
        """
        noteTags = ''
        # notes that should go before the reading
        beforeTags = ''
        if not note:
            return ['', '']
        else:
            if "/" in note:
                # multiple notes
                split = note.split("/")

                for s in split:
                    if (s == "an" or s == "vel"):
                        # this note goes before the reading (e.g. an or vel)
                        # easily generalized to catch other "before reading" notes
                        beforeTags += ('<note target="' + rdg_target + '">' + s + '</note>')
                    elif (re.match("vulgo", s)):
                        # add the ad hoc <wit> tag for vulgo. as a witness
                        noteTags += ('<wit>' + s + '</wit>')
                    else:
                        # this is a normal note (i.e. after the reading)
                        noteTags += ('<note target="' + rdg_target + '">' + s + '</note>')

                return [beforeTags, noteTags]
            else:
                # if there is only one note, wrap it in tags and return it
                return ['', '<note target="' + rdg_target + '">' + note + '</note>']

    # n.b. this is a tuple not a string
    notes = rdg_notes()

    # combine parts of the tag and return the finished <rdg> tag
    return notes[0] + '<rdg ' + wit[0] + ' ' + source + ' ' \
           + rdg_xmlid + '>' + reading + '</rdg>' + wit[1] + notes[1]


def cleanup_tag(entries):
    """a function for cleaning up an <app> tag. it encapsulates several cleanup tasks, including replacing editorial
    symbols with the appropriate XML markup and removing or condensing the (valid but superfluous) XML generated from
    empty columns in the CSV.

    Argument:
        - entries: an app tag that needs cleanup
    """

    search_no_ann = re.compile(r'<!-- NO ([A-Z]*) ANNOTATION -->')
    no_ann_replace = search_no_ann.sub('', entries)

    # Remove empty readings.
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

    # turn omissions in to self-closing reading tags
    search_omission = re.compile(r'>om\.</rdg>')
    replace_omission = search_omission.sub(r'/>', replace_deletion2)

    return replace_omission

# main function starts here

# we are now using LXML because it allows us to use a custom XML parser
# custom LMXL parser that won't remove comments
parser = ET.XMLParser(remove_comments=False)

# Create a variable for the path to the base text.
path = '../sources/calp-sicc-carmen4.txt'

# Open the file with utf-8 encoding.
source_file = codecs.open(path,'r','utf-8')

# Read the file.
source_text = source_file.read()

# Tell python what to search for (with thanks to https://stackoverflow.com/questions/13168761/python-use-regex-sub-multiple-times-in-1-pass).

print('Let\'s encode some poetry!')
time.sleep(2)


# Handle additive emendation, since it is indicated by < >, which would be swept up by other routines below.
print('Okay, we\'ll handle editorial additions next, since their angle brackets\n might cause trouble later.')
time.sleep(2)
search_addition = re.compile(r'<([a-zA-Z]*)>')
replace0 = search_addition.sub(r'&lt;supplied reason="lost"&gt;\1&lt;/supplied&gt;', source_text)
# this will make allow us to retrieve section text without duplicating it.
# the XML entities are replaced with <> at the very end.

# Handle lacuna.
print('We\'ll look for *** lacunae next')
time.sleep(2)
search_lacuna = re.compile(r'\*\*\*')
replace1 = search_lacuna.sub(r'&lt;gap reason="lost"/&gt; ', replace0)


# wrap all lines in <l> tags
print('Done. Next up: encoding lines.')
time.sleep(2)
# get all of the lines as a list
lines = replace1.split("\n")
# counter for total lines
i = 0
# counter for multiline lacunae
lCount = 0
newlines = []
# store the speaker of a lacuna
# this is declared outside the loop because it needs to survive multiple loop iterations
lac_speaker = ''
# use enumerate() so we can also get the index easily
for index, l in enumerate(lines):
    if l == '':
        # empty line caused by line breaks in source text
        continue
    if re.search('[0-9]+$', l):
        numbersplit = l.split(" ")
        i = int(numbersplit[-1])
        l = l.replace(" " + str(i), "")
    else:
        i += 1
    speaker_tag = ''
    if re.match("\(\w+\.*\)", l):
        # this line has a speaker
        # matches (Speaker) or (S.)
        speaker_tag = "<label type=\"speaker\">" + l.split(" ")[0].replace("(", "").replace(")", "") + "</label>"
        l = "<l n =\"" + str(i) + "\">" + l.replace(l.split(" ")[0], speaker_tag) + "</l>"
    else:
        # otherwise, just wrap line in l tags
        l = "<l n =\"" + str(i) + "\">" + l + "</l>"

    if re.search(r'&lt;gap reason="lost"/&gt;', l):
        # find and count multiline lacunae
        lCount += 1
        i -= 1
        if re.search("<label type=\"speaker\">", l):
            lac_speaker = speaker_tag

        # if the next line is NOT a lacuna, or if we have reached end of the poem, replace with <gap>
        # otherwise, keep looking for the end of the lacuna
        if re.search(r'&lt;gap reason="lost"/&gt;', lines[index + 1]) or index == len(lines) - 1:
            continue
        else:
            l = "<ab>" + lac_speaker + "<gap reason = \"lost\" quantity = \"" + str(lCount) + "\" unit = \"lines\" resp = \"#Giarratano\"/></ab>"
            lCount = 0

    newlines.append(l)

# put the list back into a string
replace2 = "".join(newlines)

# Handle crux.
print('Lines have been wrapped in numbered <l> tags')
print('Now handling special symbols. First up: †crux†.')
time.sleep(2)
search_crux = re.compile(r'†([a-zA-Z]*)†')
replace3 = search_crux.sub(r'&lt;sic&gt;\1&lt;/sic&gt;',replace2)

# Handle editorial deletion.
print('... now {editorial deletions}.')
time.sleep(2)
search_deletion = re.compile(r'\[([a-zA-Z]*)\]')
replace4 = search_deletion.sub(r'&lt;surplus&gt;\1&lt;/surplus&gt;',replace3)

# Write the TEI header.
print('Adding the TEI header and footer.')
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
            <div type="textpart" n="4" xml:id="part4">'''
# text part n = 4 is hardcoded in for now :/

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


# Combine the header, text, and footer
TEI = header + replace4 + footer

# write the xml-encoded base text to a new .xml file
print('Making a new file ...')
time.sleep(2)
# file path for final XML file
new_path = '../results/poetry-encoding.xml'

# Open the new file.
new_source = codecs.open(new_path,'w','utf-8')

# Write the contents of altered source_text to new_source.
print('Writing the XML base text to the new file ...')
time.sleep(2)
new_source.write(str(TEI))
source_file.close()

print('Now that the base text is encoded, we\'ll start on the app. crit.')
time.sleep(2)

# tree is an instance of ElementTree
# root is an instance of Element
tree = ET.parse(new_path, parser=parser)
root = tree.getroot()
# the following statement is necessary to avoid having 'ns0' as a prefix for every tag in the doc.
# the TEI namespace (default ns for this doc) is found at: http://www.tei-c.org/ns/1.0
ET.register_namespace('tei', 'http://www.tei-c.org/ns/1.0')

with open('../sources/poetry-test.csv', encoding='utf-8') as appFile:
    readApp = csv.reader(appFile, delimiter=',')
    for row in readApp:
        if row[0] == "Poem":
            # skip the first row, which contains column labels
            continue

        # get paragraph and section number and row length
        pNum = row[0]
        lNum = row[1]
        l = len(row)

        # make the lemma tag
        lemReturn = make_lem_tag(pNum, lNum, row[2], row[3], row[4], row[5])
        # searchLem is the literal string we want to find in the text
        searchLem = lemReturn[0]
        # lemtag is the tag we want to insert in place of searchLem
        lemtag = lemReturn[1].strip()

        # encode general annotations on this entry
        if row[6] == '':
            commenttag = ''
        else:
            commenttag = "<note>" + row[6] + "</note>"

        # counter for loop that makes <rdg> tags. Starts at 7 because readings start in column 7 of the CSV.
        i = 7
        rdgTags = ''

        # this loop can handle any number of readings
        while (i < (l - 1)):
            rdgTags += make_rdg_tag(pNum, lNum, row[i], row[i + 1], row[i + 2], row[i + 3])
            # each reading has four columns of data
            i += 4

        # combine everything into one <app> tag
        entries = '<!-- App entry for ' + str(row[0]) + '.' + str(row[1]) + ': ' + searchLem + ' -->' + \
                      '<app>' + lemtag + rdgTags + commenttag + '</app>'

        # clean up the <app> tag
        new_entries = cleanup_tag(entries)

        # we're going to check that the newly created lemma tag is valid XML
        # if it is valid, we will insert it into the text
        # if not, we will not insert it and will print an error message
        # the goal of this measure is to prevent XMLParseErrors and XMLSyntaxErrors
        # we want to guarantee that the output of this script is always a valid XML file.
        # this will minimize runtime exceptions and errors.
        if not checkXML(new_entries):
            #  i.e. if invalid XML was generated
            print("**** invalid XML was generated for poem " + pNum + ", line " + lNum + ", lemma: " + searchLem)
            print(new_entries)
            print("it was left unencoded for now.")
            continue

        # otherwise, valid XML was generated, so we find and replace
        print("Now encoding note for poem " + pNum + ", line " + lNum)

        print("Using XPath to find the section!....")

        # use Xpath to find the appropriate paragraph and section
        xpathstr = ".//tei:l[@n='" + str(lNum) + "']"
        linetag = root.find(xpathstr, namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})


        if (re.search("label", str(ET.tostring(linetag)))):
            # there is a label tag in the line

            if (re.match("\(\w+?\)", row[2])):
                # the lemma is an uncertain speaker
                xpathstr = ".//tei:label"
                labeltag = linetag.find(xpathstr, namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
                # store the text of the line
                tailtext = labeltag.tail
                # remove the existing label tag
                linetag.remove(labeltag)
                # insert the <app> tag (which contains at least 1 <label>) and the line text as the text of the <l> tag
                # this will be changed from text to tags at the end.
                linetag.text = new_entries + tailtext

            else:
                # normal lemma in a line with a (certain or uncertain) speaker

                if (re.search("<app>\s*<lem .*?>\s*<label>", str(ET.tostring(linetag)))):
                    # we have an uncertain speaker

                    #store line text
                    text = linetag.text

                    # hacky workaround to handle a line tag with no .text attribute
                    # e.g. lacuna, all text in another tag, etc.
                    if text is None:
                        text = str(ET.tostring(linetag))
                        text = re.sub("<l n=\"[0-9]+\">", "", text)
                        text = text.replace("</l>", "")
                        linetag.clear()
                        linetag.text = text

                    print("Replacing lemma instances with the proper <app> tag...")
                    if re.search("\([0-9]+\)", searchLem):
                        # this lemma does not apply to the first instance of the lemma text. of the form "lemma(#)"

                        # break up the lemma(#) thing
                        lemNum = searchLem.split('(')[1].replace(')', '')
                        lemNum = int(lemNum)  # to avoid possible type mismatch problems
                        newLem = searchLem.split('(')[0]

                        # update the tag with the new lemma text (i.e. remove (#) from comments and IDs)
                        new_entries = new_entries.replace(searchLem, newLem)

                        searchLem = newLem  # for naming consistency

                    else:
                        # if no occurrence number is specified, assume it applies to the first instance
                        lemNum = 1

                    # exclude lemma instances within other words. uses negative lookahead and lookbehind assertion.
                    replacePattern = "(?<![a-zA-Z])" + searchLem + "(?![a-zA-Z])"

                    try:
                        # insert the <app> tag into the text using a custom function defined above
                        # this will throw an exception (caught below) if the lemma is not found
                        newtext = replace_with_xml(text, replacePattern, new_entries, (lemNum - 1))
                        linetag.text = newtext
                    except:
                        # usually due to text/csv matching issue, meaning the script was unable to find the lemma in the base text
                        print("**** lemma not found in poem " + pNum + ", line " + lNum)
                        print("this is probably due to a text/csv mismatch")

                else:
                    # speaker is not uncertain on this line

                    # store the line text
                    text = linetag.text

                    # hacky workaround when there is no linetag.text attribute, but there are things in the line tag
                    # that we need to capture
                    if text is None:
                        text = str(ET.tostring(linetag))
                        text = re.sub("b'<l xmlns=\"http://www.tei-c.org/ns/1.0\" n=\"[0-9]+\">", "", text)
                        text = text.replace("</l>'", "")
                        linetag.clear()
                        linetag.text = text
                        # clear() destroys attributes, so we have to set line number again
                        linetag.set('n', str(lNum))

                    print("Replacing lemma instances with the proper <app> tag...")
                    if re.search("\([0-9]+\)", searchLem):
                        # this lemma does not apply to the first instance of the lemma text. of the form "lemma(#)"

                        # break up the lemma(#) thing
                        lemNum = searchLem.split('(')[1].replace(')', '')
                        lemNum = int(lemNum)  # to avoid possible type mismatch problems
                        newLem = searchLem.split('(')[0]

                        # update the tag with the new lemma text (i.e. remove (#) from comments and IDs)
                        new_entries = new_entries.replace(searchLem, newLem)

                        searchLem = newLem  # for simplicity

                    else:
                        # if no occurrence number is specified, assume it applies to the first instance
                        lemNum = 1

                    # exclude lemma instances within other words. uses negative lookahead and lookbehind assertion.
                    replacePattern = "(?<![a-zA-Z])" + searchLem + "(?![a-zA-Z])"

                    try:
                        # insert the <app> tag into the text using a custom function defined above
                        # this will throw an exception (caught below) if the lemma is not found
                        newtext = replace_with_xml(text, replacePattern, new_entries, (lemNum - 1))
                        linetag.text = newtext
                    except:
                        # usually due to text/csv matching issue, meaning the script was unable to find the lemma in the base text
                        print("**** lemma not found in poem " + pNum + ", line " + lNum)
                        print("this is probably due to a text/csv mismatch")

        else:
            # no <label> tag on this line

            # use Xpath to find the appropriate paragraph and section
            xpathstr = ".//tei:l[@n='" + str(lNum) + "']"
            section = root.find(xpathstr,
                                    namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})  # check this

            # get the section text
            text = "".join(section.itertext())

            print("Replacing lemma instances with the proper <app> tag...")
            if re.search("\([0-9]+\)", searchLem):
                # this lemma does not apply to the first instance of the lemma text. of the form "lemma(#)"

                # break up the lemma(#) thing
                lemNum = searchLem.split('(')[1].replace(')', '')
                lemNum = int(lemNum)  # to avoid possible type mismatch problems
                newLem = searchLem.split('(')[0]

                # update the tag with the new lemma text (i.e. remove (#) from comments and IDs)
                new_entries = new_entries.replace(searchLem, newLem)

                searchLem = newLem  # for naming consistency

            else:
                # if no occurrence number is specified, assume it applies to the first instance
                lemNum = 1

            # exclude lemma instances within other words. uses negative lookahead and lookbehind assertion.
            replacePattern = "(?<![a-zA-Z])" + searchLem + "(?![a-zA-Z])"

            try:
                # insert the <app> tag into the text using a custom function defined above
                # this will throw an exception (caught below) if the lemma is not found
                newtext = replace_with_xml(text, replacePattern, new_entries, (lemNum - 1))
                section.text = newtext
            except:
                # usually due to text/csv matching issue, meaning the script was unable to find the lemma in the base text
                print("**** problem with encoding poem " + pNum + ", line " + lNum)
                print("this is probably due to a text/csv mismatch")


# we're done with the csv file now
appFile.close()

# this is a workaround to deal with automatic escaping of < and >, and to clean up smart quotes
bigstr = ET.tostring(root, encoding="unicode").replace("&gt;", ">").replace("&lt;", "<").replace("”", "\"")
# had to use encoding="unicode" to avoid a type mismatch problem

print("Writing to a .xml file....")
time.sleep(2)

# parse the newly cleaned up XML
newRoot = ET.fromstring(bigstr)

tree._setroot(newRoot)
# write the new XML to the appropriate file
tree.write('../results/poetry-encoding.xml',
           encoding='utf-8', xml_declaration=True)

print("Valid XML coming your way!")
time.sleep(2)

# automatically open the finished XML file.
os.system("open /Volumes/data/katy/PycharmProjects/DLL/automation/results/poetry-encoding.xml")