import re  # operations for regular expressions, i.e. very powerful text matching
import os  # 'operating system' - used for file input/output and automatically opening the finished file
import time  # used to add time between output statements
import codecs  # This is important for reading files with Unicode characters.
import csv  # used for processing CSV (comma separated values) input files containing app. crit. entries.
import lxml.etree as ET # used to parse XML to insert <app> tags
import logging # support error logging to an external file
import logging.config # support for our logger configuration
import sys # command line arguments

def checkXML(tag):
    """checks a generated XML tag for correct syntax

    :param tag: the tag to be checked
    :return: True if syntactically valid, False otherwise
    """

    try:
        ET.fromstring(tag)
        return True
    except:
        return False

def replace_with_xml(text, pattern, new_entries, index):
    """replaces a lemma instance within the text with its associated <app> tag.

    :param text: the section text before replacement
    :param pattern: the regex match pattern for finding the lemma (consists of the searchLem (lemma with markup to match the text) and negative lookbehind/lookahead statements to make sure the lemma is not appearing in another word)
    :param new_entries: the <app> tag with which to replace the lemma
    :param index: the number of the lemma instance we are trying to replace (defaults to 0 (first instance) unless otherwise specified)

    :return: a string containing the text with <app> inserted
    """

    # counter for how many non-replacable lemma instances we have
    # i.e. we don't want to replace instances appearing within attributes or comments
    inc = 0

    #find indices of lemma match
    print("PATTERN TO BE MATCHED IS:", pattern)
    beg, end = [(x.start(), x.end()) for x in re.finditer(pattern, text, flags=re.IGNORECASE)][index]

    # avoid replacing lemma instances that are in comments
    if re.search("\<\!--(.)*" + pattern + "[\s\w\.]*--\>", text):
        inc += 1
    # avoid replacing lemma instances in xml:id attributes
    if re.search("xml\:id\=\"(.)*-" + pattern + "-", text):
        inc += 1

    # find updated indices if necessary
    beg, end = [(x.start(), x.end()) for x in re.finditer(pattern, text, flags=re.IGNORECASE)][index + inc]

    # return the text with the <app> tag inserted in the proper place
    return "{0}{1}{2}".format(text[:beg], new_entries, text[end:])


