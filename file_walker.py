import os
import pandas as pd
import re
import collections as col


COLUMN_NAMES = ['apogee_project_number', 'project_name', 'client', 'state', 'facility', 'file_path']
DATA = {name: [] for name in COLUMN_NAMES}


def find_year(year_dir):
    year = year_dir[:4]
    if year.isdigit():
        pass
    else:
        year = "Unknown"
    return year


def find_location(content: str) -> tuple[str, str]:
    out = col.deque([])
    count = 0
    for i, letter in enumerate(content[::-1]):
        if letter.isalpha():
            out.appendleft(letter.upper())
            count += 1

        else:
            state = ''.join(out)
            if state not in state_code_set:
                return 'Unknown', content
            return state, content[:-i - 1]


def find_project_number(content: str) -> tuple[str, str]:
    out = []
    for i, char in enumerate(content):
        if char.isalpha():
            if char == 'Q' and content[i + 1].isdigit():
                pass
            else:
                break
        out.append(char)
    out = ''.join(out).strip(' -')
    return out, content[i:]


def find_client(content: str) -> tuple[str, str]:
    out = []
    for i, letter in enumerate(content):
        if not letter.isalpha():
            break
        out.append(letter)
    content = content[i:].strip('- ')
    return ''.join(out), content


def find_project_name(content: str) -> tuple[str, str]:
    return content, content


def find_facility(content: str) -> tuple[str, str]:
    out = col.deque([])
    for i in reversed(range(len(content))):
        if content[i] == '-':
            return content[:i].strip(' -'), content
    return content, content


def create_temp_map() -> dict[str]:
    return {name: 'Unknown' for name in COLUMN_NAMES}


def create_state_codes(path_to_state_data: str) -> set[str]:
    state_abbreviations = pd.read_csv(path_to_state_data)
    abbreviations = extract_state_abbreviations(state_abbreviations.Abbrev)
    return set(code.upper() for code in state_abbreviations.Code) | abbreviations


def extract_state_abbreviations(abbreviations) -> set[str]:
    answer = set()
    for word in abbreviations:
        out = []
        for letter in filter(lambda x: x.isalpha(), word):
            out.append(letter.upper())
        answer |= {''.join(out), }
    return answer


state_code_set = create_state_codes(r'data_for_lookups/state_data.csv')


class apogeeFile:

    year_dir: str
    year: str
    project_dir: str
    function_dir: str
    additional_dirs: list
    is_project_file: bool
    apogee_project_number: str
    client: str
    facility: str
    project_name: str
    state: str
    temp_map: dict

    def __init__(self, apogee_file_path):
        self.path = apogee_file_path
        self.temp_map = create_temp_map()
        self.parse_file_path()


    def parse_file_path(self):
        directories = self.path.split('\\')
        self.additional_dirs = []
        print(self.temp_map)
        self.temp_map[COLUMN_NAMES[5]] = self.path
        for i, content in enumerate(directories):
            if i < 2:
                pass
            elif i == 2:
                self.year_dir = content
                self.year = find_year(content)

            elif i == 3:
                self.project_dir = content
                remaining = content.strip()

                self.state, remaining = find_location(remaining)
                self.temp_map[COLUMN_NAMES[3]] = self.state
                self.apogee_project_number, remaining = find_project_number(remaining)
                self.temp_map[COLUMN_NAMES[0]] = self.apogee_project_number
                self.client, remaining = find_client(remaining)
                self.temp_map[COLUMN_NAMES[2]] = self.client
                self.project_name, remaining = find_project_name(remaining)
                self.temp_map[COLUMN_NAMES[1]] = self.project_name
                self.facility, remaining = find_facility(remaining)
                self.temp_map[COLUMN_NAMES[4]] = self.facility
            elif i == 4:
                self.function_dir = content
            else:
                self.additional_dirs.append(content)

    def add_file_to_data(self):
        for column in self.temp_map:
            DATA[column].append(self.temp_map[column])


directory = r'C:\dummy'
for root, dirs, files in os.walk(directory):

    for filename in files:
        print(os.path.join(root, filename))
        this_one = apogeeFile(os.path.join(root, filename))
        this_one.add_file_to_data()

test_database = pd.DataFrame(DATA)
