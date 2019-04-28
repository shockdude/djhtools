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

# DJ Hero FSB builder v0.7
# Convert MP3s to FSBs playable in DJ Hero

import os, sys
import struct

OUTPUT_FSB = "output.fsb"
MP3_COUNT = 3

# references
# http://www.mp3-tech.org/programmer/frame_header.html
# https://hydrogenaud.io/index.php/topic,85125.0.html

# tagging
TAG_PREFIX = b"TAG"
ID3_PREFIX = b"ID3"

# MPEG v1: frame size = 1152 samples/frame * bitrate / samplerate / 8 bits/byte
#                     = 144 * bitrate / samplerate
SAMPLES_PER_FRAME = 1152
MPEG_MAGIC = SAMPLES_PER_FRAME / 8
MP3_HEADER_SIZE = 4

MPEG_VERSION_1 = 1
MP3_BITRATES = (None, 32000, 40000, 48000, 56000, 64000, 80000, 96000, 112000, 128000, 160000, 192000, 224000, 256000, 320000, None)
MP3_SAMPLERATES = (44100, 48000, 32000, None)

SAMPLE_RATE_WII = 32000
SAMPLE_RATE_PS3 = 44100

BITRATE_DEFAULT = 160000

fsb_sample_rate = None
fsb_bitrate = None

def write_fsb_header(fsb_outfile, fsb_inputfilename, fsb_size, num_frames):
	# credit to vgmstream & fsbext for the fsb documentation
	
	header_size = 0x50
	num_samples = num_frames * SAMPLES_PER_FRAME
	loop_start = 0
	loop_end = num_samples - 1
	stream_size = fsb_size
	sample_data_size = fsb_size
	mode = 0x4000200

	# copy FSB header from input fsb file
	with open(fsb_inputfilename, "rb") as fsb_inputfile:
		fsb_outfile.write(fsb_inputfile.read(8))
		fsb_inputfile.seek(8, 1)
		fsb_outfile.write(struct.pack("<II", header_size, sample_data_size))
		fsb_outfile.write(fsb_inputfile.read(32))
		fsb_inputfile.seek(2, 1)
		fsb_outfile.write(struct.pack("<H", header_size))
		fsb_outfile.write(fsb_inputfile.read(30))
		fsb_inputfile.seek(24, 1)
		fsb_outfile.write(struct.pack("<IIIIII", num_samples, stream_size, loop_start, loop_end, mode, fsb_sample_rate))
		fsb_outfile.write(fsb_inputfile.read(24))

def check_frame_get_size(header, fsb_inputfilename):
	global fsb_sample_rate
	global fsb_bitrate
	
	header_bytes = struct.unpack("BBBB", header)
	
	# check frame sync
	if header_bytes[0] != 0xFF or ((header_bytes[1] >> 4) & 0xF) != 0xF:
		print("Error: failed to parse MP3 {}, unexpected MP3 frame sync".format(fsb_inputfilename))
		usage()
	
	# check mpeg version is v1
	if ((header_bytes[1] >> 3) & 0x1) != MPEG_VERSION_1:
		print("Error: failed to parse MP3 {}, not mpeg v1".format(fsb_inputfilename))
		usage()
	
	# check mpeg layer 3
	if ((header_bytes[1] >> 1)) & 0x3 != 0x1:
		print("Error: failed to parse MP3 {}, not layer 3".format(fsb_inputfilename))
		usage()
	
	# check bitrate
	bitrate = MP3_BITRATES[((header_bytes[2] >> 4) & 0xF)]
	if bitrate == None:
		print("Error: failed to parse MP3 {}, unsupported bitrate".format(fsb_inputfilename))
		usage()
	if bitrate != fsb_bitrate:
		if fsb_bitrate == None:
			fsb_bitrate = bitrate
			print("Got bitrate: {}kbps".format(int(bitrate/1000)))
			if fsb_bitrate == BITRATE_DEFAULT:
				print("Same bitrate as Wii/PS3")
			elif fsb_bitrate > BITRATE_DEFAULT:
				print("Note: Higher bitrate than Wii/PS3 (160kbps)")
			else:
				print("Warning: Lower bitrate than Wii/PS3 (160kbps)")
		else:
			print("Error: MP3s do not all have the same constant bitrate. Got bitrate {}kbps".format(int(bitrate/1000)))
			usage()
		
	# check sample rate
	sample_rate = MP3_SAMPLERATES[((header_bytes[2] >> 2) & 0x3)]
	if sample_rate == None:
		print("Error: failed to parse MP3 {}, unsupported sample rate".format(fsb_inputfilename))
		usage()
	if sample_rate != fsb_sample_rate:
		if fsb_sample_rate == None:
			fsb_sample_rate = sample_rate
			print("Got sample rate: {}Hz".format(sample_rate))
			if fsb_sample_rate == SAMPLE_RATE_WII:
				print("Ideal sample rate for Wii")
			elif fsb_sample_rate == SAMPLE_RATE_PS3:
				print("Ideal sample rate for PS3")
			else:
				print("Note: Not an ideal sample rate for either Wii or PS3, but should be ok.")
		else:
			print("Error: MP3s do not all have the same sample rate. Got sample rate {}Hz".format(sample_rate))
			usage()
	
	# check padding bit
	padding = ((header_bytes[2] >> 1) & 0x1)
	
	return int(MPEG_MAGIC * bitrate / sample_rate) + padding
	
