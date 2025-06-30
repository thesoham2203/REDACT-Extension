import os
import re
import pandas as pd

class FileRedactor:
    def __init__(self):
        # Define patterns for sensitive information and their corresponding redaction thresholds
        self.redaction_map = {
            25: [(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', "IP")],
            50: [(r'\b\d{4}-\d{2}-\d{2}\b', "DATE"), (r'\b\d{2}:\d{2}:\d{2}\b', "TIME")],
            75: [(r'\bTCP\b|\bUDP\b', "PROTOCOL")],
            100: [(r'\b[a-zA-Z0-9.-]+\\.com\b', "HOSTNAME")]
        }

    def redact_text(self, text, symbol="█"):
        """Redacts text with a given symbol."""
        return symbol * len(text)

    def redact_line(self, line, redaction_scale, option):
        """Redacts sensitive information in a single line based on the redaction scale."""
        for threshold, patterns in self.redaction_map.items():
            if redaction_scale >= threshold:
                for pattern, label in patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        redacted = (
                            self.redact_text(match.group()) if option.lower() != 'blur' else self.redact_text(match.group(), "-")
                        )
                        line = line.replace(match.group(), redacted)
        return line

    def redact_file(self, input_file, output_file, redaction_scale, option):
        """Handles file redaction for .txt, .csv, and .xlsx formats."""
        file_extension = input_file.split('.')[-1].lower()

        if file_extension == 'txt':
            with open(input_file, 'r') as f:
                lines = f.readlines()

            redacted_lines = [self.redact_line(line.strip(), redaction_scale, option) for line in lines]

            with open(output_file, 'w') as f:
                for redacted_line in redacted_lines:
                    f.write(redacted_line + '\n')

        elif file_extension == 'csv':
            df = pd.read_csv(input_file)
            redacted_df = df.apply(
                lambda row: row.apply(
                    lambda x: self.redact_line(str(x), redaction_scale, option) if isinstance(x, str) else x
                ),
                axis=1
            )
            redacted_df.to_csv(output_file, index=False)

        elif file_extension == 'xlsx':
            df = pd.read_excel(input_file)
            redacted_df = df.apply(
                lambda row: row.apply(
                    lambda x: self.redact_line(str(x), redaction_scale, option) if isinstance(x, str) else x
                ),
                axis=1
            )
            redacted_df.to_excel(output_file, index=False)

        else:
            print(f"Unsupported file format: {file_extension}")
            return

        print(f"Redacted file saved as {output_file}")

    def process_redaction(self, input_file, output_file, redaction_scale, option):
        """Wrapper method to validate inputs and execute redaction."""
        if not os.path.exists(input_file):
            print(f"File '{input_file}' does not exist. Please provide a valid file path.")
            return

        if redaction_scale not in [25, 50, 75, 100]:
            print("Invalid redaction scale. Please enter 25, 50, 75, or 100.")
            return

        if option.lower() not in ['blackout', 'blur']:
            print("Invalid option. Please enter 'blackout' or 'blur'.")
            return

        self.redact_file(input_file, output_file, redaction_scale, option)

