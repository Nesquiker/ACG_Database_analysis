import subprocess as sp
import timeit as tt


def pdf_to_txt(target: str, save_as: str):
    exe_location = r'pdftotext'
    sp.run(f'{exe_location} "{target}" "{save_as}"', shell=True)


class ProjectSheets:

    path: str
    sheets_numbers: list[int]
    project_name: str
    building_identification: list[str]
    sheet_names: list[str]
    sheet_name_NCS: list[str]







def main():

    start = tt.default_timer()

    target = r"Stored_data\20-398 AVAHCS 65_ DD Dwgs_rot.pdf"
    test_name = 'tester'
    save_as = fr'Stored_data\drawing_sheet_text_files\{test_name}.txt'

    pdf_to_txt(target, save_as)

    end = tt.default_timer()

    print(end - start, " seconds")


if __name__ == "__main__":
    main()

