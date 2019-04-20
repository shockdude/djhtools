MP3 to FSB converter for DJ Hero Wii (djh_mp3_to_fsb.exe)
Convert MP3 stems to FSB format, compatible with DJ Hero Wii
Written in Python.

=== Usage ===

Run from the command line.
djh_mp3_to_fsb.exe input.fsb green_track.mp3 blue_track.mp3 red_track.mp3 [output.fsb]

The input.fsb should be a FSB file extracted from DJ Hero Wii.
The MP3s must be 160kbps bitrate, 32khz sample rate, joint stereo.
Specifying the name of the output FSB is optional.
	The default output name is "output.fsb"

The MP3s can all be the same file, but make sure the peak loudless is -10dB or
quieter, otherwise the audio will clip badly.

The resulting output FSB can then replace any existing FSB in DJ Hero Wii and
be playable in-game.