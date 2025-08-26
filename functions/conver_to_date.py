from datetime import datetime


def convert_date_format(date_str: str) -> str:
    """
    Convert a date string from 'YYYY-MM-DD HH:MM:SS.microseconds' to 'Mon DD, YY'.

    Args:
        date_str (str): Input date string (e.g., "2025-04-04 00:30:12.532000").

    Returns:
        str: Formatted date string (e.g., "Apr 04, 25").
    """
    try:
        # Handle potential year padding (e.g., "025" to "2025")
        if len(date_str.split("-")[0]) == 3:
            date_str = "20" + date_str
        # Parse the string
        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        # Format to desired output
        return date_obj.strftime("%b %d, %Y")
    except ValueError as e:
        return f"Invalid date format: {str(e)}"


def convert_date_format1(date_str: str) -> str:
    """
    Convert a date string from 'YYYY-MM-DD HH:MM:SS.microseconds'
    to 'Mon DD, YY HH:MM'.

    Args:
        date_str (str): Input date string
                        (e.g., "2025-08-16 22:20:01.843000").

    Returns:
        str: Formatted date string
             (e.g., "Aug 16, 25 22:20").
    """
    try:
        # Handle potential year padding (e.g., "025" → "2025")
        if len(date_str.split("-")[0]) == 3:
            date_str = "20" + date_str

        # Try parsing with microseconds
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            # Fallback: try without microseconds
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

        # Format to desired output with time
        return date_obj.strftime("%b %d, %y %H:%M")

    except ValueError as e:
        return f"Invalid date format: {str(e)}"
