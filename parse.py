from db import *
from dicts import black_labels

import random
from loguru import logger
from dateutil import parser
import requests
from bs4 import BeautifulSoup


class AgenciesID(DataBaseMixin):
	def __init__(self):
		self.ids_dict = dict()

	@staticmethod
	def __get_agencies_ids() -> dict:
		"""Отдаёт словарь всех существующих id новостей для каждого агенства"""
		"""{'agency': (id1, id2,...)}"""
		all_agencies_ids = {}
		news_ids = Query.get_all_ids(smi, 'news')
		final_ids = Query.get_all_ids(smi, 'final')
		asmi_ids = Query.get_all_ids(asmi, 'news')
		total_ids = [*news_ids, *final_ids, *asmi_ids]
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
	"""Класс парсера: собирает новости агентства, сохраняет словарь новостей и позволяет работать с ним """

	def __init__(self, channel: str, ids: tuple):
		self.channel = channel
		self.ids = ids
		self.news = []

	def __len__(self):
		return len(self.news)

	def __grab_news(self):
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
