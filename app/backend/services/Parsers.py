from abc import ABC, abstractmethod


from abc import ABC, abstractmethod

class BaseParser(ABC):

    def __init__(self, workbook):
        self.workbook = workbook

    def parse(self) -> dict:

        return {
            "project": self.parse_project(),
            "location": self.parse_location(),
            "sample": self.parse_sample(),
            "test": self.parse_test(),
            "measurements": self.parse_measurements()
        }

    @abstractmethod
    def parse_project(self) -> dict:
        pass

    @abstractmethod
    def parse_location(self) -> dict:
        pass

    @abstractmethod
    def parse_sample(self) -> dict:
        pass

    @abstractmethod
    def parse_test(self) -> dict:
        pass

    @abstractmethod
    def parse_measurements(self) -> list:
        pass
    
# Handles uniaxial (Einax) test files
class EinaxParser(BaseParser):

    def parse_project(self) -> dict:
        ...

    def parse_location(self) -> dict:
        ...

    def parse_sample(self) -> dict:
        ...

    def parse_test(self) -> dict:
        ...

    def parse_measurements(self) -> list:
        ...
    
class TriaxParser(BaseParser):

    def parse_project(self) -> dict:
        ...

    def parse_location(self) -> dict:
        ...

    def parse_sample(self) -> dict:
        ...

    def parse_test(self) -> dict:
        ...

    def parse_measurements(self) -> list:
        ...
