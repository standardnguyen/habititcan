import subprocess
import sys
import os
import threading
import random

def send_notification(title, message, urgency='normal', timeout=5000, icon=None, sound_file=None):
    """Send a desktop notification with optional custom sound.
    
    Args:
        title: Notification title
        message: Notification message
        urgency: 'low', 'normal', or 'critical'
        timeout: Timeout in milliseconds
        icon: Path to icon file or icon name
        sound_file: Path to .ogg audio file to play
    """
    # Send the notification
    cmd = ['notify-send', '-u', urgency, '-t', str(timeout)]
    if icon:
        cmd.extend(['-i', icon])
    cmd.extend([title, message])
    
    notification_success = False
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"notify-send failed: {result.stderr}", file=sys.stderr)
        else:
            notification_success = True
    except subprocess.TimeoutExpired:
        print("notify-send timed out", file=sys.stderr)
    except FileNotFoundError:
        print("notify-send not found - is libnotify installed?", file=sys.stderr)
    
    # Play sound if specified and notification was successful
    if sound_file and notification_success:
        play_sound(sound_file)
    
    return notification_success

def play_sound(sound_file):
    """Play an audio file using available audio players."""
    # Expand ~ to home directory
    sound_file = os.path.expanduser(sound_file)
    
    if not os.path.isfile(sound_file):
        print(f"Sound file not found: {sound_file}", file=sys.stderr)
        return False
    
    # List of audio players to try (in order of preference)
    players = [
        ['paplay', '--volume=49152'],
        ['mpv', '--no-video', '--really-quiet'],
        ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet'],
        ['ogg123', '-q'],
    ]
    
    for player_cmd in players:
        try:
            # Use threading to avoid blocking the main thread
            def play_async():
                try:
                    subprocess.run(player_cmd + [sound_file], 
                                 capture_output=True, 
                                 timeout=10)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            thread = threading.Thread(target=play_async, daemon=True)
            thread.start()
            return True
            
        except FileNotFoundError:
            continue
    
    print("No suitable audio player found. Install mpv, ffmpeg, vorbis-tools, or pulseaudio-utils", file=sys.stderr)
    return False

def send_balatro_notification(title="default", message="default", event_type="default", notification=False, urgency='normal', timeout=5000):
    """Send a notification with Balatro sound effects.
    
    Args:
        title: Notification title
        message: Notification message
        event: Event type for sound selection
        urgency: 'low', 'normal', or 'critical'
        timeout: Timeout in milliseconds
    """

    
    sound_file = grab_sound_file_based_off_of_notification_type(event_type)
    if notification:
        return send_notification(title, message, urgency=urgency, timeout=timeout, sound_file=sound_file)
    else:
        play_sound(sound_file)


def grab_sound_file_based_off_of_notification_type(event_type):
    """Get the sound file path based on notification type."""
    balatro_dir = os.path.expanduser("~/.local/share/sounds/balatro/stereo")

    sound_map = {
        'success': 'coin1.ogg',
        'big_success': 'win.ogg',
        'money': 'coin2.ogg',
        'error': 'cancel.ogg',
        'warning': 'negative.ogg',
        'message': 'card1.ogg',
        'card_action': 'card3.ogg',
        'info': 'button.ogg',
        'highlight': 'highlight1.ogg',
        'magic': 'tarot1.ogg',
        'mystical': 'tarot2.ogg',
        'action': 'cardSlide1.ogg',
        'whoosh': 'whoosh1.ogg',
        'ambient': 'ambientFire1.ogg',
        'explosion': 'explosion1.ogg',
        'gong': 'gong.ogg',
        'default': 'highlight1.ogg'
    }

    # if the event_type is 'trival', the sound is a random choice between crumple1 2,3,4 and crumple5
    # use the random choice to select one of the crumple sounds
    if event_type == 'trivial-doot':
        population = ['crumple1.ogg', 'crumple2.ogg', 'crumple3.ogg', 'crumple4.ogg', 'crumple5.ogg', 'crumpleLong2.ogg', 'crumpleLong1.ogg']
        sound_file = random.choice(population)
    elif event_type == 'easy-doot':
        population = ['card1.ogg', 'card3.ogg', 'chips1.ogg', 'chips2.ogg', 'cardFan2.ogg']
        sound_file = random.choice(population)
    elif event_type == 'medium-doot':
        population = ['coin1.ogg', 'coin2.ogg', 'coin3.ogg', 'coin4.ogg', 'coin5.ogg', 'coin6.ogg', 'coin7.ogg']
        sound_file = random.choice(population)
    elif event_type == 'hard-doot':
        population = ['multhit1.ogg', 'multhit2.ogg', 'foil1.ogg', 'foil2.ogg', 'holo1.ogg', 'polychrome1.ogg', 'magic_crumple3.ogg']
        sound_file = random.choice(population)
    else:
        sound_file = sound_map.get(event_type, sound_map[event_type])


    sound_file = f"{balatro_dir}/{sound_file}"
    print(f"Using sound file: {sound_file} for event type: {event_type}")
    return os.path.join(balatro_dir, sound_map.get(event_type, sound_file))

# Example usage
if __name__ == "__main__":
    # Different notification types with Balatro sounds
    
    # Success notifications
    send_balatro_notification("Payment Received", "You earned $100!", 'money')
    send_balatro_notification("Deploy Success", "All tests passed!", 'big_success')
    send_balatro_notification("Task Complete", "Backup finished", 'success')
    
    # Error/Warning notifications
    send_balatro_notification("Error", "Failed to save file", 'error')
    send_balatro_notification("Warning", "Disk space low", 'warning')
    
    # Message notifications
    send_balatro_notification("New Email", "Message from boss", 'message')
    send_balatro_notification("Chat Message", "John: Hey there!", 'card_action')
    
    # Special events
    send_balatro_notification("Rare Event", "Found secret feature!", 'magic')
    send_balatro_notification("System Alert", "Update available", 'gong')
    
    # Original function still works too
    send_notification("Custom Sound", "Direct file path", 
                     sound_file="~/sounds/balatro/explosion1.ogg")
    
    # Silent notification
    send_notification("Silent", "No sound for this one")