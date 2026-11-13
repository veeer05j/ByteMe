import ctypes
import os

SOUND_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminder_sound.mp3")


def _mci(command):
    """Send a command to Windows' built-in media player."""
    return ctypes.windll.winmm.mciSendStringW(command, None, 0, None)


def play_sound():
    """Play reminder_sound.mp3 without blocking."""
    if not os.path.exists(SOUND_FILE):
        print(f"Sound file not found: {SOUND_FILE}")
        return
    _mci("close reminder")  # close any previous play
    _mci(f'open "{SOUND_FILE}" type mpegvideo alias reminder')
    _mci("play reminder")


def stop_sound():
    """Stop the sound early."""
    _mci("stop reminder")
    _mci("close reminder")


if __name__ == "__main__":
    import time
    print("Playing reminder sound...")
    play_sound()
    time.sleep(5)  # keep the script alive while the sound plays