import re
from enum import Enum
import os
import codecs




# discussion points: the 2-step chunking procedure increases runtime significantly - maybe from kn to n^2 + kn time?
# we will probably save some time in future steps, though
# the data structures that make a lot of this automation possible add significant memory overhead as well


# enum for types of <ab>
class Type(Enum):
    SERVIUS = 1
    SERVIUS_AUCTUS = 2
    PARALLEL = 3
    SAME = 4


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



# maybe should be moved into the class for neater encapsulation
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







# plain text encoding steps

# preprocessing


# file input here
# Open the file with utf-8 encoding.
source_file = codecs.open("../kaster/bk9.txt", 'r', 'utf-8')
# Read the file.
text = source_file.read().replace("‘", "'").replace("’", "'")



# chunking: <div> elements
# current problem: splitting on "#. " while preserving the preceding | where applicable
# possible solution: re.split to split on an "or" pattern
# then only replace the number

# presumes numbers are ASCII digits only. Should be fine.
div_chunks = re.split("(\d+\.\s)|(\|\s\d+\.\s)", text, flags=re.ASCII)

print(div_chunks)


i = 0
divs = [] # put the finished div chunks here
while (i < len(div_chunks)):
    if (div_chunks[i] == ""):
        i = i + 1
        continue

    print("loop iteration: " + str(int(i/3) + 1))
    print(div_chunks[i], div_chunks[i+1], div_chunks[i+2])


    # second element is None
    if div_chunks[i+1] is None:
        n = int(div_chunks[i].replace(". ", ""))
        text = div_chunks[i+2]

    else:
        n = int(div_chunks[i+1].replace(". ", "").replace("| ", ""))
        # add an opening | to the text bit
        text = "| " + div_chunks[i+2]

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


