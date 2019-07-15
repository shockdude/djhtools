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

# DJ Hero AIS/CSV Converter v0.3
# Convert AIS/XMK to CSV, and CSV to AIS

import csv
import os, sys
import struct
import binascii

AIS_EXTENSION = ".ais"
CSV_EXTENSION = ".csv"

HEADER_SIZE = 32
ENTRY_SIZE = 16

def usage():
	print("Usage: {} [inputfile]".format(sys.argv[0]))
	print("Converts DJ Hero 2 AIS to CSV or CSV to AIS")
	sys.exit(1)

def ais_to_csv(ais_filename):
	ais_name, ais_ext = os.path.splitext(ais_filename)
	csv_filename = ais_name + CSV_EXTENSION

	with open(ais_filename, "rb") as ais_file:
		with open(csv_filename, "w", newline='') as csv_file:
			csv_writer = csv.writer(csv_file)
			
			# ais header
			# unknown, difficulty, percent hit, unknown
			ais_data = struct.unpack(">IIIf", ais_file.read(16))
			print("Unknown: {:x}".format(ais_data[0]))
			print("Difficulty: {}".format(ais_data[1]))
			print("Percent Hit: {}".format(ais_data[2]))
			print("Unknown: {}".format(ais_data[3]))
			
			# first ais note
			# unknown, time, unknown, unknown
			ais_data = struct.unpack(">IfII", ais_file.read(16))
			print("Unknown: {:x}".format(ais_data[0]))
			print("Time: {}".format(ais_data[1]))
			print("Unknown: {:x}".format(ais_data[2]))
			print("Unknown: {:x}".format(ais_data[3]))
			
			ais_bytes = ais_file.read(16)
			while len(ais_bytes) == 16:
				# type, index, time, length, lane
				ais_data = struct.unpack(">HHffi", ais_bytes)
				csv_writer.writerow(ais_data)
				ais_bytes = ais_file.read(16)
	
def csv_to_ais(csv_filename):
	csv_name, csv_ext = os.path.splitext(csv_filename)
	ais_filename = csv_name + AIS_EXTENSION

	output_array = []

	with open(csv_filename, "r", newline='') as csv_file:
		csv_reader = csv.reader(csv_file)
		for row in csv_reader:
			output_array.append(struct.pack(">HHffi",
											int(row[0]),
											int(row[1]),
											float(row[2]),
											float(row[3]),
											int(row[4])))
	
	with open(ais_filename, "wb") as ais_file:
		# ais header
		ais_file.write(struct.pack(">IIII", 0, 4, 100, 0))
		ais_file.write(struct.pack(">IIII", 0, 0, 0, 0))
		
		for line in output_array:
			ais_file.write(line)

def main():
	if len(sys.argv) < 2:
		usage()
	
	input_filename = sys.argv[1]
	input_name, input_ext = os.path.splitext(input_filename)
	
	if input_ext.lower() == AIS_EXTENSION:
		ais_to_csv(input_filename)
		sys.exit(0)
	if input_ext.lower() == CSV_EXTENSION:
		csv_to_ais(input_filename)
		sys.exit(0)
	
	print("Error: input file {} does not have extension {}".format(input_filename, AIS_EXTENSION))
	usage()

if __name__ == "__main__":
	main()