# =====================================================
# main.py
#
# Entry point for the Bodenverformung project.
#
# Responsibilities:
#   1. Define the database location
#   2. Create the database file (if it does not exist)
#   3. Create all required tables
# =====================================================

# Imports required libraries
from database.database import *

# defines the main function of the application
def main() -> None:
    """
    Main application entry point.
    """

    # creates database according to the defined schema.
    Schema()



# runs when executed
if __name__ == "__main__":
    main()