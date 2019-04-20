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

# DJ Hero FSGMUB/CSV Converter v0.1
# Convert FSGMUB to CSV, and CSV to FSGMUB
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

FSGMUB_EXTENSION = ".fsgmub"
CSV_EXTENSION = ".csv"

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
			fsgmub_data = struct.unpack(">III", fsgmub_file.read(12))
			print("Version: {}".format(fsgmub_data[0]))
			print("Hash: {:x}".format(fsgmub_data[1]))
			print("Length: {}".format(fsgmub_data[2]))
			
			# string blob size, ignore
			fsgmub_file.read(4)
			
			fsgmub_length = fsgmub_data[2]
			
			for i in range(fsgmub_length):
				# note position, note_type, note_length
				fsgmub_data = struct.unpack(">fIf", fsgmub_file.read(12))
				csv_writer.writerow(fsgmub_data)
				
				# text pointer, ignore
				fsgmub_file.read(4)
	
def csv_to_fsgmub(csv_filename):
	csv_name, csv_ext = os.path.splitext(csv_filename)
	fsgmub_filename = csv_name + FSGMUB_EXTENSION

	# get the linecount of the CSV
	# https://stackoverflow.com/questions/845058/how-to-get-line-count-cheaply-in-python
	with open(csv_filename, "r") as csv_file:
		for line_count, val in enumerate(csv_file):
			pass
	
	line_count += 1
	print("Number of lines: {}".format(line_count))
		
	with open(csv_filename, "r", newline='') as csv_file:
		with open(fsgmub_filename, "wb") as fsgmub_file:
			csv_reader = csv.reader(csv_file)
			
			# fsgmub header
			# version (2), fake hash (deadbeef), chart length, string blob size (0)
			fsgmub_file.write(struct.pack(">IIII", 2, 0xdeadbeef, line_count, 0))
			
			for row in csv_reader:
				# note position, note type, note length, text pointer (0)
				fsgmub_file.write(struct.pack(">fIfI",
											float(row[0]),
											int(row[1]),
											float(row[2]),
											0))
				
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
		fsgmub_to_csv(input_filename)
		sys.exit(0)
	if input_ext.lower() == CSV_EXTENSION:
		csv_to_fsgmub(input_filename)
		sys.exit(0)
	
	print("Error: input file {} does not have extension {} or {}".format(input_filename, FSGMUB_EXTENSION, CSV_EXTENSION))
	usage()

if __name__ == "__main__":
	main()