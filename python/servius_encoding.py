import re # operations for regular expressions, i.e. very powerful text matching
from enum import Enum # make an enumerated list of possible types for a text thing
import os # 'operating system' - used for file input/output and automatically opening the finished file
import codecs # This is important for reading files with Unicode characters.
import time # used to add time between output statements
import csv  # used for processing CSV (comma separated values) input files containing app. crit. entries.
import lxml.etree as ET # used to parse XML to insert <app> tags
import logging # support error logging to an external file
import logging.config # support for our logger configuration
import sys # command line arguments


# enum for types of <ab>
class Type(Enum):
    SERVIUS = 1
    SERVIUS_AUCTUS = 2
    PARALLEL = 3
    SAME = 4

# TODO: SOME OF THESE BUILT-INS need work
# builtin methods of this class defined with a lot of help from Chapter 9 of Fluent Python by Ramalho
# a ServThing instance is analogous to either a <seg> or two <seg>s inside a <choice>
class ServThing():
    # properties: type, SA, servius
    # methods: constructor, accessors and mutators
    # some ouptut methods, iter, maybe comparison methods, maybe a pretty-print method
    # look at Fluent Python and figure out how the heck to define this class

    # the constructor
    # we're gonna punt the responsibility of checking the type to the caller for now
    def __init__(self, type, text):
        self.__xml = ""
        if isinstance(type, Type):
            self.__textType = type
        else:
            raise TypeError("invalid type specified for thing")

        if self.__textType == Type.SAME:
            self.servius = text.strip()
            self.auctus = text.strip()

        elif self.__textType == Type.PARALLEL:
            # the class will handle splitting parallel text into SA and S
            spl = text.split("|")
            #spl[0] is either empty or whitespace
            self.auctus = spl[1].strip()
            self.servius = spl[2].strip()

        # we explicitly set unused attributes to None to make it harder to mix up the types
        elif self.__textType == Type.SERVIUS:
            self.servius = text.strip()
            self.auctus = None

        else: # i.e. __textType == Type.SERVIUS_AUCTUS
            self.auctus = text.replace("|", "").strip()
            self.servius = None

        # make XML text
        self.XMLify()

    def addtext(self, text):
        if self.__textType == Type.SAME:
            self.servius = self.servius + " " + text.strip()
            self.auctus = self.auctus + " " + text.strip()

        elif self.__textType == Type.PARALLEL:
            # here is where the magic to fix the tarahumara problem goes
            # the class will handle splitting parallel text into SA and S
            spl = text.split("|")
            # spl[0] is either empty or whitespace
            self.auctus = self.auctus + " " + spl[1].strip()
            self.servius = self.servius + " " + spl[2].strip()

            # we explicitly set unused attributes to None to make it harder to mix up the types
        elif self.__textType == Type.SERVIUS:
            self.servius = self.servius + " " + text.strip()

        else:  # i.e. __textType == Type.SERVIUS_AUCTUS
            self.auctus = self.auctus + " " + text.replace("|", "").strip()

        # we need to re-XMLify it
        self.XMLify()

    # has textType, Servius Auctus text, Servius text, and XML
    @property
    def textType(self):
        return self.__textType

    @property
    def xml(self):
        return self.__xml

    # these are some methods to make our object behave "Pythonically"
    def __iter__(self):
        pass
        # TODO: decide what we want the iterable representation to be

    def __repr__(self):
        # this is temporary
        # TODO: make this prettier
        return "type: " + str(self.textType) + "\n" + self.xml

    def __str__(self):
        # this is temporary
        # TODO: make this prettier
        return "type: " + str(self.textType) + "\n" + self.xml

    # helper method for XMLify()
    def __XMheLp(self, text):

        # editorial additions <>
        # process each angle bracket individually to allow for
        search_addition = re.compile(r'<')
        text = search_addition.sub(r'&lt;supplied reason="lost"&gt;', text)
        search_addition = re.compile(r'>')
        text = search_addition.sub(r'&lt;/supplied&gt;', text)
        # this will make allow us to retrieve section text without duplicating it.
        # the XML entities are replaced with <> at the very end.

        # assume there is only one ALL CAPS LEMMA in the text
        # if there's more than one, we have bigger problems
        match = re.match("^([A-Z][A-Z[\]() &<>'.,;:?!_*]+)(?![a-z])", text)
        if match:
            # TODO: for now, we are using Kaster's <quote type=lemma> syntax. Check this.
            quote_tag = '&lt;quote type="lemma"&gt;' + match[0] + '&lt;/quote&gt;'
            text = text.replace(match[0], quote_tag).strip()

        # clean up stray single newlines
        text = text.replace("\n", " ")



        # Handle crux.
        search_crux = re.compile(r'†([a-zA-Z]*)†')
        text = search_crux.sub(r'&lt;sic&gt;\1&lt;/sic&gt;', text)

        # Handle lacuna.
        search_lacuna = re.compile(r'\*\*\*')
        text = search_lacuna.sub(r'&lt;gap reason="lost"/&gt; ', text)

        # Handle editorial deletion.
        search_deletion = re.compile(r'\[([a-zA-Z]*)\]')
        text = search_deletion.sub(r'&lt;surplus&gt;\1&lt;/surplus&gt;', text)

        print("THIS IS WHAT XMLHELP GAVE US: " + text)
        return text


    # the main XMLify() method
    # this should be the only method allowed to modify the self.__xml attr
    def XMLify(self):
        if self.textType == Type.SERVIUS:
            self.__xml = "<seg source=\"#Σ\">" + self.__XMheLp(self.servius) + "</seg>"
        elif self.textType == Type.SERVIUS_AUCTUS:
            self.__xml = "<seg source=\"#DS\">" + self.__XMheLp(self.auctus) + "</seg>"
        elif self.textType == Type.PARALLEL:
            xmltemp = "<choice>" + "<seg source=\"#DS\">" + self.__XMheLp(self.auctus) + "</seg>"
            xmltemp = xmltemp + "<seg source=\"#Σ\">" + self.__XMheLp(self.servius) + "</seg>" + "</choice>"
            self.__xml = xmltemp
        else: # i.e. text is the same
            self.__xml = "<seg source=\"#Σ #DS\">" + self.__XMheLp(self.servius) + "</seg>"

        print("MY XML IS: " + self.xml)

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

