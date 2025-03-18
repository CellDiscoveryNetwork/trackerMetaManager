#!/bin/bash

# Lock file path
lock_file="/tmp/run_tasks.lock"

# Check for the existence of the lock file
if [ -f "$lock_file" ]; then
    echo "Another instance of run_tasks.sh is currently running."
    exit 1
else
    # Create the lock file to prevent other instances from running
    touch "$lock_file"
fi

# Ensure the lock file is removed on script exit
trap 'rm -f "$lock_file"; exit' INT TERM EXIT

# Navigate to the directory where the scripts are located
cd /home/kkimler/gca_crontab || exit

# Run the Python script
/etc/anaconda/bin/python metadata_correctness_plotting_crontab.py

# Knit the R Markdown file to HTML using Rscript command
Rscript -e "rmarkdown::render('metadata_correctness.rmd', output_file='metadata_correctness.html')"

# Upload the HTML file to the Google Cloud Storage bucket
gsutil cp metadata_correctness.html gs://hca_gut_cell_atlas/metadata_correctness.html
gsutil -m setmeta -h "Cache-Control:no-store" gs://hca_gut_cell_atlas/metadata_correctness.html

# Clean up: remove the lock file
rm -f "$lock_file"
trap - INT TERM EXIT

