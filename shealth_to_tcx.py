import pandas as pd
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime
import glob

def convert_time(timestamp):
    """Convert timestamp to ISO 8601 time format"""
    dt = datetime.fromtimestamp(timestamp / 1000)
    return dt.isoformat()

def process_file(file):
    """Process a JSON file and return activity data"""
    with open(file, "r") as f:
        data = json.load(f)
    
    trackpoints = []
    for point in data:
        if "heart_rate" in point:
            trackpoints.append({
                "time": convert_time(point["start_time"]),
                "heart_rate": int(point["heart_rate"])
            })
    
    return {
        "trackpoints": trackpoints
    }

def create_tcx_file(json_data, filename):
    # Create the root element and set its attributes
    root = ET.Element('TrainingCenterDatabase')
    root.set('xsi:schemaLocation', 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd')
    root.set('xmlns:ns5', 'http://www.garmin.com/xmlschemas/ActivityGoals/v1')
    root.set('xmlns:ns3', 'http://www.garmin.com/xmlschemas/ActivityExtension/v2')
    root.set('xmlns:ns2', 'http://www.garmin.com/xmlschemas/UserProfile/v2')
    root.set('xmlns', 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xmlns:ns4', 'http://www.garmin.com/xmlschemas/ProfileExtension/v1')
    

    
    # Create the Activities element
    activities = ET.SubElement(root, 'Activities')
    activity = ET.SubElement(activities, 'Activity')
    activity.set('Sport', 'Other')
    
    ET.SubElement(activity, 'Id').text = json_data['start_time']
    
    # Create a Lap element and set its attributes
    lap = ET.SubElement(activity, 'Lap')
    lap.set('StartTime', json_data['start_time'])
    ET.SubElement(lap, 'TotalTimeSeconds').text = str(json_data['duration'])
    distance_meters = ET.SubElement(lap, "DistanceMeters")
    distance_meters.text = "0"

    max_speed = ET.SubElement(lap, "MaximumSpeed")
    max_speed.text = "0"

    calories = ET.SubElement(lap, "Calories")
    calories.text = str(int(json_data['calories']))

    avg_hr = ET.SubElement(lap, "AverageHeartRateBpm")
    avg_hr_value = ET.SubElement(avg_hr, "Value")
    avg_hr_value.text = str(int(json_data['avg_hr']))

    max_hr = ET.SubElement(lap, "MaximumHeartRateBpm")
    max_hr_value = ET.SubElement(max_hr, "Value")
    max_hr_value.text = str(int(json_data['max_hr']))

    intensity = ET.SubElement(lap, "Intensity")
    intensity.text = "Active"

    trigger_method = ET.SubElement(lap, "TriggerMethod")
    trigger_method.text = "Manual"
    
    # Create a Track element and set its attributes
    track = ET.SubElement(lap, 'Track')
    
    # Create a Trackpoint element for each heart rate data point
    for heart_rate_data in json_data['trackpoints']:
        trackpoint = ET.SubElement(track, 'Trackpoint')
        ET.SubElement(trackpoint, 'Time').text = heart_rate_data['time']
        heart_rate_bpm = ET.SubElement(trackpoint, 'HeartRateBpm')
        ET.SubElement(heart_rate_bpm, 'Value').text = str(heart_rate_data['heart_rate'])
    
    # Write the XML tree to a file
    tree = ET.ElementTree(root)
    tree.write(filename, encoding='UTF-8', xml_declaration=True)


# search for files with the pattern "com.samsung.shealth.exercise.*.csv"
files = glob.glob("com.samsung.shealth.exercise.*.csv")

# get the latest file based on the file name
filename = max(files, key=lambda x: int(x.split(".")[-2]))

# Load data from the CSV file using pandas and select rows where "com.samsung.health.exercise.exercise_type" is 15002
df = pd.read_csv(filename, skiprows=[0], index_col=False)
df = df[df["com.samsung.health.exercise.exercise_type"] == 15002]

# Extract the filenames of the additional JSON files from the "com.samsung.health.exercise.live_data" column
json_dir = "jsons/com.samsung.shealth.exercise"
json_filenames = df["com.samsung.health.exercise.live_data"].tolist()

if not os.path.exists("tcx_files"):
    os.makedirs("tcx_files")

# Iterate over each JSON file and convert the data to TCX format
for i, json_filename in enumerate(json_filenames):
    # Load data from the JSON file
    json_path = os.path.join(json_dir, json_filename[0], json_filename)
    output_filename = "tcx_files/" + os.path.splitext(json_filename)[0] + ".tcx"
    data = process_file(json_path)
    data['start_time'] = datetime.strptime(df.iloc[i]["com.samsung.health.exercise.start_time"], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%dT%H:%M:%SZ")
    data['duration'] = df.iloc[i]["com.samsung.health.exercise.duration"]
    data['calories'] = df.iloc[i]["total_calorie"]
    data['avg_hr'] = df.iloc[i]["com.samsung.health.exercise.mean_heart_rate"]
    data['max_hr'] = df.iloc[i]["com.samsung.health.exercise.max_heart_rate"]
    create_tcx_file(data, output_filename)