# maybe should be moved into the class for neater encapsulation
# no, it shouldn't, because we check type in order to decide whether to instantiate a ServThing
def thing_type(thing):
    """This function checks the type (S, SA, parallel, or same) of a text thing.

    returns an instance of Type"""

    # parallel things follow the pattern: | (space(s)) some text (space(s)) | (whitespace(s)) other text
    # regex for this pattern "\| (\w|[[\]() <>.,;:?!_])+\| (\w|[[\]() <>.,;:?!_])+"
    if re.match("\| (\w|[[\]() <>'.,;:?!_*])+\| (\w|[[\]() <>'.,;:?!_*])+", thing):
        return Type.PARALLEL

    # S things start with 2 spaces
    elif re.match("  ", thing):
        return Type.SERVIUS

    # SA things start with a | and don't match the pattern above
    elif re.match("\|", thing):
        return Type.SERVIUS_AUCTUS

    # same things have no special markup.
    else:
        return Type.SAME

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

    # find indices of lemma match
    beg, end = [(x.start(), x.end()) for x in re.finditer(pattern, text, flags=re.IGNORECASE)][index]

    # avoid replacing lemma instances that are in comments
    if re.search("\<\!--(.)*" + pattern + "[\s\w]*--\>", text):
        inc += 1
        # avoid replacing lemma instances in xml:id attributes
        if re.search("xml\:id\=\"(.)*-" + pattern + "-", text):
            inc += 1

        # find updated indices if necessary
        beg, end = [(x.start(), x.end()) for x in re.finditer(pattern, text, flags=re.IGNORECASE)][index + inc]

     # return the text with the <app> tag inserted in the proper place
    return "{0}{1}{2}".format(text[:beg], new_entries, text[end:])

# APP CRIT ENCODING FUNCTIONS HERE
# TODO: MODIFY THESE TO WORK FOR THE SERVIUS CSV

# TODO: MODIFY TO WORK FOR THE SERVIUS CSV
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

    # deal with lemmas of the form '<word> some other words'
    if (re.match('<\w+>(\s)*\w+', lem)):
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
                    noteTags += ('<note target="' + lem_target + '">' + note + '</note>')

                return noteTags
            except:
                # if only one note, wrap it in a <note> tag and return
                return '<note target="' + lem_target + '">' + note + '</note>'

    lemnote = str(lemnote())

    # return a tuple with the cleaned up lemma for searching and the full <lem> tag as a string
    return [searchLem, '<lem ' + lemwit[0] + ' ' + lemsrc + ' ' + lem_xmlid + '>' \
            + lem + '</lem>' + lemwit[1] + lemnote]

# TODO: MODIFY TO WORK FOR THE SERVIUS CSV
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
    if (re.search('\<\w+\s*\<gap reason=”lost”/>\s*\w+\>\w+', reading)):
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
                        # this is a normal note (i.e. after the reading)
                        noteTags += ('<note target="' + rdg_target + '">' + s + '</note>')

                return [beforeTags, noteTags]
            except:
                # if there is only one note, wrap it in tags and return it
                return ['', '<note target="' + rdg_target + '">' + note + '</note>']

    # n.b. this is a tuple not a string
    notes = rdg_notes()

    # combine parts of the tag and return the finished <rdg> tag
    return notes[0] + '<rdg ' + wit[0] + ' ' + source + ' ' \
           + rdg_xmlid + '>' + reading + '</rdg>' + wit[1] + notes[1]

