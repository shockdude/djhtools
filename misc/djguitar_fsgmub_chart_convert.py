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

# Guitar Chart to DJ Hero FSGMUB Converter v0.1
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
notetype, easy, medium, hard, expert
G, 20, 25, 30, 35
R, 21, 26, 31, 36
Y, 22, 27, 32, 37
B, 23, 28, 33, 38
O, 24, 29, 34, 39
forced note, 40, 41, 42, 43
star power, 53, 54, 55, 56
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
  Genre = ""
  MediaType = "djhero_guitar"
}
[SyncTrack]
{
  0 = TS 4
  0 = B 120000
}
[Events]
{
}"""

CHART_EASY_SECTION = "[EasySingle]"
CHART_EASY_NOTES = (20, 21, 22, 23, 24, 40, 53)
CHART_MEDIUM_SECTION = "[MediumSingle]"
CHART_MEDIUM_NOTES = (25, 26, 27, 28, 29, 41, 54)
CHART_HARD_SECTION = "[HardSingle]"
CHART_HARD_NOTES = (30, 31, 32, 33, 34, 42, 55)
CHART_EXPERT_SECTION = "[ExpertSingle]"
CHART_EXPERT_NOTES = (35, 36, 37, 38, 39, 43, 56)
STARPOWER_NOTE = 6
CHART_END_NOTES = (44, 45)
CHART_MEASURE = 192 * 4
MIN_LENGTH = 1.0/32 + .0001

def usage():
	print("Usage: {} [inputfile]".format(sys.argv[0]))
	print("Converts DJ Hero 1 Guitar FSGMUB to CHART or Guitar CHART to FSGMUB")
	sys.exit(1)
	
def chart_note_str(tick, note, length):
	if note < STARPOWER_NOTE:
		return "  {} = N {} {}".format(int(round(tick)), note, int(round(length)))
	elif note == STARPOWER_NOTE:
		return "  {} = S 2 {}".format(int(round(tick)), int(round(length)))
	else:
		print("Warning: invalid note {}".format(note))
		return ""

def chart_write_section(chart_file, section_header, chart_notes):
	print(section_header, file=chart_file)
	print("{", file=chart_file)
	for note in chart_notes:
		print(note, file=chart_file)
	print("}", file=chart_file)

def fsgmub_to_chart(fsgmub_filename):
	fsgmub_name, fsgmub_ext = os.path.splitext(fsgmub_filename)
	chart_filename = fsgmub_name + CHART_EXTENSION
	
	easy_notes = []
	medium_notes = []
	hard_notes = []
	expert_notes = []
	
	notes_dict = {}
	for note in CHART_EASY_NOTES:
		notes_dict[note] = (easy_notes, CHART_EASY_NOTES)
	for note in CHART_MEDIUM_NOTES:
		notes_dict[note] = (medium_notes, CHART_MEDIUM_NOTES)
	for note in CHART_HARD_NOTES:
		notes_dict[note] = (hard_notes, CHART_HARD_NOTES)
	for note in CHART_EXPERT_NOTES:
		notes_dict[note] = (expert_notes, CHART_EXPERT_NOTES)

	with open(fsgmub_filename, "rb") as fsgmub_file:
		# fsgmub header
		# version, hash, length
		fsgmub_data = struct.unpack(">III", fsgmub_file.read(12))
		print("Version: {}".format(fsgmub_data[0]))
		print("Hash: {:x}".format(fsgmub_data[1]))
		print("Length: {}".format(fsgmub_data[2]))
		
		# string blob size, ignore
		fsgmub_file.seek(4, 1)
		
		fsgmub_length = fsgmub_data[2]
		
		for i in range(fsgmub_length):
			# note position, note_type, note_length
			note_position, note_type, note_length = struct.unpack(">fIf", fsgmub_file.read(12))
			if note_length <= MIN_LENGTH:
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
			fsgmub_file.seek(4, 1)
				
	with open(chart_filename, "w") as chart_file:
		print(CHART_HEADER, file=chart_file)
		chart_write_section(chart_file, CHART_EASY_SECTION, easy_notes)
		chart_write_section(chart_file, CHART_MEDIUM_SECTION, medium_notes)
		chart_write_section(chart_file, CHART_HARD_SECTION, hard_notes)
		chart_write_section(chart_file, CHART_EXPERT_SECTION, expert_notes)
		
def chart_section_to_fsgmub(chart_file, chart_notes):
	line = ""
	fsgmub_notes = []
	while line.find("}") < 0:
		line = chart_file.readline().strip()
		# position, =, N, note, length
		notes = line.strip().split(" ")
		if len(notes) != 5:
			continue
		if notes[2] == "S" and int(notes[3]) == 2:
			note = chart_notes[STARPOWER_NOTE]
		elif notes[2] == "N" and int(notes[3]) <= 5:
			note = chart_notes[int(notes[3])]
		else:
			continue
		position = float(notes[0])/CHART_MEASURE
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
	
	easy_notes = []
	medium_notes = []
	hard_notes = []
	expert_notes = []
	
	with open(chart_filename, "r") as chart_file:
		line = chart_file.readline().strip()
		while len(line) > 0:
			if line == CHART_EASY_SECTION:
				easy_notes = chart_section_to_fsgmub(chart_file, CHART_EASY_NOTES)
			elif line == CHART_MEDIUM_SECTION:
				medium_notes = chart_section_to_fsgmub(chart_file, CHART_MEDIUM_NOTES)
			elif line == CHART_HARD_SECTION:
				hard_notes = chart_section_to_fsgmub(chart_file, CHART_HARD_NOTES)
			elif line == CHART_EXPERT_SECTION:
				expert_notes = chart_section_to_fsgmub(chart_file, CHART_EXPERT_NOTES)
			line = chart_file.readline().strip()
	
	# merge the arrays into a single array
	temp_array_1 = merge_note_arrays(easy_notes, medium_notes)
	temp_array_2 = merge_note_arrays(hard_notes, expert_notes)
	fsgmub_array = merge_note_arrays(temp_array_1, temp_array_2)
	
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