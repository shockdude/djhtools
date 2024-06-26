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

# DJ Hero Freestyle Sample (FSS) FSB builder v0.3
# Convert sample WAVs/MP3s to FSS FSBs playable in DJ Hero

import os, sys
import struct

OUTPUT_FSB = "FSS.fsb"

FSB_EXTENSION = ".fsb"
MP3_EXTENSION = ".mp3"
WAV_EXTENSION = ".wav"

# references
# http://www.mp3-tech.org/programmer/frame_header.html
# https://hydrogenaud.io/index.php/topic,85125.0.html
# http://www.topherlee.com/software/pcm-tut-wavformat.html

# tagging
TAG_PREFIX = b"TAG"
ID3_PREFIX = b"ID3"
INFO_TAG_SILENCE = (0,0,0,0,0,0,0,0)
INFO_TAG_ID = (1868983881, 1735289176) # Info, Xing in little endian
INFO_TAG_READSIZE = 0x24

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
SAMPLE_RATE_48 = 48000

BITRATE_DEFAULT = 160000

WAV_HEADER_SIZE = 44

fsb_sample_rate = None
fsb_bitrate = None

# fsb format pseudoenum
FORMAT_MP3 = 0
FORMAT_WAV = 1

def write_fsb_header(fsb_outfile, fsb_format, audio_count, audio_filenames, sample_counts, fsb_sizes):
	# credit to vgmstream & fsbext for the fsb documentation
	
	header_size = 0x50
	total_header_size = header_size * audio_count
	sample_data_size = sum(fsb_sizes)
	loop_start = 0
	if fsb_format == FORMAT_MP3:
		header_mode = 0x20
		mode = 0x240
	elif fsb_format == FORMAT_WAV:
		header_mode = 0x28
		mode = 0x150
	num_channels = 2

	fsb_outfile.write(struct.pack("<4sIII", "FSB4".encode("utf-8"), audio_count, total_header_size, sample_data_size))
	fsb_outfile.write(struct.pack("<IIII", 0x40000, header_mode, 0, 0))
	fsb_outfile.write(struct.pack("<IIII", 0, 0, 0, 0))
	for i in range(audio_count):
		stream_size = fsb_sizes[i]
		num_samples = sample_counts[i]
		loop_end = num_samples - 1
		audio_name = os.path.basename(audio_filenames[i]).encode("utf-8")
		fsb_outfile.write(struct.pack("<H30s", header_size, audio_name))
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
				print("Note: Same bitrate as Wii/PS3")
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
			elif fsb_sample_rate == SAMPLE_RATE_PS3 or fsb_sample_rate == SAMPLE_RATE_48:
				print("Warning: may be unstable on Wii")
			else:
				print("Warning: unusual sample rate")
		else:
			print("Error: MP3s do not all have the same sample rate. Got sample rate {}Hz".format(sample_rate))
			usage()
	
	# check padding bit
	padding = ((header_bytes[2] >> 1) & 0x1)
	
	# check if stereo
	channel_mode = ((header_bytes[3] >> 6) & 0x3)
	if channel_mode & 0x10 != 0x00:
		print("Error: failed to parse MP3, not stereo or joint stereo")
		usage()
	
	return int(MPEG_MAGIC * bitrate / sample_rate) + padding
	
def usage():
	print("DJ FSS FSB Usage: {} sample1.mp3 sample2.mp3 sample3.mp3 ... [output.fsb]".format(sys.argv[0]))
	print("Any number of sample MP3s is allowed; however DJ Hero 1 only supports FSBs with 5 samples.")
	print("All MP3s must be 32/44.1/48khz, constant bitrate (preferably 160kbps or higher)")
	print("The default output filename is \"{}\"; specifying a different output filename is optional.".format(OUTPUT_FSB))
	sys.exit(1)

