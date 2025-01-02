
#-------------------------------------------------------------------------------
# Name:        Horus e-mail (for HorusGUI in Windows)
# Purpose:
#
# Author:      9A4AM
#
# Created:     01.08.2024 Rev 02.01.2025
# Copyright:   (c) 9A4AM 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import time
import smtplib
import schedule
import shutil
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Read config file
def load_config(config_file):
    config = {}
    try:
        with open(config_file, 'r') as file:
            for line in file:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error reading config file: {e}")
    return config

# Make list of file in directory
def get_files_in_directory(directory_path):
    try:
        files = os.listdir(directory_path)
        return files
    except Exception as e:
        print(f"Error accessing directory: {e}")
        return []

# Check and move old files to backup directory
def move_old_files_to_backup(directory_path, backup_path):
    current_time = time.time()
    six_hours_in_seconds = 6 * 60 * 60

    # Create backup directory if it doesn't exist
    os.makedirs(backup_path, exist_ok=True)

    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)

        if os.path.isfile(file_path):
            last_modified_time = os.stat(file_path).st_mtime

            # Check if the file was not modified in the last 6 hours
            if current_time - last_modified_time > six_hours_in_seconds:
                try:
                    shutil.move(file_path, os.path.join(backup_path, file_name))
                    print(f"Moved {file_name} to backup directory.")
                except Exception as e:
                    print(f"Error moving file {file_name}: {e}")

# Extract relevant part of file name
def extract_log_info(file_name):
    try:
        if '_' in file_name and file_name.endswith('.csv'):
            return file_name.split('_')[1].split('.csv')[0]
    except Exception as e:
        print(f"Error extracting log info from {file_name}: {e}")
    return "Unknown"

# Send e-mail
def send_email(new_files, email_config):
    try:
        # Extract log info from file names
        log_info = [extract_log_info(file) for file in new_files]

        # Set MIME
        msg = MIMEMultipart()
        msg['From'] = email_config['from_email']
        msg['To'] = email_config['to_email']
        msg['Subject'] = "New HORUS sonde flight detected in area"

        body = (
            f"New log files found for call:\n\n" +
            "\n\n".join(
            f"{info}: https://amateur.sondehub.org/#!mt=Mapnik&mz=6&qm=1h&mc=45.99696,17.01782&f={info}\n"
            for info in log_info
            ) +
            "\n"
        )
        msg.attach(MIMEText(body, 'plain'))

        # Set server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_config['from_email'], email_config['app_password'])
            server.sendmail(email_config['from_email'], email_config['to_email'], msg.as_string())

        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Check for new log file in directory and if exist new file, send e-mail
def check_for_new_files(directory_path, email_config, backup_path):
    global previous_files

    # Move old files to backup before checking for new files
    move_old_files_to_backup(directory_path, backup_path)

    current_files = get_files_in_directory(directory_path)
    if not current_files:
        return

    new_files = set(current_files) - set(previous_files)
    if new_files:
        send_email(list(new_files), email_config)
        previous_files = current_files  # Reset file list

# Read config
base_config_file = 'config.txt'
base_config = load_config(base_config_file)

# Dobijanje prave putanje do config.txt
config_file = base_config['config_path']
config = load_config(config_file)

# Settings
directory_path = config['directory_path']
backup_path = config['backup_path']
email_config = {
    'from_email': config['from_email'],
    'to_email': config['to_email'],
    'app_password': config['app_password']
}
print(f"Attempting to login with email: {email_config['from_email']}")

# Init
previous_files = get_files_in_directory(directory_path)

# Check for new file every 1 minute
schedule.every(1).minutes.do(check_for_new_files, directory_path, email_config, backup_path)

print("Monitoring started. Press Ctrl+C to stop.")
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("Monitoring stopped.")
