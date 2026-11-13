import pyttsx3

def speak(reply):
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    engine.setProperty('volume', 1.0)

    engine.say(reply)
    engine.runAndWait()

