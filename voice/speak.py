from __future__ import annotations


def speak(text: str) -> bool:
    try:
        import pyttsx3
    except ImportError:
        return False

    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    return True