def main():
	global fsb_sample_rate
	if len(sys.argv) < 2:
		usage()
	
	file_args = sys.argv[1:]
	audio_count = 0
	audio_filenames = []
	fsb_outfilename = OUTPUT_FSB
	
	fsb_format = None
	
	for file_arg in file_args:
		file_arg_name, file_arg_ext = os.path.splitext(file_arg)
		if file_arg_ext.lower() == MP3_EXTENSION:
			if fsb_format == None:
				fsb_format = FORMAT_MP3
			elif fsb_format != FORMAT_MP3:
				print("Error: input files are not all the same file format")
				usage()
			audio_count += 1
			audio_filenames.append(file_arg)
		elif file_arg_ext.lower() == WAV_EXTENSION:
			if fsb_format == None:
				fsb_format = FORMAT_WAV
			elif fsb_format != FORMAT_WAV:
				print("Error: input files are not all the same file format")
				usage()
			audio_count += 1
			audio_filenames.append(file_arg)
		elif file_arg_ext.lower() == FSB_EXTENSION:
			if audio_count == 0:
				print("Error: specified output fsb {} but no input audio files".format(file_arg))
				usage()
			else:
				fsb_outfilename = file_arg
				break
		else:
			print("Error: file {} is not an MP3, WAV, or FSB".format(file_arg))
			usage()
	
	if fsb_format == FORMAT_MP3:
		print("Converting {} MP3s to DJH FSS FSB, outputting to {}".format(audio_count, fsb_outfilename))
	elif fsb_format == FORMAT_WAV:
		print("Converting {} WAVs to DJH FSS FSB, outputting to {}".format(audio_count, fsb_outfilename))
	else:
		print("Error: no FSB format identified.")
		usage()
	if audio_count != 5:
		print("Warning: DJH1 requires 5 samples")

	fsb_sizes = []
	offsets = []
	sample_counts = []
	if fsb_format == FORMAT_MP3:
		tag_sizes = []
		frame_sizes = []
		frame_counts = []
		
		# check for tags so that they can be ignored
		for i in range(audio_count):
			tag_sizes.append(0)
			with open(audio_filenames[i], "rb") as mp3_file:
				# check for ID3 tags
				id3_data = mp3_file.read(3)
				if id3_data == ID3_PREFIX: #ID3v2
					mp3_file.read(3)
					id3_sizebytes = struct.unpack(">BBBB",mp3_file.read(4))
					tag_sizes[i] = (id3_sizebytes[3] & 0x7F) + ((id3_sizebytes[2] & 0x7F) << 7) + ((id3_sizebytes[1] & 0x7F) << 14) + ((id3_sizebytes[0] & 0x7F) << 21) + 10
					print("Note: MP3 file {} has ID3v2 tags, size {}".format(audio_filenames[i], tag_sizes[i]))
				elif id3_data == TAG_PREFIX: #ID3v1
					tag_sizes[i] = 256
					print("Note: MP3 file {} has ID3v1 tags, size {}".format(audio_filenames[i], tag_sizes[i]))
				
				# check for the Info tag
				mp3_file.seek(tag_sizes[i])
				frame_header = mp3_file.read(MP3_HEADER_SIZE)
				if len(frame_header) < MP3_HEADER_SIZE or frame_header[0:3] == TAG_PREFIX:
					continue
				frame_size = check_frame_get_size(frame_header, audio_filenames[i])
				mp3_info_tag = mp3_file.read(INFO_TAG_READSIZE)
				if len(mp3_info_tag) != INFO_TAG_READSIZE:
					continue
				mp3_info_data = struct.unpack("IIIIIIIII", mp3_info_tag)
				if mp3_info_data[:8] == INFO_TAG_SILENCE and mp3_info_data[8] in INFO_TAG_ID:
					print("Note: MP3 file {} has Info tag, size {}".format(audio_filenames[i], frame_size))
					tag_sizes[i] += frame_size
		
		# count frames in mp3s
		for i in range(audio_count):
			frame_sizes.append([])
			frame_counts.append(0)
			sample_counts.append(0)
			with open(audio_filenames[i], "rb") as mp3_file:
				mp3_file.seek(tag_sizes[i])
				reading_mp3 = True
				while reading_mp3:
					frame_header = mp3_file.read(MP3_HEADER_SIZE)
					# stop at the end of each MP3
					if len(frame_header) < MP3_HEADER_SIZE or frame_header[0:3] == TAG_PREFIX:
						reading_mp3 = False
						continue
					frame_size = check_frame_get_size(frame_header, audio_filenames[i])
					frame_sizes[i].append(frame_size)
					frame_counts[i] += 1
					sample_counts[i] += SAMPLES_PER_FRAME
					mp3_file.seek(frame_size - MP3_HEADER_SIZE, 1)
		
		# compute fsb sizes by adding up the frame sizes
		for i in range(audio_count):
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
			write_fsb_header(fsb_out, fsb_format, audio_count, audio_filenames, sample_counts, fsb_sizes)

			for i in range(audio_count):
				with open(audio_filenames[i], "rb") as mp3_file:
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
			
	elif fsb_format == FORMAT_WAV:
		RIFF_MAGIC = b"RIFF"
		WAV_MAGIC = b"WAVEfmt "
		DATA_MAGIC = b"data"
		for i in range(audio_count):
			with open(audio_filenames[i], "rb") as wav_file:
				data = struct.unpack("<4sI8s",wav_file.read(16)) # RIFF magic, file size, WAVEFmt magic
				if data[0] != RIFF_MAGIC:
					print("Error: failed to parse WAV, no RIFF header")
					usage()
				if data[2] != WAV_MAGIC:
					print("Error: failed to parse WAV, no WAVEfmt header")
					usage()
				data = struct.unpack("<IHHII",wav_file.read(16)) # format data length, format type, channels, sample rate, unneeded math
				if data[1] != 1:
					print("Error: failed to parse WAV, format type not PCM")
					usage()
				if data[2] != 2:
					print("Error: failed to parse WAV, not stereo")
					usage()
				sample_rate = data[3]
				if sample_rate != fsb_sample_rate:
					if fsb_sample_rate == None:
						fsb_sample_rate = sample_rate
						print("Got sample rate: {}Hz".format(sample_rate))
						if fsb_sample_rate == SAMPLE_RATE_WII:
							print("Ideal sample rate for Wii")
						elif fsb_sample_rate == SAMPLE_RATE_PS3 or fsb_sample_rate == SAMPLE_RATE_48:
							print("Warning: may be unstable on Wii")
						else:
							print("Warning: unusual sample rate")
					else:
						print("Error: WAVs do not all have the same sample rate. Got sample rate {}Hz".format(sample_rate))
						usage()
				data = struct.unpack("<HH",wav_file.read(4)) # unneeded math, bits per sample
				if data[1] != 16:
					print("Error: failed to parse WAV, only 16-bit WAV is supported")
					usage()
				data_bytes = wav_file.read(4)
				chunk_name = struct.unpack("<4s",data_bytes)[0] # data chunk header or some other header
				while len(data_bytes) == 4 and chunk_name != DATA_MAGIC:
					# some other chunk that's not data
					# read its length and then skip it
					chunk_length = struct.unpack("<I",wav_file.read(4))[0] # chunk length
					print("skipping chunk {} with length {}".format(chunk_name.decode("utf-8"), chunk_length))
					wav_file.seek(chunk_length, 1)
					data_bytes = wav_file.read(4)
					if len(data_bytes) == 4:
						chunk_name = struct.unpack("<4s",data_bytes)[0] # maybe this is data chunk header?
					else:
						chunk_name = None
				if chunk_name != DATA_MAGIC:
					print("Error: failed to parse WAV, no data chunk header")
					usage()
				data = struct.unpack("<I",wav_file.read(4)) # payload size
				payload_size = data[0]
				fsb_sizes.append(payload_size)
				sample_counts.append(int(payload_size / 4)) # 2 channels of 16-bit samples
		
		with open(fsb_outfilename, "wb") as fsb_out:
			write_fsb_header(fsb_out, fsb_format, audio_count, audio_filenames, sample_counts, fsb_sizes)

			for i in range(audio_count):
				with open(audio_filenames[i], "rb") as wav_file:
					# skip headers
					wav_file.seek(WAV_HEADER_SIZE)
					for f in range(0, fsb_sizes[i], 2):
						# swap endianness of each 16-bit sample
						byte0 = wav_file.read(1)
						byte1 = wav_file.read(1)
						fsb_out.write(byte1)
						fsb_out.write(byte0)
					
	print("Wrote {}".format(fsb_outfilename))

if __name__ == "__main__":
	main()