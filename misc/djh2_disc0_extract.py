# DJ Hero 2 IMG Extractor
# Original code from ArchiveExplorer by maxton
# https://github.com/maxton/GameArchives/
# Ported to Python by shockdude

import os, sys
import struct
import time

IMG_EXT = ".img"
PART0_EXT = ".part0"
PART1_EXT = ".part1"

def usage():
	filename = os.path.basename(sys.argv[0])
	print(filename)
	print("Usage: {} [DISC0.IMG or DISC0.IMG.part0]".format(filename))
	print("Or drag-and-drop DISC0.IMG or DISC0.IMG.part0 onto {}".format(filename))
	time.sleep(3)
	sys.exit(1)

class FSGFileDescriptor:
	def __init__(self):
		self.filename_hash = 0
		self.type = 0
		self.offset = 0
		self.data_offset = 0
		self.size = 0

class ImgFile:
	def __init__(self, img_file_0, img_file_1):
		self.img_filename = img_file_0
		self.img_0 = None
		self.img_1 = None
		self.img_0_size = 0
		self.img_1_size = 0
		self.seekpos = 0
	
		self.img_0 = open(img_file_0, "rb")
		self.img_0.seek(0,2)
		self.img_0_size = self.img_0.tell()
		self.img_0.seek(0)
		if img_file_1 != None:
			self.img_1 = open(img_file_1, "rb")
			self.img_1.seek(0,2)
			self.img_1_size = self.img_1.tell()
			self.img_1.seek(0)
		
	def read(self, count):
		self.seekpos += count
		if self.seekpos - count < self.img_0_size:
			if self.img_1 != None and self.seekpos >= self.img_0_size:
				data = self.img_0.read()
				self.img_1.seek(0)
				data += self.img_1.read(self.seekpos - self.img_0_size)
				return data
			else:
				return self.img_0.read(count)
		else:
			return self.img_1.read(count)
			
	def read_string(self):
		data = self.read(1)
		bytestring = b''
		while data != b'\x00':
			bytestring += data
			data = self.read(1)
		return bytestring.decode("utf-8")
			
	def seek(self, pos):
		self.seekpos = pos
		if pos >= self.img_0_size:
			self.img_1.seek(pos - self.img_0_size)
		else:
			self.img_0.seek(pos)
			
	def dump_files(self):
		MAGIC_STR = b'FSG-FILE-SYSTEM\x00'
		MAGIC_STR_LEN = 16
		try:
			magic = self.read(MAGIC_STR_LEN)
			if magic != MAGIC_STR:
				raise Exception
		except:
			print("Error: {} is not a valid DJH2 IMG file".format(self.img_filename))
			usage()
			
		self.read(4) # unknown, == 2
		self.read(4) # header_length
		self.read(4) # num_sectors
		
		# points to a list of all (used) sectors?
		# starting at 0x180 and increasing by 0x80 up to (num_sectors + 3) << 17
		self.read(4) # sector_map_offset
		base_offset = struct.unpack(">I", self.read(4))[0]
		self.read(4) # unknown, read buffer size?
		self.read(4) # unknown, == 8
		num_files = struct.unpack(">I", self.read(4))[0]
		self.read(4) # zero
		self.read(4) # checksum
		nodes = {}
		
		for i in range(num_files):
			node = FSGFileDescriptor()
			node.filename_hash = struct.unpack(">I", self.read(4))[0]
			node.type = struct.unpack("B", self.read(1))[0]
			node.offset = struct.unpack(">I",  b'\x00' + self.read(3))[0]
			nodes[node.filename_hash] = node
		for node in nodes.values():
			self.seek(node.offset)
			offset = struct.unpack(">I", self.read(4))[0]
			node.data_offset = (offset << 10) + base_offset
			node.size = struct.unpack(">I", self.read(4))[0]
		self.recursively_get_files(None, "/", base_offset, "", nodes)
	
	def hash(self, str):
		if str[0] == "/":
			str = str[1:]
		str = str.upper()
		hash = 2166136261
		for i in range(len(str)):
			hash = (1677619 * hash) & 0xFFFFFFFF
			hash ^= ord(str[i])
		return hash
	
	def recursively_get_files(self, parent, name, base_offset, path_acc, nodes):
		self.seek(base_offset)
		filename = ""
		
		filename = self.read_string()
		while (filename != ""):
			pos = self.seekpos
			real_name = filename[1:]
			if path_acc == "":
				next_path = real_name
			else:
				next_path = "{}/{}".format(path_acc, real_name)
			desc = nodes[self.hash(next_path)]
			if filename[0] == "D":
				if os.path.exists(real_name):
					if not os.path.isdir(real_name):
						print("Error: {} exists and is not a folder".format(real_name))
						usage()
				else:
					os.mkdir(real_name)
				os.chdir(real_name)
				self.recursively_get_files(None, real_name, desc.data_offset, next_path, nodes)
				os.chdir("..")
				self.seek(pos)
			elif filename[0] == "F":
				if os.path.exists(real_name):
					if not os.path.isfile(real_name):
						print("Error: {} exists and is not a file".format(real_name))
						usage()
				self.seek(desc.data_offset)
				with open(real_name, "wb") as outfile:
					outfile.write(self.read(desc.size))
				self.seek(pos)
			else:
				print("Error: invalid filename prefix for {}".format(filename))
				usage()
				
			filename = self.read_string()
		
	def close(self):
		if self.img_0 != None:
			self.img_0.close()
		if self.img_1 != None:
			self.img_1.close()

def main():
	if len(sys.argv) < 2:
		print("Error: not enough arguments")
		usage()
	
	img_file_0 = sys.argv[1]
	img_file_1 = None
	
	img_filename, img_fileext = os.path.splitext(img_file_0)
	if img_fileext.lower() == PART0_EXT:
		img_file_1 = img_filename + PART1_EXT
	elif img_fileext.lower() != IMG_EXT:
		print("Error: {} is not an IMG file".format(img_file_0))
		usage()
	
	print("Opening {}...".format(img_file_0))
	img = ImgFile(img_file_0, img_file_1)
	print("Extracting files...")
	img.dump_files()
	img.close()
	print("Done")

if __name__ == "__main__":
	main()