# TODO: MODIFY TO WORK FOR SERVIUS CSV
# this one maybe doesn't need to modified? don't know yet
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

# this is the main function
def main():
    # TODO: write function-level doc for this

    # ######### file inputs and logger config #########
    # we are now using LXML because it allows us to use a custom XML parser
    # custom LMXL parser that won't remove comments
    parser = ET.XMLParser(remove_comments=False)

    # Create a variable for the path to the base text.
    path = sys.argv[1]

    # Open the file with utf-8 encoding.
    source_file = codecs.open(path, 'r', 'utf-8')

    # Read the file.
    text = source_file.read().replace("‘", "'").replace("’", "'")

    # Open a log file. We will write errors improperly generated XML to this file.
    if len(sys.argv) > 4:
        # i.e. a log file is specified
        log_file = sys.argv[4]
    else:
        log_file = sys.argv[3].replace(sys.argv[3].split("/")[-1], "") + "servius-log-file.txt"

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
    logger = logging.getLogger("Servius")
    logger.info(" Now encoding a some Servius!")


    # ######### plain text encoding steps #########
    # preprocessing


    



    # chunking: <div> elements
    # current problem: splitting on "#. " while preserving the preceding | where applicable
    # possible solution: re.split to split on an "or" pattern
    # then only replace the number

    # presumes numbers are ASCII digits only. Should be fine.
    div_chunks = re.split("(\d+\.\s)|(\|\s\d+\.\s)", text, flags=re.ASCII)

    print(div_chunks)

    i = 0
    divs = []  # put the finished div chunks here
    while (i < len(div_chunks)):
        if (div_chunks[i] == ""):
            i = i + 1
            continue

        print("loop iteration: " + str(int(i / 3) + 1))
        print(div_chunks[i], div_chunks[i + 1], div_chunks[i + 2])

        # second element is None
        if div_chunks[i + 1] is None:
            n = int(div_chunks[i].replace(". ", ""))
            text = div_chunks[i + 2]

        else:
            n = int(div_chunks[i + 1].replace(". ", "").replace("| ", ""))
            # add an opening | to the text bit
            text = "| " + div_chunks[i + 2]

        # we now have the text of a div - process the ABs in it

        caps_pattern = re.compile("\n\n(?=((\|\s)*(\s{2})*[A-Z]+(?![a-z]|\s*[0-9])))")
        anon_blocks = re.split(caps_pattern, text)

        print(anon_blocks)

        finished_blocks = []
        ### LOOP TO PROCESS THE ANON BLOCKS
        for a in anon_blocks:
            print("ANONYMOUS BLOCK LOOP EXECUTION")
            # skip unneeded match captures
            if a is None or a == "" or not re.search("\w*\s\w", a):
                print("skipped processing: " + str(a))
                continue

            print("did not skip processing: " + a)
            things = a.split("\n\n")
            print("****** these are the things******")
            print(things)
            prevType = -1
            thisType = -1
            ab_things = []
            abIndex = 0
            # iterate over things, check types and combine things as necessary
            for index, t in enumerate(things):
                if index == 0:
                    thisType = thing_type(t)
                else:
                    prevType = thisType
                    thisType = thing_type(t)

                print("Loop iteration: " + str(index))

                if prevType == thisType:
                    # we need to combine this thing with the last one
                    print("FOUND THE SAME TYPE")
                    ab_things[abIndex - 1].addtext(t)
                elif prevType == Type.PARALLEL and (thisType == Type.SERVIUS or thisType == Type.SERVIUS_AUCTUS):
                    # TARAHUMARA PROBLEM
                    # when we find a parallel chunk immediately followed by an SA chunk (or S chunk?),
                    # append the text of the second chunk to the SA (or S, as appropriate) text of the first chunk
                    # then remove the second chunk from the list.
                    print("FOUND THE LINE 547 THING")
                    ab_things[abIndex - 1].addtext(t)
                else:
                    # otherwise, make a new thing
                    ab_things.append(ServThing(thisType, t))
                    abIndex = abIndex + 1

            print("###### here are the generated <seg> tags #####")
            print(ab_things)
            # combine the things and wrap them in an <ab>
            a = "<ab>"
            for ab in ab_things:
                a = a + ab.xml

            a = a + "</ab>"
            print(a)
            finished_blocks.append(a)

        text = '<div type="textpart" n="' + str(n) + '">' + "\n".join(finished_blocks) + "</div>"

        divs.append(text)
        i = i + 3

    print(divs)

    # let's output some shit to an xml file
    new_path = "./test-output.xml"
    out_file = codecs.open(new_path, 'w', 'utf-8')
    big_str = "<root>" + "\n".join(divs).replace("&gt;", ">").replace("&lt;", "<").strip() + "</root>"
    out_file.write(big_str)
    os.system("open ./test-output.xml")

if __name__ == '__main__':
    main()