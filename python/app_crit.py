#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 22 15:13:57 2017

@author: sjhuskey
"""
import csv, re

# Open the file to write new entries to.
output = open('app-crit-entries.txt','w', encoding='utf-8')

# Open the file and read it into memory so that you have a list of lists.
with open('/Users/sjhuskey/Dropbox/DLL/Technical/Automate/automation/app-crit-test.csv', encoding='utf-8') as appFile:
    readApp = csv.reader(appFile, delimiter=',')
    for row in readApp:

# For the sake of reference, here's a map of the columns.
#        para = row[0]
#        sec = row[1]
#        lem = row[2]
#        lem_wit = row[3]
#        lem_src = row[4]
#        lem_ann = row[5]
#        rdg_1 = row[6]
#        rdg_1_wit = row[7]
#        rdg_1_src = row[8]
#        rdg_1_ann = row[9]
#        rdg_2 = row[10]
#        rdg_2_wit = row[11]
#        rdg_2_src = row[12]
#        rdg_2_ann = row[13]
#        comm = row[14]
      
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
            return 'xml:id="lem-'+str(row[0])+'.'+str(row[1])+'-'+joined+'"'
            
        lem_xmlid = str(lem_xmlid())
        
# A function for creating the xml:id as the value for @target.
        def lem_target():
            split = row[2].split(' ')
            joined = '-'.join(split)
            return str(row[0])+'.'+str(row[1])+'-'+joined
        
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
                spaced_wit = search_wit.sub(r' \1',joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1',spaced_wit)
                return 'wit="'+str(first_wit)+'"'    
            
        lemwit = str(lemwit())
        
 # A function for wrapping the source(s) for a lemma in the correct XML.       
        def lemsrc():
            if not row[4]:
                return 'source="None"'
            else:
                #return 'source="'+row[4]+'"'
                # List the sigla, putting # before each one. Space will be added below.
                split = row[4].split(' ')
                joined = '#'.join(split)
                # This produces A#B#C. We need some space:
                search_wit = re.compile(r'(#[a-zA-Z(a-z)?])')
                spaced_wit = search_wit.sub(r' \1',joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1',spaced_wit)
                return 'source="'+str(first_wit)+'"'    
            
        lemsrc = str(lemsrc())
 
# A function for encoding any annotation on the lemma as a <note>.           
        def lemnote():
            if not row[5]:
                return '<!-- NO LEMMA ANNOTATION -->'
            else:
                return '<note target="'+lem_target+'">'+row[5]+'</note>'
            
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
                spaced_wit = search_wit.sub(r' \1',joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1',spaced_wit)
                return 'wit="'+str(first_wit)+'"'    
        
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
                spaced_wit = search_wit.sub(r' \1',joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1',spaced_wit)
                return 'source="'+str(first_wit)+'"'    
            
        rdg1src = str(rdg1src())

# Handling the xml:id for the first reading
        def rdg1_xmlid():
            # Handle readings with multiple words so that they are joined with "-"
            split = row[6].split(' ')
            joined = '-'.join(split)
            return 'xml:id="rdg-'+str(row[0])+'.'+str(row[1])+'-'+joined+'"'

        rdg1_xmlid = str(rdg1_xmlid())

# Target for rdg1        
        def rdg1_target():
            split = row[2].split(' ')
            joined = '-'.join(split)
            return 'rdg'+str(row[0])+'.'+str(row[1])+'-'+joined
        
        rdg1_target = str(rdg1_target())

# Note for rdg1
        def rdg1_note():
            if not row[9]:
                return '<!-- NO READING ANNOTATION -->'
            else:
                return '<note target="'+rdg1_target+'">'+row[9]+'</note>'
        
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
                spaced_wit = search_wit.sub(r' \1',joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1',spaced_wit)
                return 'wit="'+str(first_wit)+'"'    
        
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
                spaced_wit = search_wit.sub(r' \1',joined)
                # Now we have A #B #C. Let's put # on that first one.
                search_joined = re.compile(r'((?<!#)^[a-zA-Z(a-z)?\s])')
                first_wit = search_joined.sub(r'#\1',spaced_wit)
                return 'source="'+str(first_wit)+'"'    
            
        rdg2src = str(rdg2src())

# Handling the xml:id for the second reading
        def rdg2_xmlid():
            # Handle readings with multiple words so that they are joined with "-"
            split = row[10].split(' ')
            joined = '-'.join(split)
            return 'xml:id="rdg-'+str(row[0])+'.'+str(row[1])+'-'+joined+'"'

        rdg2_xmlid = str(rdg2_xmlid())

# Target for rdg2        
        def rdg2_target():
            split = row[10].split(' ')
            joined = '-'.join(split)
            return 'rdg-'+str(row[0])+'.'+str(row[1])+'-'+joined
        
        rdg2_target = str(rdg2_target())

# Note for rdg2
        def rdg2_note():
            if not row[13]:
                return '<!-- NO READING ANNOTATION -->'
            else:
                return '<note target="'+rdg1_target+'">'+row[13]+'</note>'
        
        rdg2_note = str(rdg2_note())

        entries = '<!-- App entry for '+str(row[0])+'.'+str(row[1])+': '+lem+' -->'+\
                    '<app><lem '+lemwit+' '+lemsrc+' '+lem_xmlid+'>'\
                    +lem+'</lem>'+\
                    lemnote+\
                    '<rdg '+rdg1wit+' '+rdg1src+' '+rdg1_xmlid+'>'+rdg1+'</rdg>'+\
                    rdg1_note+\
                    '<rdg '+rdg2wit+' '+rdg2src+' '+rdg2_xmlid+'>'+rdg2+'</rdg>'+\
                    rdg2_note+\
                    '</app>\n'
        
        print(entries)

        output.writelines([entries])

output.close()
appFile.close()