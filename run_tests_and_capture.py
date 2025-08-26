import subprocess
import sys

def run_tests():
    command = [sys.executable, "-m", "pytest", "fastapi_switchable_storage/tests"]
    print(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Tests completed successfully.")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        with open("test_results.txt", "w", encoding="utf-8") as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("STDERR:\n")
            f.write(result.stderr)
        print("Test results saved to test_results.txt")
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code {e.returncode}.")
        print("STDOUT:")
        print(e.stdout)
        print("STDERR:")
        print(e.stderr)
        with open("test_results.txt", "w", encoding="utf-8") as f:
            f.write("STDOUT:\n")
            f.write(e.stdout)
            f.write("STDERR:\n")
            f.write(e.stderr)
        print("Test results (failures) saved to test_results.txt")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        with open("test_results.txt", "w", encoding="utf-8") as f:
            f.write(f"An unexpected error occurred: {e}\n")

if __name__ == "__main__":
    run_tests()
