#!/bin/bash

# Define the directory and zip file paths
base_dir="/home/cloudshell-user"
target_dir="$base_dir/sam"
zip_file="$base_dir/sam-toolbox-main.zip"
temp_dir="$base_dir/temp-sam-extract"

# Create the target directory if it doesn't exist
echo "Checking for the directory..."
if [ ! -d "$target_dir" ]; then
    echo "Creating the directory: $target_dir"
    mkdir -p "$target_dir"
fi

# Unzip the file into the temp directory
echo "Unzipping $zip_file..."
unzip -o "$zip_file" -d "$temp_dir"

# Move the contents from the extracted folder to the target directory
extracted_folder=$(ls "$temp_dir") # Assuming there's only one folder extracted
echo "Moving files to the 'sam' directory..."
mv -n "$temp_dir/$extracted_folder/"* "$target_dir"

# Change permissions of the files starting with 'sam' in the target directory
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
