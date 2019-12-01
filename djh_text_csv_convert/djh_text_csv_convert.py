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

import csv
import os
import sys
import time

# DJH Text/CSV converter v0.41
        
def error_and_exit(e):
    print(e)
    print("Make a backup of your game files before using any DJ Hero tools.")
    print("Usage: Run script in DJH 1 or 2's Text folder to convert text files to CSV")
    print("Edit CSV files in a text editor (NOT MS Excel)")
    print("Save edited CSV, drag-and-drop CSV onto script to save text files")
    time.sleep(3)
    sys.exit(1)
        
def csv_to_txt(csv_filename):
    folder_name, csv_ext = os.path.splitext(os.path.basename(csv_filename))
    
    # make a folder if it doesn't exist
    if not os.path.isdir(folder_name):
        if os.path.exists(folder_name):
            error_and_exit("Error: {} exists but is not a folder".format(folder_name))
        os.mkdir(folder_name)
    
    # read the CSV and write to text files
    print("Writing text files to folder {}".format(folder_name))
    with open(csv_filename, "r", encoding="utf_8_sig", newline="") as text_csvfile:
        text_csv = csv.reader(text_csvfile, dialect="excel")
        os.chdir(folder_name)
        text_files = []
        num_files = -1
        id_index = -1
        for row in text_csv:
            if num_files < 0:
                num_files = len(row)
                if num_files < 2: # need 1 ID file and at least 1 string file
                    error_and_exit("Error: corrupt CSV/Text files; need at least 2 columns")
                for i in range(num_files):
                    text_filename = row[i] + ".txt"
                    if row[i] == folder_name + "ID":
                        id_index = i # string ID file
                        text_files.append(open(text_filename, "w", encoding="utf-8", newline="\r\n"))
                    elif row[i].find(folder_name) == 0: # string file
                        text_files.append(open(text_filename, "wb"))
                    else:
                        error_and_exit("Error: corrupt CSV/Text files; invalid header filename {}".format(row[i]))
                if id_index < 0:
                    error_and_exit("Error: corrupt CSV/Text files; missing {}ID in header row".format(folder_name))
            elif len(row) > 0: # ignore blank lines
                if row[0][0:2] == "//": # ignore commented lines
                    continue

                i = id_index
                text_files[i].write(row[i] + "\n")
                # use string id as text string if no other text string is provided
                string_bin = row[i].encode("utf-8") + b"\x00"
                
                for i in range(num_files):
                    if i == id_index:
                        continue
                    elif i < len(row):
                        string_bin = row[i].encode("utf-8") + b"\x00"
                        text_files[i].write(string_bin)
                    else: # copy the last string in the row to all remaining columns
                        text_files[i].write(string_bin)
                        
        for file in text_files:
            file.close()
        os.chdir("..")
    print("Text files written to folder {}".format(folder_name))
    time.sleep(3)

def txt_to_csv():
    # check if current directory is valid
    if os.path.basename(os.getcwd()).lower() != "text":
        error_and_exit("Error: script must be run in a DJ Hero \"Text\" folder")

    # find all folders
    for text_folder in os.listdir("."):
        if os.path.isdir(text_folder):
            print("Found folder {}".format(text_folder))
            
            text_id_arr = []
            text_value_arr = []
            text_value_lengths = []
            text_value_filenames = []
            
            id_found = False
            
            # get all text files in folder
            os.chdir(text_folder)
            for text_file in os.listdir("."):
                text_name, text_ext = os.path.splitext(os.path.basename(text_file))
                if text_ext.lower() != ".txt":
                    print("Warning: {} is not a .txt file".format(text_file))
                    continue
                if text_name.find(text_folder) != 0:
                    print("Warning: text file {} does not start with folder name {}".format(text_file, text_folder))
                    continue
                if text_name == text_folder + "ID":
                    # ID text file is a special case
                    print("\tFound ID txt file {}".format(text_file))
                    id_found = True
                    with open(text_file, "r", encoding="utf-8") as id_file:
                        text_id_arr = id_file.read().split("\n")
                else:
                    print("\tFound txt file {}".format(text_file))
                    text_value_filenames.append(text_name)
                    with open(text_file, "rb") as value_file:
                        text_value_arr.append(value_file.read().split(b"\x00"))
                        text_value_lengths.append(len(text_value_arr[-1]))
            os.chdir("..")
            
            if not id_found:
                print("No {}ID.txt found, skipping".format(text_folder))
                continue
                
            # write CSV for folder
            csv_filename = "{}.csv".format(text_folder)
            if os.path.exists(csv_filename):
                print("Warning, {} already exists, skipping".format(csv_filename))
                continue
                
            with open(csv_filename, "w", encoding="utf_8_sig", newline="") as text_csvfile:
                text_csv = csv.writer(text_csvfile, dialect="excel")
                text_csv.writerow([text_folder + "ID"] + text_value_filenames)
                num_rows = len(text_id_arr) - 1 # don't count the last \n
                num_cols = len(text_value_arr)
                for i in range(num_rows):
                    row = [text_id_arr[i]]
                    for j in range(num_cols):
                        if i < text_value_lengths[j]:
                            row.append(text_value_arr[j][i].decode("utf-8"))
                        else:
                            row.append(" ")
                    text_csv.writerow(row)
            
            print("Wrote CSV file {}".format(csv_filename))
    print("Done converting Text folders to CSV")
    time.sleep(3)

def main():
    print("DJ Hero Text/CSV converter")
    
    if len(sys.argv) == 1:
        txt_to_csv()
    else:
        for arg in sys.argv[1:]:
            csv_to_txt(arg)

if __name__ == "__main__":
    main()