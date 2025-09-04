import json
import logging
import os
from models import StructuredCV
from latex_generator import generate_latex_string
from latex_compiler import compile_latex_to_pdf

# Setup basic logging to see output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define a log file for compiler errors
COMPILER_LOG_FILE = "compiler_error.log"

def run_manual_test():
    """
    Tests the latex_generator with real data from a saved session.
    Logs compiler errors to a dedicated file.
    """
    logging.info("--- Starting Manual LaTeX Generation Test ---")

    # 1. Load the saved session file
    try:
        with open("cv_generation_session.json", "r", encoding="utf-8") as f:
            saved_state = json.load(f)
        logging.info("Successfully loaded cv_generation_session.json")
    except Exception as e:
        logging.error(f"Failed to load or parse session file: {e}")
        return

    # 2. Get the 'final_cv' data and reconstruct the Pydantic model
    final_cv_data = saved_state.get("final_cv")
    if not final_cv_data:
        logging.error("Session file does not contain a 'final_cv' object.")
        return

    try:
        cv_object = StructuredCV.model_validate(final_cv_data)
        logging.info("Successfully reconstructed StructuredCV object from session data.")
    except Exception as e:
        logging.error(f"Pydantic validation failed: {e}")
        return

    # 3. Run the LaTeX generator
    logging.info("Generating LaTeX string...")
    try:
        latex_string = generate_latex_string(cv_object)
        logging.info("Generator created LaTeX string successfully.")
    except Exception as e:
        logging.error(f"The latex_generator.py script itself crashed: {e}")
        return

    # 4. Run the LaTeX compiler
    logging.info("Compiling LaTeX string...")
    result = compile_latex_to_pdf(latex_string)

    # 5. Report the final result
    if result["success"]:
        logging.info("✅ ✅ ✅ SUCCESS: PDF compiled successfully!")
        logging.info("The generator is now working correctly with real data.")
        # Clean up old error log if it exists
        if os.path.exists(COMPILER_LOG_FILE):
            os.remove(COMPILER_LOG_FILE)
    else:
        logging.error("❌ ❌ ❌ FAILURE: PDF compilation failed.")
        error_log = result.get("log", "No log content available.")

        # Log the error to a dedicated file
        try:
            with open(COMPILER_LOG_FILE, "w", encoding="utf-8") as f:
                f.write(error_log)
            logging.error(f"Detailed compiler error log has been saved to: {COMPILER_LOG_FILE}")
        except Exception as e:
            logging.error(f"Failed to write to {COMPILER_LOG_FILE}: {e}")

        # Also print a snippet to the console for quick view
        print("\n--- Compiler Error Snippet ---")
        print(error_log[:1000] + "...")
        print("----------------------------")

if __name__ == "__main__":
    run_manual_test()