import requests
import json
import pprint
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


LANGUAGES = ["JavaScript", "Java", "Python", "Ruby", "PHP", "Go"]
PAGE_QUANTITY = "100"
VACANCIES_AREA_ID_HH = '1'


def get_vacancies_hh(language, page=0):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
    }
    params = {
        "text": f"Программист {language}",
        "area": VACANCIES_AREA_ID_HH,
        "page": page,
        "per_page": PAGE_QUANTITY
    }
    response = requests.get("https://api.hh.ru/vacancies", headers=headers, params=params)
    response.raise_for_status()
    vacancies = response.json()

    return vacancies


def get_vacancies_sj(language, secret_key, page=0):
    headers = {
        "X-Api-App-Id": secret_key
    }
    params = {
        "town": "Москва",
        "count": PAGE_QUANTITY,
        "page": page,
        "keyword": f"Программист {language}"
    }
    response = requests.get("https://api.superjob.ru/2.0/vacancies/", headers=headers, params=params)
    response.raise_for_status()
    vacancies = response.json()

    return vacancies


def get_predict_rub_salary(vacancy):
    currencies = ['RUR', 'rub']
    if vacancy.get('currency'):
        salary_from = vacancy.get('payment_from')
        salary_to = vacancy.get('payment_to')
        salary_currency = vacancy.get('currency')
    elif vacancy.get("salary"):
        salary = vacancy.get('salary')
        salary_from = salary.get('from')
        salary_to = salary.get('to')
        salary_currency = salary.get('currency')
    else:
        return None
    if salary_currency in currencies and salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_currency in currencies and salary_from:
        return salary_from * 1.2
    elif salary_currency in currencies and salary_to:
        return salary_to * 0.8
    else:
        return None


def get_average_salary(vacancies_array):
    salaries = []
    for vacancy in vacancies_array:
        salary = get_predict_rub_salary(vacancy)
        if salary:
            salaries.append(salary)
    if salaries:
        average_salary = int(sum(salaries) / len(salaries))
        vacancies_processed = len(salaries)
        return average_salary, vacancies_processed
    else:
        return 0, 0


def get_statistics(vacancies, vacancies_array):
    statistics = {}
    if vacancies.get("found"):
        vacancies_found = vacancies.get("found")
    else:
        vacancies_found = vacancies.get("total")
    average_salary, vacancies_processed = get_average_salary(vacancies_array)
    statistics = {
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
        "average_salary": average_salary
    }

    return statistics


def print_statistics_table(statistics, name_site):
    title = f"{name_site} Moscow"
    table_data = [
        [
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий обработано",
            "Средняя зарплата"
        ]
    ]
    for language in LANGUAGES:
        vacancies_data = list(statistics.get(language).values())
        vacancies_data.insert(0, language)
        table_data.append(vacancies_data)
    table = AsciiTable(table_data, title)
    print(table.table)


def main():
    load_dotenv()
    secret_key = os.environ["SJ_SECRET_KEY"]
    statistics_sj = {}
    statistics_hh = {}
    for language in LANGUAGES:

        vacancies_array_hh = []
        page_hh = 0
        while True:
            vacancies_hh = get_vacancies_hh(language, page_hh)
            for vacancy_hh in vacancies_hh.get('items'):
                vacancies_array_hh.append(vacancy_hh)
            if page_hh >= vacancies_hh.get('pages'):
                break
            page_hh += 1
        statistics_hh[language] = get_statistics(vacancies_hh, vacancies_array_hh)

        vacancies_array_sj = []
        page_sj = 0
        while True:
            vacancies_sj = get_vacancies_sj(language, secret_key, page_sj)
            for vacancy_sj in vacancies_sj.get('objects'):
                    vacancies_array_sj.append(vacancy_sj)
            if not vacancies_sj.get('more'):
                break
            page_sj += 1
        statistics_sj[language] = get_statistics(vacancies_sj, vacancies_array_sj)

    print_statistics_table(statistics_sj, "SuperJob")
    print()
    print_statistics_table(statistics_hh, "HeadHunter")


if __name__ == "__main__":
    main()