def make_lem_tag(p, s, lem, wit, source, note):
    """makes a <lem> tag for one lemma.

    :param p: paragraph number
    :param s: section number
    :param lem: the lemma as it appears in the spreadsheet
    :param wit: lemma witnesses as one string, separated by spaces (e.g. "A B Cac D")
    :param source: lemma source(s), separated by spaces (e.g. "Name OtherName ThirdName")
    :param note: lemma notes as one string. Multiple notes should be separated with the forward slash /, e.g. "This is a note / (this is another note)"

    :return: a list containing the searchLem at index 0 and the complete lemma tag at index 1
    """

    # deal with an empty lemma
    if lem == '':
           lem = '<!-- NO LEMMA -->'


    # this block deals with editorial additions, which have <> in the lemma

    # deal with lemmas of the form '<word> some other words' or 'some words here <word>'
    if (re.match('<\w+(\s+\w+)*>(\s)*\w+|(\w+(\s)*)+<\w+>', lem)):
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

    # deal with crux of the form †word†
    elif (re.match('†\w+†', lem)):
        searchLem = lem.replace('†', '')

        # a copy of the lemma with †† removed to use in xml:id attributes
        idLem = searchLem + " crux"

        # add <sic> tags and set searchLem
        searchLem = '<sic>' + searchLem + '</sic>'
        lem = searchLem


    # initialize variables for all other lemmas (i.e. those that don't contain editorial additions)
    else:
        searchLem = lem
        idLem = lem


    def lem_xmlid():
        """A function for creating the xml:id value like lem-1.1-vicit."""

        # Handle lemmas with multiple words so that they are joined with "-"
        split = idLem.split(' ')
        joined = '-'.join(split)

        # clean out remaining markup to create a valid XML attribute
        joined = joined.replace("gap-reason=”lost”", "lacuna")
        return 'xml:id="lem-' + str(p) + '.' + str(s) + '-' + joined + '"'

    # clean punctuation out of xml:id so that it is valid
    lem_xmlid = str(lem_xmlid())
    puncRE = re.compile('[,;\'<>()/]')
    lem_xmlid = puncRE.sub('', lem_xmlid)

    def lem_target():
        """ A function for creating the xml:id as the value for @target."""
        split = idLem.split(' ')
        joined = '-'.join(split)
        joined = joined.replace("gap-reason=”lost”", "lacuna")
        return "lem-" + str(p) + '.' + str(s) + '-' + joined

    lem_target = str(lem_target())

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

            # iterate through witnesses and check if each has ac, c, spl, sbl
            # could add other markup here as needed
            # the regex used to match sigla will match uppercase Latin letters A-Z and upper and lowercase Greek letters
            for s in split:
                # handle original corrections
                if re.match(u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(ac\)', s):
                    # witDetail for correction-original
                    detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + lem_target + "\" type=\"correction-original\"/>"
                # matches both c and pc to maintain backwards compatibility as much as possible
                # only pc is correct. our guidelines and specs reflect this.
                elif re.match(u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(c\)', s) or re.match(u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(pc\)', s):
                    # witDetail for correction-altered
                    detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + lem_target + "\" type=\"correction-altered\"/>"
                # supra lineam
                elif re.match(u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(spl\)', s):
                    detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + lem_target + "\">supra lineam</witDetail>"
                # sub lineam
                elif re.match(u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(sbl\)', s):
                    detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + lem_target + "\">sub lineam</witDetail>"
                # in margin
                elif re.match(u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(inmg\)', s):
                    detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + lem_target + "\">in margin</witDetail>"
                # if the sigla doesn't have an annotation, it doesn't need a <witDetail>
                else:
                    pass


            joined = '#'.join(split)
            # This produces A#B#C. We need some space:
            search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
            spaced_wit = search_wit.sub(r' \1', joined)
            # Now we have A #B #C. Let's put # on that first one.
            search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
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

        returns all note tags in a single string, e.g. "<note></note><note>this is another note</note>"

        forward slash / is used as a delimiter for multiple notes, because Unicode snowman ☃ was rejected
        """

        noteTags = ''
        if not note:
            return '<!-- NO LEMMA ANNOTATION -->'
        else:
            try:
                # throws an exception if no / in the string
                # this is caught below
                split = note.split("/")

                for s in split:
                    # wrap each note in a tag
                    # these chained replaces are sort of hacky, but it'll do
                    # use &&& as a temp placeholder for > that we DON'T want replaced
                    s = s.replace('<', '<supplied&&&').replace('>', '</supplied>').replace('&&&', '>')
                    noteTags += ('<note target="' + lem_target + '">' + s + '</note>')

                return noteTags
            except:
                # if only one note, wrap it in a <note> tag and return
                # these chained replaces are sort of hacky, but it'll do
                # use &&& as a temp placeholder for > that we DON'T want replaced
                newNote = note.replace('<', '<supplied&&&').replace('>', '</supplied>').replace('&&&', '>')
                return '<note target="' + lem_target + '">' + newNote + '</note>'

    lemnote = str(lemnote())

    # return a tuple with the cleaned up lemma for searching and the full <lem> tag as a string
    return [searchLem.strip(), '<lem ' + lemwit[0] + ' ' + lemsrc + ' ' + lem_xmlid + '>' \
            + lem + '</lem>' + lemwit[1] + lemnote]


def make_rdg_tag(p, s, reading, wit, source, note):
    """makes a <rdg> tag for one reading.

    :param p: paragraph number
    :param s: section number
    :param reading: the reading as it appears in the spreadsheet
    :param wit: reading witnesses as one string, separated by spaces (e.g. "A B Cac D")
    :param source: reading source(s), separated by spaces (e.g. "Name OtherName ThirdName")
    :param note: reading notes as one string. Multiple notes should be separated with the forward slash /,  e.g. "This is a note / (this is another note)"

    :return: the entire reading tag as a str
    """

    # deal with an empty reading
    if reading == '':
        return ''

    # this block deals with editorial additions, which have <> in the reading

    # deal with a <supplied> tag which only includes part of a word
    if (re.search('\<\w+\s*\<gap reason=”lost”/>\s*\w+\>\w+|\<\w+\s*\*\*\*\s*\w+\>\w+', reading)):
        # deal with a lacuna in the middle of a word
        # this was written to deal with 13.5 but can be generalized as necessary
        reading = '<supplied reason="lost">' + reading.split('>')[0].replace('<', '', 1) + ">" +reading.split('>')[1] + '</supplied>' + reading.split('>')[2]
        # we use a separate variable to contain the reading to use in xml:id
        idRdg = reading.replace('<', '').replace('>', '').replace('supplied', '').replace('reason="lost"', '') + " addition"

    # deal with readings of the form <word> some other words or some words <word>
    elif (re.search('\<\w+\>(\s)*\w+ | \w+(\s)*\<\w+\>', reading)):
        reading = '<supplied reason="lost">' + reading.split('>')[0].replace('<', '') + '</supplied>' + \
                        reading.split('>')[1]
        # we use a separate variable to contain the reading to use in xml:id
        idRdg = reading.replace('<', '').replace('>', '').replace('supplied', '').replace('reason="lost"', '') + " addition"

    # now deal with readings of the form '<word>' or '<some words>'
    elif (re.search('<\w+(\s+\w+)*>', reading)):
        reading = reading.replace('<', '').replace('>', '')
        idRdg = reading + " addition"
        reading = '<supplied reason="lost">' + reading + '</supplied>'

    # deal with a deletion in a reading [some words] or {some words}
    # curly braces {} are preferred but square brackets are used in some older editions
    elif (re.search('\[\w+(\s+\w+)*\]|\{\w+(\s+\w+)*\} ', reading)):
        reading = reading.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
        idRdg = reading + " deletion"
        reading = '<surplus>' + reading + '</surplus>'

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

    # Handling the xml:id for the reading
    def rdg_xmlid():
        """A function for creating the xml:id value like rdg-1.1-vicit."""

        # Handle readings with multiple words so that they are joined with "-"
        split = idRdg.split(' ')
        joined = '-'.join(split).replace("\"", '')
        joined = joined.replace("gap-reason=”lost”", "lacuna")
        return 'xml:id="rdg-' + str(p) + '.' + str(s) + '-' + joined + '"'

    # remove punctuation that would make @xml:id invalid
    rdg_xmlid = str(rdg_xmlid())
    puncRE = re.compile('[,;\'<>()/]')
    rdg_xmlid = puncRE.sub('', rdg_xmlid)

    def rdg_target():
        """ A function for creating the xml:id as the value for @target."""
        split = idRdg.split(' ')
        joined = '-'.join(split)
        joined = joined.replace("gap-reason=”lost”", "lacuna").replace("/", '')
        return 'rdg-' + str(p) + '.' + str(s) + '-' + joined

    rdg_target = str(rdg_target())

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
            for s in split:

                # iterate through witnesses and check if each has ac, c, spl, sbl
                # could add other markup here as needed
                # the regex used to match sigla will match uppercase Latin letters A-Z and upper and lowercase Greek letters
                for s in split:
                    # handle original corrections
                    if re.match(u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(ac\)', s):
                        # witDetail for correction-original
                        detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + rdg_target + "\" type=\"correction-original\"/>"
                    # matches both c and pc to maintain backwards compatibility as much as possible
                    # only pc is correct. our guidelines and specs reflect this.
                    elif re.match(u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(c\)', s) or re.match(
                            u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(pc\)', s):
                        # witDetail for correction-altered
                        detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + rdg_target + "\" type=\"correction-altered\"/>"
                    # supra lineam
                    elif re.match(u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(spl\)', s):
                        detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + rdg_target + "\">supra lineam</witDetail>"
                    # sub lineam
                    elif re.match(u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(sbl\)', s):
                        detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + rdg_target + "\">sub lineam</witDetail>"
                    # in margin
                    elif re.match(u'[A-Z\u0391-\u03A9\u03B1-\u03C9]\(inmg\)', s):
                        detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + rdg_target + "\">in margin</witDetail>"
                    # in rasura
                    elif re.match(u'[A-Za-z\u0391-\u03A9\u03B1-\u03C9]\(ir\)', s):
                        detailTags += "<witDetail wit=\"#" + s + "\" target=\"#" + rdg_target + "\">in rasura</witDetail>"
                    # if the sigla doesn't have an annotation, it doesn't need a <witDetail>
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
            try:
                # throws an exception if no / in the string
                # this is caught below
                split = re.split("(?<!\(\w)/(?!\w+\))")

                for s in split:
                    if (s == "an" or s == "vel"):
                        # this note goes before the reading (e.g. an or vel)
                        # easily generalized to catch other "before reading" notes
                        beforeTags += ('<note target="' + rdg_target + '">' + s + '</note>')

                    else:
                        # these chained replaces are sort of hacky, but it'll do
                        # use &&& as a temp placeholder for > that we DON'T want replaced
                        s = s.replace('<', '<supplied&&&').replace('>', '</supplied>').replace('&&&', '>')
                        # this is a normal note (i.e. after the reading)
                        noteTags += ('<note target="' + rdg_target + '">' + s + '</note>')

                return [beforeTags, noteTags]
            except:
                # if there is only one note, wrap it in tags and return it
                # these chained replaces are sort of hacky, but it'll do
                # use &&& as a temp placeholder for > that we DON'T want replaced
                newNote = note.replace('<', '<supplied&&&').replace('>', '</supplied>').replace('&&&', '>')
                return ['', '<note target="' + rdg_target + '">' + newNote + '</note>']

    # n.b. this is a tuple not a string
    notes = rdg_notes()

    # combine parts of the tag and return the finished <rdg> tag
    return [rdg_xmlid, notes[0] + '<rdg ' + wit[0] + ' ' + source + ' ' \
           + rdg_xmlid + '>' + reading + '</rdg>' + wit[1] + notes[1]]


def cleanup_tag(entries):
    """a function for cleaning up an <app> tag

    :param entries: a tag generated by either make_lem_tag() or make_rdg_tag()

    :return: the same tag, but with extraneous tags and markup removed
    """

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

    # turn omissions in to self-closing reading tags
    search_omission = re.compile(r'>om\.</rdg>')
    replace_omission = search_omission.sub(r'/>', replace_deletion2)

    return replace_omission

def main():

    # we are now using LXML because it allows us to use a custom XML parser
    # custom LMXL parser that won't remove comments
    parser = ET.XMLParser(remove_comments=False)

    # Create a variable for the path to the base text.
    path = sys.argv[1]

    # Open the file with utf-8 encoding.
    source_file = codecs.open(path, 'r', 'utf-8')

    # Read the file.
    source_text = source_file.read()

    # Open a log file. We will write errors improperly generated XML to this file.
    if len(sys.argv) > 4:
        # i.e. a log file is specified
        log_file = sys.argv[4]
    else:
        log_file = sys.argv[3].replace(sys.argv[3].split("/")[-1], "") + "prose-log-file.txt"

    # this dict contains configuration info for logging errors.
    # I chose to use a dict in order to avoid having a separate config file.
    # This was done to keep this script as portable as possible.
    dictLogConfig = {
        "version": 1,
        "handlers": {
            "fileHandler": {
                "class": "logging.FileHandler",
                "formatter": "myFormatter",
                "filename": log_file
                # this is done to keep output sensible to the user
                # to disable this and keep all the output, comment this line:
                , "mode": "w"
            }
        },
        "loggers": {
            "exampleApp": {
                "handlers": ["fileHandler"],
                "level": "INFO",
            }
        },

        "formatters": {
            "myFormatter": {
                "format": "%(message)s"
            }
        }
    }
    logging.basicConfig(filename=log_file, level=logging.INFO)
    logging.config.dictConfig(dictLogConfig)
    logger = logging.getLogger("Prose")

    # counters for checking CSV processing quality measures
    rows_processed = 0
    successful_rows = 0
    invalid_tags = 0
    not_found = 0

    logger.info(" Now encoding a prose text!")

    # Tell python what to search for (with thanks to https://stackoverflow.com/questions/13168761/python-use-regex-sub-multiple-times-in-1-pass).
    print('Gosh, that\'s a lot of unencoded text! We\'d better get started!')
    # time.sleep(2)

    # Handle additive emendation, since it is indicated by < >, which would be swept up by other routines below.
    print('Okay, we\'ll handle editorial additions first, since their angle brackets\n might cause trouble later.')
    # time.sleep(2)
    # for now, allowing alpha characters and spaces in additions. May also need to allow some punctuation.
    search_addition = re.compile(r'<([a-zA-Z\s]*)>')
    replace0 = search_addition.sub(r'&lt;supplied reason="lost"&gt;\1&lt;/supplied&gt;', source_text)
    # this will make allow us to retrieve section text without duplicating it.
    # the XML entities are replaced with <> at the very end.

    # Search for numbers at beginning of paragraphs, then wrap paragraph in <p n="[number]"> </p>/
    print('Done. Next up: encoding the paragraphs.')
    # time.sleep(2)
    search_paragraph = re.compile(r'\n([0-9]*)(.*)')
    replace1 = search_paragraph.sub(r'<p n="\1">\2</p>', replace0)

    # Remove empty paragraphs.
    print('Done. Now let\'s kill any empty paragraphs caused by line breaks in the original document.')
    # time.sleep(2)
    search_empty_paragraph = re.compile(r'<p n="">([\s]*)</p>')
    replace2 = search_empty_paragraph.sub(r'', replace1)
    logger.info(" Paragraphs have been encoded.")

    # Search for (number) and reformat it as <seg n="number">(number).
    print('Empty paragraphs have been killed. Handling segments now.')
    # time.sleep(2)
    search_segment = re.compile(r'\(([0-9]*)\)')
    replace3 = search_segment.sub(r'<seg n="\1">', replace2)

    # Add the closing </seg>.
    search_add_close_seg = re.compile(r'(<seg|</p>)')
    replace4 = search_add_close_seg.sub(r'</seg>\1', replace3)

    # Remove the orphan </seg> at the beginning of the paragraph.
    search_remove_orphan_seg = re.compile(r'\s</seg>(<seg n="1">)\s')
    replace5 = search_remove_orphan_seg.sub(r'\1', replace4)

    # Remove space before and after <seg> markers.
    search_remove_seg_space = re.compile(r'\s</seg><seg n="([0-9]*)">\s')
    replace6 = search_remove_seg_space.sub(r'</seg> <seg n="\1">', replace5)
    logger.info(" Segments have been encoded.")

    # Handle crux.
    print('Now handling special symbols. First up: †crux†.')
    # time.sleep(2)
    search_crux = re.compile(r'†([a-zA-Z]*)†')
    replace7 = search_crux.sub(r'&lt;sic&gt;\1&lt;/sic&gt;', replace6)

    # Handle lacuna.
    print('... now *** lacunae')
    # time.sleep(2)
    search_lacuna = re.compile(r'\*\*\*')
    replace8 = search_lacuna.sub(r'&lt;gap reason="lost"/&gt; ', replace7)

    # Handle editorial deletion.
    print('... now {editorial deletions}.')
    # time.sleep(2)
    search_deletion = re.compile(r'\[([a-zA-Z]*)\]')
    replace9 = search_deletion.sub(r'&lt;surplus&gt;\1&lt;/surplus&gt;', replace8)

    # Go back and fix the first paragraph, for some reason.
    search_first_p = re.compile(r'1<seg(.*)<p n="2"')
    replace10 = search_first_p.sub(r'<p n="1"><seg\1</seg></p>\n\n<p n="2"', replace9)
    logger.info(" Editorial symbols have been encoded.")

    logger.info(" Base text wrapped in XML.")

    # Write the TEI header.
    print('Now we\'ll add the TEI header and footer.')
    logger.info(' Adding the TEI header and footer.')
    # time.sleep(2)

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

    # Combine the header, text, and footer
    TEI = header + replace10 + footer

    # write the xml-encoded base text to a new .xml file
    print('Making a new file ...')
    # time.sleep(2)
    # file path for target XML file
    new_path = sys.argv[3]

    # Open the new file.
    new_source = codecs.open(new_path, 'w', 'utf-8')

    # Write the contents of altered source_text to new_source.
    print('Writing the XML base text to the new file ...')
    logger.info(" The encoded base text has been written to: " + new_path)
    # time.sleep(2)
    new_source.write(str(TEI))
    source_file.close()

    logger.info(" Now encoding the critical apparatus. \nEncoding errors will be shown below. \n\n")
    print('Now that the base text is encoded, we\'ll start on the app. crit.')
    # time.sleep(2)

    # tree is an instance of ElementTree
    # root is an instance of Element
    tree = ET.parse(new_path, parser=parser)
    root = tree.getroot()
    # the following statement is necessary to avoid having 'ns0' as a prefix for every tag in the doc.
    # the TEI namespace (default ns for this doc) is found at: http://www.tei-c.org/ns/1.0
    ET.register_namespace('tei', 'http://www.tei-c.org/ns/1.0')

    with open(sys.argv[2], encoding='utf-8') as appFile:
        readApp = csv.reader(appFile, delimiter=',')
        for row in readApp:
            if row[1] == "Paragraph":
                # skip the first row, which contains column labels
                continue
            rows_processed += 1

            pNum = row[1]
            sNum = row[2]
            print(pNum, sNum)
            #try:
            # get paragraph and section number and row length
            l = len(row)

            # make the lemma tag
            lemReturn = make_lem_tag(pNum, sNum, row[3], row[4], row[5], row[6])
            searchLem = lemReturn[0]
            lemtag = lemReturn[1].strip()
            print(searchLem)

            # encode general annotations on this entry
            if row[35] == '':
                commenttag = ''
            else:
                commenttag = "<note>" + row[35] + "</note>"

            # counter for loop that makes <rdg> tags. Starts at 7 because readings start in column 7 of the CSV.
            i = 7
            rdgTags = ''
            rdgIDs = []

            # this loop can handle any number of readings
            while (i < 32):
                rdg = make_rdg_tag(pNum, sNum, row[i], row[i + 1], row[i + 2], row[i + 3])
                if (len(rdg) != 0):
                    rdgTags += rdg[1]
                    rdgIDs.append(rdg[0])
                # each reading has four columns of data
                i += 4

            # combine everything into one <app> tag
            entries = '<!-- App entry for ' + str(row[1]) + '.' + str(row[2]) + ': ' + searchLem + ' -->' + \
                      '<app>' + lemtag + rdgTags + commenttag + '</app>'

            # clean up the <app> tag
            new_entries = cleanup_tag(entries)

            # we're going to check that the newly created tag is valid XML
            # if it is valid, we will insert it into the text
            # if not, we will not insert it and will print an error message
            # the goal of this measure is to prevent XMLParseErrors and XMLSyntaxErrors
            # we want to guarantee that the output of this script is always a valid XML file.
            # this will minimize runtime exceptions and errors.
            if not checkXML(new_entries):
                #  i.e. if invalid XML was generated
                print("**** invalid app tag was generated for section " + pNum + "." + sNum + ", lemma: " + searchLem)
                print(new_entries)
                print("it was left unencoded for now.")

                logmsg = " invalid app tag was generated for section " + pNum + "." + sNum + ", lemma: " + searchLem + "\n" + new_entries
                logger.error(logmsg.encode(encoding='utf-8'))
                invalid_tags += 1

                # insert ALERT comment to make it easy to fix by hand

                continue

            # code above this point written by Samuel Huskey with edits by Katy Felkner
            # code below this point written by Katy Felkner

            print("Now encoding note for section " + pNum + "." + sNum)

            print("Using XPath to find the section!....")
            # use Xpath to find the appropriate paragraph and section
            xpathstr = ".//tei:p[@n='" + str(pNum) + "']/tei:seg[@n='" + str(sNum) + "']"
            section = root.find(xpathstr,
                                namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})  # check this

            # get the section text
            text = "".join(section.itertext())
            print(text)

            # if any of the reading or lemma ids already exist in the section, we need to fix that
            # check lemma first
            lemID = lemtag.split("xml:id=\"")[1].split('"')[0]
            if re.search(lemID, text):
                # this currently only works for 2 identical lemmata
                new_entries = new_entries.replace(lemID, lemID + "-2")

            # now check readings
            for r in rdgIDs:
                if re.search(r, text):
                    # this currently only works for 2 identical readings
                    new_entries = new_entries.replace(r, r[:-1] + "-2\"")

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

            # similar thing for lemmas of the form lem2 - not all have () in this text
            elif re.search("[0-9]+$", searchLem):
                # this lemma does not apply to the first instance of the lemma text. of the form "lemma#"

                # break up the lemma# thing
                match = re.search('(([A-Za-z]+\s*)*)([0-9]+)', searchLem)
                lemNum = int(match[3])  # to avoid possible type mismatch problems
                newLem = match[1]

                # update the tag with the new lemma text (i.e. remove (#) from comments and IDs)
                new_entries = new_entries.replace(searchLem, newLem)

                searchLem = newLem  # for simplicity

            else:
                # if no occurrence number is specified, assume it applies to the first instance
                lemNum = 1

            # exclude lemma instances within other words. uses negative lookahead and lookbehind assertion.
            # this will throw an exception (caught below) if the lemma is not found
            replacePattern = "(?<![a-zA-Z\#])" + searchLem + "(?![a-zA-Z\#])"

            try:
                # insert the <app> tag into the text using a custom function defined above
                newtext = replace_with_xml(text, replacePattern, new_entries, (lemNum - 1))
            except:
                # if the above call fails, then we can't find the lemma. Print out and move on.
                # usually due to text/csv matching issue, meaning the script was unable to find the lemma in the base text
                print("**** problem with encoding section " + pNum + "." + sNum)
                print("this is probably due to a text/csv mismatch")

                logmsg = " problem finding lemma for section " + pNum + "." + sNum + ", lemma: " + searchLem + "\n"
                logger.error(logmsg.encode(encoding='utf-8'))
                not_found += 1
                continue

            # we're going to check that the newly created lemma tag is valid XML
            # if it is valid, we will insert it into the text
            # if not, we will not insert it and will print an error message
            # the goal of this measure is to prevent XMLParseErrors and XMLSyntaxErrors
            # we want to guarantee that the output of this script is always a valid XML file.
            # this will minimize runtime exceptions and errors.

            try:
                # this will throw an exception if new_entries (i.e. the new <app> tag) contains any invalid XML
                ET.fromstring(new_entries)

                # if newtext contains only valid XML, we replace the section text
                section.text = newtext

                # if we got here, replacement was successful
                successful_rows += 1
            except:
                # catch the exception from possible invalid XML
                print("**** invalid XML was generated for section " + pNum + "." + sNum + ", lemma: " + searchLem)
                print("it was left unencoded for now.")

                logmsg = " invalid XML was generated for section " + pNum + "." + sNum + ", lemma: " + searchLem + "\n" + newtext
                logger.error(logmsg.encode(encoding='utf-8'))
                invalid_tags += 1

    # we're done with the csv file now
    appFile.close()
    logger.info("Finished encoding app. crit.")

    # this is a workaround to deal with automatic escaping of < and >, and to clean up smart quotes
    bigstr = ET.tostring(root, encoding="unicode").replace("&gt;", ">").replace("&lt;", "<").replace("”", "\"")

    # write to text file so we can debug
    output_txt = codecs.open('./prelim_output.txt', 'w', 'utf-8')
    output_txt.write(bigstr)
    output_txt.close()

    # had to use encoding="unicode" to avoid a type mismatch problem
    print("Writing to a .xml file....")
    logger.info(" Finishing up the XML.")
    # time.sleep(2)

    # parse the newly cleaned up XML
    newRoot = ET.fromstring(bigstr)

    tree._setroot(newRoot)
    # write the new XML to the appropriate file
    tree.write(sys.argv[3], encoding='utf-8', xml_declaration=True)

    print("Valid XML coming your way!")
    logger.info(" Valid XML generated, encoding is complete.")

    # print some quality metrics
    print("Here are some quality metrics for overall execution: ")
    print("total CSV rows processed:", rows_processed)
    print("Rows processed successfully:", successful_rows)
    print("Syntactically invalid app tags generated:", invalid_tags)
    print("lemmas not found:", not_found)
    if rows_processed > 0: print("Success rate:", successful_rows/rows_processed)

    # automatically open the finished XML file.
    os.system("open " + sys.argv[3])

if __name__ == '__main__':
    main()