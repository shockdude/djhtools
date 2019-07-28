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

# DJ Hero IMG Byteswap v0.1
# Swap the bytes of DJH IMG files.
# E.g. convert from PS3 IMG to 360 IMG
# E.g. convert 360 IMG so that the DXT1/DXT5 data is viewable on PC

import sys, os, struct

def main():
	if len(sys.argv) < 2:
		usage()
	
	input_filename = sys.argv[1]
	input_name, input_ext = os.path.splitext(input_filename)
	
	if input_ext.lower() == ".img":
		with open(input_filename, "rb") as input_img, open(input_name + "_endswap" + input_ext, "wb") as output_img:
			output_img.write(input_img.read(20))
			data = input_img.read(2)
			while len(data) == 2:
				short_data = struct.unpack("<H",data)[0]
				output_img.write(struct.pack(">H",short_data))
				data = input_img.read(2)
			return 0

if __name__ == "__main__":
	main()