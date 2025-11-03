import os
import json
from parser_api import parse_resume # Your main parsing function

# Define the input and output paths
INPUT_DIR = "test_files"
OUTPUT_FILE = "processed_resumes.json"

def process_all_resumes():
    """
    Scans the input directory, processes all resumes, and saves the results
    to a single JSON file with added debugging feedback.
    """
    
    print("--- Starting Batch Resume Processing ---")
    print(f"Project directory: {os.getcwd()}")
    print(f"Looking for input files in: {os.path.abspath(INPUT_DIR)}")
    
    all_results = []
    
    # Check if the input directory exists
    if not os.path.exists(INPUT_DIR):
        print(f"❌ FATAL ERROR: Input directory '{INPUT_DIR}' not found.")
        print("Please ensure you have a 'test_files' folder in your project root.")
        return

    # 1. Iterate through the input directory
    file_list = os.listdir(INPUT_DIR)
    if not file_list:
        print(f"🛑 STOPPED: Input directory '{INPUT_DIR}' is empty.")
        return
    
    for filename in file_list:
        file_path = os.path.join(INPUT_DIR, filename)
        
        # Skip directories and non-resume files
        if os.path.isdir(file_path) or not (filename.lower().endswith('.pdf') or filename.lower().endswith('.docx')):
            print(f"Skipping non-resume file: {filename}")
            continue

        print(f"Processing: {filename}...")
        
        # 2. Use your core parser function
        result = parse_resume(file_path)
        
        # Check for errors in the parsing function
        if 'error' in result:
             print(f"❌ PARSING ERROR for {filename}: {result['error']}")
             continue 

        # Add the filename to the result for easy tracking
        result['filename'] = filename
        
        all_results.append(result)

    print(f"\nFinished processing {len(all_results)} files.")
    
    # 3. Save the aggregated results to a master JSON file
    if not all_results:
        print("🛑 STOPPED: No resumes were successfully processed to save.")
        return

    try:
        abs_output_path = os.path.abspath(OUTPUT_FILE)
        
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(all_results, f, indent=4)
        
        print(f"\n✅ SUCCESS: Batch processing complete!")
        print(f"   Processed {len(all_results)} files.")
        print(f"   Results saved to: {abs_output_path}") 
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR saving results: {e}")

if __name__ == "__main__":
    process_all_resumes()