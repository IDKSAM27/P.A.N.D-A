class SpeechToTextInterface():
    @abstractmethod
    def transcribe(self,audio_path: str) -> str:
        pass

