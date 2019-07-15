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

# DJ Hero 2 XMK/AIS Converter v0.3
# Convert DJH2 XMK to DJH2 AIS - create an AI for your DJ Hero 2 chart!
# Credit to pikminguts92 from ScoreHero for documenting the FSGMUB format
# https://www.scorehero.com/forum/viewtopic.php?p=1827382#1827382

import os, sys
import struct
from random import random
import xml.etree.ElementTree as ET

XMK_EXTENSION = ".xmk"
AIS_EXTENSION = ".ais"

NOTE_WHITELIST = (0,1,2,3,4,5,6,7,8,9,10,11,26,27,28,29)
NOTE_FADES = (9,10,11,27,28,29)
NOTE_MAXLEN = 1.0/16
# todo freestyle effects/samples/crossfades

HIT_RATES = (65,75,85,95)
#HIT_RATES = (100,)

CHARTS = ("DJ_Beginner.xmk", "DJ_Easy.xmk", "DJ_Medium.xmk", "DJ_Hard.xmk", "DJ_Expert.xmk")
DIFF_ABBR = ("beg", "easy", "med", "hard", "exp")

def usage():
	print("Usage: {} [song_directory]".format(sys.argv[0]))
	print("Convert all XMKs in a song directory to AIS - create an AI for your DJ Hero 2 chart!")
	print("If no directory is specified, the script will attempt to use the current directory")
	print("Experimental, not all features are supported, things may be broken")
	sys.exit(1)

def get_active_streams(chunk, streams_active = [True, True, True]):
	players = chunk["players"].lower()
	if players == "p1":
		streams_active = [False, False, False]
	else:
		if "streamA" in chunk:
			streams_active[0] = chunk["streamA"].lower() != "p1"
		else:
			streams_active[0] = True
		if "streamB" in chunk:
			streams_active[1] = chunk["streamB"].lower() != "p1"
		else:
			streams_active[1] = True
		if "streamS" in chunk:
			streams_active[2] = chunk["streamS"].lower() != "p1"
		else:
			streams_active[2] = True
	return streams_active

