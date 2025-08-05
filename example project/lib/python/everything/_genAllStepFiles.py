
import requests
import sys
import os

#
#     Hello!
#
#
# Replace this with the sheet ID found in the URL of your google drive sheet link:
# https://docs.google.com/spreadsheets/d/{THIS PART HERE}/edit?gid=0#gid=0 

sheetID = "1VDwPe9hKSHXVEZSls5vFoe_vihTM-lGpmwxSjNe8wNI"

#
# Additionally, make sure the sheet is set to at least anyone with the link can view
#
# Thanks!

url = f'https://docs.google.com/spreadsheets/d/{sheetID}/gviz/tq?tqx=out:csv&sheet=0'
print("requesting google sheet")
try:
    resp = requests.get(url)
    resp.raise_for_status()  # will raise HTTPError on bad status
except requests.exceptions.HTTPError as e:
    print("Error: could not download the Google Sheet.")
    print("  • Please check that your sheet ID is correct.")
    print("  • Make sure the Google Sheet’s sharing is set to 'Anyone with the link can VIEW.'")
    print(f"(HTTP {resp.status_code} – {e})")
    sys.exit(1)
except requests.exceptions.RequestException as e:
    # catch other requests-related errors (network, DNS, etc.)
    print("Error: failed to download the Google Sheet due to a network issue:")
    print(f"  {e}")
    sys.exit(1)

input_file = 'data.csv'
if os.path.exists(input_file):
    print("moving old sheet to z_old_data.csv")
    os.replace(input_file, 'z_old_data.csv')

with open('data.csv', 'wb') as f:
    f.write(resp.content)

print("new google sheet downloaded as data.csv")

# Continue using the same output filename
tmp_prefix = "tmp-"
live_prefix = "../../"
granulator_file = "granulator-steps.txt"
sample_file = "sample-steps.txt"
reverb_file = "reverb-steps.txt"
sequencer_file = "step-sequencer-info.txt"
manual_file = "step-is-manual.txt"

def timestamp_to_milliseconds(timestamp):
    """
    Converts a timestamp in the format MM:SS.MMM or M:SS.MMM into total milliseconds.
    
    Args:
        timestamp (str): The timestamp string (e.g., "10:29.824").
    
    Returns:
        int: Total milliseconds.
    """
    try:
        # Split the timestamp into minutes, seconds, and milliseconds
        minutes, rest = timestamp.strip('"').split(":")
        seconds, milliseconds = rest.split(".")
        
        # Convert each component to integers
        minutes = int(minutes)
        seconds = int(seconds)
        milliseconds = int(milliseconds)
        
        # Calculate total milliseconds
        total_milliseconds = (minutes * 60 * 1000) + (seconds * 1000) + milliseconds
        return total_milliseconds
    except ValueError:
        # Return None if the timestamp is invalid
        return None

# Open and read the input file as a string
with open(input_file, 'r') as f:
    data = f.read()

# Split the string into rows
lines = data.splitlines()
output_lines = []

# Parse the lines into a list of steps and values
rows = []
first_real_row = 9999999999999
for idx, line in enumerate(lines):
    # Split the line into columns using ,s
    columns = line.split(',')
    if("Cue Information" in line):
        first_real_row = idx+2
    
    # Ensure the row has enough columns and try conv"erting to integers
    try:
        auto_manual = columns[1].strip('"')
        step = columns[2].strip('"')
        millis = timestamp_to_milliseconds(columns[3].strip('"'))
        reset = columns[5].strip('"')
        play_stop = columns[7].strip('"')
        filename = columns[8].strip('"')
        fadetime = columns[9].strip('"')
        granulator_onoff = columns[10].strip('"')
        granulator_channel = columns[11].strip('"')
        granulator_fadetime = columns[12].strip('"')
        reverb_onoff = columns[13].strip('"')
        reverb_channel = columns[14].strip('"')
        reverb_fadetime = columns[15].strip('"')
        if(idx >= first_real_row):
            record = {
                "auto_manual": auto_manual,
                "step": step,
                "millis": millis,
                "reset": reset,
                "play_stop": play_stop,
                "filename": filename,
                "fadetime": fadetime,
                "granulator_onoff": granulator_onoff,
                "granulator_channel": granulator_channel,
                "granulator_fadetime": granulator_fadetime,
                "reverb_onoff": reverb_onoff,
                "reverb_channel": reverb_channel,
                "reverb_fadetime": reverb_fadetime,
            }
            rows.append(record)
    except (IndexError, ValueError):
        print("here?")
        print("error!!!!")
        print(IndexError)
        # Skip rows that don't have enough data or have invalid integers
        continue
    
