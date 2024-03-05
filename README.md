![image](https://github.com/NIA-cnewton/sam-toolbox/assets/140832515/cb3ffb62-d558-43db-b412-63554beeabe2)

# Simple AWS Manager (SAM) Toolbox

The Simple AWS Manager (SAM) Toolbox is a collection of lightweight Python scripts designed for AWS CloudShell, aimed at providing AWS sysadmins with a highly portable and customizable toolkit for managing AWS EC2 instances in a repeatable and portable way.

## Features
The SAM Toolbox consists of four main modules, each offering distinct functionalities to streamline your AWS EC2 management tasks. These modules are designed to be standalone, allowing for easy integration into various applications with minimal setup required. They leverage AWS CLI commands to interact with your EC2 instances efficiently. There are instructions within the comments on how to customize each module to your specific needs, and I hope to add examples of Lambda functions showing how to automate actions based on these scripts.

## Modules Overview

sam-spade: Executes custom commands on selected EC2 instances via AWS SSM and outputs the results in the file spade.csv.

sam-init: Provides the ability to start, stop, or reboot selected instances, with a log of actions taken saved in init.csv.

sam-tags: Applies user-defined tags to selected instances, with a completion status report saved in tags.csv.

sam-list: Generates a CSV report (list.csv) of selected EC2 metadata for chosen instances.


## Getting Started

To utilize the SAM Toolbox, follow these simple steps:

1. Click on the <> Code button in the repo, and select Download Zip
   ![image](https://github.com/NIA-cnewton/sam-toolbox/assets/140832515/23dc54dd-7f38-430c-9fe0-a3a07b604c51)
 
2. Extract the zip file on your local machine, and log into your Cloudshell environment
![image](https://github.com/NIA-cnewton/sam-toolbox/assets/140832515/24c335cc-7df3-4997-bd8b-1da9df781652)

3. Select the Actions dropdown menu, and choose Upload File for each of the .py files. The files will be stored in the /home/cloudshell-user directory, regardless of your working directory when you select the option from the drop down menu 
![image](https://github.com/NIA-cnewton/sam-toolbox/assets/140832515/30280e3d-cc90-4eac-9a3c-bdb52e0cfe98)

4. Add the execution permission to the scripts > chmod u+x sam-*
> chmod u+x sam-*
5. Run the commands as needed
> ./sam-spade.py

## Using the Toolbox

Each script in the SAM Toolbox starts by mapping all EC2 instances in the current AWS account and region. This approach ensures that sysadmins are not overwhelmed by the output and can easily manage instances region by region.

## Basic Workflow

Instance Selection: Upon execution, you're prompted to select EC2 instances from the generated map. You can choose specific instances or select "All".

Execute Module Functionality: Depending on the module you're running, you'll either execute commands on instances, manage instance states, apply tags, or generate metadata reports.

Review Outputs: Each module generates a specific output file, providing a clear and concise summary of the actions taken or information gathered.

## Customization

The SAM Toolbox is designed with customization in mind. Each script includes comments guiding you on how to extend or modify its functionality to suit your specific needs. Whether you're looking to automate more complex tasks or integrate with other tools, SAM Toolbox provides a solid foundation to build upon.

## License
This project is licensed under the GPL License - see the LICENSE file for details.
