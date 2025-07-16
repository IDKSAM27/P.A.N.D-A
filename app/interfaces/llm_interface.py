from typing import Dict

class LLMParserInterface():
    @abstractmethod
    def parse_intent(self, command: str) -> Dict:
        pass
