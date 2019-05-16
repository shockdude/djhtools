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

# DJ Hero Freestyle Sample (FSS) FSB builder v0.1
# Convert sample MP3s to FSS FSBs playable in DJ Hero

import os, sys
import struct

OUTPUT_FSB = "FSS.fsb"

FSB_EXTENSION = ".fsb"
MP3_EXTENSION = ".mp3"

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

def write_fsb_header(fsb_outfile, mp3_count, mp3_filenames, frame_counts, fsb_sizes):
	# credit to vgmstream & fsbext for the fsb documentation
	
	header_size = 0x50
	total_header_size = header_size * mp3_count
	sample_data_size = sum(fsb_sizes)
	loop_start = 0
	mode = 0x240
	num_channels = 2

	fsb_outfile.write(struct.pack("<4sIII", "FSB4".encode("utf-8"), mp3_count, total_header_size, sample_data_size))
	fsb_outfile.write(struct.pack("<IIII", 0x40000, 0x20, 0, 0))
	fsb_outfile.write(struct.pack("<IIII", 0, 0, 0, 0))
	for i in range(mp3_count):
		stream_size = fsb_sizes[i]
		num_samples = frame_counts[i] * SAMPLES_PER_FRAME
		loop_end = num_samples - 1
		mp3_name = os.path.basename(mp3_filenames[i]).encode("utf-8")
		fsb_outfile.write(struct.pack("<H30s", header_size, mp3_name))
		fsb_outfile.write(struct.pack("<IIII", num_samples, stream_size, loop_start, loop_end))
		fsb_outfile.write(struct.pack("<IIHHHH", mode, fsb_sample_rate, 0xFF, 0x80, 0x80, num_channels))
		fsb_outfile.write(struct.pack("<IIII", 1065353216, 1176256512, 0, 0))

def check_frame_get_size(header, mp3_filename):
	global fsb_sample_rate
	global fsb_bitrate
	
	header_bytes = struct.unpack("BBBB", header)
	
	# check frame sync
	if header_bytes[0] != 0xFF or ((header_bytes[1] >> 4) & 0xF) != 0xF:
		print("Error: failed to parse MP3 {}, unexpected MP3 frame sync".format(mp3_filename))
		usage()
	
	# check mpeg version is v1
	if ((header_bytes[1] >> 3) & 0x1) != MPEG_VERSION_1:
		print("Error: failed to parse MP3 {}, not mpeg v1".format(mp3_filename))
		usage()
	
	# check mpeg layer 3
	if ((header_bytes[1] >> 1)) & 0x3 != 0x1:
		print("Error: failed to parse MP3 {}, not layer 3".format(mp3_filename))
		usage()
	
	# check bitrate
	bitrate = MP3_BITRATES[((header_bytes[2] >> 4) & 0xF)]
	if bitrate == None:
		print("Error: failed to parse MP3 {}, unsupported bitrate".format(mp3_filename))
		usage()
	if bitrate != fsb_bitrate:
		if fsb_bitrate == None:
			fsb_bitrate = bitrate
			print("Got bitrate: {}kbps".format(int(bitrate/1000)))
			if fsb_bitrate == BITRATE_DEFAULT:
				print("Same bitrate as Wii/PS3")
			elif fsb_bitrate > BITRATE_DEFAULT:
				print("Note: Higher bitrate than Wii/PS3 (160kbps), which is fine.")
			else:
				print("Warning: Lower bitrate than Wii/PS3 (160kbps)")
		else:
			print("Error: MP3s do not all have the same constant bitrate. Got bitrate {}kbps".format(int(bitrate/1000)))
			usage()
		
	# check sample rate
	sample_rate = MP3_SAMPLERATES[((header_bytes[2] >> 2) & 0x3)]
	if sample_rate == None:
		print("Error: failed to parse MP3 {}, unsupported sample rate".format(mp3_filename))
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
	print("DJ FSS FSB Usage: {} sample1.mp3 sample2.mp3 sample3.mp3 ... [output.fsb]".format(sys.argv[0]))
	print("Any number of sample MP3s is allowed; however DJ Hero 1 only supports FSBs with 5 samples.")
	print("All MP3s must be 32/44.1/48khz, constant bitrate (preferably 160kbps or higher)")
	print("The default output filename is \"{}\"; specifying a different output filename is optional.".format(OUTPUT_FSB))
	sys.exit(1)

