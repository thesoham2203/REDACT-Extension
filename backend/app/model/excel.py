import os
import re
import pandas as pd


def redact_text(text, symbol="█"):
    """Redacts text with a given symbol."""
    return symbol * len(text)


def redact_line(line, redaction_scale, option):
    """Redacts sensitive information in a single line based on redaction scale."""
    # Patterns for sensitive information
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'  # IP addresses
    date_pattern = r'\b\d{4}-\d{2}-\d{2}\b'  # Dates
    time_pattern = r'\b\d{2}:\d{2}:\d{2}\b'  # Time
    protocol_pattern = r'\bTCP\b|\bUDP\b'  # Protocols
    hostname_pattern = r'\b[a-zA-Z0-9.-]+\.com\b'  # Hostnames


    # Define patterns and their corresponding redaction levels
    patterns = [
        (25, ip_pattern),
        (50, date_pattern),
        (50, time_pattern),
        (75, protocol_pattern),
        (100, hostname_pattern)
    ]


    # Apply redactions based on the redaction scale
    for threshold, pattern in patterns:
        if redaction_scale >= threshold:
            matches = re.finditer(pattern, line)
            for match in matches:
                redacted = redact_text(match.group()) if option.lower() != 'blur' else redact_text(match.group(), "-")
                line = line.replace(match.group(), redacted)


    return line


def redact_excel(input_file, output_file, redaction_scale, option):
    """Handles redaction for .xlsx files."""
    try:
        df = pd.read_excel(input_file)
       
        # Apply redaction row by row
        redacted_df = df.apply(
            lambda row: row.apply(
                lambda x: redact_line(str(x), redaction_scale, option) if isinstance(x, str) else x
            ),
            axis=1
        )


        # Save the redacted data to a new file
        redacted_df.to_excel(output_file, index=False)
        print(f"Redacted file saved as {output_file}")
    except Exception as e:
        print(f"Error processing file: {e}")


def main():
    while True:
        input_file = input("Enter the path of the input file (.xlsx): ")
        if not os.path.exists(input_file):
            print(f"File '{input_file}' does not exist. Please enter a valid file path.")
        else:
            break


    output_file = input("Enter the path for the redacted output file (.xlsx): ")
    redaction_scale = int(input("Enter the redaction scale (25, 50, 75, 100): "))
    option = input("Enter the redaction option (blackout/blur): ")


    if redaction_scale not in [25, 50, 75, 100]:
        print("Invalid redaction scale. Please enter 25, 50, 75, or 100.")
        return


    if option.lower() not in ['blackout', 'blur']:
        print("Invalid option. Please enter 'blackout' or 'blur'.")
        return


    redact_excel(input_file, output_file, redaction_scale, option)


if __name__ == "__main__":
    main()