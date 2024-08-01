#-------------------------------------------------------------------------------
# Name:        Horus e-mail (for HorusGUI in Windows)
# Purpose:
#
# Author:      9A4AM
#
# Created:     01.08.2024
# Copyright:   (c) 9A4AM 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import time
import smtplib
import schedule
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

# Send e-mail
def send_email(new_files, email_config):
    try:
        # Set MIME
        msg = MIMEMultipart()
        msg['From'] = email_config['from_email']
        msg['To'] = email_config['to_email']
        msg['Subject'] = "New HORUS sonde flight detected in area"

        body = f"New log files added:\n\n" + "\n".join(new_files)
        msg.attach(MIMEText(body, 'plain'))

        # Set server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_config['from_email'], email_config['app_password'])

        # Send e-mail
        text = msg.as_string()
        server.sendmail(email_config['from_email'], email_config['to_email'], text)
        server.quit()

        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Check for new log file in directory and if exist new file, send e-mail
def check_for_new_files(directory_path, email_config):
    global previous_files
    current_files = get_files_in_directory(directory_path)
    if not current_files:
        return

    new_files = set(current_files) - set(previous_files)
    if new_files:
        send_email(list(new_files), email_config)
        previous_files = current_files  # Ažuriranje popisa datoteka

# Read config
base_config_file = 'config.txt'
base_config = load_config(base_config_file)

# Dobijanje prave putanje do config.txt
config_file = base_config['config_path']
config = load_config(config_file)

# Settings
directory_path = config['directory_path']
email_config = {
    'from_email': config['from_email'],
    'to_email': config['to_email'],
    'app_password': config['app_password']
}

# Init
previous_files = get_files_in_directory(directory_path)

# Check for new file every 1 minute
schedule.every(1).minutes.do(check_for_new_files, directory_path, email_config)

print("Monitoring started. Press Ctrl+C to stop.")
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("Monitoring stopped.")

