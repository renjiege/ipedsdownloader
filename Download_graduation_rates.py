from zipfile import ZipFile
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from random import uniform
import time
from selenium.common.exceptions import NoSuchElementException
import re
import os
from urllib.request import urlopen
import json

start_page = "http://nces.ed.gov/ipeds/datacenter/login.aspx?gotoReportId=7"
data_path = "/Users/renjiege/Documents/Data/IPEDS/"
survey_name = "Graduation Rates"
initials = "GR"
start_year = 1997
end_year = 2015

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")
driver = webdriver.Chrome(chrome_options=chrome_options)

# def get_list_years():
#     select = Select(driver.find_element_by_id('contentPlaceHolder_ddlYears'))
#     years = list()
#     for option in select.options:
#         years.append(option.get_attribute('value'))
#     return years

def enter_1st_page():
    driver.get(start_page)
    driver.find_element_by_xpath("//input[@id='ImageButton1' and @title='Continue']").click()

def query(year, survey):
    Select(driver.find_element_by_id('ddlSurveys')).select_by_visible_text(survey)
    Select(driver.find_element_by_id('contentPlaceHolder_ddlYears')).select_by_value(str(year))
    driver.find_element_by_xpath("//input[@id='contentPlaceHolder_ibtnContinue']").click()

def get_data_url():
    data_links = driver.find_elements_by_css_selector("tbody > tr > td:nth-of-type(5) > a")  # all links in column 5
    row = 0  # used to locate the stata do file (row number)
    for each in data_links:
        row += 1
        data_url = each.get_attribute("href")
        if re.search(initials + "\d\d(\d\d)?_Data_Stata", data_url, re.IGNORECASE):
            return data_url, str(row)

def get_do_file_url(row):
    stata = driver.find_element_by_css_selector("tbody > tr:nth-of-type(%s) > td:nth-of-type(6) > a:nth-of-type(3)" % row)
    do_file_url = stata.get_attribute("href")
    return do_file_url

def get_url_dictionary(data_url, do_file_url):
    url = dict()
    url['data'] = data_url
    url['do_file'] = do_file_url
    return url

def store_urls(urls):
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    with open(data_path + survey_name + ".txt", 'w') as file:
        json.dump(urls, file)

def get_urls(start, end, survey = None):
    enter_1st_page()
    urls = []
    for year in range(start, end):
        try:
            query(year, survey)
            data_url, row = get_data_url()
            print("Get Data and Dictionary Link " + str(year))
            print(data_url)
            do_file_url = get_do_file_url(row)
            print(do_file_url)
            url = get_url_dictionary(data_url, do_file_url)
            urls.append(url)
            time.sleep(uniform(0.5, 1.5))
        except NoSuchElementException:
            print("Year " + str(year) + " does not exist")
            pass
    store_urls(urls)

def extract_file(file):
    with ZipFile(file, 'r') as myzip:
        myzip.extractall(data_path)

def download_data():
    with open(data_path + survey_name + ".txt", 'r') as file:
        urls = json.loads(file.read())
    print("downloading and extracting data...")
    for each in urls:
        data = urlopen(each['data'])
        stata_do = urlopen(each['do_file'])
        data_name = each['data'].replace("https://nces.ed.gov/ipeds/datacenter/data/", "")
        stata_do_name = each['do_file'].replace("https://nces.ed.gov/ipeds/datacenter/data/", "")
        file1 = data_path + data_name
        file2 = data_path + stata_do_name
        print(data_name)
        with open(file1, 'wb') as data_file:
            data_file.write(data.read())
        extract_file(file1)
        os.remove(file1)
        with open(file2, 'wb') as do_file:
            do_file.write(stata_do.read())
        extract_file(file2)
        os.remove(file2)

def main():
    if not os.path.isfile(data_path + survey_name + ".txt"):
        get_urls(start_year, end_year, survey=survey_name)
    download_data()

##############################################################################################################
##############################################################################################################

def add_capture(data):
    for i in range(0,len(data)):
        if re.search(r'^label', data[i]):
            data[i] = "capture " + data[i]

def rewrite_do_file():
    if not os.path.exists(data_path + survey_name):
        os.mkdir(data_path + survey_name)
    for file in os.listdir(data_path):
        if file.endswith(".do"):
            print("do \"" + file + "\"")
            with open(data_path+file, 'r') as openfile:
                data = openfile.readlines()
                add_capture(data)
                if data[-1] != "\n":
                    data.append("\n")
                data[-2] = "save " + file[:-3] + ".dta, replace"
                csv = openfile.name[:-3] + "_data_stata.csv"
                data[28] = "insheet using \"%s\", comma clear" % csv + "\n"
                data.insert(28, "set more off\n")
                data.insert(28, "clear all\n")
            with open(data_path + survey_name + "/" + file, 'w') as newfile:
                newfile.writelines(data)

def remove_files():
    for file in os.listdir(data_path):
        if file.endswith(".do"):
            os.remove(data_path + file)
    for file in os.listdir(data_path):
        if file.endswith(".csv"):
            os.remove(data_path+file)

def rename_data_files():
    for filename in os.listdir(data_path + survey_name):
        if filename.endswith(".dta"):
            year = re.search("(\d\d\d\d)|(\d\d)", filename).group()
            if int(year) > 2100:
                year = year[:-2]
            if int(year) < 100:
                year = int(year) + 1900
            print(str(year))
            os.chdir(data_path + survey_name)
            os.rename(filename, initials + str(year) + ".dta")

# run main() if data are not downloaded yet
# main()
# rewrite stata do files and run do files for variable labeling
# rewrite_do_file()
# rename_data_files()
# remove redudant csv files after running do files
remove_files()
