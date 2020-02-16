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

# DJ Hero 2 to DJ Engine Converter v0.4

import os, sys
import xml.etree.ElementTree as ET
import configparser
import csv
import subprocess
import shutil
import time

trac_dict = {}
output_dir = "songs"

def usage():
	basename = os.path.basename(sys.argv[0])
	print("DJH2 to DJ Engine Converter v0.4")
	print("Convert DJH2 audiotracks folder or DJH2 custom charts to a songs folder compatible with DJ Engine Alpha v1.1")
	print()
	print("Usage: Drag-and-drop DJ Hero 2's AUDIO\Audiotracks folder onto {}".format(basename))
	print("or drag-and-drop a custom song's folder (or its DJH2 folder) onto {}.".format(basename))
	print("You can drag-and-drop multiple custom songs and the script will attempt to convert them all")
	print("Or use the commandline: {} [folder_path]".format(basename))
	print()
	time.sleep(3)
	sys.exit(1)

def add_ini_key(track, ini_dict, ini_key, xml_elem, is_trac = False, xml_attr = None, xml_attr_value = None):
	elems = track.findall(xml_elem)
	if len(elems) == 0:
		return
	
	count = 1
	
	for elem in elems:
		value = elem.text
		
		# need to lookup from the trac dict?
		if is_trac:
			trac_key = value.upper()
			if trac_key in trac_dict:
				value = trac_dict[trac_key]

		# dependent on an xml attribute?
		if xml_attr != None:
			if elem.attrib[xml_attr] == str(xml_attr_value):
				ini_dict[ini_key] = value
				return
		# e.g. multiple MixName elements become "name" and "name2"
		elif count > 1:
			ini_dict[ini_key + str(count)] = value
		else:
			ini_dict[ini_key] = value
		count += 1

