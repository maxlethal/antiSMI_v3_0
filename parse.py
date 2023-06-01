from db import *
from dicts import black_labels

import random
import datetime as dt
import time
from loguru import logger
from dateutil import parser
import requests
from bs4 import BeautifulSoup

from apscheduler.schedulers.background import BlockingScheduler


class Parser(Query):
	"""Класс парсера: собирает новости агентства, сохраняет словарь новостей и позволяет работать с ним """

	def __init__(self, channel: str, last_id: int):
		self.channel = channel
		self.last_id = last_id
		self.news = []
		self.exist_urls = Query.get_all_articles_dict(smi)

	def __len__(self):
		return len(self.news)

	def __grab_news(self):
		"""Создаёт словарь последних новостей СМИ и возвращает его"""
		my_news = []
		agency = self.channel.split('/')[-1]
		user_agents = open('proxy/user-agents.txt').read().splitlines()
		random_user_agent = random.choice(user_agents)
		headers = {'User-Agent': random_user_agent}
		answer = requests.get(self.channel, headers=headers)
		if answer and answer.status_code != 204:
			try:
				soup = BeautifulSoup(answer.text, features="html.parser")
				page = soup.body.main.section.find_all(attrs={'class': 'tgme_widget_message_bubble'})
				for news_content in page:
					dirty_news = news_content.find(attrs={'class': 'tgme_widget_message_text js-message_text'})
					news_id = int(news_content.find(attrs={'class': 'tgme_widget_message_date'}).get('href').split('/')[
						              -1])
					if dirty_news and (news_id > self.last_id and news_id not in self.exist_urls[agency]):
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


def start_parsing():
	last_news_id = Query.get_last_news_id()
	total_news = 0
	start_time = dt.datetime.now()
	logger.info(f'Начинается обработка новостей от {start_time}:\n')
	if DataBaseMixin.is_not_empty('news'):
		logger.error(
			f'Сбор новостей не может быть проведён, так как временная база данных smi по какой-то не пуста')
		logger.info('Очистите базу данных вручную и запустите снова')
	for full_channel_link, last_id in last_news_id.items():
		channel_name = full_channel_link.split("/")[-1]
		channel = Parser(full_channel_link, last_id)
		channel.set_news
		if len(channel):
			DataBaseMixin.record(smi, 'news', channel.get_news)
			logger.info(f'{channel_name}: собрано {len(channel)} новостей')
		total_news += len(channel)
		channel.del_news
		time.sleep(random.randint(3, 5))
	result_time = dt.datetime.now() - start_time
	logger.info(
		f'\nСбор завершен успешно.\nПолучено {total_news} новостей за {round(result_time.seconds / 60, 2)} минут')


if __name__ == '__main__':
	# scheduler = BlockingScheduler()
	# scheduler.add_job(start_parsing, 'interval', hours=1, next_run_time=dt.datetime(2023, 5, 26, 21, 55, 0))
	# scheduler.start()
	start_parsing()
