import re
import codecs # This is important for reading files with Unicode characters.

# Create a variable for the path to the appendix critica.
path = '/Users/sjhuskey/Documents/Sam-Py/DLL-Scripts/appendix-critica.txt'

# Open the file with utf-8 encoding.
source_file = codecs.open(path,'r','utf-8')

# Read the file.
source_text = source_file.read()

# Tell python what to search for.
# First, define a search term. This one searches for strings like 1.1 lemma] variant W.

search_text = re.compile(r'''
    ([0-9]*\.[0-9]*)\s              # Paragraph and section number.
    ([a-zA-Z(\s)?]*)\]\s            # Lemma followed by ]
    ([a-zA-Z\-(\s)?]*)\s            # Reading
    ([A-Z(\*)?])                    # Witness
    ''',re.VERBOSE)

# Now, do the substitution to encode the match, using captured groups.
replace = search_text.sub(r'<app><lem xml:id="lem-\1">\2</lem><rdg wit="#\4">\3</rdg></app>\n', source_text)

# Tell the script where to write the new file.
new_path = '/Users/sjhuskey/Documents/Sam-Py/DLL-Scripts/replace.txt' 

# Open the new file.
new_source = codecs.open(new_path,'w','utf-8')

# Write the contents of altered source_text to new_source.
new_source.write(str(replace))

# Close the old and new source files.
source_file.close()
new_source.close()

# Open the new source file.
path = '/Users/sjhuskey/Documents/Sam-Py/DLL-Scripts/replace.txt'
new_source_file = codecs.open(path,'r','utf-8')

# Read the new file.
new_source_text = new_source_file.read()

# Search for the entries where there is an omission (e.g., 1.1 lemma om. M).
search_text = re.compile(r'''
    ([0-9]*\.[0-9]*)\s              # Paragraph and section number.
    ([a-zA-Z(\s)?^(?!om\.)*$]*)\s   # Lemma, excluding "om."
    (om\.)\s                        # "om."
    ([A-Z(\*)?])                    # Witness that omits the lemma.
    ''',re.VERBOSE)

# Do the substitution.
replace = search_text.sub(r'<app><lem xml:id="\1">\2</lem><rdg wit="#\4"/></app>\n', new_source_text)

# Print to screen to see if we're doing this correctly.
print(replace)

# Tell the script where to write the new file.
newer_path = '/Users/sjhuskey/Documents/Sam-Py/DLL-Scripts/replace1.txt'
newer_source = codecs.open(new_path,'w','utf-8')

# Write the contents of source_text to new_test.
newer_source.write(str(replace))

# Close the open documents.
source_file.close()
newer_source.close()

print('Wow! That saved a lot of time!')
