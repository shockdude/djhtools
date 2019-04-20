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

# DJ Hero FSB builder v0.4
# Convert MP3s to FSBs playable in DJ Hero Wii

import os, sys
import struct

# mp3 frame size for 160kbps 32khz joint stereo
FRAME_SIZE = 720
FRAME_FFFA = bytearray.fromhex("FFFA")
FRAME_FFFB = bytearray.fromhex("FFFB")
OUTPUT_FSB = "output.fsb"
MP3_COUNT = 3

def write_fsb_header(fsb_outfile, fsb_inputfilename, mp3_size):
	# credit to vgmstream & fsbext for the fsb documentation
	
	num_samples = int(mp3_size * 1.6)
	loop_start = 0
	loop_end = num_samples - 1
	stream_size = mp3_size * 3
	sample_data_size = stream_size + 1440

	# copy FSB header from input fsb file
	with open(fsb_inputfilename, "rb") as fsb_inputfile:
		fsb_outfile.write(fsb_inputfile.read(12))
		fsb_inputfile.read(4)
		fsb_outfile.write(struct.pack("<I", sample_data_size))
		fsb_outfile.write(fsb_inputfile.read(64))
		fsb_inputfile.read(16)
		fsb_outfile.write(struct.pack("<IIII", num_samples, stream_size, loop_start, loop_end))
		fsb_outfile.write(fsb_inputfile.read(32))

def usage():
	print("Usage: {} input.fsb green_track.mp3 blue_track.mp3 red_track.mp3 [output.fsb]".format(sys.argv[0]))
	print("An input FSB from DJ Hero Wii is required for copying the FSB header data")
	print("All mp3s must be 160kbps, 32khz, Joint Stereo")
	print("The default output filename is \"output.fsb\"; specifying a different output filename is optional")
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
	mp3_sizes = []

	for mp3_filename in mp3_filenames:
		if not os.path.isfile(mp3_filename):
			print("Error: could not find input MP3 file {}".format(mp3_filename))
			usage()
		mp3_sizes.append(os.path.getsize(mp3_filename))
	
	# check for ID3 tags so that they can be ignored
	id3_sizes = [0, 0, 0]
	with open(mp3_filenames[0], "rb") as mp3_files[0], open(mp3_filenames[1], "rb") as mp3_files[1], open(mp3_filenames[2], "rb") as mp3_files[2]:
		for i in range(MP3_COUNT):
			id3_data = mp3_files[i].read(3)
			if id3_data == b'ID3':
				print("Note: MP3 file {} has ID3 tags, this may cause warnings.".format(mp3_filenames[i]))
				mp3_files[i].read(3)
				id3_sizebytes = struct.unpack(">BBBB",mp3_files[i].read(4))
				id3_sizes[i] = (id3_sizebytes[3] & 0x7F) + ((id3_sizebytes[2] & 0x7F) << 7) + ((id3_sizebytes[1] & 0x7F) << 14) + ((id3_sizebytes[0] & 0x7F) << 21) + 10
				mp3_sizes[i] -= id3_sizes[i]
	
	# all MP3s should be the same size
	mp3_size = min(mp3_sizes)
	if mp3_sizes[0] != mp3_sizes[1] or mp3_sizes[1] != mp3_sizes[2]:
		print("Warning: mp3s are not all the same size!")
		print("Sizes: {}".format(mp3_sizes))
		print("Using the size of the smallest mp3: {}".format(mp3_size))
	
	if mp3_size % FRAME_SIZE != 0:
		print("Warning: mp3 size is not a multiple of expected frame size (720)")
	num_frames = int(mp3_size / FRAME_SIZE)
	
	with open(fsb_outfilename, "wb") as fsb_out:
		write_fsb_header(fsb_out, fsb_inputfilename, mp3_size)
			
		with open(mp3_filenames[0], "rb") as mp3_files[0], open(mp3_filenames[1], "rb") as mp3_files[1], open(mp3_filenames[2], "rb") as mp3_files[2]:	
			for i in range(MP3_COUNT):
				mp3_files[i].read(id3_sizes[i])
			for i in range(num_frames):
				# interleave every mp3 frame
				for i in range(MP3_COUNT):
					read_data = mp3_files[i].read(FRAME_SIZE)
					if read_data[0:2] != FRAME_FFFA and read_data[0:2] != FRAME_FFFB:
						print("Error: unexpected MP3 frame header in {}; MP3 is not in the expected format.".format(mp3_filenames[i]))
						usage()
					fsb_out.write(read_data)

if __name__ == "__main__":
	main()