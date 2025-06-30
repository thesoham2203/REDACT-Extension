#csv run 97%
import os
import re
import pandas as pd


def redact_text(text, symbol="█"):
    """Redacts text with a given symbol."""
    return symbol * len(text)


def redact_line(line, redaction_scale, option):
    """Redacts sensitive information in a single line based on redaction scale."""
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    date_pattern = r'\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}[A-Za-z]+\d{2}\b'
    time_pattern = r'\b\d{2}:\d{2}:\d{2}\b'
    relay_pattern = r'relay=.*?@.*? '


    patterns = [
        (25, ip_pattern),
        (50, date_pattern),
        (75, time_pattern),
        (100, relay_pattern)
    ]


    for threshold, pattern in patterns:
        if redaction_scale >= threshold:
            matches = re.finditer(pattern, line)
            for match in matches:
                redacted = redact_text(match.group()) if option.lower() != 'blur' else redact_text(match.group(), "-")
                line = line.replace(match.group(), redacted)


    return line


def redact_file(input_file, output_file, redaction_scale, option):
    """Handles file redaction for .txt, .csv, .xlsx, and .11 formats."""
    file_extension = input_file.split('.')[-1].lower()


    if file_extension in ['txt', '11']:
        with open(input_file, 'r') as f:
            lines = f.readlines()


        redacted_lines = [redact_line(line.strip(), redaction_scale, option) for line in lines]


        with open(output_file, 'w') as f:
            for redacted_line in redacted_lines:
                f.write(redacted_line + '\n')


    elif file_extension == 'csv':
        df = pd.read_csv(input_file)
        redacted_df = df.apply(lambda row: row.apply(lambda x: redact_line(str(x), redaction_scale, option) if isinstance(x, str) else x), axis=1)
        redacted_df.to_csv(output_file, index=False)


    elif file_extension == 'xlsx':
        df = pd.read_excel(input_file)
        redacted_df = df.apply(lambda row: row.apply(lambda x: redact_line(str(x), redaction_scale, option) if isinstance(x, str) else x), axis=1)
        redacted_df.to_excel(output_file, index=False)


    else:
        print(f"Unsupported file format: {file_extension}")
        return


    print(f"Redacted file saved as {output_file}")


def main():
    while True:
        input_file = input("Enter the path of the input file (.txt, .csv, .xlsx, .11): ")
        if not os.path.exists(input_file):
            print(f"File '{input_file}' does not exist. Please enter a valid file path.")
        else:
            break


    output_file = input("Enter the path for the redacted output file: ")
    redaction_scale = int(input("Enter the redaction scale (25, 50, 75, 100): "))
    option = input("Enter the redaction option (blackout/blur): ")


    if redaction_scale not in [25, 50, 75, 100]:
        print("Invalid redaction scale. Please enter 25, 50, 75, or 100.")
        return


    if option.lower() not in ['blackout', 'blur']:
        print("Invalid option. Please enter 'blackout' or 'blur'.")
        return


    redact_file(input_file, output_file, redaction_scale, option)


if __name__ == "__main__":
    main()