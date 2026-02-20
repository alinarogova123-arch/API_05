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


def get_predict_rub_salary(salary_from, salary_to, salary_currency):
    currencies = ['RUR', 'rub']
    if salary_currency in currencies and salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_currency in currencies and salary_from:
        return salary_from * 1.2
    elif salary_currency in currencies and salary_to:
        return salary_to * 0.8
    else:
        return None


def get_average_salary(salaries):
    if salaries:
        average_salary = int(sum(salaries) / len(salaries))
        vacancies_processed = len(salaries)
        return average_salary, vacancies_processed
    else:
        return 0, 0


def get_statistics(vacancies_found, salaries):
    average_salary, vacancies_processed = get_average_salary(salaries)
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

        salaries_hh = []
        page_hh = 0
        while True:
            vacancies_hh = get_vacancies_hh(language, page_hh)
            for vacancy_hh in vacancies_hh.get('items'):
                salary_hh = vacancy_hh.get('salary')
                if salary_hh:
                    vacancy_salary_hh = get_predict_rub_salary(salary_hh.get('from'), salary_hh.get('to'), salary_hh.get('currency'))
                if vacancy_salary_hh:
                    salaries_hh.append(vacancy_salary_hh)
            if page_hh >= vacancies_hh.get('pages'):
                break
            page_hh += 1
        statistics_hh[language] = get_statistics(vacancies_hh.get("found"), salaries_hh)

        salaries_sj = []
        page_sj = 0
        while True:
            vacancies_sj = get_vacancies_sj(language, secret_key, page_sj)
            for vacancy_sj in vacancies_sj.get('objects'):
                vacancy_salary_sj = get_predict_rub_salary(vacancy_sj.get('payment_from'), vacancy_sj.get('payment_to'), vacancy_sj.get('currency'))
                if vacancy_salary_sj:
                    salaries_sj.append(vacancy_salary_sj)
            if not vacancies_sj.get('more'):
                break
            page_sj += 1
        statistics_sj[language] = get_statistics(vacancies_sj.get("total"), salaries_sj)

    print_statistics_table(statistics_sj, "SuperJob")
    print()
    print_statistics_table(statistics_hh, "HeadHunter")


if __name__ == "__main__":
    main()
