import psycopg2

from psycopg2 import sql


class DBManager:
    """
    Класс для работы с базой данных PostgreSQL.
    Предполагается наличие таблиц:
    - employers (employer_id INT PRIMARY KEY, employer_name VARCHAR(255) NOT NULL,
                 employer_url VARCHAR(255))
    - vacancies (vacancy_id INT PRIMARY KEY,
                employer_id INT REFERENCES employers(employer_id),
                vacancy_name VARCHAR(255) NOT NULL,
                salary_from INT,
                salary_to INT,
                currency VARCHAR(10),
                vacancy_url VARCHAR(255))
    """

    def __init__(self, dbname: str, user: str, password: str, host: str = "localhost", port: str = "5432"):
        """
        Инициализация подключения к БД.
        :param dbname: имя базы данных
        :param user: пользователь
        :param password: пароль
        :param host: хост (по умолчанию localhost)
        :param port: порт (по умолчанию 5432)
        """
        self.conn_params = {"dbname": dbname, "user": user, "password": password, "host": host, "port": port}
        self.conn_autocommit = True  # автоматическое подтверждение транзакций

    def _execute_query(self, query: str, params=None) -> list:
        """
        Вспомогательный метод для выполнения запросов и возврата результатов.
        :param query: SQL-запрос
        :param params: параметры для подстановки
        :return: список строк результата (list of tuples)
        """
        with psycopg2.connect(**self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()


    def get_companies_and_vacancies_count(self) -> list:
        """
        Получает список всех компаний и количество вакансий у каждой компании.
        :return: список кортежей (company_name, vacancies_count)
        """
        query = """
            SELECT e.employer_name, COUNT(v.vacancy_id) AS vacancy_count
            FROM employers e
            LEFT JOIN vacancies v ON e.employer_id = v.employer_id
            GROUP BY e.employer_name
            ORDER BY vacancy_count DESC;
        """
        return self._execute_query(query)

    def get_all_vacancies(self) -> list:
        """
        Получает список всех вакансий с указанием названия компании,
        названия вакансии, зарплаты и ссылки на вакансию.
        :return: список кортежей (company_name, vacancy_title, salary, vacancy_url)
        """
        query = """
            SELECT e.employer_name AS employer_name, 
            v.vacancy_name AS  vacancy_name, 
            v.salary_from, v.salary_to, v.currency, v.vacancy_url
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id;
        """
        return self._execute_query(query)

    def get_avg_salary(self) -> float:
        """
        Получает среднюю зарплату по вакансиям.
        Учитываются только вакансии с указанной зарплатой (не NULL).
        :return: средняя зарплата (float)
        """
        query = """
            SELECT AVG((COALESCE(salary_from, 0) + COALESCE(salary_TO, 0)) / 2.0)
            AS avg_salary FROM vacancies WHERE salary_from IS NOT NULL or salary_to IS NOT NULL;
        """
        result = self._execute_query(query)
        if result and result[0] and result[0][0] is not None:
            return float(result[0][0])
        return 0.0

    def get_vacancies_with_higher_salary(self) -> list:
        """
        Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям.
        :return: список кортежей (company_name, vacancy_title, salary, vacancy_url)
        """
        query = """
            SELECT vacancy_name, salary_from, salary_to, currency, vacancy_url
            FROM vacancies WHERE ((COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2.0) >
            (SELECT AVG((COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2.0)
            FROM vacancies WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL);
        """
        return self._execute_query(query)

    # def get_vacancies_with_keyword(self, keyword: str) -> list:
    #     """
    #     Получает список всех вакансий, в названии которых содержится переданное слово.
    #     :param keyword: ключевое слово для поиска (регистронезависимо)
    #     :return: список кортежей (company_name, vacancy_title, salary, vacancy_url)
    #     """
    #     query = """
    #         SELECT c.name, v.title, v.salary, v.url
    #         FROM vacancies v
    #         JOIN companies c ON v.company_id = c.id
    #         WHERE v.title ILIKE %s;
    #     """
    #     # Добавляем символы % для поиска подстроки
    #     like_pattern = f"%{keyword}%"
    #     return self._execute_query(query, (like_pattern,))
    #
    # def close(self):
    #     """Закрывает соединение с БД."""
    #     if self.conn:
    #         self.conn.close()
