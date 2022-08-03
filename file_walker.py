import os
import pandas as pd
import re
import collections as col




def extract_state_abbreviations(abbreviations) -> set[str]:
    answer = set()
    for word in abbreviations:
        out = []
        for letter in filter(lambda x: x.isalpha(), word):
            out.append(letter.upper())
        answer |= {''.join(out), }
    return answer


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


def find_campus(content: str) -> tuple[str, str]:
    out = col.deque([])
    for i in reversed(range(len(content))):
        if content[i] == '-':
            return content[:i].strip(' -'), content
    return content, content






directory = r'C:\dummy'
state_abbreviations = pd.read_csv(r'data_for_lookups/state_data.csv')
abbreviations = extract_state_abbreviations(state_abbreviations.Abbrev)
state_code_set = set(code.upper() for code in state_abbreviations.Code) | abbreviations


class apogeeFile:

    year_dir: str
    year: str
    project_dir: str
    function_dir: str
    additional_dirs: list
    is_project_file: bool
    apogee_project_number: str
    client: str
    campus = "Unknown"
    project_name: str
    state: str

    def __init__(self, apogee_file_path):
        self.path = apogee_file_path
        self.parse_file_path()
        # self.add_to_database()
        # if previous_file != None:
        #     self.other

    def parse_file_path(self):
        directories = self.path.split('\\')
        self.additional_dirs = []
        print(directories)
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
                print(self.state)
                self.apogee_project_number, remaining = find_project_number(remaining)
                print(self.apogee_project_number)
                print(remaining)
                self.client, remaining = find_client(remaining)
                print(self.client)
                print(remaining)
                self.project_name, remaining = find_project_name(remaining)
                self.campus, remaining = find_campus(remaining)
                print(self.campus)
                print(remaining)
            elif i == 4:
                self.function_dir = content
            else:
                self.additional_dirs.append(content)

    def add_to_database(self, data):
        file_data = [self.apogee_project_number, self.project_name, self.client, self.state, self.campus, self.path]
        for name, file_dat in zip(data, file_data):
            data[name].append(file_dat)



column_names = ['Apogee_Project_Number', 'Project_Name', 'Client', 'State', 'Facility', 'File_Path']
data = {name : [] for name in column_names}
for root, dirs, files in os.walk(directory):

    for filename in files:
        print(os.path.join(root, filename))
        this_one = apogeeFile(os.path.join(root, filename))
        this_one.add_to_database(data)

test_database = pd.DataFrame(data)
