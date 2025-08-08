# tools/__init__.py

"""
This file makes the 'tools' directory a Python package, allowing for easy
import of all the custom-built OpenFOAM agent tools.
"""

from .setup_case_directory import setup_case_directory
from .check_case_completeness import check_case_completeness
from .visualize_blockmesh import visualize_blockmesh
from .edit_controlDict import edit_controlDict
from .edit_blockMeshDict import edit_blockMeshDict
from .edit_fvSchemes import edit_fvSchemes
from .edit_fvSolution import edit_fvSolution
from .edit_physical_properties import edit_physical_properties
from .knowledge_placement import query_chemkinetics, place_constant_file
from .create_initial_field_from_template import create_initial_field_from_template

# The __all__ variable defines the public API of this package.
# When a user writes 'from tools import *', only these names will be imported.
__all__ = [
    "setup_case_directory",
    "check_case_completeness",
    "visualize_blockmesh",
    "edit_controlDict",
    "edit_blockMeshDict",
    "edit_fvSchemes",
    "edit_fvSolution",
    "edit_physical_properties",
    "query_chemkinetics",
    "place_constant_file",
    "create_initial_field_from_template",
]

