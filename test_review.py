def calculate_total(items):
    """Calculate the sum of all items in the given list.

    Args:
        items (list): List of numbers to sum

    Returns:
        float: The total sum of all items
    """
    total = 0
    for item in items:
        total += item
    return total


class DataTransformer:
    """A class for transforming and validating data.

    This class provides methods for processing numerical data and validating input formats.
    """

    def process_data(self, data):
        """Process the input data by doubling positive values.

        Args:
            data (list): List of numbers to process

        Returns:
            list: List containing doubled values for positive numbers
        """
        result = []
        for item in data:
            if item > 0:
                result.append(item * 2)
        return result

    def validate_input(self, input_data):
        """Validate that the input data is a list.

        Args:
            input_data: The data to validate

        Returns:
            bool: True if input is a list

        Raises:
            ValueError: If input is not a list
        """
        if not isinstance(input_data, list):
            raise ValueError("Input must be a list")
        return True
