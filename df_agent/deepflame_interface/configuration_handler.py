class Region:
    def __init__(self, region_type):
        self.region_type = region_type

class Circle(Region):
    def __init__(self, center, radius):
        super().__init__('circle')
        self.center = center
        self.radius = radius

    def properties(self):
        return {
            'type': self.region_type,
            'center': self.center,
            'radius': self.radius
        }

class Box(Region):
    def __init__(self, top_left, bottom_right):
        super().__init__('box')
        self.top_left = top_left
        self.bottom_right = bottom_right

    def properties(self):
        return {
            'type': self.region_type,
            'top_left': self.top_left,
            'bottom_right': self.bottom_right
        }

class DictConfiguration:
    def __init__(self):
        self.settings = {}

    def set_value(self, key, value):
        self.settings[key] = value

    def get_value(self, key):
        return self.settings.get(key)

    def delete_value(self, key):
        if key in self.settings:
            del self.settings[key]

    def to_dict(self):
        return self.settings

class FuelConfig(DictConfiguration):
    def __init__(self):
        super().__init__()
        self.settings = {
            "fuel": "H2",
            "equiv_ratio": 1,
            "temperature": 600,
            "pressure": 1,
        }

class BlockMeshDict(DictConfiguration):
    def __init__(self):
        super().__init__()
        self.settings = {
            "cells_per_direction": [1024, 1024],
            "domain_size": [0.05, 0.05],
        }

class SetFieldsDict(DictConfiguration):
    def __init__(self):
        super().__init__()
        self.regions = []

    def add_region(self, region):
        self.regions.append(region)

    def get_regions(self):
        return [region.properties() for region in self.regions]

    def to_dict(self):
        return {
            'regions': self.get_regions(),
            **self.settings
        }

class ControlDict(DictConfiguration):
    def __init__(self):
        super().__init__()
        self.settings = {
            "endTime": 0.0003,
            "deltaT": 1e-6,
            "writeInterval": 1e-5,
        }

    def to_dict(self):
        return self.settings

class UnsupportedCaseTypeError(Exception):
    """Exception raised for unsupported case types."""
    pass

class CaseConfiguration:
    SUPPORTED_CASE_TYPES = {'1D_free_flame', '2D_HIT'}

    def __init__(self, case_type, config_data=None):
        if case_type not in self.SUPPORTED_CASE_TYPES:
            raise UnsupportedCaseTypeError(f"Unsupported case type: {case_type}")
        
        if case_type == '1D_free_flame':
            raise NotImplementedError("The case type '1D_free_flame' is not implemented.")

        if case_type == '2D_HIT':
            self.case_type = case_type
            self.fuel_config = FuelConfig()
            self.block_mesh_dict = BlockMeshDict()
            self.set_fields_dict = SetFieldsDict()
            self.control_dict = ControlDict()

            # If config_data is provided, you can initialize set_fields_dict and control_dict
            if config_data:
                self._initialize_from_dict(config_data)

    def _initialize_from_dict(self, config_data):
        """Initializes the CaseConfiguration from a provided dictionary."""
        if 'setFields' in config_data:
            for region in config_data['setFields']:
                region_type = region.get('type')
                if region_type == 'circle':
                    circle = Circle(center=region['center'], radius=region['radius'])
                    self.set_fields_dict.add_region(circle)
                elif region_type == 'box':
                    box = Box(top_left=region['top_left'], bottom_right=region['bottom_right'])
                    self.set_fields_dict.add_region(box)

        if 'controlDict' in config_data:
            for key, value in config_data['controlDict'].items():
                self.control_dict.set_value(key, value)

    def to_dict(self):
        """Converts the CaseConfiguration to a dictionary format."""
        return {
            'fuel': self.fuel_config.to_dict(),
            'blockMeshDict': self.block_mesh_dict.to_dict(),
            'setFieldsDict': self.set_fields_dict.to_dict(),
            'controlDict': self.control_dict.to_dict(),
        }

if __name__ == "__main__":
    # Create a configuration handler
    case_config_handler = {}

    # Define configuration data
    config_data = {
        'setFields': [
            {'type': 'circle', 'center': (0, 0), 'radius': 5},
            {'type': 'box', 'top_left': (1, 1), 'bottom_right': (4, 4)}
        ],
        'controlDict': {
            'startTime': 0,
            'endTime': 10
        }
    }

    # Add a case configuration
    case_name = 'case1'
    case_type = '2D_HIT'  # Supported case type

    try:
        case_config_handler[case_name] = CaseConfiguration(case_type, config_data)

        # Retrieve and print case information
        case_info = case_config_handler[case_name].to_dict()
        print("Case Configuration Info:")
        print(case_info)

    except UnsupportedCaseTypeError as e:
        print(e)

    # Example of trying an unsupported case type
    try:
        unsupported_case_name = 'case2'
        unsupported_case_type = '3D_FLOW'  # Unsupported case type
        case_config_handler[unsupported_case_name] = CaseConfiguration(unsupported_case_type)
    except UnsupportedCaseTypeError as e:
        print(e)