def main():
	if len(sys.argv) < 2:
		usage()
	
	file_args = sys.argv[1:]
	mp3_count = 0
	mp3_filenames = []
	fsb_outfilename = OUTPUT_FSB
	for file_arg in file_args:
		file_arg_name, file_arg_ext = os.path.splitext(file_arg)
		if file_arg_ext.lower() == MP3_EXTENSION:
			mp3_count += 1
			mp3_filenames.append(file_arg)
		elif file_arg_ext.lower() == FSB_EXTENSION:
			if mp3_count == 0:
				print("Error: specified output fsb {} but no input MP3s".format(file_arg))
				usage()
			else:
				fsb_outfilename = file_arg
				break
		else:
			print("Error: file {} is not an MP3 or FSB".format(file_arg))
			usage()
	
	print("Converting {} MP3s to DJH FSS FSB, outputting to {}".format(mp3_count, fsb_outfilename))
	if mp3_count != 5:
		print("Warning: DJH1 requires 5 samples")

	tag_sizes = []
	frame_sizes = []
	frame_counts = []
	fsb_sizes = []
	offsets = []
	
	# check for ID3 tags so that they can be ignored
	for i in range(mp3_count):
		tag_sizes.append(0)
		with open(mp3_filenames[i], "rb") as mp3_file:
			id3_data = mp3_file.read(3)
			if id3_data == ID3_PREFIX: #ID3v2
				mp3_file.read(3)
				id3_sizebytes = struct.unpack(">BBBB",mp3_file.read(4))
				tag_sizes[i] = (id3_sizebytes[3] & 0x7F) + ((id3_sizebytes[2] & 0x7F) << 7) + ((id3_sizebytes[1] & 0x7F) << 14) + ((id3_sizebytes[0] & 0x7F) << 21) + 10
				print("Note: MP3 file {} has ID3v2 tags, size {}".format(mp3_filenames[i], tag_sizes[i]))
			elif id3_data == TAG_PREFIX: #ID3v1
				tag_sizes[i] = 256
				print("Note: MP3 file {} has ID3v1 tags, size {}".format(mp3_filenames[i], tag_sizes[i]))
	
	# count frames in mp3s
	for i in range(mp3_count):
		frame_sizes.append([])
		frame_counts.append(0)
		with open(mp3_filenames[i], "rb") as mp3_file:
			mp3_file.seek(tag_sizes[i])
			reading_mp3 = True
			while reading_mp3:
				frame_header = mp3_file.read(MP3_HEADER_SIZE)
				# stop at the end of each MP3
				if len(frame_header) < MP3_HEADER_SIZE or frame_header[0:3] == TAG_PREFIX:
					reading_mp3 = False
					continue
				frame_size = check_frame_get_size(frame_header, mp3_filenames[i])
				frame_sizes[i].append(frame_size)
				frame_counts[i] += 1
				mp3_file.seek(frame_size - MP3_HEADER_SIZE, 1)
	
	# compute fsb sizes by adding up the frame sizes
	for i in range(mp3_count):
		fsb_sizes.append(0)
		offsets.append(0)
		for f in range(frame_counts[i]):
			frame_size = frame_sizes[i][f]
			fsb_sizes[i] += frame_size
			# all frames must be 0x2 aligned
			if fsb_sizes[i] % 2 != 0:
				fsb_sizes[i] += 1
		# all mp3s must be 0x10 aligned
		offsets[i] = fsb_sizes[i] % 0x10
		if offsets[i] > 0:
			offsets[i] = 0x10 - offsets[i]
			fsb_sizes[i] += offsets[i]
	
	# write fsb
	with open(fsb_outfilename, "wb") as fsb_out:
		write_fsb_header(fsb_out, mp3_count, mp3_filenames, frame_counts, fsb_sizes)

		for i in range(mp3_count):
			with open(mp3_filenames[i], "rb") as mp3_file:
				# skip tag headers
				mp3_file.seek(tag_sizes[i])
				bytes_written = 0
				for f in range(frame_counts[i]):
					frame_size = frame_sizes[i][f]
					fsb_out.write(mp3_file.read(frame_size))
					bytes_written += frame_size
					# all frames must be 0x2 aligned
					if bytes_written % 2 != 0:
						bytes_written += 1
						fsb_out.write(b"\x00")
				# all mp3s must be 0x10 aligned
				fsb_out.write(b"\x00"*offsets[i])
					
	print("Wrote {}".format(fsb_outfilename))

if __name__ == "__main__":
	main()