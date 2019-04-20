"""
MIT License

Copyright (c) 2019 shockdude

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# DJ Hero FSGMUB/CHART Converter v0.3
# Convert FSGMUB to CHART, and CHART to FSGMUB
# Credit to pikminguts92 from ScoreHero for documenting the FSGMUB format
# https://www.scorehero.com/forum/viewtopic.php?p=1827382#1827382

"""
Header
Entries[]
StringBlob

HEADER (16 bytes)
=================
INT32 - Version (1 or 2)
INT32 - Hash (CRC32)
INT32 - Count of entries
INT32 - Size of string blob

ENTRY (16 bytes)
================
FLOAT - Start (0-index)
INT32 - Pitch / Identifier
FLOAT - Length
INT32 - Text Pointer (Usually 0)
	Pointer to text value in blob, starting from first entry 
"""

"""
Guitar - Crossfader, Euphoria, Red Lane
G = 11 = crossfader left/green
R = 10 = crossfader center
Y = 9 = crossfader right/blue
B = 15 = euphoria
O = 2 = red tap

Guitar Coop - Green Lane
G = 7 = green scratch anydirection
R = 5 = green directional scratch down
Y = 3 = green directional scratch up
B = 48 = green scratch zone (the rectangle behind scratches)
O = 0 = green tap

Bass - Blue Lane
G = 8 = blue scratch anydirection
R = 6 = blue directional scratch down
Y = 4 = blue directional scratch up
B = 49 = blue scratch zone (the rectangle behind scratches)
O = 1 = blue tap