def usage():
	print("Usage: {} input.fsb green_track.mp3 blue_track.mp3 red_track.mp3 [output.fsb]".format(sys.argv[0]))
	print("An input FSB from DJ Hero is required for copying FSB header data.")
	print("All MP3s must be 32/44.1/48khz, constant bitrate (preferably 160kbps or higher)")
	print("The default output filename is \"output.fsb\"; specifying a different output filename is optional.")
	sys.exit(1)

def main():
	if len(sys.argv) < 5:
		usage()

	fsb_inputfilename = sys.argv[1]
	mp3_filenames = sys.argv[2:5]
	fsb_outfilename = OUTPUT_FSB
	if len(sys.argv) > 5:
		fsb_outfilename = sys.argv[5]
		
	if not os.path.isfile(fsb_inputfilename):
		print("Error: could not find input FSB file {}".format(fsb_inputfilename))
		usage()

	mp3_files = [None, None, None]
	
	# check for ID3 tags so that they can be ignored
	tag_sizes = [0, 0, 0]
	with open(mp3_filenames[0], "rb") as mp3_files[0], open(mp3_filenames[1], "rb") as mp3_files[1], open(mp3_filenames[2], "rb") as mp3_files[2]:
		for i in range(MP3_COUNT):
			id3_data = mp3_files[i].read(3)
			if id3_data == ID3_PREFIX: #ID3v2
				mp3_files[i].read(3)
				id3_sizebytes = struct.unpack(">BBBB",mp3_files[i].read(4))
				tag_sizes[i] = (id3_sizebytes[3] & 0x7F) + ((id3_sizebytes[2] & 0x7F) << 7) + ((id3_sizebytes[1] & 0x7F) << 14) + ((id3_sizebytes[0] & 0x7F) << 21) + 10
				print("Note: MP3 file {} has ID3v2 tags, size {}".format(mp3_filenames[i], tag_sizes[i]))
			elif id3_data == TAG_PREFIX: #ID3v1
				tag_sizes[i] = 256
				print("Note: MP3 file {} has ID3v1 tags, size {}".format(mp3_filenames[i], tag_sizes[i]))
	
	frame_sizes = [[], [], []]
	frame_counts = [0, 0, 0]
	mp3_not_done = [True, True, True]
	
	# count frames in mp3s
	with open(mp3_filenames[0], "rb") as mp3_files[0], open(mp3_filenames[1], "rb") as mp3_files[1], open(mp3_filenames[2], "rb") as mp3_files[2]:	
		for i in range(MP3_COUNT):
			mp3_files[i].seek(tag_sizes[i])
			reading_mp3 = True
			while reading_mp3:
				frame_header = mp3_files[i].read(MP3_HEADER_SIZE)
				# stop at the end of each MP3
				if len(frame_header) < MP3_HEADER_SIZE or frame_header[0:3] == TAG_PREFIX:
					reading_mp3 = False
					continue
				frame_size = check_frame_get_size(frame_header, mp3_filenames[i])
				frame_sizes[i].append(frame_size)
				frame_counts[i] += 1
				mp3_files[i].seek(frame_size - MP3_HEADER_SIZE, 1)
	
	# count the number of mp3 frames
	num_frames = min(frame_counts)
	if sum(frame_counts) > num_frames * MP3_COUNT:
		print("Warning: mp3s are not the same length/do not have the same number of frames")
		print("Frame counts: {}".format(frame_counts))
		print("Using the smallest number of frames: {}".format(num_frames))
	else:
		print("Counted {} frames per MP3".format(num_frames))

	# compute fsb size by adding up the frame sizes
	fsb_size = 0
	for i in range(MP3_COUNT):
		for f in range(num_frames):
			frame_size = frame_sizes[i][f]
			fsb_size += frame_size
			# all fsb frames must be 0x10 aligned
			offset = frame_size % 0x10
			if offset > 0:
				fsb_size += 0x10 - offset
	print("Total FSB size: {}".format(fsb_size))
	
	# write fsb
	with open(fsb_outfilename, "wb") as fsb_out:
		write_fsb_header(fsb_out, fsb_inputfilename, fsb_size, num_frames)
			
		with open(mp3_filenames[0], "rb") as mp3_files[0], open(mp3_filenames[1], "rb") as mp3_files[1], open(mp3_filenames[2], "rb") as mp3_files[2]:
			# skip tag headers
			for i in range(MP3_COUNT):
				mp3_files[i].seek(tag_sizes[i])
			
			# interleave mp3 frames
			for f in range(num_frames):
				for i in range(MP3_COUNT):
					frame_size = frame_sizes[i][f]
					fsb_out.write(mp3_files[i].read(frame_size))
					# all fsb frames must be 0x10 aligned
					offset = frame_size % 0x10
					if offset > 0:
						offset = 0x10 - offset
						for j in range(offset):
							fsb_out.write(b"\x00")
					
	print("Wrote FSB {}".format(fsb_outfilename))

if __name__ == "__main__":
	main()