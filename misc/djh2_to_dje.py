"""
MIT License

Copyright (c) 2020 shockdude

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

# DJ Hero 2 to DJ Engine Converter v0.62

import os, sys
import xml.etree.ElementTree as ET
import json
import csv
import subprocess
import shutil
import time

SLEEP_TIME = 3

trac_dict = {}
output_dir = "songs"

def usage():
	basename = os.path.basename(sys.argv[0])
	print()
	print("DJH2 to DJ Engine Converter v0.62")
	print("Convert DJH2 audiotracks folder or DJH2 custom charts to a songs folder compatible with DJ Engine Alpha v1.5p1")
	print()
	print("Usage: Drag-and-drop DJ Hero 2's AUDIO\Audiotracks folder onto {}".format(basename))
	print("or drag-and-drop a custom song's folder (or its DJH2 folder) onto {}.".format(basename))
	print("You can drag-and-drop multiple custom songs and the script will attempt to convert them all")
	print("Or use the commandline: {} [folder_path]".format(basename))
	print()
	time.sleep(SLEEP_TIME)
	sys.exit(1)

def get_from_trac(key):
	trac_key = key.upper()
	if trac_key in trac_dict:
		return trac_dict[trac_key]
	return key

def add_to_json(song_json, json_path, value):
	current_root = song_json
	for json_entry in json_path[:-1]:
		if json_entry not in current_root:
			current_root[json_entry] = {}
		current_root = current_root[json_entry]
	current_root[json_path[-1]] = value

def build_json(track):
	song_json = {}
	bpm = 0
	
	elems = track.findall("MixName")
	if len(elems) > 0:
		add_to_json(song_json, ["song", "first", "name"], get_from_trac(elems[0].text))
		add_to_json(song_json, ["extra", "id", "id_name"], elems[0].text)
		if len(elems) > 1:
			add_to_json(song_json, ["song", "second", "name"], get_from_trac(elems[1].text))
			add_to_json(song_json, ["extra", "id", "id_name2"], elems[1].text)
		
	elems = track.findall("MixArtist")
	if len(elems) > 0:
		add_to_json(song_json, ["song", "first", "artist"], get_from_trac(elems[0].text))
		add_to_json(song_json, ["extra", "id", "id_artist"], elems[0].text)
		if len(elems) > 1:
			add_to_json(song_json, ["song", "second", "artist"], get_from_trac(elems[1].text))
			add_to_json(song_json, ["extra", "id", "id_artist2"], elems[1].text)
	
	elem = track.find("MixHeadlineDJName")
	if elem != None:
		add_to_json(song_json, ["song", "dj"], get_from_trac(elem.text))
		
	elem = track.find("TrackDuration")
	if elem != None:
		add_to_json(song_json, ["song", "song_length"], int(elem.text) * 1000)

	elem = track.find("BPM")
	if elem != None:
		bpm = float(elem.text)
		add_to_json(song_json, ["difficulty", "bpm"], bpm)
	
	elem = track.find("PreviewLoopPointStartInBars")
	if elem != None:
		bar = float(elem.text)
		add_to_json(song_json, ["song", "preview_start_time"], int(round(240000.0*(bar-1)/bpm)))

	elem = track.find("PreviewLoopPointEndInBars")
	if elem != None:
		bar = float(elem.text)
		add_to_json(song_json, ["song", "preview_end_time"], int(round(240000.0*(bar-1)/bpm)))

	elems = track.findall("DeckSpeedMultiplier")
	for elem in elems:
		elem_diff = elem.attrib["Difficulty"]
		if elem_diff == "0":
			add_to_json(song_json, ["difficulty", "deck_speed", "deckspeed_beginner"], float(elem.text))
		elif elem_diff == "1":
			add_to_json(song_json, ["difficulty", "deck_speed", "deckspeed_easy"], float(elem.text))
		elif elem_diff == "2":
			add_to_json(song_json, ["difficulty", "deck_speed", "deckspeed_medium"], float(elem.text))
		elif elem_diff == "3":
			add_to_json(song_json, ["difficulty", "deck_speed", "deckspeed_hard"], float(elem.text))
		elif elem_diff == "4":
			add_to_json(song_json, ["difficulty", "deck_speed", "deckspeed_expert"], float(elem.text))
			
	elem = track.find("TrackComplexity")
	if elem != None:
		add_to_json(song_json, ["difficulty", "complexity", "track_complexity"], int(elem.text))
		
	elem = track.find("TapComplexity")
	if elem != None:
		add_to_json(song_json, ["difficulty", "complexity", "tap_complexity"], int(elem.text))
			
	elem = track.find("CrossfadeComplexity")
	if elem != None:
		add_to_json(song_json, ["difficulty", "complexity", "cross_complexity"], int(elem.text))
			
	elem = track.find("ScratchComplexity")
	if elem != None:
		add_to_json(song_json, ["difficulty", "complexity", "scratch_complexity"], int(elem.text))
			
	elem = track.find("IsMegamixBridge")
	if elem != None:
		if elem.text == "1":
			add_to_json(song_json, ["extra", "megamix", "megamix_transitions"], True)

	elem = track.find("HasExtendedIntro")
	if elem != None:
		if elem.text == "1":
			add_to_json(song_json, ["extra", "megamix", "megamix_has_intro"], True)

	elem = track.find("HighwayRevealBarOffset")
	if elem != None:
		bar = float(elem.text)
		add_to_json(song_json, ["extra", "megamix_highway_offset"], int(round(240000.0*(bar-1)/bpm)))
	
	elems = track.findall("SortArtist")
	sort_artists = []
	for elem in elems:
		sort_artists.append(get_from_trac(elem.text))
	if len(sort_artists) > 0:
		add_to_json(song_json, ["extra", "sort_artists"], sort_artists)

	elem = track.find("EnvironmentIntroStartBar")
	if elem != None:
		bar = float(elem.text)
		add_to_json(song_json, ["extra", "env_start_time"], int(round(240000.0*(bar-1)/bpm)))
	
	elem = track.find("IsADMCTrack")
	if elem != None:
		if elem.text == "1":
			add_to_json(song_json, ["extra", "battle_music"], True)
	
	elem = track.find("IsMenuMusic")
	if elem != None:
		if elem.text == "1":
			add_to_json(song_json, ["extra", "menu_music"], True)
	
	return song_json

def main():
	convert_audio = True
	is_audiotracks_folder = True
	converted_count = 0
	error_count = 0
	
	# hack to ensure working directory is the script directory
	# for some reason this isn't guaranteed with the exe
	os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
	
	# check that convert tools exist
	vgms_path = "vgmstream/test.exe"
	sox_path = "sox/sox.exe"
	
	if not os.path.isfile(vgms_path) or not os.path.isfile(sox_path):
		print("Error: vgmstream or sox not found, skipping audio conversion")
		convert_audio = False
		error_count += 1
	
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
		except Exception as e:
			print("Warning: failed to use TRAC files, using IDs as strings instead")
			print(e)

		# make output "songs" directory
		try:
			if not os.path.isdir(output_dir):
				os.mkdir(output_dir)
		except Exception as e:
			print("Error: Failed to make output folder {}".format(output_dir))
			print(e)
			usage()
		
		# parse tracklisting.xml
		tracklisting_text = None
		with open(tracklisting_filename, "r") as tracklisting_file:
			tracklisting_text = tracklisting_file.read()
		try:
			tracklist = ET.fromstring(tracklisting_text)
			if tracklist.tag == "Track":
				raise ET.ParseError
		except Exception as e:
			try:
				tracklisting_text = "<TrackList>" + tracklisting_text + "</TrackList>"
				tracklist = ET.fromstring(tracklisting_text)
			except Exception as e:
				print("Failed to process xml file {}".format(tracklisting_filename))
				print(e)
				usage()
			
		tracks = tracklist.findall("Track")
		if len(tracks) <= 0:
			print("Error: no Tracks found in {}".format(tracklisting_filename))
			usage()

		for track in tracklist.findall("Track"):
			idtag_tag = track.find("IDTag")
			if idtag_tag == None:
				print("Error: found Track without IDTag, skipping")
				error_count += 1
				continue
			idtag = idtag_tag.text
			
			loc_tag = track.find("FolderLocation")
			if loc_tag == None:
				print("Error: {} has no FolderLocation, skipping".format(idtag))
				error_count += 1
				continue
			loc = loc_tag.text.replace("\\", "/")
			loc_track_folder = loc.split("/")[-1]
			
			print("Converting {}".format(idtag))
			
			if is_audiotracks_folder:
				loc = "{}/../../{}".format(chart_path, loc)
			else:
				loc = "{}/{}".format(chart_path, loc_track_folder)
			
			if not os.path.isdir(loc):
				print("Error: folder for {} does not exist, skipping".format(idtag))
				error_count += 1
				continue
			
			# make output track directory
			output_track_dir = "{}/{}".format(output_dir, loc_track_folder)
			try:
				if not os.path.isdir(output_track_dir):
					os.mkdir(output_track_dir)
			except Exception as e:
				print("Error: Failed to make output folder for {}, skipping".format(idtag))
				print(e)
				error_count += 1
				continue
			
			# build song.json
			song_json = build_json(track)
			try:
				with open("{}/song.json".format(output_track_dir), "w") as json_file:
					print(json.dumps(song_json, sort_keys=False, indent=4), file=json_file)
			except Exception as e:
				print("Error: Failed to write song.json for {}, skipping".format(idtag))
				print(e)
				error_count += 1
			
			# copy DJ_Expert.xmk to chart.xmk
			chart_diffs = ("DJ_Beginner.xmk", "DJ_Easy.xmk", "DJ_Medium.xmk", "DJ_Hard.xmk", "DJ_Expert.xmk")
			chart_copied = False
			for chart_xmk in chart_diffs:
				try:
					chart_filepath = "{}/{}".format(loc, chart_xmk)
					if os.path.isfile(chart_filepath):
						shutil.copyfile(chart_filepath, "{}/{}".format(output_track_dir, chart_xmk))
						chart_copied = True
				except Exception as e:
					print("Error: Failed to copy {} for {}, skipping".format(chart_xmk, idtag))
					print(e)
					error_count += 1
			if not chart_copied:
				print("Error: No chart copied for {}".format(idtag))
				error_count += 1
			
			# convert DJ.fsb to song.ogg
			if convert_audio:
				try:
					temp_wav = "{}/temp.wav".format(output_track_dir)
					vgm_out = subprocess.run([vgms_path, "-i", "{}/DJ.fsb".format(loc), "-o", temp_wav], stdout=subprocess.DEVNULL)
					if vgm_out.returncode != 0:
						print("Error: Failed to extract DJ.fsb for song.ogg for {}, skipping".format(idtag))
						error_count += 1
					else:
						sox_out0 = subprocess.Popen([sox_path, temp_wav, 
													"-C", "8", "{}/green.ogg".format(output_track_dir), "-D",
													"remix", "-m", "1", "2",
													"rate", "-v", "44100"])
						sox_out1 = subprocess.Popen([sox_path, temp_wav, 
													"-C", "8", "{}/blue.ogg".format(output_track_dir), "-D",
													"remix", "-m", "3", "4",
													"rate", "-v", "44100"])
						sox_out2 = subprocess.Popen([sox_path, temp_wav, 
													"-C", "8", "{}/red.ogg".format(output_track_dir), "-D",
													"remix", "-m", "5", "6",
													"rate", "-v", "44100"])
						sox_out0.wait()
						sox_out1.wait()
						sox_out2.wait()
						if sox_out0.returncode != 0 or sox_out1.returncode != 0 or sox_out2.returncode != 0:
							print("Error: Failed to mix DJ.fsb to ogg stems for {}, skipping".format(idtag))
							error_count += 1
					if os.path.isfile(temp_wav):
						os.remove(temp_wav)
				except Exception as e:
					print("Error: Failed to convert DJ.ogg to ogg stems for {}, skipping".format(idtag))
					print(e)
					error_count += 1
			
			converted_count += 1
	
	print("{} chart(s) processed".format(converted_count))
	print("{} error(s)".format(error_count))
	time.sleep(SLEEP_TIME)

if __name__ == "__main__":
	main()