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

# DJ Hero FSGMUB/CSV Converter v0.3
# Convert FSGMUB/XMK to CSV, and CSV to FSGMUB (can be renamed to XMK)
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

import csv
import os, sys
import struct
import binascii

FSGMUB_EXTENSION = ".fsgmub"
XMK_EXTENSION = ".xmk"
CSV_EXTENSION = ".csv"

HEADER_SIZE = 16
ENTRY_SIZE = 16
ALIGN_SIZE = 32

FLAG_NAMES = ("AUTHOR", "SECTION", "CHART_BPM", "BEAT_LENGTH", "CHART_BEGIN", "FX_FILTER", "FX_BEATROLL", "FX_BITREDUCE", "FX_WAHWAH", "FX_RINGMOD", "FX_STUTTER", "FX_FLANGER", "FX_ROBOT", "FX_ADV_BEATROLL", "FX_DELAY")
FLAG_TYPES = (0x0AFFFFFF,0x09FFFFFF,0x0B000002,0x0B000001,0xFFFFFFFF,0x05FFFFFF,0x06000000,0x06000001,0x06000002,0x06000003,0x06000004,0x06000005,0x06000006,0x06000007,0x06000009)

if len(FLAG_NAMES) != len(FLAG_TYPES):
	print("Error: mismatched number of flag names & flag types")
	sys.exit(1)

FLAG_AUTHOR = 0
FLAG_SECTION = 1
FLAG_CHART_BPM = 2
FLAG_BEAT_LENGTH = 3
FLAG_CHART_BEGIN = 4

def usage():
	print("Usage: {} [inputfile]".format(sys.argv[0]))
	print("Converts DJ Hero 1 FSGMUB to CSV or CSV to FSGMUB")
	sys.exit(1)

def fsgmub_to_csv(fsgmub_filename):
	fsgmub_name, fsgmub_ext = os.path.splitext(fsgmub_filename)
	csv_filename = fsgmub_name + CSV_EXTENSION

	with open(fsgmub_filename, "rb") as fsgmub_file:
		with open(csv_filename, "w", newline='') as csv_file:
			csv_writer = csv.writer(csv_file)
			
			# fsgmub header
			# version, hash, length
			fsgmub_data = struct.unpack(">IIII", fsgmub_file.read(16))
			print("Version: {}".format(fsgmub_data[0]))
			print("Hash: {:x}".format(fsgmub_data[1]))
			print("Length: {}".format(fsgmub_data[2]))
			print("String data length: {}".format(fsgmub_data[3]))
			string_length = fsgmub_data[3] - 1
			fsgmub_length = fsgmub_data[2]
			fsgmub_strings = None
			
			if string_length > 0:
				fsgmub_file.seek(ENTRY_SIZE*fsgmub_length+HEADER_SIZE)
				fsgmub_strings = fsgmub_file.read(string_length)
				fsgmub_file.seek(HEADER_SIZE)
			
			for i in range(fsgmub_length):
				# note position, note_type, note_length, other
				position, note_type, note_length = struct.unpack(">fIf", fsgmub_file.read(12))
				other_data = fsgmub_file.read(4)
				try:
					flag_i = FLAG_TYPES.index(note_type)
				except ValueError:
					flag_i = -1
				if flag_i >= 0:
					note_type = FLAG_NAMES[flag_i]
					if flag_i == FLAG_AUTHOR or flag_i == FLAG_SECTION:
						str_index = struct.unpack(">I",other_data)[0] - ENTRY_SIZE*fsgmub_length
						other_data = fsgmub_strings[str_index:].split(b"\x00",1)[0].decode("utf-8")
					elif flag_i == FLAG_CHART_BPM:
						other_data = struct.unpack(">f",other_data)[0]
					else:
						other_data = struct.unpack(">I",other_data)[0]
				else:
					other_data = struct.unpack(">I",other_data)[0]
				fsgmub_data = (position, note_type, note_length, other_data)
				csv_writer.writerow(fsgmub_data)
	
def csv_to_fsgmub(csv_filename):
	csv_name, csv_ext = os.path.splitext(csv_filename)
	fsgmub_filename = csv_name + FSGMUB_EXTENSION

	fsgmub_length = 0
	output_array = []
	string_blob = bytearray()
	string_blob_size = 0
		
	with open(csv_filename, "r", newline='') as csv_file:
		for line in csv_file:
			fsgmub_length += 1

	with open(csv_filename, "r", newline='') as csv_file:
		csv_reader = csv.reader(csv_file)
		for row in csv_reader:
			note_type = None
			other_data = None
			pack_str = None
			nt_upper = row[1].strip().upper()
			try:
				flag_i = FLAG_NAMES.index(nt_upper)
			except ValueError:
				flag_i = -1
			if flag_i >= 0:
				note_type = FLAG_TYPES[flag_i]
				if flag_i == FLAG_AUTHOR or flag_i == FLAG_SECTION:
					string_index = string_blob_size + ENTRY_SIZE*fsgmub_length
					new_blob = row[3].encode("utf-8") + b"\x00"
					string_blob += new_blob
					string_blob_size += len(new_blob)
					other_data = string_index
					pack_str = ">fIfI"
				elif flag_i == FLAG_CHART_BPM:
					pack_str = ">fIff"
					other_data = float(row[3])
				else:
					pack_str = ">fIfI"
					other_data = int(row[3])
			else:
				pack_str = ">fIfI"
				if note_type == None:
					note_type = int(row[1])
				other_data = int(row[3])
			output_array.append(struct.pack(pack_str,
											float(row[0]),
											note_type,
											float(row[2]),
											other_data))

	
	with open(fsgmub_filename, "wb") as fsgmub_file:
		# compute crc
		# chart length, string blob size (0), chart lines
		size_bin = struct.pack(">II", fsgmub_length, string_blob_size)
		crc = binascii.crc32(size_bin)
		for line in output_array:
			# note position, note type, note length, text pointer
			crc = binascii.crc32(line, crc)
		if string_blob_size > 0:
			crc = binascii.crc32(string_blob, crc)
		
		# fsgmub header
		# version (2), crc, chart length, string blob size
		fsgmub_file.write(struct.pack(">II", 2, crc))
		fsgmub_file.write(size_bin)
		
		for line in output_array:
			# note position, note type, note length, text pointer
			fsgmub_file.write(line)
										
		if string_blob_size > 0:
			fsgmub_file.write(string_blob)
		
		# ensure the chart filesize is a multiple of 32 for some reason
		file_size = HEADER_SIZE + fsgmub_length*ENTRY_SIZE + string_blob_size
		size_offset = file_size % ALIGN_SIZE
		if size_offset != 0:
			fsgmub_file.write(b"\x00"*(ALIGN_SIZE - size_offset))

def main():
	if len(sys.argv) < 2:
		usage()
	
	input_filename = sys.argv[1]
	input_name, input_ext = os.path.splitext(input_filename)
	
	if input_ext.lower() in (FSGMUB_EXTENSION, XMK_EXTENSION):
		fsgmub_to_csv(input_filename)
		sys.exit(0)
	if input_ext.lower() == CSV_EXTENSION:
		csv_to_fsgmub(input_filename)
		sys.exit(0)
	
	print("Error: input file {} does not have extension {} or {}".format(input_filename, FSGMUB_EXTENSION, CSV_EXTENSION))
	usage()

if __name__ == "__main__":
	main()