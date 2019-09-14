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

# DJ Hero BeatsMe Converter v0.1
# Convert BeatsMe .track charts to DJH2 xmk
# BeatsMe by port and Evar678: https://atomic-software.github.io/dj/
# Credit to pikminguts92 from ScoreHero for documenting the FSGMUB format
# https://www.scorehero.com/forum/viewtopic.php?p=1827382#1827382

"""
Header
Entries[]
StringBlob

HEADER (16 bytes)
=================
INT32 - Version (1 or 2)
INT32 - Hash
INT32 - Count of entries
INT32 - Size of string blob

ENTRY (16 bytes)
================
FLOAT - Start (0-index)
INT32 - Pitch / Identifier
FLOAT - Length
INT32 - Text Pointer (Usually 0)
    Pointer to text value in blob, starting from first entry 
"""

import os, sys
import struct
import binascii
from collections import deque
import re

FSGMUB_EXTENSION = ".fsgmub"
XMK_EXTENSION = ".xmk"
BEATSME_EXTENSION = ".track"

HEADER_SIZE = 16
ENTRY_SIZE = 16
ALIGN_SIZE = 32

DJH1_MAX_NOTELEN = 1.0/16
DJH1_MIN_NOTELEN = 1.0/32

TO_SPIKE = {9:28, 10:29, 11:27}

def usage():
    print("Usage: {} [inputfile]".format(sys.argv[0]))
    print("Basic conversion from BeatsMe .track to DJH2 XMK")
    print("Get BeatsMe from: https://atomic-software.github.io/dj/")
    sys.exit(1)

def note_sortkey(x):
    return x[0]

def check_spike(crossfades):
    # higher index = older
    # assumption: cf[2] may or may not spike, cf[1] and cf[0] are not spikes
    # check if cf[1] is a spike
    if crossfades[0][1] == crossfades[1][1] or crossfades[1][1] == crossfades[2][1]:
        print("Error: overlapping crossfades")
        for fade in crossfades:
            print(fade[0], fade[1], fade[2])
        return False
    if crossfades[1][2] <= DJH1_MAX_NOTELEN:
        # anything can go to an edgespike except for a centerspike
        if crossfades[2][1] != 29 and crossfades[1][1] in (9, 11):
            return True
        # centerspike
        if crossfades[2][1] == crossfades[0][1]:
            return True
    return False

