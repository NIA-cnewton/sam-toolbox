#!/usr/bin/env python3

# Version 1.0

#Simple AWS Manager (SAM) Toolbox is a set of lightweight scripts and modules for sysadmins in AWS
#Copyright (C) 2024 Newton Advisory, LLC

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import time
import csv
import subprocess
import json

# Displays current AWS account and region information
# You will need to upload the SAM toolkit in each region of Cloudshell

def print_aws_account_info():
    session = boto3.session.Session()
    sts_client = session.client('sts')
    try:
        account_id = sts_client.get_caller_identity()["Account"]
        region = session.region_name
        print(f"AWS Account ID: {account_id}")
        print(f"Region: {region}\n")
    except NoCredentialsError:
        print("No AWS credentials found. Please configure your AWS CLI.")
        sys.exit(1)
    except ClientError as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

# Uses AWS CLI commands to create a real-time list of EC2 instances
# This function is scoped to the region and account and does not see global resources
# Does not check if SSM is installed or configured on the instance
        
def create_instance_map():
    ec2 = boto3.client('ec2')
    instances = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['pending', 'running', 'shutting-down', 'terminated', 'stopping', 'stopped']}]
    )
    statuses = ec2.describe_instance_status(IncludeAllInstances=True)

    status_dict = {status['InstanceId']: status['InstanceState']['Code'] for status in statuses['InstanceStatuses']}
    status_text = {0: 'pending', 16: 'running', 32: 'shutting-down', 48: 'terminated', 64: 'stopping', 80: 'stopped'}
    status_color = {0: '\033[93m', 16: '\033[92m', 32: '\033[93m', 48: '\033[91m', 64: '\033[93m', 80: '\033[91m'}

    instance_dict = {}
    ref_number = 1
    print("Available EC2 Instances:")

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_name = next(
                (tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'),
                'No Name Tag'
            )
            instance_status_code = status_dict.get(instance_id, None)
            instance_status = status_text.get(instance_status_code, 'Unknown')
            color = status_color.get(instance_status_code, '\033[0m')  # Default to no color if status unknown
            print(f"{ref_number}. {color}{instance_status}\033[0m {instance_id} ({instance_name})")
            instance_dict[instance_id] = (instance_name, instance_status)  # Store instance name and previous state
            ref_number += 1

    print(f"{ref_number}. Select All")
    selected_refs = input("Enter the reference numbers of the instances to target, separated by commas, or select all: ")
    
    selected_instance_id_name_map = {}
    if selected_refs.strip().lower() == str(ref_number):  # User selects all
        return instance_dict
    else:
        selected_refs_list = selected_refs.split(',')
        for i, (instance_id, instance_details) in enumerate(instance_dict.items(), start=1):
            if str(i) in selected_refs_list:
                selected_instance_id_name_map[instance_id] = instance_details
     
# To create custom scripts, comment out the entire section from here back to the beginning of this function, and uncomment the lines below
# Add your specific instance ids to the map below, and the script will target them automatically each time without prompting
# Instance name does not dynamically populate, but you can hard code the values here that you want to display on the screen or in the csv
    # selected_instance_id_name_map = {
    #     'i-05dfxxxxxxxxxxx44': ('Instance Name 1', 'Instance Previous State 1'),
    #     'i-0d87ddxxxxxxxxxxx': ('Instance Name 2', 'Instance Previous State 2')
    # }

    return selected_instance_id_name_map

# Prompts to type which command to send
#
# To create a custom script with a hard-coded selection, comment out the entire select_command() function and then follow the instructions in
# the main() function

def select_command():
    print("\nSelect the action to perform on the selected instances:")
    print("1. Start instances")
    print("2. Stop instances")
    print("3. Reboot instances")
    print("4. Exit")
    choice = input("Enter your choice (1-4): ")

    actions = {
        '1': 'aws ec2 start-instances',
        '2': 'aws ec2 stop-instances',
        '3': 'aws ec2 reboot-instances',
        '4': 'exit'
    }

    if choice in actions:
        action = actions[choice]
        action_word = action.split()[2].replace('-instances', '')  # This removes '-instances' from the command
        if choice == '4':
            confirm = input("Do you wish to exit? (y/n): ")
        else:
            confirm = input(f"Do you wish to {action_word} the selected instances (y/n)? ")
        
        if confirm.lower() == 'y':
            if choice == '4':
                print("Exiting program...")
                sys.exit(0)
            return action
        else:
            print("Action canceled by user.")
            return None
    else:
        print("Invalid selection, please try again.")
        return None

def execute_command(instance_id_name_map, action):
    successful_instances = {}
    action_map = {
        'aws ec2 start-instances': 'starting',
        'aws ec2 stop-instances': 'stopping',
        'aws ec2 reboot-instances': 'rebooting'  # AWS CLI reboot command does not seem to work reliably
    }
    current_action = action_map.get(action, 'processing')

    for instance_id, (instance_name, previous_state) in instance_id_name_map.items():
        try:
            # Construct the AWS CLI command
            cli_command = f"{action} --instance-ids {instance_id}"
            # Execute the AWS CLI command
            process = subprocess.Popen(cli_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                # Specific message for reboot action
                if action == 'aws ec2 reboot-instances':
                    print(f"Reboot command sent to {instance_name}. This script does not monitor for successful reboot completion.")
                    new_state = 'Reboot command sent'  # Edit to change what is recorded as the current_state for reboots for CSV logging
                else:
                    # Command executed successfully for start and stop
                    print(f"\033[92mCommand for {current_action} sent to {instance_name}.\033[0m")
                    response = json.loads(stdout.decode('utf-8'))
                    if 'StartingInstances' in response:
                        new_state = response['StartingInstances'][0]['CurrentState']['Name']
                    elif 'StoppingInstances' in response:
                        new_state = response['StoppingInstances'][0]['CurrentState']['Name']
                    else:
                        new_state = 'unknown'
                successful_instances[instance_id] = (instance_name, previous_state, new_state)
            else:
                # Command execution failed
                print(f"\033[91mFailed to execute {current_action} command for {instance_id} ({instance_name}): {stderr.decode('utf-8')}\033[0m")
        except Exception as e:
            # Handle other exceptions
            print(f"\033[91mAn unexpected error occurred while {current_action} {instance_id} ({instance_name}): {e}\033[0m")

    return successful_instances

def monitor_command_status_and_fetch_output(ec2_client, instance_ids, action):
    # Define desired state mapping based on action
    desired_state_map = {
        'aws ec2 start-instances': 'running',
        'aws ec2 stop-instances': 'stopped'
    }

    # No monitoring for reboot instances
    if action == 'aws ec2 reboot-instances':
        print("\nSkipping monitoring for reboot action as per script configuration.")
        # Directly return the status without checking
        return {instance_id: 'Reboot command sent' for instance_id in instance_ids}

    desired_state = desired_state_map.get(action)
    if desired_state:
        print(f"\nMonitoring instances for reaching '{desired_state}' state...")
        final_statuses = {}
        for instance_id in instance_ids:
            print(f"Checking status for instance ID: {instance_id}...")
            while True:
                response = ec2_client.describe_instances(InstanceIds=[instance_id])
                current_state = response['Reservations'][0]['Instances'][0]['State']['Name']
                print(f" - Instance ID {instance_id} is currently {current_state}")
                if current_state == desired_state:
                    print(f"\033[92m - Instance ID {instance_id} reached the '{desired_state}' state.\033[0m")
                    final_statuses[instance_id] = desired_state
                    break
                else:
                    time.sleep(10)  # Wait for ten seconds before checking again
        return final_statuses
    else:
        # Return empty statuses if action does not require state monitoring
        return {}

# Init is designed to save the output with the same file name every time and overwrite any previous versions
# Once you find the right command and scope for what you are trying to do, move the resulting init.csv file to 
# preventing overwriting

def output_csv(instances_details):
    # Define the CSV file name. Edit below to change the output file name
    csv_file = "init.csv"

    # Define the field names/order for the CSV file
    fieldnames = ['instance_id', 'instance_name', 'previous_state', 'current_state']

    # Open the CSV file for writing
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Write the header row
        writer.writeheader()
        
        # Iterate over the instances details and write each as a row in the CSV
        for instance_id, details in instances_details.items():
            instance_name, previous_state, current_state = details
            writer.writerow({
                'instance_id': instance_id, 
                'instance_name': instance_name, 
                'previous_state': previous_state, 
                'current_state': current_state
            })
    
    print(f"Data saved to {csv_file}")

def main():
    print_aws_account_info()  # Print AWS account info at the start
    instance_id_name_map = create_instance_map()  # Create a map of instance IDs to names and previous states

    if not instance_id_name_map:
        print("No instances specified. Exiting...")
        sys.exit(1)

    # Continuously run until the user decides to exit
    while True:
        action = select_command()  # Let the user select the action
        if action is None:
            continue  # If the action selection was cancelled, restart the loop
# To create custom scripts, comment out the three lines above and uncomment the line below. Choose your desired action from the 'actions' section
# of the select_command() function        
        # action = 'aws ec2 start-instances'

        if action != 'exit':
            successful_instances = execute_command(instance_id_name_map, action)  # Execute the specified action on the selected instances

            if successful_instances:
                ec2_client = boto3.client('ec2')
                # Pass only the instance IDs to monitor_command_status_and_fetch_output
                instance_ids = list(successful_instances.keys())
                final_statuses = monitor_command_status_and_fetch_output(ec2_client, instance_ids, action)  # Monitor the status changes of the instances

                # Reformat instance details for CSV output (include previous and current states)
                instances_details_for_csv = {
                    inst_id: (
                        instance_id_name_map[inst_id][0],  # Name
                        instance_id_name_map[inst_id][1],  # Previous state
                        final_statuses[inst_id]  # Current state from final_statuses
                    ) for inst_id in final_statuses
                }
                # To disable the automatic saving of a csv file, comment out the line below
                output_csv(instances_details_for_csv)  # Output the final statuses to a CSV file
                break
            else:
                print("No instances were successfully processed.")
        else:
            break  # Exit the loop and end the program if action is 'exit'

if __name__ == "__main__":
    main()