# =================== do the steps-is-manual =====================
    
output_lines = []
for row in rows:
    if(row['auto_manual'] == 'manual'):
        output_lines.append(""+row['step'].strip('"')+", "+str(1)+";")

with open(tmp_prefix+manual_file, 'w') as f:
    print("outputting "+str(len(output_lines))+" lines to "+ f.name)
    f.write("\n".join(output_lines))

# =================== do the sample-steps.txt =====================

output_lines = []
last_real_cue = -1
samples_instructions = ""
for idx, row in enumerate(rows):
    if(row['step']!=''):
        if(last_real_cue!=-1 and len(samples_instructions)>1):
            output_lines.append(str(last_real_cue)+","+samples_instructions+";")
        last_real_cue = row['step'].strip('"')
        samples_instructions = ""
    play = row['play_stop']
    if((play == "play") or (play == "stop")):
        try:
            play_stop = 0
            if(play == "play"):
                play_stop = 1
            sample = row['filename']
            fadetime = int(row['fadetime'])
            samples_instructions += " "+str(sample)+" "+str(play_stop)+" "+str(fadetime)
        except Exception as e:
            print("issue reading fade time! Is it a number? problem with line: \n"+str(row))
            print(e)
if(last_real_cue!=-1 and len(samples_instructions)>1):
    output_lines.append(str(last_real_cue)+","+samples_instructions+";")

with open(tmp_prefix+sample_file, 'w') as f:
    print("outputting "+str(len(output_lines))+" lines to "+ f.name)
    f.write("\n".join(output_lines))



# =================== do the granulator-steps.txt =====================

output_lines = []
last_real_cue = -1
granulator_instructions = ""
for idx, row in enumerate(rows):
    if(row['step']!=''):
        if(last_real_cue!=-1 and len(granulator_instructions)>1):
            output_lines.append(str(last_real_cue)+","+granulator_instructions+";")
        last_real_cue = row['step'].strip('"')
        granulator_instructions = ""
    granonoff = row['granulator_onoff']
    if((granonoff == "on") or (granonoff == "off")):
        try:
            onoff = 0
            if(granonoff == "on"):
                onoff = 1
            channel = row['granulator_channel']
            fadetime = int(row['granulator_fadetime'])
            granulator_instructions += " "+str(channel)+" "+str(onoff)+" "+str(fadetime)
        except Exception as e:
            print("issue reading fade time! Is it a number? problem with line: \n"+str(row))
            print(e)
if(last_real_cue!=-1 and len(granulator_instructions)>1):
    output_lines.append(str(last_real_cue)+","+granulator_instructions+";")

with open(tmp_prefix+granulator_file, 'w') as f:
    print("outputting "+str(len(output_lines))+" lines to "+ f.name)
    f.write("\n".join(output_lines))



# =================== do the reverb-steps.txt =====================

