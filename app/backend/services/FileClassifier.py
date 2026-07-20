# determines the file type
class FileClassifier:

    # properties of the class
    UNIAXIAL_KEYWORDS = ["einax", "uniax"]
    TRIAXIAL_KEYWORDS = ["triax"]

    @staticmethod
    def classify(filename: str) -> str:

        # gets the filename in lower case to make comparison easier
        filename = filename.lower()

        # checks if the words are present in the file name
        for keyword in FileClassifier.UNIAXIAL_KEYWORDS:
            
            if keyword in filename:
                return "uniaxial"

        # checks if the words are present in the file name
        for keyword in FileClassifier.TRIAXIAL_KEYWORDS:
            if keyword in filename:
                return "triaxial"

        # if any of the keywords appeard in the file, then returns unknown
        return "unknown"