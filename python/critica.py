#! /usr/bin/env python3

# This is a program for encoding the contents of a text file as entries in the apparatus criticus of an LDLT edition. 

import re
import time
import os
import codecs # This is important for reading files with Unicode characters.

# Create a variable for the path to the appendix critica.
path = '/Users/sjhuskey/Documents/Sam-Py/DLL-Scripts/appendix-critica.txt'

# Open the file with utf-8 encoding.
source_file = codecs.open(path,'r','utf-8')

# Read the file.
source_text = source_file.read()

# Tell python what to search for.
# First, define a search term. This one searches for strings like 1.1 lemma] variant W.
print('Searching for text to encode …')
time.sleep(3)
search_text_entries = re.compile(r'''
    ([0-9]*\.[0-9]*)\s              # Paragraph and section number.
    ([a-zA-Z(\s)?]*)\]\s            # Lemma followed by ]
    ([a-zA-Z\-(\s)?]*)\s            # Reading
    ([A-Z(\*)?])                    # Witness
    ''',re.VERBOSE)

# Now, do the substitution to encode the match, using captured groups.
print('Found it! Encoding now …')
replace1 = search_text_entries.sub(r'<app><lem xml:id="lem-\1">\2</lem><rdg wit="#\4">\3</rdg></app>\n', source_text)

# Search for the entries where there is an omission (e.g., 1.1 lemma om. M).
print('Now looking for entries with an omission.')
time.sleep(3)
search_text_omissions = re.compile(r'''
    ([0-9]*\.[0-9]*)\s              # Paragraph and section number.
    ([a-zA-Z(\s)?^(?!om\.)*$]*)\s   # Lemma, excluding "om."
    (om\.)\s                        # "om."
    ([A-Z(\*)?])                    # Witness that omits the lemma.
    ''',re.VERBOSE)

# Do the substitution.
print('Found them. Encoding now …')
time.sleep(3)
replace2 = search_text_omissions.sub(r'<app><lem xml:id="\1">\2</lem><rdg wit="#\4"/></app>\n', replace1)

# Tell the script where to write the new file.
print('Writing changes to new file.')
time.sleep(3)
new_path = '/Users/sjhuskey/Documents/Sam-Py/DLL-Scripts/replace.txt' 

# Open the new file.
new_source = codecs.open(new_path,'w','utf-8')

# Write the contents of altered source_text to new_source.
new_source.write(str(replace2))

# Close the old and new source files.
source_file.close()
new_source.close()

print('Wow! That saved a lot of time!')
print('Encoded entries coming your way!')
time.sleep(3)

os.system("open "+ new_path)
