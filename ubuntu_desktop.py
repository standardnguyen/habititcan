import subprocess
import sys

def send_notification(title, message, urgency='normal', timeout=5000, icon=None):
    cmd = ['notify-send', '-u', urgency, '-t', str(timeout)]
    
    if icon:
        cmd.extend(['-i', icon])
    
    cmd.extend([title, message])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"notify-send failed: {result.stderr}", file=sys.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        print("notify-send timed out", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("notify-send not found - is libnotify installed?", file=sys.stderr)
        return False