def main():
    if len(sys.argv) < 2:
        usage()
    
    input_filename = sys.argv[1]
    input_name, input_ext = os.path.splitext(input_filename)
    
    if input_ext.lower() == BEATSME_EXTENSION:
        print("Converting beatsme .track to djh fsgmub")
    else:
        print("Error: input file {} does not have extension {} or {}".format(input_filename, FSGMUB_EXTENSION, CSV_EXTENSION))
        usage()

    notes_dict = {}
    bpm = 0
    notes_index = 0
    lanes_index = 0

    # trash string parser
    note_re = re.compile('^_\[(\d+)\]\s*=\s*{(.*)}$')
    index_re = re.compile('^_\[(\d+)\]$')
    metadata_re = re.compile('^return\s+{(.*)}$')
    metabpm_re = re.compile('^bpm\s*=\s*(.+)\s*$')
    metanotes_re = re.compile('^notes\s*=\s*_\[(.+)\]\s*$')
    metalanes_re = re.compile('^lanes\s*=\s*_\[(.+)\]\s*$')
    with open(input_filename, "r") as input_file:
        for line in input_file:
            line = line.strip()
            m = note_re.match(line)
            if m:
                # print(m.group(1), m.group(2))
                note_i = int(m.group(1))
                if '"' not in line:
                    notes_dict[note_i] = []
                    note_data = m.group(2).split(",")
                    for n in note_data:
                        n = n.strip()
                        table_m = index_re.match(n)
                        if table_m:
                            table_i = int(table_m.group(1))
                            if table_i in notes_dict:
                                notes_dict[note_i].append(table_i)
                        else:
                            try:
                                notes_dict[note_i].append(float(n))
                            except ValueError:
                                pass
            else:
                m = metadata_re.match(line)
                if m:
                    metadata_raw = m.group(1).strip()
                    print(metadata_raw)
                    # naive split on comma
                    metadata = metadata_raw.split(",")
                    for mdata in metadata:
                        mdata = mdata.strip()
                        meta_m = metabpm_re.match(mdata)
                        if meta_m:
                            bpm = float(meta_m.group(1))
                        else:
                            meta_m = metanotes_re.match(mdata)
                            if meta_m:
                                notes_index = int(meta_m.group(1))
                            else:
                                meta_m = metalanes_re.match(mdata)
                                if meta_m:
                                    lanes_index = int(meta_m.group(1))

    # 0XFFFFFFFF note
    note_array = [[0, 0xFFFFFFFF, 0, 0]]
    
    max_note_pos = 0
    for note_i in notes_dict[notes_index]:
        note = notes_dict[note_i]
        note_pos = note[0] / 4
        max_note_pos = max(max_note_pos, note_pos)
        note_lane = note[1]
        note_len = DJH1_MIN_NOTELEN
        if len(note) > 2:
            note_len = note[2] / 4
            if note_len < DJH1_MIN_NOTELEN:
                note_len = DJH1_MIN_NOTELEN
        note_arr = [note_pos, 0, note_len, 0]
        if note_lane < 3:
            note_arr[1] = 0
        elif note_lane > 3:
            note_arr[1] = 1
        else:
            note_arr[1] = 2
        note_array.append(note_arr)

    cf_queue = deque()

    note_prev = [0, 10, 0, 0]
    note_count = len(note_array)
    for note_i in notes_dict[lanes_index]:
        note = notes_dict[note_i]
        note_pos = note[0] / 4
        max_note_pos = max(max_note_pos, note_pos)
        note_lane = note[1]
        note_arr = [note_pos, 0, 0, 0]
        if note_lane < 0:
            note_arr[1] = 11
        elif note_lane > 0:
            note_arr[1] = 9
        else:
            note_arr[1] = 10
        note_prev[2] = note_arr[0] - note_prev[0]
        note_array.append(note_prev)
        cf_queue.appendleft(note_count)
        if len(cf_queue) == 3:
            if check_spike([note_array[x] for x in cf_queue]):
                note_array[cf_queue[1]][1] = TO_SPIKE[note_array[cf_queue[1]][1]]
            cf_queue.pop()
        note_count += 1
        note_prev = note_arr
    note_prev[2] = max_note_pos + 1 - note_prev[0]
    note_array.append(note_prev)
    if note_prev[1] != 10:
        note_array.append([max_note_pos + 1, 10, 1, 0])
            
    # BPM notes
    output_array = []
    output_array.append(struct.pack(">IIII", 0, 0x0B000001, 0, int(60000000.0 / bpm)))
    output_array.append(struct.pack(">IIIf", 0, 0x0B000002, 0, bpm))

    fsgmub_length = len(note_array)
    for i in range(fsgmub_length):
        output_array.append(struct.pack(">fIfI", note_array[i][0], note_array[i][1], note_array[i][2], note_array[i][3]))
    # add 2 bpm notes
    fsgmub_length += 2
    
    output_ext = XMK_EXTENSION
    output_filename = input_name + output_ext
    string_length = 0

    with open(output_filename, "wb") as output_file:
        # compute crc
        # chart length, string blob size (0), chart lines
        size_bin = struct.pack(">II", fsgmub_length, string_length)
        crc = binascii.crc32(size_bin)
        for line in output_array:
            # note position, note type, note length, text pointer
            crc = binascii.crc32(line, crc)
        if string_length > 0:
            crc = binascii.crc32(fsgmub_strings, crc)
        
        # fsgmub header
        # version (2), crc, chart length, string blob size
        output_file.write(struct.pack(">II", 2, crc))
        output_file.write(size_bin)
        
        print("Output chart: {}".format(output_filename))
        print("Version: {}".format(2))
        print("Hash: {:x}".format(crc))
        print("Length: {}".format(fsgmub_length))
        print("String data length: {}".format(string_length))
        
        for line in output_array:
            # note position, note type, note length, text pointer
            output_file.write(line)
                                        
        if string_length > 0:
            output_file.write(fsgmub_strings)
        
        # ensure the chart filesize is a multiple of 32 for some reason
        file_size = HEADER_SIZE + fsgmub_length*ENTRY_SIZE + string_length
        size_offset = file_size % ALIGN_SIZE
        if size_offset != 0:
            output_file.write(b"\x00"*(ALIGN_SIZE - size_offset))

if __name__ == "__main__":
    main()