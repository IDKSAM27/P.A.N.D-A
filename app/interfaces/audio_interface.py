from abc import ABC, abstractmethod
from typing import Optional

class AudioInterface(ABC):
    """
    Abstract Base Class for an audio handling and transcription service.
    """

    @abstractmethod
    def transcribe_audio(self, audio_filepath: str) -> Optional[str]:
        """
        Transcribes the audio from a given file path.

        Args:
            audio_filepath (str): The path to the audio file to transcribe.

        Returns:
            Optional[str]: The transcribed text, or None if transcription fails.
        """
        pass
