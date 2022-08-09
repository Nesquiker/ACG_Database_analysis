import subprocess as sp
import timeit as tt
import collections as col
import re
import pandas as pd


def pdf_to_txt(target: str, save_as: str):
    exe_location = r'pdftotext'
    sp.run(f'{exe_location} "{target}" "{save_as}"', shell=True)


class ProjectSheets:

    val_to_column = {}
    search_end_key = 'Set Unknown'
    default_val = 'Unknown'
    project_directory = default_val
    project_name = default_val
    location_name = default_val
    acg_project_number = default_val
    va_project_number = default_val
    sheet_development_level = default_val
    building_identifications = col.deque([])
    sheet_titles = col.deque([])
    sheet_names = col.deque([])
    sheets_numbers = col.deque([])
    drawn_by = col.deque([])
    checked_by = col.deque([])

    def __init__(self, root_pdf_path: str, sheet_in_text_path: str, save_path: str):
        self.root_path = root_pdf_path
        self.text_data = open(sheet_in_text_path, 'r')
        self.mine_acg_project_data()
        self.map_val_to_column()
        self.save_data(save_path)

    def save_data(self, save_path: str):
        data = {name: [] for name in self.val_to_column}
        while self.sheets_numbers:
            for name in self.val_to_column:
                if type(self.val_to_column[name]) is str:
                    data[name].append(self.val_to_column[name])
                else:
                    data[name].append(self.val_to_column[name].popleft())

        pd.DataFrame(data).to_pickle(save_path)

    def map_val_to_column(self):

        self.val_to_column = {
            'Base_PDF_path': self.root_path,
            'Project_Name': self.project_name,
            'Facility_Address': self.location_name,
            'ACG_Project_Number': self.acg_project_number,
            'VA_Project_Number': self.va_project_number,
            'Sheet_Development_Level': self.sheet_development_level,
            'Drawing_Title': self.sheet_titles,
            'Building_Numbers/Letters': self.building_identifications,
            'NCS_Building_Designation': self.sheet_names,
            'Drawing_#_of_#': self.sheets_numbers,
            'Drawn_By': self.drawn_by,
            'Checked_By': self.checked_by
        }

    def mine_acg_project_data(self):

        # These queries happen only once and are then exhausted. These points are only needed to be found once as they
        # are true for the entire file.
        query_stack_functions = {
                    'Project Number': self.find_acg_project_number,
                    'Location': self.find_location_address,
                    ' ': self.find_sheet_development_level,
                    'Project Title': self.find_project_name,
                    'VA PROJECT NUMBER': self.find_va_project_number
                    }

        # These queries are made for every sheet in the set. These queries also occur in the order shown below.
        query_loop_functions = {
                    'Drawing Title': self.find_sheet_title,
                    'Checked': self.find_checked_initials,
                    'Drawn': self.find_drawn_initials,
                    'Building Number': self.find_building_number,
                    'Drawing Number': self.find_drawing_tag,
                    'Dwg.': self.find_drawing_number
                    }

        current_line = self.text_data.readline()
        current_loop_search = col.deque(list(query_loop_functions))
        current_stack_search = list(reversed(query_stack_functions))

        is_found = True
        while current_line:

            # If the last function ran has not yet recorded a value after being called the program will continue to
            # look for a value until it has been found or another property indicator has been found in which case
            # the current property will be set to 'Unknown'.
            if not is_found:
                is_found = cached_function[0](current_line)
                if is_found:
                    current_line = self.text_data.readline()
                    continue

            if current_stack_search and current_stack_search[-1] in current_line:

                # Set unknown if the last cached function never found a recognized property.
                if not is_found:
                    cached_function[0](self.search_end_key)
                current_search = current_stack_search.pop()
                is_found = query_stack_functions[current_search](current_line)
                if not is_found:
                    cached_function = [query_stack_functions[current_search]]

            elif current_loop_search[0] in current_line:

                if not is_found:
                    cached_function[0](self.search_end_key)

                is_found = query_loop_functions[current_loop_search[0]](current_line)

                if not is_found:
                    cached_function = [query_loop_functions[current_loop_search[0]]]

                current_loop_search.rotate(-1)

            current_line = self.text_data.readline()

        self.text_data.close()

    def find_acg_project_number(self, line: str) -> bool:
        if line == self.search_end_key:
            return True
        # ACG project number XX-XXX where X is digit from 1-9.
        acg_number_pattern = re.compile('\d{2}-\d{3}')

        match = re.search(acg_number_pattern, line)
        if match:
            self.acg_project_number = match.group()

        return match is not None

    def find_location_address(self, line: str) -> bool:
        if line == self.search_end_key:
            return True

        is_location = (line.isupper() and len(line) > 2)

        if is_location:
            self.location_name = line.strip('\n')

        return is_location

    def find_sheet_development_level(self, line: str) -> bool:
        if line == self.search_end_key:
            return True

        if not re.search('[A-Z]+', line) or 'FULLY SPRINKLERED' in line:
            return False
        else:
            self.sheet_development_level = line.strip('\n')
            return True

    def find_project_name(self, line: str) -> bool:
        if line == self.search_end_key:
            return True

        # The project name may happen over several lines will need to keep updating until a true is reached.
        if not line.isupper() and self.project_name == self.default_val:
            return False
        elif line.isupper():
            self.project_name = line.strip('\n') if self.project_name == self.default_val \
                                else ' '.join([self.project_name, line.strip('\n')])
            return False
        else:
            return True

    def find_va_project_number(self, line:str) -> bool:
        if line == self.search_end_key:
            return True

        # VA project number XXX-XX-XXX where X is digit from 0-9.
        va_number_pattern = re.compile("\d{3}-\d{2}-\d{3}")

        match = re.search(va_number_pattern, line)
        if match:
            self.va_project_number = match.group()

        return match is not None

    def find_sheet_title(self, line: str) -> bool:
        if line == self.search_end_key:
            self.sheet_titles.append(self.default_val)
            return True

        if line.isupper() and len(line) > 3:
            self.sheet_titles.append(line.strip('\n'))
            return True
        else:
            return False

    def find_checked_initials(self, line: str) -> bool:
        if line == self.search_end_key:
            self.checked_by.append(self.default_val)
            return True

        checked_pattern = re.compile('[A-Z]{2,3}')
        match = re.search(checked_pattern, line)
        if match:
            self.checked_by.append(match.group())

        return match is not None

    def find_drawn_initials(self, line: str) -> bool:
        if line == self.search_end_key:
            self.drawn_by.append(self.default_val)
            return True

        checked_pattern = re.compile('[A-Z]{2,3}')
        match = re.search(checked_pattern, line)
        if match:
            self.drawn_by.append(match.group())

        return match is not None

    def find_building_number(self, line: str) -> bool:
        if line == self.search_end_key:
            self.building_identifications.append(self.default_val)
            return True
        pattern = re.compile('#')
        match = re.search(pattern, line)
        if match or len(line) < 2 or "Drawing Number" in line or "Building Number" in line:
            return False
        else:
            self.building_identifications.append(line.strip('\n'))
            return True

    def find_drawing_tag(self, line: str) -> bool:
        if line == self.search_end_key:
            self.sheet_names.append(self.default_val)
            return True
        pattern = re.compile('\d{3}')
        match = re.search(pattern, line)
        if match:
            self.sheet_names.append(line.strip('\n'))
            return True
        else:
            return False

    def find_drawing_number(self, line: str) -> bool:
        if line == self.search_end_key:
            self.sheets_numbers.append(self.default_val)
            return True
        start = len(line)
        for i, char in enumerate(line):
            if char == '.':
                start = i + 1
                break

        out = line[start:]
        if out:
            self.sheets_numbers.append(line[start:].strip('\n'))
            return True
        else:
            return False


def main():

    start = tt.default_timer()

    target = r"Stored_data/20-393 DWGs.pdf"
    test_name = 'tester'
    save_text_as = fr'Stored_data\drawing_sheet_text_files\{test_name}.txt'

    pdf_to_txt(target, save_text_as)

    save_pickle_as = fr'Stored_data\sheet_databases\{test_name}.pickle'
    ProjectSheets(target, save_text_as, save_pickle_as)



    end = tt.default_timer()

    print(end - start, " seconds")


if __name__ == "__main__":
    main()
    for_test = pd.read_pickle(r'Stored_data/sheet_databases/tester.pickle')
