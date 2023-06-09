from imports_shop import *
from taste import *
from imports_common import *


logger.add('debugging//debug_shop.json', format="{time} {message}", level='INFO', rotation="1 week", compression="zip",
           serialize=True)


class AgenciesID(DataBaseMixin):
    """Собирает словарь всех существующих id новостей для каждого агентства и работает с ним"""

    def __init__(self):
        self.ids_dict = dict()

    @staticmethod
    def __get_agencies_ids() -> dict:
        """Отдаёт словарь id-новостей каждого агентства в виде {'agency': (id1, id2,...)}"""
        all_agencies_ids = {}
        news_ids = Query.get_all_ids(smi, 'news')
        final_ids = Query.get_all_ids(smi, 'final')
        error_ids = Query.get_all_ids(smi, 'error_table')
        asmi_ids = Query.get_all_ids(asmi, 'news')
        total_ids = [*news_ids, *final_ids, *error_ids, *asmi_ids]
        all_active_agencies_query = "SELECT telegram FROM agencies WHERE is_parsing is True"
        all_active_agencies = DataBaseMixin.get(all_active_agencies_query, asmi)

        for agency in all_active_agencies:
            articles_ids = tuple(
                el['id'] for el in total_ids if el['agency'] == agency['telegram'])
            all_agencies_ids[agency['telegram']] = articles_ids

        return all_agencies_ids

    @property
    def get_ids(self):
        return self.ids_dict if self.ids_dict else logger.error(f'Словарь id пока не сформирован')

    @property
    def set_ids(self):
        self.ids_dict = self.__get_agencies_ids() if not self.ids_dict else logger.error('Словарь id уже в наличие')

    @property
    def del_ids(self):
        self.ids_dict.clear()
        logger.info('Словарь id новостей успешно очищен')

    def get_agency(self, agency):
        return self.ids_dict[agency]


class Parser(Query):
    """Класс сбора новостей: парсит новости агентства, сохраняет словарь новостей и позволяет работать с ним """

    def __init__(self, channel: str, ids: tuple):
        self.channel = channel
        self.ids = ids
        self.news = []

    def __len__(self):
        return len(self.news)

    def __grab_news(self) -> list[dict]:
        """Создаёт словарь последних новостей СМИ и возвращает его"""
        my_news: list[dict] = []
        agency = self.channel
        agency_url = 'https://t.me/s/' + agency
        user_agents = open('proxy/user-agents.txt').read().splitlines()
        random_user_agent = random.choice(user_agents)
        headers = {'User-Agent': random_user_agent}
        answer = requests.get(agency_url, headers=headers)
        if answer and answer.status_code != 204:
            try:
                soup = BeautifulSoup(answer.text, features="html.parser")
                page = soup.body.main.section.find_all(attrs={'class': 'tgme_widget_message_bubble'})
                for news_content in page:
                    dirty_news = news_content.find(attrs={'class': 'tgme_widget_message_text js-message_text'})
                    news_id = int(news_content.find(attrs={'class': 'tgme_widget_message_date'}).get('href').split('/')[
                                      -1])
                    if dirty_news and (news_id not in self.ids):
                        news = Parser.clean_news(dirty_news.text, agency)
                        url = news_content.find(attrs={'class': 'tgme_widget_message_date'}).get('href')
                        links = dirty_news.find('a').get('href').split('?utm')[0] if dirty_news.find(
                            'a') and not dirty_news.find(
                            'a').get('href').startswith(('tg://resolve?domain=', 'https://t.me/+')) else url
                        date = parser.parse(news_content.find(attrs={'class': 'time'}).get('datetime'))
                        my_news.append({'url': url, 'date': date, 'news': news, 'links': links, 'agency': agency})
            except (ValueError, KeyError, AttributeError):
                print(f'Обработка {agency} не удалась')

        return my_news

    @property
    def get_news(self):
        return self.news

    @property
    def set_news(self):
        self.news = self.__grab_news() if not self.news else print('Новости уже собраны')

    @property
    def del_news(self):
        """Очищает словарь новостей"""
        self.news.clear()
        return 'Обработка источника завершена, новости удалены'

    @staticmethod
    def clean_news(news: str, channel: str) -> str:
        """Очищает новость агентства от мусора согласно настройкам словаря black_labels"""
        total_label = {*black_labels['common_labels'],
                       *black_labels[channel]} if channel in black_labels.keys() else {
            *black_labels['common_labels']}
        news = news.replace("\xa0", ' ').replace('​​', ' ').replace('\n', '. ').strip()
        for label in total_label:
            news = news.replace(label, ' ')
        return news.strip()


def go_shopping():
    """Основная функция сбора: собираем новости, валидируем поля на соответствие, пишем во временную базу news"""
    total_news = 0
    start_time = dt.datetime.now()
    logger.info(f'Начинается сбор новостей от {start_time}:')

    agencies_ids = AgenciesID()
    agencies_ids.set_ids
    for channel, ids_tuple in agencies_ids.get_ids.items():
        channel = Parser(channel, ids_tuple)
        channel.set_news
        if len(channel):
            len_news = validate_and_write_to_news_db(channel.get_news)
            logger.info(f'{channel.channel}: собрано {len_news} новостей')
        total_news += len(channel)
        channel.del_news
        time.sleep(random.randint(1, 3))
    agencies_ids.del_ids

    result_time = dt.datetime.now() - start_time
    try:
        logger.info(
            f'Сбор завершен успешно.Получено {total_news} новостей за {round(result_time.seconds / 60, 2)} минут '
            f'со скоростью {round(result_time.seconds / total_news, 2)}  новостей в секунду\n')
    except ZeroDivisionError:
        logger.info('В этот раз ничего не собрано')
