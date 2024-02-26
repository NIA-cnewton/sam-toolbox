#!/bin/bash

# Define the directory and zip file paths
base_dir="/home/cloudshell-user"
target_dir="$base_dir/sam"
zip_file="$base_dir/sam-toolbox-main.zip"
temp_dir="$base_dir/temp-sam-extract"

# Create temp directory for extraction
echo "Preparing extraction..."
mkdir -p "$temp_dir"
unzip -o "$zip_file" -d "$temp_dir"

# Determine the extracted folder's name and path
extracted_folder=$(ls "$temp_dir")
extracted_path="$temp_dir/$extracted_folder"

# Check if the target directory exists
echo "Setting up the 'sam' directory..."
if [ -d "$target_dir" ]; then
    echo "Directory $target_dir already exists."
else
    # Move the extracted contents to the target directory
    mv "$extracted_path" "$target_dir"
    echo "'sam' directory has been set up successfully."
fi

# Change permissions of the files starting with 'sam'
echo "Changing permissions of the files..."
chmod +x $target_dir/sam*

# Add directory to PATH if not already present
if [[ ":$PATH:" != *":$target_dir:"* ]]; then
    echo "Adding $target_dir to PATH..."
    export PATH="$PATH:$target_dir"
    echo 'export PATH="$PATH:'$target_dir'"' >> ~/.bashrc
fi

# Clean up the temporary extraction directory
echo "Cleaning up..."
rm -rf "$temp_dir"

# Final confirmation, printed in green if possible
echo -e "\033[0;32mAll steps completed successfully!\033[0m"
