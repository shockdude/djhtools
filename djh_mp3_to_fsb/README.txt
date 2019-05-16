MP3 to FSB converter for DJ Hero (djh_mp3_to_fsb.py)
Convert MP3 stems to FSB format, compatible with DJ Hero 1 & 2
Tested on Wii, PS3, 360
Written in Python, tested in Python 3.7

=== Usage ===

Run from the command line.
For DJ songs: djh_mp3_to_fsb.py green_track.mp3 blue_track.mp3 red_track.mp3 [output.fsb]
For Guitar songs: djh_mp3_to_fsb.py guitar.mp3 song.mp3 [output.fsb]

All MP3s must be 32/44.1/48khz, constant bitrate (preferably 160kbps or higher)
	See "Supported MP3 settings" for more detail.
Specifying the name of the output FSB is optional.
	The default output name is "output.fsb"

The MP3s can all be the same file, BUT make sure the peak loudless is -10dB or
quieter, otherwise the audio will be obnoxiously loud and will also clip badly.

The resulting output FSB can then replace any existing FSB in DJ Hero or DJ Hero 2 and
be playable in-game. Just make sure to only replace DJ songs with DJ songs,
and Guitar songs with Guitar songs.

=== Supported MP3 settings ===

List of supported constant MP3 bitrates (kbps):
	32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320
160kbps or higher is recommended.
Variable bitrate is not supported.

Supported MP3 sample rates (khz):
	44.1, 48, 32

Wii default: 32khz, 160kbps
	Note the game supports 44.1khz and 48khz MP3s, but the Wii hardware itself
	will resample and output 32khz.
PS3 default: 44.1khz, 160kbps
Xbox default: N/A (uses XMA format instead)
Higher bitrate is supported and recommended.