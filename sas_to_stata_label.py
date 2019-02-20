import os
import re
import xlrd

path = "/Users/renjiege/Documents/Data/NSCG/documentation/"
data_path = "/Users/renjiege/Documents/Data/NSCG/"
label_file = "PCG03.SAS"
var_file = "DPCG03.xls"
data_file = "public_2003.dta"
VAR = "NBAMEMG"
alph_num_dict = {'A': '-1', 'B': '-2', 'C': '-3',
                 'd': '-4', 'e': '-5', 'F': '-6',
                 'g': '-7', 'h': '-8', 'i': '-9',
                 'j': '-10', 'k': '-11', 'L': '-12',
                 'M': '-13', 'N': '-14', 'o': '-15',
                 'p': '-16', 'q': '-17', 'r': '-18', 's': '-19',
                 't': '-20', 'u': '-21', 'v': '-22',
                 'w': '-23', 'X': '-24', 'y': '-25', 'z': '-26',
                 'Not applicable': '-100', 'OTHER': '-101', '.': '-102'}

os.chdir(path)

def get_varlist_from_xls():
    book = xlrd.open_workbook(var_file)
    sheet = book.sheet_by_index(0)
    VARS = sheet.col_values(colx=0, start_rowx=1, end_rowx=sheet.nrows)
    return VARS

def write_into_file(command):
    with open(label_file[:-3] + "do", 'a') as do_file:
        do_file.writelines(command)

def get_label_define(i, VAR, value, label):
    if i == 1:
        command = "cap label define label_{0} {1} \"{2}\"\n".format(VAR.lower(), value, label)
    elif i > 1:
        command = "cap label define label_{0} {1} \"{2}\", add\n".format(VAR.lower(), value, label)
    return command

def write_label_commands(VAR):
    with open(path + label_file, "r") as file:
        text = file.readlines()
        for line, each in enumerate(text):
            if re.search("VALUE\s\$?" + VAR, each):
                i = 0
                while True:
                    i += 1
                    analysis = text[line + i]
                    value = re.search("=\s\"(.*):", analysis).group(1)
                    label = re.search(":\s(.*)\"", analysis).group(1)
                    if not value.isdigit():
                        value = alph_num_dict[value]
                    commands = get_label_define(i, VAR, value, label)
                    write_into_file(commands)
                    if not re.search("=\s\"(.*):", text[line + i + 1]):
                        write_into_file("cap label values %s label_%s\n" % (VAR.lower(), VAR.lower()))
                        break

def write_setup_commands():
    do_file = open(label_file[:-3] + "do", 'w')
    set_up = "clear\nset more off\ncd %s\nuse %s, clear\n" % (data_path, data_file)
    set_up += "ds*\nforeach var of varlist `r(varlist)\' {\n"
    for key, value in alph_num_dict.items():
        set_up += "cap replace `var\'=\"%s\" if `var\'==\"%s\"\n" % (value, key)
    set_up += "cap destring `var\', replace\n}\n"
    do_file.writelines(set_up)
    do_file.close()

def write_do_file():
    write_setup_commands()
    VARS = get_varlist_from_xls()
    for each in VARS:
        write_label_commands(each)
    write_into_file("save %s, replace\n" % data_file)


import slate
with open(label_file[:-3] + 'PDF') as f:
    doc = slate.PDF
    print(doc)