def main():
	convert_audio = True
	is_audiotracks_folder = True
	
	# hack to ensure working directory is the script directory
	# for some reason this isn't guaranteed with the exe
	os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
	
	# check that convert tools exist
	vgms_path = "vgmstream/test.exe"
	sox_path = "sox/sox.exe"
	
	if not os.path.isfile(vgms_path) or not os.path.isfile(sox_path):
		print("Warning: vgmstream or sox not found, skipping audio conversion")
		convert_audio = False
	
	chart_paths = None
	if len(sys.argv) > 1:
		chart_paths = sys.argv[1:]
	else:
		chart_paths = [os.getcwd(),]
	
	for chart_path in chart_paths:
		# detect a DJH2 folder in a custom song folder
		chart_path_basename = os.path.basename(chart_path).upper()
		if chart_path_basename != "AUDIOTRACKS" and chart_path_basename != "DJH2":
			if os.path.isdir("{}/DJH2".format(chart_path)):
				print("Located custom song {}'s DJH2 folder".format(chart_path_basename))
				chart_path = "{}/DJH2".format(chart_path)

		# look for tracklisting
		tracklisting_filename = "{}/TrackListing.xml".format(chart_path)
		if os.path.isfile(tracklisting_filename):
			print("Found 'TrackListing.xml', assuming audiotracks folder")
		else:
			print("Did not find 'TrackListing.xml', assuming customs folder")
			is_audiotracks_folder = False
			tracklisting_filename = "{}/Info for TrackListing.xml".format(chart_path)
			if os.path.isfile(tracklisting_filename):
				print("Found 'Info for TrackListing.xml'")
			else:
				print("Error: Did not find 'Info for TrackListing.xml' in {}".format(chart_path))
				usage()
		
		try:
			if is_audiotracks_folder:
				# build trac string dict from text strings
				with open("{}/../../Text/TRAC/TRACID.txt".format(chart_path), "r") as tracid_file:
					with open ("{}/../../Text/TRAC/TRACE.txt".format(chart_path), "rb") as trace_file:
						tracids = tracid_file.read().split("\n")
						traces = trace_file.read().split(b"\x00")
						num_tracs = len(tracids)

						if num_tracs != len(traces):
							print("Error: mismatched number of trac IDs and trac strings: {}, {}".format(len(tracids), len(traces)))
							usage()
							
						for i in range(num_tracs):
							trac_dict[tracids[i].upper()] = traces[i].decode("utf-8")
			else:
				# build trac string dict from Info for TRAC.csv
				with open("{}/Info for TRAC.csv".format(chart_path), "r", encoding="utf_8_sig", newline="") as trac_file:
					trac_csv = csv.reader(trac_file, dialect="excel")
					for row in trac_csv:
						if len(row) > 0: # ignore blank lines
							if row[0][0:2] == "//": # ignore commented lines
								continue
							trac_dict[row[0]] = row[-1]
		except FileNotFoundError:
			print("Warning: missing TRAC files, using IDs as strings instead")

		# make output "songs" directory
		if not os.path.isdir(output_dir):
			os.mkdir(output_dir)
		
		# parse tracklisting.xml
		tracklisting_text = None
		with open(tracklisting_filename, "r") as tracklisting_file:
			tracklisting_text = tracklisting_file.read()
		try:
			tracklist = ET.fromstring(tracklisting_text)
			if tracklist.tag == "Track":
				raise ET.ParseError
		except ET.ParseError:
			tracklisting_text = "<TrackList>" + tracklisting_text + "</TrackList>"
			tracklist = ET.fromstring(tracklisting_text)

		for track in tracklist.findall("Track"):
			ini_dict = {}
			idtag = track.find("IDTag").text.replace("\\", "/")
			loc = track.find("FolderLocation").text.replace("\\", "/")
			loc_track_folder = loc.split("/")[-1]
			print(idtag)
			
			if is_audiotracks_folder:
				loc = "{}/../../{}".format(chart_path, loc)
			else:
				loc = "{}/{}".format(chart_path, loc_track_folder)
			
			if not os.path.isdir(loc):
				print("Error: folder for {} does not exist, skipping".format(idtag))
				continue
			
			# make output track directory
			output_track_dir = "{}/{}".format(output_dir, loc_track_folder)
			if not os.path.isdir(output_track_dir):
				os.mkdir(output_track_dir)
			
			# build info.ini
			add_ini_key(track, ini_dict, "artist", "MixArtist", True)
			add_ini_key(track, ini_dict, "name", "MixName", True)
			add_ini_key(track, ini_dict, "dj", "MixHeadlineDJName", True)
			add_ini_key(track, ini_dict, "bpm", "BPM")
			add_ini_key(track, ini_dict, "deckspeed_beginner", "DeckSpeedMultiplier", False, "Difficulty", "0")
			add_ini_key(track, ini_dict, "deckspeed_easy", "DeckSpeedMultiplier", False, "Difficulty", "1")
			add_ini_key(track, ini_dict, "deckspeed_medium", "DeckSpeedMultiplier", False, "Difficulty", "2")
			add_ini_key(track, ini_dict, "deckspeed_hard", "DeckSpeedMultiplier", False, "Difficulty", "3")
			add_ini_key(track, ini_dict, "deckspeed_expert", "DeckSpeedMultiplier", False, "Difficulty", "4")
			add_ini_key(track, ini_dict, "track_complexity", "TrackComplexity")
			add_ini_key(track, ini_dict, "tap_complexity", "TapComplexity")
			add_ini_key(track, ini_dict, "crossfade_complexity", "CrossfadeComplexity")
			add_ini_key(track, ini_dict, "scratch_complexity", "ScratchComplexity")
			add_ini_key(track, ini_dict, "song_length", "TrackDuration")

			info_ini = configparser.ConfigParser()
			info_ini["song"] = ini_dict
			with open("{}/info.ini".format(output_track_dir), "w") as ini_file:
				info_ini.write(ini_file)
			
			# copy DJ_Expert.xmk to chart.xmk
			shutil.copyfile("{}/DJ_Expert.xmk".format(loc), "{}/chart.xmk".format(output_track_dir))
			
			# convert DJ.fsb to song.ogg
			if convert_audio:
				try:
					vgm_out = subprocess.run([vgms_path, "-i", "-p", "{}/DJ.fsb".format(loc)], capture_output = True)
					if vgm_out.returncode != 0:
						print("Error: Failed to extract DJ.fsb")
					else:
						sox_out = subprocess.run([sox_path, "-t", ".wav", "-",
												   "-C", "8", "{}/song.ogg".format(output_track_dir), "-D",
												   "remix", "-m", "1,3,5", "2,4,6",
												   "rate", "-v", "44100"], input = vgm_out.stdout)
						if sox_out.returncode != 0:
							print("Error: Failed to mix DJ.fsb to ogg")
				except FileNotFoundError:
					print("Warning: vgmstream or sox not found, audio not converted")
					continue

if __name__ == "__main__":
	main()