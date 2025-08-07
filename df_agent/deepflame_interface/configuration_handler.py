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

    def to_dict(self):
        return self.settings

class UnsupportedCaseTypeError(Exception):
    """Exception raised for unsupported case types."""
    pass

class CaseConfiguration:
    SUPPORTED_CASE_TYPES = {'1D_free_flame', '2D_HIT'}

    def __init__(self, case_type):
        if case_type not in self.SUPPORTED_CASE_TYPES:
            raise UnsupportedCaseTypeError(f"Unsupported case type: {case_type}")
        self.case_type = case_type
        self.set_fields_dict = SetFieldsDict()
        self.control_dict = ControlDict()

    def get_case_info(self):
        return {
            'case_type': self.case_type,
            'set_fields': self.set_fields_dict.to_dict(),
            'control_dict': self.control_dict.to_dict(),
        }

if __name__ == "__main__":
    # Create a configuration handler
    case_config_handler = {}

    # Add a case configuration
    case_name = 'case1'
    case_type = '2D_HIT'  # Supported case type

    try:
        case_config_handler[case_name] = CaseConfiguration(case_type)

        # Adding regions to the case
        circle = Circle(center=(0, 0), radius=5)
        box = Box(top_left=(1, 1), bottom_right=(4, 4))

        case_config_handler[case_name].set_fields_dict.add_region(circle)
        case_config_handler[case_name].set_fields_dict.add_region(box)

        # Set values in controlDict
        case_config_handler[case_name].control_dict.set_value('startTime', 0)
        case_config_handler[case_name].control_dict.set_value('endTime', 10)

        # Retrieve and print case information
        case_info = case_config_handler[case_name].get_case_info()
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