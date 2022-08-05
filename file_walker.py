import collections as col
import os
import pandas as pd

COLUMN_NAMES = ['apogee_project_number',
                'project_name',
                'client',
                'state',
                'facility',
                'major_sub_directory',
                'file_path',
                'file_name',
                'file_type']

IGNORED_FILE_TYPES = {'.bak',
                      '.rws',
                      '.slog',
                      '.dat',
                      '.db'}


def _create_empty_data():
    return {name: [] for name in COLUMN_NAMES}


def _create_state_codes(path_to_state_data: str) -> set[str]:
    state_abbreviations = pd.read_csv(path_to_state_data)
    abbreviations = _extract_state_abbreviations(state_abbreviations.Abbrev)
    return set(code.upper() for code in state_abbreviations.Code) | abbreviations | {'US', 'SS'}


def _extract_state_abbreviations(abbreviations) -> set[str]:
    answer = set()
    for word in abbreviations:
        out = []
        for letter in filter(lambda x: x.isalpha(), word):
            out.append(letter.upper())
        answer |= {''.join(out), }
    return answer


_STATE_CODE_SET = _create_state_codes(r'data_for_lookups/state_data.csv')


def _find_year(year_dir):
    year = year_dir[:4]
    if year.isdigit() and len(year) == 4:
        return year
    else:
        return "Unknown"


def _find_location(content: str) -> tuple[str, str]:
    out = col.deque([])
    count = 0
    for i, letter in enumerate(content[::-1]):
        if letter.isalpha():
            out.appendleft(letter.upper())
            count += 1

        else:
            state = ''.join(out)
            if state not in _STATE_CODE_SET:
                return 'Unknown', content
            return state, content[:-i - 1]


def _find_project_number(content: str) -> tuple[str, str, int]:
    out = []
    digit_count = 0
    for i, char in enumerate(content):
        if char.isalpha():
            if char != 'Q' or not content[i + 1].isdigit():
                break

        digit_count += 1
        out.append(char)
    out = ''.join(out).strip(' -')
    return out, content[i:], digit_count


def _find_client(content: str) -> tuple[str, str]:
    out = []
    for i, letter in enumerate(content):
        if not letter.isalpha():
            break
        out.append(letter)
    content = content[i:].strip('- ')
    return ''.join(out), content


def _find_project_name(content: str) -> tuple[str, str]:
    return content, content


def _find_facility(content: str) -> tuple[str, str]:
    out = col.deque([])
    for i in reversed(range(len(content))):
        if content[i] == '-':
            return content[:i].strip(' -'), content
    return "Unknown", content


def _find_file_type(content: str) -> tuple[str, str, bool]:
    out = col.deque([])
    for i in reversed(range(len(content))):

        if content[i] == '.':
            break
    file_type = content[i:]
    ignore = False
    if file_type in IGNORED_FILE_TYPES:
        ignore = True
    return file_type, content[:i], ignore


class __ApogeeFile:
    """
    ApogeeFile is meant to take a file path from the Apogee project file database and apply labels to help
    describe the file. If the file is in a project folder and it is not considered clutter as determined by
    the ignore file types set then the file is parsed and saved to a data file.
    This can then be used to do advanced queries of the Apogee database using the labels.
    """

    # Initializing default values for file labels.
    default_val = "Unknown"
    year_dir = default_val
    year = default_val
    project_dir = default_val
    function_dir = default_val
    additional_dirs = default_val
    apogee_project_number = default_val
    client = default_val
    facility = default_val
    project_name = default_val
    state = default_val
    file_name = default_val
    ignore_token = False
    val_to_column = {}
    file_type = default_val

    def __init__(self, apogee_file_path, data):
        self.path = apogee_file_path

        # Fills all applicable file labels (project label, client, etc...).
        self.parse_file_path()

        # Do not continue if the file does not appear to be a project file of acceptable type.
        # This program will attempt to ignore certain files and types in order to reduce clutter.
        if not self.ignore_token:
            self.map_val_to_column()
            self.add_file_to_data(data)

    def map_val_to_column(self):
        # If the order / number of COLUMN_NAMES global variables is changed the mapping below will need to be altered.
        column_attributes = [self.apogee_project_number,
                             self.project_name,
                             self.client,
                             self.state,
                             self.facility,
                             self.function_dir,
                             self.path,
                             self.file_name,
                             self.file_type]

        for name, val in zip(COLUMN_NAMES, column_attributes):
            self.val_to_column[name] = val

    def parse_file_path(self):
        directories = self.path.split('\\')

        size = len(directories)

        # Do not store data if it is not data associated with a project. Here we check if the
        # file has a number of directories that is typical of project files. This also helps to
        # protect from index errors.
        if size < 6:
            self.ignore_token = True
            return

        # Begin File Name analysis
        self.file_name = directories[-1]

        self.file_type, remaining_name, self.ignore_token = _find_file_type(self.file_name)

        # find_file_type checks if the file type is in the ignore file type set.
        if self.ignore_token:
            return

        # Begin year directory analysis
        self.year_dir = directories[2]
        self.year = _find_year(self.year_dir)

        # Begin project directory analysis
        self.project_dir = directories[3]
        remaining = self.project_dir.strip()
        self.state, remaining = _find_location(remaining)

        self.apogee_project_number, remaining, digit_count = _find_project_number(remaining)

        # Do not store data if it is not data associated with a project. Here we check if the
        # project number has a reasonable number of digits for an apogee project number.
        # Projects before 2015 will have 7-digit dates instead of project numbers.
        if digit_count < 5:
            self.ignore_token = True
            return

        self.client, remaining = _find_client(remaining)

        self.project_name, remaining = _find_project_name(remaining)

        self.facility, remaining = _find_facility(remaining)

        # Begin additional directory analysis
        self.function_dir = directories[4]
        if size - 1 > 5:
            self.additional_dirs = directories[5:size - 1]

    def add_file_to_data(self, data):
        for column in COLUMN_NAMES:
            data[column].append(self.val_to_column[column])


def scan_directory(directory: str) -> pd.DataFrame:
    # This is the interface for this file. The user queries a directory
    # and receives a dataframe of labelled file_paths.

    data = _create_empty_data()

    for root, dirs, files in os.walk(directory):
        for filename in files:
            __ApogeeFile(os.path.join(root, filename), data)

    return pd.DataFrame(data)


def _read_test_pickle():
    return pd.read_pickle('Stored_data/test_dataframe.pickle')


def _main():
    directory = r'C:\dummy'
    test_database = scan_directory(directory)
    return test_database


if __name__ == "__main__":
    test = _main()
