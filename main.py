import requests
import json
import pprint
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


LANGUAGES = ["JavaScript", "Java", "Python", "Ruby", "PHP", "Go"]


def get_vacancies_hh(language, page_quantity=1):
    vacancies_array = []
    for i in range(page_quantity):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }
        params = {
            "text": f"Программист {language}",
            "area": "1",
            "page": i,
            "per_page": "100"
        }
        response = requests.get("https://api.hh.ru/vacancies", headers=headers, params=params)
        response.raise_for_status()
        vacancies_array.append(response.json())

    return vacancies_array


def get_vacancies_sj(language, secret_key):
    headers = {
        "X-Api-App-Id": secret_key
    }
    params = {
        "town": "Москва",
        "count": "100",
        "keyword": f"Программист {language}"
    }
    response = requests.get("https://api.superjob.ru/2.0/vacancies/", headers=headers, params=params)
    response.raise_for_status()
    vacancies = response.json().get('objects')

    return vacancies


def get_predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if salary is None:
        return None
    elif salary.get('currency') == 'RUR' and salary.get('from') and salary.get('to'):
        return (salary.get('from') + salary.get('to')) / 2
    elif salary.get('currency') == 'RUR' and salary.get('from'):
        return salary.get('from') * 1.2
    elif salary.get('currency') == 'RUR' and salary.get('to'):
        return salary.get('to') * 0.8
    else:
        return None


def get_predict_rub_salary_sj(vacancy):
    if vacancy.get('currency') == 'rub' and vacancy.get('payment_from') != 0 and vacancy.get('payment_to') != 0:
        return (vacancy.get('payment_from') + vacancy.get('payment_to')) / 2
    elif vacancy.get('currency') == 'rub' and vacancy.get('payment_from') != 0:
        return vacancy.get('payment_from') * 1.2
    elif vacancy.get('currency') == 'rub' and vacancy.get('payment_to') != 0:
        return vacancy.get('payment_to') * 0.8
    else:
        return None


def get_average_salary_hh(language):
    salary_list = []
    vacancies_array = get_vacancies_hh(language, 20)
    for vacancies in vacancies_array:      
        for vacancy in vacancies.get("items"):
            predict_salary = get_predict_rub_salary_hh(vacancy)
            if predict_salary is not None:
                salary_list.append(predict_salary)
    if salary_list == []:
        return 0, 0
    else:
        average_salary = int(sum(salary_list) / len(salary_list))
        vacancies_processed = len(salary_list)
        return average_salary, vacancies_processed


def get_average_salary_sj(language, secret_key):
    vacancies = get_vacancies_sj(language, secret_key)
    salary_list = []
    for vacancy in vacancies:
        predict_salary = get_predict_rub_salary_sj(vacancy)
        if predict_salary is not None:
            salary_list.append(predict_salary)
    if salary_list == []:
        return 0, 0
    else:
        average_salary = int(sum(salary_list) / len(salary_list))
        vacancies_processed = len(salary_list)
        return average_salary, vacancies_processed


def get_statistics_sj(secret_key):
    statistics = {}
    for language in LANGUAGES:
        vacancies_found = len(get_vacancies_sj(language, secret_key))
        average_salary, vacancies_processed = get_average_salary_sj(language, secret_key)
        statistics[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
            }   
    
    return statistics


def get_statistics_hh():
    statistics = {}
    for language in LANGUAGES:
        vacancies_found = get_vacancies_hh(language)[0].get("found")
        average_salary, vacancies_processed = get_average_salary_hh(language)
        statistics[language] = {
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
        added_list = list(statistics.get(language).values())
        added_list.insert(0, language)
        table_data.append(added_list)
    table = AsciiTable(table_data, title)
    print(table.table)


def main():
    load_dotenv()
    secret_key = os.environ["SJ_SECRET_KEY"]
    statistics_sj = get_statistics_sj(secret_key)
    statistics_hh = get_statistics_hh()
    print_statistics_table(statistics_sj, "SuperJob")
    print()
    print_statistics_table(statistics_hh, "HeadHunter")


if __name__ == "__main__":
    main()
