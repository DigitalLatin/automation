# Excel to CSV Instructions for Kaster's Servius

## Introduction
Kaster's apparatus criticus is in an Excel sheet. For other texts, the excel sheet has had plaintext inside each cell, so it can be exported directly from Excel as a CSV and used as script input. However, Kaster's excel sheets contain text formatting within cells (e.g. bold and italics) that is semantically important. Therefore, we need to preserve this semantic information when changing to a plaintext CSV format to use a script input.

## Dependencies
You're going to need recent-ish versions of MS Excel and MS Word. You'll also need [Pandoc](https://pandoc.org), a command line utility for converting between document formats. Finally, you'll need a spreadsheet program _other than Excel_. We need to open and edit CSVs without introducing Excel-specific markup that sometimes happens when you export from Excel as a CSV. [LibreOffice](https://www.libreoffice.org) is free and useful.

A text editor with a markdown preview plug-in (e.g. Atom's Markdown Preview) is helpful, but not strictly necessary.

## Phase 1: File format conversions
The first phase of this process is a conversion through a few file formats to get to a CSV.

1. **CLEAN UP EXCEL** Pandoc cannot handle line breaks within table cells. Find and remove these. The easiest way is to find `|` and delete the line breaks in the cells where it appears. This won't catch all of them, unfortunately. I'm working on a better way to do this - Excel find and replace is not helpful, at least on Mac. Also, you need to escape all pipe `|` characters or it will cause problems down the line. Just find `|` and replace it by `\|`.
2. **EXCEL -> WORD**
Copy the entire excel spreadsheet and paste it as a table into a Word document. Do this in increments of about 200-300 lines, or else Word WILL crash. Save frequently, because it probably will anyway. This operation is slow and tedious. We do this to preserve Microsoft formatting but get it into a format we can handle using Pandoc. Save the Word document (.docx format) in the same directory as the Excel workbook.
3. **WORD -> MARKDOWN**
Next, open up a terminal. Use Pandoc to convert the Word document to Github-flavored Markdown with the following command:
```pandoc -o <output filename> -f docx -t gfm <input filename>```
We use GFM rather than Pandoc markdown because its table format is easier to deal with in the next step.
Open the resulting Markdown file in a text editor and check that the table looks correct. It should use pipe characters | for cell delimiters. Make sure that the data seems to be generally in the same order as in the excel document.
4. **MARKDOWN -> CSV**
Finally, we will use a spreadsheet program to convert from a big Markdown table to a CSV. Open the .md file in your spreadsheet program. Deselect comma as a separator and select the pipe | instead. Open the file, then save it as a .csv with comma as the field delimiter.

## Phase 2: CSV Cleanup
Now that we have a CSV, we need to do a few more things to get it ready for processing with a script.
1. **Add a "Book" Column.** This should be in the far left column, and should contain only integers for the book number you are currently working on. This will be the same number for every row.
2. **Remove extra columns.** Remove any remaining blank columns and those that are now specified in the DLL CSV guidelines. This includes the "line" and "lemma match?" columns
3. **Remove row of dashes ---** Remove row 2, which contains just dashes. This is an artifact from the way Markdown handles table headers, and it is not needed in the final CSV.
4. **Unescape escaped characters** Use find and replace to replace `\<` with `<`, `\>` with `>`, `\[` with `[`, and `\]` with `]`.
5. **Remove extra whitespace** Sometimes, cells end up with a lot of whitespace characters and nothing else. We want to remove those. Use find and replace to replace the regex `^\s+$` with `` (empty string).
5. **Check for missing reading** Do a quick visual scan of the reading columns to look for missing readings. Sometimes they get pushed into the preceding comment column.
6. **Save and process file** Save the file as a CSV in the directory where your scripts look for input. It should be ready to go!
