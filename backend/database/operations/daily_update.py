#!/usr/bin/env python3
"""
Python version of the daily update script
Runs the complete daily update process for tech jobs insights
"""
import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print()
    
    try:
        # Run the command
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=False, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"❌ {description} failed with error: {e}")
        return False

def main():
    """Run the complete daily update process"""
    start_time = datetime.now()
    
    print("=" * 80)
    print(f"STARTING DAILY UPDATE - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Define the update steps
    steps = [
        {
            "command": "docker exec tech-jobs-backend python database/incremental_scrape.py --pages 3",
            "description": "Step 1: Scraping new jobs"
        },
        {
            "command": "docker exec tech-jobs-backend python database/run_nlp_pipeline.py",
            "description": "Step 2: Running NLP pipeline"
        },
        {
            "command": "docker exec tech-jobs-backend python database/verify_data.py",
            "description": "Step 3: Verifying data quality"
        }
    ]
    
    # Execute each step
    success_count = 0
    for step in steps:
        if run_command(step["command"], step["description"]):
            success_count += 1
        else:
            print(f"\n⚠️  Step failed, but continuing with remaining steps...")
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print(f"DAILY UPDATE COMPLETE - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(f"Duration: {duration}")
    print(f"Steps completed successfully: {success_count}/{len(steps)}")
    
    if success_count == len(steps):
        print("🎉 All steps completed successfully!")
        sys.exit(0)
    else:
        print("⚠️  Some steps failed. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
