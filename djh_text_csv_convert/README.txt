Text to CSV converter for DJ Hero (djh_text_csv_convert)
Tool to help edit text strings in DJ Hero 1 and 2
Tested on Wii, PS3, 360
Written in Python, tested in Python 3.7

=== Usage ===

Make a backup of all your game files before using this tool.

Put this tool in DJ Hero's Text folder.
Double-click djh_text_csv_convert to convert the Text folders & files into CSV files
Open a CSV file in a text editor (NOT MS Excel, which is incompatible)
    E.g. TRAC.csv will contain all the strings for song names & artists

The CSV files will contain strings separated (aka delimited) by commas.
The first row of the CSV is the Header. The remaining rows are Strings IDs and Strings.
For each row, the first entry contains the String ID. The remaining entries contain the strings associated with the String ID, used for the different languages supported by the game.

You can now edit existing strings or add new string IDs and strings.
If the same string will be used in all languages, you don't have to copy the same string for each column; one copy of the string is enough.

Example String IDs and their associated Strings:

STR_MY_NEW_ID,MY NEW STRING
STR_ARTIST_DRAGONFORCE,DRAGONFORCE
STR_TRACK_TTFAF,THROUGH THE FIRE AND FLAMES

The CSV file can contain blank lines
The CSV files can also contain comments, i.e. helpful text that will be ignored by djh_text_csv_convert, so long as the row starts with "//"

// This is an example comment

When you have finished editing the CSV, import it back to the game by dragging-and-dropping the CSV file onto djh_text_csv_convert

You can now use your new String IDs elsewhere in the game files, e.g. tracklisting.xml or EmpireMode.xml
