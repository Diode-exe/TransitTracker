api_key_file = "txt/api.txt"
try:
    with open(api_key_file, "r") as f:
        api_key = f.read()
except FileNotFoundError:
    print(f"[WARN] {api_key_file} not found!")
    print(f"You need a file called {api_key_file} with an API key in it")
    input("Press Enter to continue...")