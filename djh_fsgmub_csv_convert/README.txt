DJ Hero fsgmub/csv converter (djh_fsgmub_csv_convert.py)
shockdude

Convert DJ Hero charts (fsgmub/xmk files) to .csv files for editing in
a spreadsheet program (MS Excel, Google Sheets, LibreOffice Calc).
Convert DJ Hero .csv files back to fsgmub.
Supports DJ Hero 1 & 2
Written in Python.

=== Usage ===

To convert a DJ Hero fsgmub/xmk to a csv:
	Drag-and-drop the fsgmub onto djh_fsgmub_csv_convert.py
	Or from the command line: djh_fsgmub_csv_convert.py [fsgmub_file]

To convert a csv to a DJ Hero fsgmub:
	Drag-and-drop the csv onto djh_fsgmub_csv_convert.py
	Or from the command line: djh_fsgmub_csv_convert.py [csv_file]

For DJ Hero 2, you will need to change the file extension from ".fsgmub"
to ".xmk"

The resulting CSV will have 4 columns:
[Position] [NoteType] [Length] [ExtraData]

=== DJ Hero 1 Reference ===

NoteTypes
0 - green tap
1 - blue tap
2 - red tap
3 - green directional scratch up
4 - blue directional scratch up
5 - green directional scratch down
6 - blue directional scratch down
7 - green scratch anydirection
8 - blue scratch anydirection
9 - crossfader right/blue
10 - crossfader center
11 - crossfader left/green
12 - green effects
13 - blue effects
14 - red effects
15 - euphoria
16 - freestyle samples
44 - not important (chart file end?)
45 - not important (chart file end?)
48 - green scratch zone (the rectangle behind scratches)
49 - blue scratch zone (the rectangle behind scratches)
50 - all lanes effects

=== DJ Hero 2 Reference ===

NoteTypes
[optional extra data in brackets]
0 - green tap
1 - blue tap
2 - red tap
	taps can be placed in scratch zones and work ok
3 - green scratch up
4 - blue scratch up
5 - green scratch down
6 - blue scratch down
7 - green anydirection scratch
8 - blue anydirection scratch
9 - crossfade right/blue
10 - crossfade center
11 - crossfade left/green
12 - green effects
13 - blue effects
14 - red effects
15 - euphoria
16 - freestyle samples/scratches [int, sample number]
	note that the sample lane is specified in tracklisting.xml
17 - freestyle crossfade zone
20 - green scratchzone
21 - blue scratchzone
22 - all lanes effects
26 - battle-charts only, player switching & checkpoints from ChunkRemix.xml
27 - crossfade spike green
28 - crossfade spike blue
29 - crossfade spike center
30 - megamix transition
	must be crossfade centered
31 - freestyle crossfade green marker
32 - freestyle crossfade blue marker

AUTHOR - charter's name [string address]
	chart hex value: 0x0AFFFFFF
CHART_BPM - beats per minute [float] (ignored in-game?)
	chart hex value: 0x0B000002
BEAT_LENGTH - distance between beat markers in microseconds [int]
	equivalent to 60,000,000 / bpm
	djh2 charts are fixed bpm, but give the illusion of variable bpm by adjusting the beat marker distance.
	chart hex value: 0x0B000001
SECTION - section/rewind checkpoint [string address, section name]
	chart hex value: 0x09FFFFFF
CHART_BEGIN - when the chart begins? ignored in-game?
	chart hex value: 0xFFFFFFFF
FX_ - different effect types to use with effects (notes 12 ,13, 14, 22)
	FX_FILTER, FX_BEATROLL, FX_BITREDUCE, FX_WAHWAH, FX_RINGMOD, FX_STUTTER, FX_FLANGER, FX_ROBOT, FX_ADV_BEATROLL, FX_DELAY
	without an FX type, the effect used is FX_FILTER
	chart hex values: 0x05FFFFFF - 0x06000009 (except for 0x06000008)
