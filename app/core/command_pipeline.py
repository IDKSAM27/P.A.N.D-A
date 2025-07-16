from app.interfaces.audio_interfaces import SpeachToTextInterface
from app.interfaces.llm_interface import LLMParserInterface 
from app.interfaces.processor_interface import DataProcessorInterface 
from pandas import DataFrame 

class CommandPipeline:
    def __init__(
        self,
        audio_interface: SpeachToTextInterface,
        llm_parser: LLMParserInterface,
        processor: DataProcessorInterface,
        data: DataFrame
    ):
        self.audio_interface = audio_interface
        self.llm_parser = llm_parser
        self.processor = processor
        self.data = data

    def run(self, audio_path: str):
        command = self.audio_interface.transcribe(audio_path)
        intent = self.llm_parser.parse_intent(command)
        result = self.processor.process(self.data, intent)
        return command, intent, result
