import subprocess as sp
import timeit as tt
import collections as col
import re


def pdf_to_txt(target: str, save_as: str):
    exe_location = r'pdftotext'
    sp.run(f'{exe_location} "{target}" "{save_as}"', shell=True)




class ProjectSheets:

    default_val = 'Unknown'
    project_directory = default_val
    project_name = default_val
    location_name = default_val
    acg_project_number = default_val
    va_project_number = default_val
    sheet_development_level = default_val
    building_identifications: list[list[int]]
    sheet_titles: list[str]
    sheet_names: list[str]
    sheets_numbers: list[int]
    drawn_by: list[str]
    checked_by: list[str]



    def __init__(self, sheet_in_text_path: str):



        self.text_data = open(sheet_in_text_path, 'r')
        self.mine_project_data()


    def mine_project_data(self):

        # These queries happen only once and are then exhausted. These points are only needed to be found once as they
        # are true for the entire file.
        query_stack_functions = {'ACG Project Number': self.find_acg_project_number,
                       'Location': self.find_location_address,
                       '%': self.find_sheet_development_level,
                       'Project Title': self.find_project_name,
                       'VA Project Number': self.find_va_project_number
                       }

        #These queries are made for every sheet in the set. These queries also occur in the order shown below.
        query_loop_functions = {'Drawing Title': self.find_sheet_title,
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

            if not is_found:
                is_found = cached_function[0](current_line)

            if current_stack_search and current_stack_search[-1] in current_line:

                if not is_found:
                    cached_function[0]('Set Unknown')

                is_found = query_stack_functions[current_stack_search.pop()](current_line)
                if not is_found:
                    cached_function = [query_stack_functions[current_stack_search.pop()]]

            if current_loop_search[0] in current_line:

                if not is_found:
                    cached_function[0]('Set Unknown')

                is_found = query_loop_functions[current_loop_search[0]](current_line)
                current_loop_search.rotate(-1)
                if not is_found:
                    cached_function = [query_stack_functions[current_stack_search.pop()]]

            current_line = self.text_data.readline()

        self.text_data.close()


    def find_sheet_title(self, line: str) -> bool:

    def find_checked_initials(self, line: str) -> bool:





def main():

    start = tt.default_timer()

    target = r"Stored_data\20-398 AVAHCS 65_ DD Dwgs_rot.pdf"
    test_name = 'tester'
    save_as = fr'Stored_data\drawing_sheet_text_files\{test_name}.txt'

    pdf_to_txt(target, save_as)

    ProjectSheets(save_as)



    end = tt.default_timer()

    print(end - start, " seconds")


if __name__ == "__main__":
    main()