def main():
	if len(sys.argv) >= 2:
		os.chdir(sys.argv[1])
		
	xml_filename = "ChunkRemix.xml"
	chunks = None
	if os.path.isfile(xml_filename):
		print("Found {}".format(xml_filename))
		chunkremix = ET.parse(xml_filename)
		chunks = chunkremix.getroot()
	else:
		print("Note: {} not found".format(xml_filename))
		
	for diff in range(len(CHARTS)):
		input_filename = CHARTS[diff]
		if not os.path.isfile(input_filename):
			print("Note: {} not found".format(input_filename))
			continue
		
		input_name, input_ext = os.path.splitext(input_filename)
		
		for hit_rate in HIT_RATES:
			note_array = []
			output_array = []
			bpm = 0
			force_cf = 0
			chunk_count = 0

			with open(input_filename, "rb") as input_file:
				# fsgmub header
				# version, hash, length
				fsgmub_data = struct.unpack(">IIII", input_file.read(16))
				fsgmub_length = fsgmub_data[2]
					
				for i in range(fsgmub_length):
					# note position, note_type, note_length, other
					note_data = list(struct.unpack(">fIf", input_file.read(12)))
					if note_data[1] == 0x0B000002:
						bpm = struct.unpack(">f", input_file.read(4))[0]
					else:
						input_file.seek(4, 1)
					if note_data[1] == 23:
						force_cf = note_data[0] + note_data[2]
					# hack to allow chunkremix notes to be processed before other notes
					if note_data[1] == 26:
						note_data[0] -= .001
					if note_data[1] in NOTE_WHITELIST:
						if note_data[1] not in NOTE_FADES or note_data[0] > force_cf:
							note_array.append(note_data)
							
			note_array.sort(key=lambda note:note[0])

			fsgmub_length = len(note_array)
			measure_time = 60/bpm * 4
			start_time = measure_time * 2
			cf_lane = 0
			is_spike = False
			current_chunk = 0
			if chunks != None:
				streams_active = get_active_streams(chunks[current_chunk].attrib)
			else:
				streams_active = [True, True, True]
			for i in range(fsgmub_length):
				type = None
				float_data = 0
				int_data = 0
				pos, note, length = note_array[i][:3]
				ai_time = start_time + pos*measure_time
				is_hit = random() * 100 <= hit_rate
				hit_offset = 0
				
				if note == 26: # chunkremix
					if chunks == None:
						print("Error: battle chart is missing ChunkRemix.xml")
						sys.exit(1)
					current_chunk += 1
					if current_chunk >= len(chunks):
						streams_active = [True, True, True]
					else:
						streams_active = get_active_streams(chunks[current_chunk].attrib, streams_active)
					continue

				# skip inactive streams
				if not streams_active[0] and note in (0,3,5,7):
					continue
				if not streams_active[1] and note in (1,4,6,8):
					continue
				if not streams_active[2] and note == 2:
					continue
							
				if note in (0,1,2): # tap
					if is_hit:
						if length > NOTE_MAXLEN:
							type = 0x0
						else:
							type = 0x20
						int_data = note
				elif note in (3,4): # upscratch
					if is_hit:
						type = 0x40
						int_data = note - 3
				elif note in (5,6): # downscratch
					if is_hit:
						if length > NOTE_MAXLEN:
							type = 0x50
						else:
							type = 0x60
						int_data = note - 5
				elif note in (7,8): # anydir scratch
					if is_hit:
						type = 0x40
						int_data = note - 7
				elif note in (9,10,11,27,28,29): # crossfades
					# ugly code incoming
					type = 0x80
					if note in (9,28):
						int_data = 2 # blue fade/spike
					elif note in (10,29):
						int_data = 0 # center fade/spike
					elif note in (11,27):
						int_data = 1 # green fade/spike
					else:
						print("Error: bug in crossfade conversion")
						sys.exit(1)
					if not is_hit:
						if note in (27,28,29): # skip spike
							type = None
						elif not is_spike: # delay crossfade - but always hit unspikes
							hit_offset = .1
					if cf_lane == int_data: # don't do unnecessary crossfades, e.g. after skipped spike
						type = None
					if type != None: # keep track of the current crossfade
						cf_lane = int_data
						if note in (27,28,29):
							is_spike = True
						else:
							is_spike = False
					
				if type != None:
					output_array.append([type, ai_time + hit_offset, float_data, int_data])
				
				if type == 0x0: # tap unhold
					output_array.append([0x10, ai_time + length*measure_time, float_data, int_data])
				elif type == 0x50: # downscratch unhold
					output_array.append([0x70, ai_time + length*measure_time, float_data, int_data])
				elif note in (7,8):
					i = 1.0/32
					while i < length: # hit anydir scratches
						is_hit = random() * 100 <= hit_rate
						if is_hit:
							output_array.append([0x40, ai_time + i*measure_time, float_data, int_data])
							i += 1.0/32
			
			output_array.sort(key=lambda ai_note: ai_note[1])
			
			output_ext = AIS_EXTENSION
			output_filename = "DJH-p2-{}-{}.ais".format(DIFF_ABBR[diff], hit_rate)
			
			print("Creating AI file {}".format(output_filename))
			
			with open(output_filename, "wb") as output_file:
				# ais header
				# unimportant, difficulty, percent hit, unimportant float
				output_file.write(struct.pack(">IIII", 0, diff, hit_rate, 1))
				# timestamp and unknown dword, all unimportant so set it all to 0
				output_file.write(struct.pack(">IIII", 0, 0, 0, 0))
				
				# type, unimportant short count, time in seconds, float data, int data
				for line in output_array:
					output_file.write(struct.pack(">HHffI", line[0], 0, line[1], line[2], line[3]))

if __name__ == "__main__":
	main()