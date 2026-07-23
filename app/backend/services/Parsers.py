from abc import ABC, abstractmethod

class BaseParser(ABC):

    def __init__(self, workbook):
        self.workbook = workbook

    def parse(self) -> dict[str, any]:

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
        
        # defines varaible that contains the sheet
        sheet=self.workbook["Tabelle1"]

        # gets projectnumber
        project_number=sheet["B2"].value

        # gets the project title
        project_title=sheet["B3"].value

        # gets description
        description=None # no description

        # gets creation date
        created_at=sheet["B7"].value # Datum

        # returns results
        return {
            "project_number": project_number,
            "project_title": project_title,
            "description": description,
            "created_at": created_at
        }

    def parse_location(self) -> dict:
        
        # defines varaible that contains the sheet
        sheet=self.workbook["Tabelle1"]

        # gets the location name
        location_name= sheet["B9"].value

        # gets the depth
        depth=sheet["B10"].value

        # returns results
        return {     
            "location_name": location_name,
            "depth_from_m": float(depth.split("-")[0].replace(",", ".").strip()),
            "depth_to_m": float(depth.split("-")[1].replace("m", "").replace(",", ".").strip())
        }

    def parse_sample(self) -> dict:
        
        # defines variable that contains the sheet
        sheet = self.workbook["Tabelle1"]

        # gets material
        material = sheet["B8"].value

        # gets average water content
        water_content = sheet["B28"].value

        # gets density
        density_kg_m3 = sheet["B22"].value

        # gets intial mass in kg
        initial_mass_kg=sheet["B21"].value

        # returns results
        return {
            "material": material,
            "water_content": water_content,
            "density_kg_m3": density_kg_m3,
            "initial_mass_kg": initial_mass_kg
        }

    def parse_test(self) -> dict:

        # defines variable that contains the sheet
        sheet = self.workbook["Tabelle1"]

        # returns results
        return {
            "test_type": "uniaxial",
            "test_date": sheet["B7"].value,
            "initial_height_mm": sheet["B19"].value * 1000,
            "initial_diameter_mm": sheet["B17"].value * 1000,
            "young_modulus_kpa": sheet["B30"].value,
            "compressive_strength_kpa": sheet["B31"].value,
            "failure_strain_pct": sheet["B32"].value,
            "operator_name": None
        }

    def parse_measurements(self) -> list:

        # defines variable that contain the workbook with the data to parse
        sheet = self.workbook["Tabelle1"]

        # find header row
        row = 1

        while sheet[f"A{row}"].value != "Zeit seit Versuchsbegin":
            row += 1

        # first data row
        row += 2

        # creates a list to store the information
        measurements = []

        # loops till there is None in the cell
        while sheet[f"B{row}"].value is not None:

            # appends data to list
            measurements.append({
                "time_s": sheet[f"A{row}"].value,
                "force_kn": sheet[f"B{row}"].value,
                "displacement_mm": sheet[f"C{row}"].value,
                "sample_height_mm": sheet[f"D{row}"].value,
                "strain_ratio": sheet[f"E{row}"].value,
                "strain_pct": sheet[f"F{row}"].value,
                "stress_kpa": sheet[f"G{row}"].value,
                "strain_at_max_stress_pct": sheet[f"H{row}"].value
            })

            # moves on to next row
            row += 1

        # returns results
        return measurements
        
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
