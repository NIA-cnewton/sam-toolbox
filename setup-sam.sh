#!/bin/bash

# Define the directory and zip file paths
dir="/home/cloudshell-user/sam"
zip_file="/home/cloudshell-user/sam-toolbox-main.zip"

# Create the directory if it doesn't exist
echo "Checking for the directory..."
if [ ! -d "$dir" ]; then
    echo "Creating the directory: $dir"
    mkdir -p "$dir"
fi

# Unzip the file into the directory
echo "Unzipping $zip_file into $dir..."
unzip -o "$zip_file" -d "$dir"

# Change permissions of the files starting with 'sam'
echo "Changing permissions of the files..."
chmod +x $dir/sam*

# Add directory to PATH if not already present
if [[ ":$PATH:" != *":$dir:"* ]]; then
    echo "Adding $dir to PATH..."
    export PATH="$PATH:$dir"
    echo 'export PATH="$PATH:'$dir'"' >> ~/.bashrc
fi

echo -e "\033[0;32mAll steps completed successfully!\033[0m"
