import speech_recognition as sr
from typing import Optional
from app.interfaces.audio_interface import AudioInterface

class SpeechRecognitionHandler(AudioInterface):
    """

    Handles audio transcription using the speech_recognition library, which
    leverages the Google Web Speech API by default.
    """
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def transcribe_audio(self, audio_filepath: str) -> Optional[str]:
        """
        Transcribes an audio file to text.

        Args:
            audio_filepath (str): Path to the audio file (e.g., a .wav file).

        Returns:
            The transcribed text as a string, or None if it fails.
        """
        if not audio_filepath:
            return None

        with sr.AudioFile(audio_filepath) as source:
            audio_data = self.recognizer.record(source)
            try:
                # Using Google Web Speech API for transcription
                text = self.recognizer.recognize_google(audio_data)
                print(f"-> [Audio] Transcribed text: '{text}'")
                return text
            except sr.UnknownValueError:
                print("-> [Audio] Google Web Speech API could not understand the audio.")
                return None
            except sr.RequestError as e:
                print(f"-> [Audio] Could not request results from Google Web Speech API; {e}")
                return None
