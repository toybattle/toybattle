import winreg

def save_to_registry(key_path, value_name, value_data):
    """
    Save a string value to the Windows Registry.
    """
    try:
        # Open or create the registry key
        registry_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        # Set the value (REG_SZ = string)
        winreg.SetValueEx(registry_key, value_name, 0, winreg.REG_SZ, value_data)
        winreg.CloseKey(registry_key)
        print(f"Saved '{value_name}' = '{value_data}' to {key_path}")
    except OSError as e:
        print(f"Error saving to registry: {e}")

def read_from_registry(key_path, value_name):
    """
    Read a string value from the Windows Registry.
    """
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, value_name)
        winreg.CloseKey(registry_key)
        return value
    except FileNotFoundError:
        print("Registry key or value not found.")
    except OSError as e:
        print(f"Error reading from registry: {e}")
    return None

if __name__ == "__main__":
    # Example usage
    registry_path = r"Software\ToyBattle"
    value_name = "Username"
    value_data = "JohnDoe"

    # Save data
    save_to_registry(registry_path, value_name, value_data)

    # Read data
    retrieved_value = read_from_registry(registry_path, value_name)
    if retrieved_value is not None:
        print(f"Retrieved from registry: {retrieved_value}")
