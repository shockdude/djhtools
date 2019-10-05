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

# DJ Hero 2 Savefile Converter v0.1
# Convert DJH2 savefile data from one console to another console.

import os, sys
import struct
import binascii

DAT_EXTENSION = ".dat"

def usage():
    print("Usage: {} [input_savefile] [target_savefile]".format(sys.argv[0]))
    print("Converts DJ Hero 2 DAT savefiles from one console to another console")
    print("Experimental, conversion may not be perfect")
    sys.exit(1)

def main():
    if len(sys.argv) < 3:
        usage()
    
    input_filename = sys.argv[1]
    input_name, input_ext = os.path.splitext(input_filename)
    target_filename = sys.argv[2]
    target_name, target_ext = os.path.splitext(target_filename)
    
    if input_ext.lower() != DAT_EXTENSION:
        print("Error: input file {} does not have extension {}".format(input_filename, DAT_EXTENSION))
        usage()
    if target_ext.lower() != DAT_EXTENSION:
        print("Error: target file {} does not have extension {}".format(target_filename, DAT_EXTENSION))
        usage()
        
    output_filename = target_name + "_converted" + target_ext
    
    header = b"DJ20"
    savedata_len = 0x12DC0
    
    with open(input_filename, "rb") as input_file:
        with open(target_filename, "rb") as target_file:
            if input_file.read(4) != header:
                print("Error: input file {} is not a valid DJH2 savefile".format(input_filename))
                usage()
            if target_file.read(4) != header:
                print("Error: target file {} is not a valid DJH2 savefile".format(target_filename))
                usage()

            input_file.seek(0x10)
            target_file.seek(0)
            with open(output_filename, "wb") as output_file:
                output_file.write(target_file.read(0x10))
                output_file.write(input_file.read(savedata_len))
                target_file.seek(savedata_len, 1)
                output_file.write(target_file.read())                
    
if __name__ == "__main__":
    main()