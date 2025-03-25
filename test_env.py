import os
try:
    from dotenv import load_dotenv
    print("Successfully imported dotenv")
    
    # Load environment variables
    load_dotenv()
    
    # Check if OPENAI_API_KEY is set
    if "OPENAI_API_KEY" in os.environ:
        print("OPENAI_API_KEY is set")
        # Print first few characters for verification (don't print the whole key for security)
        print(f"Key starts with: {os.environ['OPENAI_API_KEY'][:10]}...")
    else:
        print("OPENAI_API_KEY is not set")
except ImportError as e:
    print(f"Import error: {e}")

    # Try alternative import
    try:
        import python_dotenv
        print(f"Found python_dotenv at: {python_dotenv.__file__}")
    except ImportError:
        print("Could not import python_dotenv either")

    # List installed packages
    print("\nInstalled packages:")
    import subprocess
    result = subprocess.run(["uv", "pip", "list"], capture_output=True, text=True)
    print(result.stdout)
