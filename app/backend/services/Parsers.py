from abc import ABC, abstractmethod


class BaseParser(ABC):
    """
    Base class for all laboratory test parsers.

    Every parser must return a dictionary with
    the information required for database storage.
    """

    def __init__(self, workbook):
        self.workbook = workbook

    @abstractmethod
    def parse(self,workbook) -> dict:
        """
        Extract information from the workbook.

        Returns
        -------
        dict
            Dictionary containing:
            - project
            - location
            - sample
            - test
            - measurements
        """
        
        return {
                    "project": self.parse_project(workbook),
                    "location": self.parse_location(workbook),
                    "sample": self.parse_sample(workbook),
                    "test": self.parse_test(workbook),
                    "measurements": self.parse_measurements(workbook)
                }


    @abstractmethod
    def parse_metadata(self) -> dict:
        """
        Extract project, sample and test metadata.
        """
        pass

    @abstractmethod
    def parse_measurements(self) -> list:
        """
        Extract measurement series.
        """
        pass
    
# Handles uniaxial (Einax) test files
class EinaxParser(BaseParser):

    def parse(self, workbook) -> dict:
        """
        Extract all relevant information from the workbook.

        Returns
        -------
        dict
            Information ready to be inserted into the database.
        """

        return {
            "project": self.parse_project(workbook),
            "location": self.parse_location(workbook),
            "sample": self.parse_sample(workbook),
            "test": self.parse_test(workbook),
            "measurements": self.parse_measurements(workbook)
        }

    def parse_project(self, workbook) -> dict:

        return {
            "project_number": None,
            "project_title": None,
            "description": None
        }

    def parse_location(self, workbook) -> dict:

        return {
            "location_name": None,
            "x_coordinate": None,
            "y_coordinate": None
        }

    def parse_sample(self, workbook) -> dict:

        return {
            "material": None,
            "depth_from_m": None,
            "depth_to_m": None,
            "water_content": None,
            "density_kg_m3": None
        }

    def parse_test(self, workbook) -> dict:

        return {
            "test_type": "uniaxial",
            "test_date": None,
            "initial_height_mm": None,
            "initial_diameter_mm": None,
            "young_modulus_kpa": None,
            "compressive_strength_kpa": None,
            "failure_strain_pct": None,
            "operator_name": None
        }

    def parse_measurements(self, workbook) -> list:

        measurements = []

        # TODO:
        # Locate the measurement table.
        # Each row should become a dictionary.

        return measurements
    
class TriaxParser(BaseParser):

    def parse(self, workbook):

        ...