output_lines = []
last_real_cue = -1
reverb_instructions = ""
for idx, row in enumerate(rows):
    if(row['step']!=''):
        if(last_real_cue!=-1 and len(reverb_instructions)>1):
            output_lines.append(str(last_real_cue)+","+reverb_instructions+";")
        last_real_cue = row['step'].strip('"')
        reverb_instructions = ""
    play = row['reverb_onoff']
    if((play == "on") or (play == "off")):
        try:
            onoff = 0
            if(play == "on"):
                onoff = 1
            channel = row['reverb_channel']
            fadetime = int(row['reverb_fadetime'])
            reverb_instructions += " "+str(channel)+" "+str(onoff)+" "+str(fadetime)
        except Exception as e:
            print("issue reading fade time! Is it a number? problem with line: \n"+str(row))
            print(e)
if(last_real_cue!=-1 and len(reverb_instructions)>1):
    output_lines.append(str(last_real_cue)+","+reverb_instructions+";")

with open(tmp_prefix+reverb_file, 'w') as f: 
    print("outputting "+str(len(output_lines))+" lines to "+ f.name)
    f.write("\n".join(output_lines))


# =================== do the step-sequencer-info.txt =====================

output_lines = []
for idx, row in enumerate(rows):
    if(row['step']!='' and row['auto_manual']!='manual'):
        resetbit = ""
        if(row['reset']=='yes'):
            resetbit = " reset"
        lineToPrint = ""+str(row['step'])+", "+str(row['millis']) +resetbit+";"
        output_lines.append(lineToPrint)


with open(tmp_prefix+sequencer_file, 'w') as f: 
    print("outputting "+str(len(output_lines))+" lines to "+ f.name)
    f.write("\n".join(output_lines))






# =================== print the output to the user for them to confirm =====================
import shutil
from datetime import datetime

def count_lines(filename):
    if not os.path.exists(filename):
        return 0
    with open(filename, 'r') as f:
        return sum(1 for _ in f)

def compare_files(file1, file2):
    if not os.path.exists(file1) or not os.path.exists(file2):
        return None
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()
        if lines1 == lines2:
            return 0
        diffs = sum(1 for a, b in zip(lines1, lines2) if a != b)
        diffs += abs(len(lines1) - len(lines2))
        return diffs

# Files to report on
output_files = [
    (tmp_prefix + manual_file, live_prefix + manual_file),
    (tmp_prefix + sample_file, live_prefix + sample_file),
    (tmp_prefix + granulator_file, live_prefix + granulator_file),
    (tmp_prefix + reverb_file, live_prefix + reverb_file),
    (tmp_prefix + sequencer_file, live_prefix + sequencer_file),
]

# Get max filename width for alignment
max_name_len = max(len(outfile) for _, outfile in output_files)

# Display changes
print("\n======== File Line Changes ========")
for tmp_file, outfile in output_files:
    old_count = count_lines(outfile)
    new_count = count_lines(tmp_file)
    name_field = outfile.ljust(max_name_len)
    count_field = f"{str(old_count).rjust(4)} -> {str(new_count).ljust(4)}"
    
    change_note = ""
    if old_count == new_count:
        diff_count = compare_files(tmp_file, outfile)
        if diff_count == 0:
            change_note = "(no change)"
        elif diff_count is not None:
            change_note = f"({diff_count} changes)"

    print(f"{name_field} : {count_field}  {change_note}")

# Confirm overwrite
answer = input("\nConfirm overwriting old files? y/n: ").strip().lower()
if answer != 'y':
    print("Aborting. No files overwritten.")
    sys.exit(0)

# Make archive folder
timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
archive_dir = os.path.join("z_old", timestamp)
os.makedirs(archive_dir, exist_ok=True)

# Archive and overwrite
for tmp_file, outfile in output_files:
    if os.path.exists(outfile):
        archived_path = os.path.join(archive_dir, os.path.basename(outfile))
        shutil.copy(outfile, archived_path)
        print(f"Archived: {outfile} -> {archived_path}")
    os.replace(tmp_file, outfile)
    print(f"Updated:  {outfile}")

try:
    os.replace('z_old_data.csv', archive_dir+"/"+'data.csv')
except:
    pass


print("\n✅ All files updated and old versions archived.")
