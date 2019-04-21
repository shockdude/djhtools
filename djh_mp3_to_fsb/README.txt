MP3 to FSB converter for DJ Hero (djh_mp3_to_fsb.exe)
Convert MP3 stems to FSB format, compatible with DJ Hero
Tested in DJ Hero Wii
Written in Python, tested in Python 3.7

=== Usage ===

Run from the command line.
djh_mp3_to_fsb.exe input.fsb green_track.mp3 blue_track.mp3 red_track.mp3 [output.fsb]

The input.fsb should be a FSB file extracted from DJ Hero.
All MP3s must be 32/44.1/48khz, constant bitrate (preferably 160kbps or higher)
	See "Supported MP3 settings" for more detail.
Specifying the name of the output FSB is optional.
	The default output name is "output.fsb"

The MP3s can all be the same file, but make sure the peak loudless is -10dB or
quieter, otherwise the audio will be obnoxiously loud and will also clip badly.

The resulting output FSB can then replace any existing FSB in DJ Hero and
be playable in-game.

=== Supported MP3 settings ===

DJ Hero Wii default: 32khz, 160kbps
	Note the Wii hardware cannot output a higher sample rate than 32khz.
DJ Hero PS3 default: 44.1khz, 160kbps

Supported constant MP3 bitrates (kbps):
	32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320
160kbps or higher is recommended.
Variable bitrate is not supported.

Supported MP3 sample rates (khz):
	44.1, 48, 32
