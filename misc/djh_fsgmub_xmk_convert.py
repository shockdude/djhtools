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

# DJ Hero FSGMUB/XMK Converter v0.41
# Convert DJH1 FSGMUB to DJH2 XMK and vice versa
# Credit to pikminguts92 from ScoreHero for documenting the FSGMUB format
# https://www.scorehero.com/forum/viewtopic.php?p=1827382#1827382

"""
Header
Entries[]
StringBlob

HEADER (16 bytes)
=================
INT32 - Version (1 or 2)
INT32 - Hash
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

import os, sys
import struct
import binascii
from collections import deque

FSGMUB_EXTENSION = ".fsgmub"
XMK_EXTENSION = ".xmk"

HEADER_SIZE = 16
ENTRY_SIZE = 16
ALIGN_SIZE = 32

STRING_NOTES = (0x0AFFFFFF,0x09FFFFFF,0x0B000000)
NOTE_WHITELIST = (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20,21,22,23,27,28,29,48,49,50,51,
	0x05FFFFFF,0x06000000,0x06000001,0x06000002,0x06000003,0x06000004,0x06000005,0x06000006,0x06000007,0x06000008,0x06000009,
	0x0B000001,0x0B000002)
CHART_BEGIN = [0, 0xFFFFFFFF, 0 ,0] # not part of the whitelist, manually added to djh2 charts

DJH1_MAX_NOTELEN = 1.0/16
DJH1_MIN_NOTELEN = 1.0/32

TO_SPIKE = {9:28, 10:29, 11:27}

def usage():
	print("Usage: {} [inputfile]".format(sys.argv[0]))
	print("Basic conversion from FSGMUB (DJH1) to XMK (DJH2), or XMK to FSGMUB")
	print("Now converts DJH1 spikes to DJH2 spikes!")
	sys.exit(1)

def check_spike(crossfades):
	# higher index = older
	# assumption: cf[2] may or may not spike, cf[1] and cf[0] are not spikes
	# check if cf[1] is a spike
	if crossfades[1][2] <= DJH1_MAX_NOTELEN:
		# anything can go to an edgespike except for a centerspike
		if crossfades[2][1] != 29 and crossfades[1][1] in (9, 11):
			return True
		# centerspike
		if crossfades[2][1] == crossfades[0][1]:
			return True
	return False
		
def main():
	if len(sys.argv) < 2:
		usage()
	
	input_filename = sys.argv[1]
	input_name, input_ext = os.path.splitext(input_filename)
	
	input_chart_mode = 0
	if input_ext.lower() == FSGMUB_EXTENSION:
		input_chart_mode = 1
		print("Converting djh1 fsgmub to djh2 xmk")
	elif input_ext.lower() == XMK_EXTENSION:
		input_chart_mode = 2
		print("Converting djh2 xmk to djh1 fsgmub")
	else:
		print("Error: input file {} does not have extension {} or {}".format(input_filename, FSGMUB_EXTENSION, CSV_EXTENSION))
		usage()

	note_array = []
	note_count = 0
	output_array = []
	string_length = 0
	fsgmub_strings = None
	cf_queue = deque()
	has_chart_begin = False

	with open(input_filename, "rb") as input_file:
		# fsgmub header
		# version, hash, length
		fsgmub_data = struct.unpack(">IIII", input_file.read(16))
		print("Input chart: {}".format(input_filename))
		print("Version: {}".format(fsgmub_data[0]))
		print("Hash: {:x}".format(fsgmub_data[1]))
		print("Length: {}".format(fsgmub_data[2]))
		print("String data length: {}".format(fsgmub_data[3]))
		string_length = fsgmub_data[3]
		fsgmub_length = fsgmub_data[2]
		
		if string_length > 0:
			input_file.seek(ENTRY_SIZE*fsgmub_length+HEADER_SIZE)
			fsgmub_strings = input_file.read(string_length)
			input_file.seek(HEADER_SIZE)
			
		for i in range(fsgmub_length):
			# note position, note_type, note_length, other
			note_data = list(struct.unpack(">fIfI", input_file.read(16)))
			if note_data[1] in STRING_NOTES:
				# string address is dependent on chart length
				# subtract out the old chart length for now
				note_data[3] -= ENTRY_SIZE*fsgmub_length
			elif note_data[1] not in NOTE_WHITELIST:
				note_data = None
			elif input_chart_mode == 1: # djh1 to djh2
				if note_data[1] in (48,49,50,51):
					note_data[1] -= 28
				elif note_data[1] in (0,1,2,3,4,5,6): # remove holds
					note_data[2] = DJH1_MIN_NOTELEN
				if not has_chart_begin and note_data[0] > 0: # manually add chart_begin note
					has_chart_begin = True
					note_array.append(CHART_BEGIN);
					note_count += 1
			else: #djh2 to djh1
				if note_data[1] in (20,21,22,23):
					note_data[1] += 28
				elif note_data[1] == 27: # green spike
					note_data[1] = 11
				elif note_data[1] == 28: # blue spike`
					note_data[1] = 9
				elif note_data[1] == 29: # center spike
					note_data[1] = 10
				elif note_data[1] in (0,1,2,3,4,5,6): # remove holds
					note_data[2] = DJH1_MIN_NOTELEN
			if note_data != None:
				# crossfade handling
				if input_chart_mode == 1 and note_data[1] in (9,10,11):
					# combine consecutive crossfades in djh1 charts
					if len(cf_queue) >= 1 and note_array[cf_queue[0]][1] == note_data[1]:
						note_array[cf_queue[0]][2] = note_data[0] + note_data[2] - note_array[cf_queue[0]][0]
					else:
						note_array.append(note_data)
						cf_queue.appendleft(note_count)
						# check crossfades for spikes
						if len(cf_queue) == 3:
							if check_spike([note_array[x] for x in cf_queue]):
								note_array[cf_queue[1]][1] = TO_SPIKE[note_array[cf_queue[1]][1]]
							cf_queue.pop()
						note_count += 1
				else:
					note_array.append(note_data)
					note_count += 1
			
	fsgmub_length = len(note_array)
	for i in range(fsgmub_length):
		if note_array[i][1] in STRING_NOTES:
			note_array[i][3] += ENTRY_SIZE*fsgmub_length
		output_array.append(struct.pack(">fIfI", note_array[i][0], note_array[i][1], note_array[i][2], note_array[i][3]))
	output_ext = None
	if input_chart_mode == 1: # input djh1, output djh2 xmk
		output_ext = XMK_EXTENSION
	else: # input djh2, output djh1 fsgmub
		output_ext = FSGMUB_EXTENSION
	output_filename = input_name + output_ext
			
	with open(output_filename, "wb") as output_file:
		# compute crc
		# chart length, string blob size (0), chart lines
		size_bin = struct.pack(">II", fsgmub_length, string_length)
		crc = binascii.crc32(size_bin)
		for line in output_array:
			# note position, note type, note length, text pointer
			crc = binascii.crc32(line, crc)
		if string_length > 0:
			crc = binascii.crc32(fsgmub_strings, crc)
		
		# fsgmub header
		# version (2), crc, chart length, string blob size
		output_file.write(struct.pack(">II", 2, crc))
		output_file.write(size_bin)
		
		print("Output chart: {}".format(output_filename))
		print("Version: {}".format(2))
		print("Hash: {:x}".format(crc))
		print("Length: {}".format(fsgmub_length))
		print("String data length: {}".format(string_length))
		
		for line in output_array:
			# note position, note type, note length, text pointer
			output_file.write(line)
										
		if string_length > 0:
			output_file.write(fsgmub_strings)
		
		# ensure the chart filesize is a multiple of 32 for some reason
		file_size = HEADER_SIZE + fsgmub_length*ENTRY_SIZE + string_length
		size_offset = file_size % ALIGN_SIZE
		if size_offset != 0:
			output_file.write(b"\x00"*(ALIGN_SIZE - size_offset))

if __name__ == "__main__":
	main()