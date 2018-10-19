# Plain Text Guidelines: Poetry

## Overview

The purpose of this document is to establish guidelines for the .txt file used in preparing an LDLT edition of a poetry text. These files should be plain text (i.e. .txt, not .rtf) and should be saved in UTF-8 encoding.

## Structure
### Numbering
#### Poem numbers
Poems within a collection should be numbered at the beginning of the first line of each poem. The poem number should be digits only (no punctuation) and should be separated from the first word by a space. For example,
> 2 this is the first line of the second poem

In texts which only contain a single poem, the beginning of the first line should be marked "1", e.g.
> 1 Here is the first line of a single poem

#### Line numbers
Lines should be broken up with line breaks, i.e. the newline character (\\n). Our scripts can automatically number lines of poetry and can handle transposed lines. If the poem starts at line 1, you do not need to mark this. If it does not start at line 1, you should include the line number at the end of the first line, separated from the text by one space and with no additional punctuation, e.g. for line 4 of some poem:
> this is a line 4

For transposed or discontinuous line numbers, the script will number sequentially until it sees a numbered line, then jump to that number, then number sequentially until it sees another number. So, if the editor thinks that line 3 should be between line 1 and line 2, you should encode this:

> This is a line  
> here's a third line 3  
> here's the second line 2   
> here's the fourth line 4  
> and the fifth line

### Speakers
Some poems have different speakers for different lines. These should be encoded at the beginning of the line in parentheses, like so:
> (Speaker) these are some words

You do not need to include the speaker on every line, only on the first line of a new speaker, e.g.:
> (Speaker1) this is a line   
> here's another line by Speaker1  
>(Speaker2) now Speaker2 is talking  
> still Speaker2

### Editorial Markup

#### Editorial additions
Editorial additions should be enclosed in angle brackets \<\>, e.g.
> these are some <added\> words.

##### Lacunae
Lacunae (i.e. places where the editor believes there is text missing) should be marked with three asterisks, e.g.:
> there is probably some \*\*\* here

For multiline lacunae, you should include three asterisks \*\*\* on each missing line.

#### Crux
Sections which the editor believes are corrupted but chooses not to emend should be enclosed in daggers † †, e.g.:
> here is some †confusing text corrupted maybe†

#### Editorial deletions
Editorial deletions should be enclosed in curly braces {} e.g.:
> these are some {deleted} words.