Rhythm - Effects
G = 12 = green effects
R = 16 = freestyle samples
Y = 50 = all lanes effects
B = 13 = blue effects
"""

import os, sys
import struct
import binascii

FSGMUB_EXTENSION = ".fsgmub"
CHART_EXTENSION = ".chart"

CHART_HEADER = """[Song]
{
  Offset = 0
  Resolution = 192
  Player2 = bass
  Difficulty = 0
  PreviewStart = 0
  PreviewEnd = 0
  Genre = "Turntablism"
  MediaType = "djhero"
}
[SyncTrack]
{
  0 = TS 4
  0 = B 120000
}
[Events]
{
}"""

CHART_RED_CF_SECTION = "[ExpertSingle]"
CHART_RED_CF_NOTES = (11, 10, 9, 15, 2)
CHART_GREEN_SECTION = "[ExpertDoubleGuitar]"
CHART_GREEN_NOTES = (7, 5, 3, 48, 0)
CHART_BLUE_SECTION = "[ExpertDoubleBass]"
CHART_BLUE_NOTES = (8, 6, 4, 49, 1)
CHART_EFFECTS_SECTION = "[ExpertDoubleRhythm]"
CHART_EFFECTS_NOTES = (12, 16, 50, 13, None)
CHART_END_NOTES = (44, 45)
CHART_MEASURE = 192 * 4
MIN_LENGTH = 1.0/192

def usage():
	print("Usage: {} [inputfile]".format(sys.argv[0]))
	print("Converts DJ Hero 1 FSGMUB to CHART or CHART to FSGMUB")
	sys.exit(1)
	
def chart_note_str(tick, note, length):
	return "  {} = N {} {}".format(int(round(tick)), note, int(round(length)))

def chart_write_section(chart_file, section_header, chart_notes):
	print(section_header, file=chart_file)
	print("{", file=chart_file)
	for note in chart_notes:
		print(note, file=chart_file)
	print("}", file=chart_file)

def fsgmub_to_chart(fsgmub_filename):
	fsgmub_name, fsgmub_ext = os.path.splitext(fsgmub_filename)
	chart_filename = fsgmub_name + CHART_EXTENSION
	
	red_cf_notes = []
	green_notes = []
	blue_notes = []
	effects_notes = []
	
	notes_dict = {}
	for note in CHART_RED_CF_NOTES:
		notes_dict[note] = (red_cf_notes, CHART_RED_CF_NOTES)
	for note in CHART_GREEN_NOTES:
		notes_dict[note] = (green_notes, CHART_GREEN_NOTES)
	for note in CHART_BLUE_NOTES:
		notes_dict[note] = (blue_notes, CHART_BLUE_NOTES)
	for note in CHART_EFFECTS_NOTES:
		if note:
			notes_dict[note] = (effects_notes, CHART_EFFECTS_NOTES)

	with open(fsgmub_filename, "rb") as fsgmub_file:
		# fsgmub header
		# version, hash, length
		fsgmub_data = struct.unpack(">III", fsgmub_file.read(12))
		print("Version: {}".format(fsgmub_data[0]))
		print("Hash: {:x}".format(fsgmub_data[1]))
		print("Length: {}".format(fsgmub_data[2]))
		
		# string blob size, ignore
		fsgmub_file.read(4)
		
		fsgmub_length = fsgmub_data[2]
		
		for i in range(fsgmub_length):
			# note position, note_type, note_length
			note_position, note_type, note_length = struct.unpack(">fIf", fsgmub_file.read(12))
			# tap notes and directional scratches should be zero length in a chart
			if note_type <= 6:
				note_length = 0
			try:
				chart_array, chart_notes = notes_dict[note_type]
				chart_array.append(chart_note_str(note_position * CHART_MEASURE,
													chart_notes.index(note_type),
													note_length * CHART_MEASURE))
			except KeyError:
				if note_type not in CHART_END_NOTES:
					print("Warning: unknown note type {} at fsgmub note {}".format(note_type, i))
			
			# text pointer, ignore
			fsgmub_file.read(4)
				
	with open(chart_filename, "w") as chart_file:
		print(CHART_HEADER, file=chart_file)
		chart_write_section(chart_file, CHART_RED_CF_SECTION, red_cf_notes)
		chart_write_section(chart_file, CHART_GREEN_SECTION, green_notes)
		chart_write_section(chart_file, CHART_BLUE_SECTION, blue_notes)
		chart_write_section(chart_file, CHART_EFFECTS_SECTION, effects_notes)
		
def chart_section_to_fsgmub(chart_file, chart_notes):
	line = ""
	fsgmub_notes = []
	while line.find("}") < 0:
		line = chart_file.readline().strip()
		# position, =, N, note, length
		notes = line.strip().split(" ")
		if len(notes) != 5 or notes[2] != "N" or int(notes[3]) > 4:
			continue
		# position, note, length
		position = float(notes[0])/CHART_MEASURE
		note = chart_notes[int(notes[3])]
		length = float(notes[4])/CHART_MEASURE
		if length < MIN_LENGTH:
			length = MIN_LENGTH
		fsgmub_notes.append([position, note, length])
	return fsgmub_notes
		
def merge_note_arrays(x, y):
	i = 0
	j = 0
	lenx = len(x)
	leny = len(y)
	n = lenx+leny
	output_array = []
	for k in range(n):
		if i >= lenx:
			output_array.append(y[j])
			j += 1
		elif j >= leny:
			output_array.append(x[i])
			i += 1
		elif x[i][0] > y[j][0]:
			output_array.append(y[j])
			j += 1
		else:
			output_array.append(x[i])
			i += 1
	return output_array
			
def chart_to_fsgmub(chart_filename):
	chart_name, chart_ext = os.path.splitext(chart_filename)
	fsgmub_filename = chart_name + FSGMUB_EXTENSION
	
	red_cf_notes = []
	green_notes = []
	blue_notes = []
	effects_notes = []
	
	with open(chart_filename, "r") as chart_file:
		line = chart_file.readline().strip()
		while len(line) > 0:
			if line == CHART_RED_CF_SECTION:
				red_cf_notes = chart_section_to_fsgmub(chart_file, CHART_RED_CF_NOTES)
			elif line == CHART_GREEN_SECTION:
				green_notes = chart_section_to_fsgmub(chart_file, CHART_GREEN_NOTES)
			elif line == CHART_BLUE_SECTION:
				blue_notes = chart_section_to_fsgmub(chart_file, CHART_BLUE_NOTES)
			elif line == CHART_EFFECTS_SECTION:
				effects_notes = chart_section_to_fsgmub(chart_file, CHART_EFFECTS_NOTES)
			line = chart_file.readline().strip()
	
	# merge the arrays into a single array
	temp_array_1 = merge_note_arrays(red_cf_notes, green_notes)
	temp_array_2 = merge_note_arrays(blue_notes, effects_notes)
	fsgmub_array = merge_note_arrays(temp_array_1, temp_array_2)
	
	# append ending notes 44 & 45
	fsgmub_array.append([4, 44, 0.0625])
	fsgmub_array.append([4, 45, 0.0625])
	
	# binary lines to write
	output_array = []
	for line in fsgmub_array:
		output_array.append(struct.pack(">fIfI",
										float(line[0]),
										int(line[1]),
										float(line[2]),
										0))
	
	with open(fsgmub_filename, "wb") as fsgmub_file:
		line_count = len(fsgmub_array)
		
		# compute crc
		# chart length, string blob size (0), chart lines
		crc = binascii.crc32(struct.pack(">II", line_count, 0))
		for line in output_array:
			# note position, note type, note length, text pointer (0)
			crc = binascii.crc32(line, crc)
		
		# fsgmub header
		# version (2), crc, chart length, string blob size (0)
		fsgmub_file.write(struct.pack(">IIII", 2, crc, line_count, 0))
		
		for line in output_array:
			# note position, note type, note length, text pointer (0)
			fsgmub_file.write(line)
										
		# write extra row if the linecount is even
		# all the other charts do this so why not
		if line_count % 2 == 0:
			fsgmub_file.write(struct.pack(">IIII", 0,0,0,0))

def main():
	if len(sys.argv) < 2:
		usage()
	
	input_filename = sys.argv[1]
	input_name, input_ext = os.path.splitext(input_filename)
	
	if input_ext.lower() == FSGMUB_EXTENSION:
		fsgmub_to_chart(input_filename)
		sys.exit(0)
	if input_ext.lower() == CHART_EXTENSION:
		chart_to_fsgmub(input_filename)
		sys.exit(0)
	
	print("Error: input file {} does not have extension {} or {}".format(input_filename, FSGMUB_EXTENSION, CHART_EXTENSION))
	usage()

if __name__ == "__main__":
	main()