Simple AWS Manager (SAM) Toolbox

Welcome to the Simple AWS Manager (SAM) Toolbox! This project is a collection of lightweight Python scripts designed for AWS CloudShell, aimed at providing AWS sysadmins with a highly portable and customizable toolkit for managing AWS EC2 instances.

Features
The SAM Toolbox consists of four main modules, each offering distinct functionalities to streamline your AWS EC2 management tasks. These modules are designed to be standalone, allowing for easy integration into various applications with minimal setup required. They leverage AWS CLI commands to interact with your EC2 instances efficiently.

Modules Overview

sam-spade: Executes custom commands on selected EC2 instances via AWS SSM and outputs the results into a CSV file (spade.csv).

sam-init: Provides the ability to start, stop, or reboot selected instances, with a log of actions taken saved in sam-init-audit.log.

sam-tag: Applies user-defined tags to selected instances, with a completion status report saved in sam-init-audit.log.

sam-list: Generates a CSV report (list.csv) of selected EC2 metadata for chosen instances.


Getting Started

To utilize the SAM Toolbox, follow these simple steps:

1. Clone the Repository: Clone this repository to your local machine using Git or download the ZIP file from GitHub.

git clone https://github.com/<your-username>/simple-aws-manager-toolbox.git

Upload to AWS CloudShell: Log in to your AWS Management Console, open CloudShell, and use the GUI to upload the scripts you've cloned or downloaded.

2. Set Execution Permissions: Before using the scripts, you'll need to grant them execution permissions. You can do this by running:

chmod +x sam-*

Using the Toolbox

Each script in the SAM Toolbox starts by mapping all EC2 instances in the current AWS account and region. This approach ensures that sysadmins are not overwhelmed by the output and can easily manage instances region by region.

Basic Workflow

Instance Selection: Upon execution, you're prompted to select EC2 instances from the generated map. You can choose specific instances or select "All".

Execute Module Functionality: Depending on the module you're running, you'll either execute commands on instances, manage instance states, apply tags, or generate metadata reports.

Review Outputs: Each module generates a specific output file, providing a clear and concise summary of the actions taken or information gathered.

Customization

The SAM Toolbox is designed with customization in mind. Each script includes comments guiding you on how to extend or modify its functionality to suit your specific needs. Whether you're looking to automate more complex tasks or integrate with other tools, SAM Toolbox provides a solid foundation to build upon.

License
This project is licensed under the GPL License - see the LICENSE file for details.
