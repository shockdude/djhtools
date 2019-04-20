DJ Hero fsgmub/chart converter (djh_fsgmub_chart_convert.exe)

Convert DJ Hero charts (fsgmub files) to .chart files for editing in
Moonscraper, and convert .chart files back to fsgmub to play in DJ Hero.
Written in Python.

=== Usage ===

To convert a DJ Hero fsgmub to a chart:
	Drag-and-drop the fsgmub onto djh_fsgmub_chart_convert.exe
	Or from the command line: djh_fsgmub_chart_convert.exe [fsgmub_file]

To convert a chart to a DJ Hero fsgmub:
	Drag-and-drop the chart onto djh_fsgmub_chart_convert.exe
	Or from the command line: djh_fsgmub_chart_convert.exe [chart_file]

=== DJ Hero Chart Format ===

In Moonscraper, ensure that extended sustains are enabled (press E).

DJ Hero charts span multiple instruments in the .chart file.
The mapping is as follows:

Guitar - Crossfader, Euphoria, Red Lane
G	crossfader left/green
R	crossfader center
Y	crossfader right/blue
B	euphoria
O	red tap
	Crossfades must span the entire chart, and there must be zero gap
	between crossfader notes.

Guitar Coop - Green Lane
G	green scratch anydirection
R	green directional scratch down
Y	green directional scratch up
B	green scratch zone (the rectangle behind scratches)
O	green tap
	All scratches must overlap with a scratch zone.

Bass - Blue Lane
G	blue scratch anydirection
R	blue directional scratch down
Y	blue directional scratch up
B	blue scratch zone (the rectangle behind scratches)
O	blue tap
	All scratches must overlap with a scratch zone.

Rhythm - Effects
G	green effects
R	freestyle samples
Y	all lanes effects
B	blue effects
	Effects should not overlap each other.