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
        
def create_instance_map():
    ec2 = boto3.client('ec2')
    instances = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )

    instance_dict = {}
    ref_number = 1
    print("Available EC2 Instances:")

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_name = next(
                (tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), # To use a different tag value, change the 'Name' to the key of the desired tag's key/value pair
                'No Name Tag'
            )
            print(f"{ref_number}. {instance_id} ({instance_name})")
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

# Prompts to select which parameters to collect

def select_values():
    options = [
        "InstanceId", "ImageId", "InstanceType", "KeyName", "LaunchTime",
        "Placement.AvailabilityZone", "Placement.Tenancy", "PrivateDnsName",
        "PrivateIpAddress", "PublicDnsName", "PublicIpAddress", "State.Name",
        "SubnetId", "VpcId", "SecurityGroups", "Tags", "Architecture",
        "RootDeviceType", "RootDeviceName", "BlockDeviceMappings", 
        "IamInstanceProfile.Arn", "VirtualizationType", "CpuOptions", 
        "PlatformDetails"
    ]
    
    print("\nSelect the values to collect from the instances:")
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    print(f"{len(options) + 1}. Select All")
    
    selected = input("Enter the numbers of the values you want to collect, separated by commas, or select all: ")
    selected_list = selected.split(',')
    value_map = []

    if str(len(options) + 1) in selected_list:  # User selects all
        value_map = options
    else:
        for index in selected_list:
            try:
                value_map.append(options[int(index)-1])
            except (ValueError, IndexError):
                print(f"Invalid selection: {index}. Please enter valid numbers separated by commas.")
                return []
                
    return value_map

import boto3

def create_report(value_map):
    # Initialize a boto3 client
    ec2 = boto3.client('ec2')

    # Construct the query parameters to select only the required instance attributes
    query = {'Filters': [{'Name': 'instance-state-name', 'Values': ['running']}]}
    
    # Call describe_instances with the query
    response = ec2.describe_instances(**query)
    
    # Initialize a list to hold the instance data
    instances_data = []

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_data = {}
            for value in value_map:
                # For complex values like SecurityGroups, Tags, etc., aggregate their values
                if value == "SecurityGroups":
                    instance_data[value] = ','.join([sg['GroupName'] for sg in instance.get(value, [])])
                elif value == "Tags":
                    instance_data[value] = ','.join([f"{tag['Key']}={tag['Value']}" for tag in instance.get(value, [])])
                elif value == "BlockDeviceMappings":
                    instance_data[value] = ','.join([bdm['Ebs']['VolumeId'] for bdm in instance.get(value, []) if 'Ebs' in bdm])
                elif value == "NetworkInterfaces":
                    instance_data[value] = ','.join([ni['NetworkInterfaceId'] for ni in instance.get(value, [])])
                else:
                    # Directly copy the value for simple attributes
                    instance_data[value] = instance.get(value, 'N/A')
            instances_data.append(instance_data)
    
    return instances_data

def output_csv(instances_data, value_map):
    # Define the CSV file name
    csv_file = "list.csv"
    
    # Open the CSV file for writing
    with open(csv_file, mode='w', newline='') as file:
        # Initialize the CSV writer with dynamic fieldnames based on value_map
        writer = csv.DictWriter(file, fieldnames=value_map)
        
        # Write the header row
        writer.writeheader()
        
        # Iterate over the instances data and write each as a row in the CSV
        for instance_data in instances_data:
            writer.writerow(instance_data)
    
    print(f"\033[92mData saved to {csv_file}\033[0m")

def main():
    print_aws_account_info()  # Display AWS account and region information
    instance_id_name_map = create_instance_map()  # Let user select instances

    if not instance_id_name_map:
        print("No instances selected. Exiting...")
        sys.exit(1)

    # Let user select which values to collect
    value_map = select_values()
    if not value_map:
        print("No values selected. Exiting...")
        sys.exit(1)

    # Collect data based on selected instances and values
    instances_data = create_report(value_map)
    if not instances_data:
        print("No data collected from instances. Exiting...")
        sys.exit(1)

    # Output the collected data to a CSV file
    output_csv(instances_data, value_map)

if __name__ == "__main__":
    main()