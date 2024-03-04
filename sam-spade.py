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

# Displays current AWS account and region information
# You will need to upload the SAM toolkit in each region of Cloudshell you intend to use

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
            instance_dict[instance_id] = instance_name
            ref_number += 1

    print(f"{ref_number}. Select All")
    selected_refs = input("Enter the reference numbers of the instances to target, separated by commas, or select all: ")
    
    selected_instance_id_name_map = {}
    if selected_refs.strip().lower() == str(ref_number):  # User selects all
        return instance_dict
    else:
        selected_refs_list = selected_refs.split(',')
        for i, (instance_id, instance_name) in enumerate(instance_dict.items(), start=1):
            if str(i) in selected_refs_list:
                selected_instance_id_name_map[instance_id] = instance_name

    return selected_instance_id_name_map

# Prompts to type which command to send
#
# Replace this function to create custom modules

def select_command():
    command = input("\nWhat command would you like to send to the selected instances? (ex: apt-get update) ")
    confirm = input(f"Do you wish to send this command:\n {command} \n(y/n)? ")
    if confirm.lower() == 'y':
        return command
    else:
        print("Action canceled by user")
        return None

# Checks if the instance is available for commands before sending
# Instances may not be available if they do not have SSM installed, are in a hung state
# or if the Cloudshell user does not have the appropriate permissions to access the SSM functions

def filter_ssm_ready_instances(instance_id_name_map):
    ssm = boto3.client('ssm')
    ssm_ready_instance_ids = set()

    paginator = ssm.get_paginator('describe_instance_information')
    page_iterator = paginator.paginate()
    
    for page in page_iterator:
        for instance_info in page['InstanceInformationList']:
            if instance_info['InstanceId'] in instance_id_name_map:
                ssm_ready_instance_ids.add(instance_info['InstanceId'])

    valid_instance_id_name_map = {id: name for id, name in instance_id_name_map.items() if id in ssm_ready_instance_ids}
    
    if not valid_instance_id_name_map:
        print("No valid SSM-ready instances found. Exiting...")
        sys.exit(1)
    
    return valid_instance_id_name_map

# Takes the command selected in the select_command() function and sends it to the instances selected
# 
# To create custom modules, replace the select_command() function with your desired command structure
# or workflow, and have the new function return the [command] parameter. The function below will execute the
# command on your desired endpoint
#
# WARNING: Only use execute_command() for modules designed to interact with the instances' OS, not for
# modules which interact with the AWS API

def execute_command(instance_id_name_map, command):
    ssm = boto3.client('ssm')
    successful_instances = {}
    command_ids = {}
    for instance_id, instance_name in instance_id_name_map.items():
        try:
            response = ssm.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={'commands': [command]},  # Here we use the command passed to the function
            )
            command_id = response['Command']['CommandId']
            print(f"Command sent to {instance_id} ({instance_name})")
            successful_instances[instance_id] = instance_name
            command_ids[instance_id] = command_id
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidInstanceId':
                print(f"\033[91m{instance_id} ({instance_name}) is not eligible for commands.\033[0m")
            else:
                print(f"\033[91mAn error occurred while executing the command on {instance_id} ({instance_name}): {e}\033[0m")
    return successful_instances, command_ids

# Handles the sessions and data flow from the target instances
# The ideal retry and sleep values will depend on your environment, but if you receive 'InvocationDoesNotExist' errors
# you should consider increasing the delays

def monitor_command_status_and_fetch_output(ssm_client, command_id, instance_id, instance_name):
    waiting_statuses = ['Pending', 'InProgress', 'Delayed']
    completed_statuses = ['Success', 'Cancelled', 'Failed', 'TimedOut', 'Cancelling']
    
    print(f"\nMonitoring command execution status for {instance_id} ({instance_name})...")
    retries = 0
    max_retries = 5  # Maximum number of retries
    retry_delay = 5  # Delay between retries in seconds
    command_results = []  # Initialize an empty list to hold the command results for CSV output

    while True:
        try:
            invocation_response = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id,
            )
            status = invocation_response['Status']
            if status in completed_statuses:
                print(f"{instance_id} ({instance_name}) command status: {status}")
                if status == 'Success':
                    print(f"\033[92mOutput for {instance_id} ({instance_name}):\033[0m\n{invocation_response['StandardOutputContent']}\n")
                
# To create custom modules, modify which portions of the invocation_response are filtered. Here, we only return the StandardOutputContent
# The full invocation_response value can be see by swapping the commented lines within this function
                command_results.append({
                    "instance_id": instance_id,
                    "instance_name": instance_name,
                    "invocation_response": invocation_response['StandardOutputContent']  # Save only the StandardOutputContent
                    #"invocation_response": invocation_response,  # Save full invocation_response output
                })
                break  # Exit the loop once status is in completed_statuses
            else:
                print(f"{instance_id} ({instance_name}) {status}...")
        except ssm_client.exceptions.InvocationDoesNotExist as e:
            if retries < max_retries:
                print(f"Waiting for command invocation to be registered for {instance_id} ({instance_name})...")
                time.sleep(retry_delay)
                retries += 1
                continue
            else:
                print(f"Error getting command invocation for {instance_id} ({instance_name}) after retries: {e}")
                break  # Exit the loop after exceeding retry attempts
        except ClientError as e:
            print(f"Error getting command invocation for {instance_id} ({instance_name}): {e}")
            break  # Exit the loop on error
        time.sleep(10)
    
    return command_results  # Return the list containing command results for further processing

# Spade is designed to save the output with the same file name every time and overwrite any previous versions
# Once you find the right command and scope for what you are trying to do, move the resulting spade.csv file to 
# preventing overwriting

def output_csv(command_results):
    # Define the CSV file name
    csv_file = "spade.csv"
    
    # Define the field names/order for the CSV file
    fieldnames = ['instance_id', 'instance_name', 'invocation_response']

    # Open the CSV file for writing
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Write the header row
        writer.writeheader()
        
        # Iterate over the command results and write each as a row in the CSV
        for result in command_results:
            result['invocation_response'] = str(result['invocation_response'])
            writer.writerow(result)
    
    print(f"Data saved to {csv_file}")

def main():
    print_aws_account_info()
    instance_id_name_map = create_instance_map()

    if not instance_id_name_map:
        print("No instances specified. Exiting...")
        sys.exit(1)

    # Prompt the user for the command to send
    command = select_command()
    if command is None:  # Check if the user canceled the action
        sys.exit(1)  # Exit if the user decided not to send a command

    # Execute the command on specified instances
    successful_instances, command_ids = execute_command(instance_id_name_map, command)
    
    all_command_results = []  # List to aggregate results from all instances
    
    if successful_instances:
        print("\nSending command to selected instances...")
        ssm_client = boto3.client('ssm')
        for instance_id, command_id in command_ids.items():
            instance_name = successful_instances[instance_id]
            command_results = monitor_command_status_and_fetch_output(ssm_client, command_id, instance_id, instance_name)
            all_command_results.extend(command_results)  # Aggregate results

    if all_command_results:
        output_csv(all_command_results)  # Write results to CSV
    else:
        print("No commands were successfully sent to instances or no output to save.")

if __name__ == "__main__":
    main()
