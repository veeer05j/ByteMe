from winsound import winsound

def play_reminder_sound():
    winsound.PlaySound("reminder_sound.wav", winsound.SND_FILENAME)