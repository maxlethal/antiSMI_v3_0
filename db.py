from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text, insert, update, MetaData, Table, Column, Text, TIMESTAMP
from loguru import logger
import pickle
import datetime as dt

load_dotenv()

db_name = os.getenv("DB_NAME")
db_test = os.getenv("DB_TEST")
db_pass = os.getenv("DB_PASS")
db_host = os.getenv("DB_HOST")

asmi = create_engine(
	f'postgresql+psycopg2://{db_name}:{db_pass}@{db_host}/{db_name}')
smi = create_engine(
	f'postgresql+psycopg2://{db_test}:{db_pass}@{db_host}/{db_test}')


class DataBaseMixin:

	@staticmethod
	def get_table(engine, table_name):
		table_small = Table(table_name, MetaData(),
		                    Column('url', Text),
		                    Column('date', TIMESTAMP),
		                    Column('news', Text),
		                    Column('links', Text),
		                    Column('agency', Text),
		                    extend_existing=True,
		                    autoload_with=engine)
		table_big = Table(table_name, MetaData(),
		                  Column('url', Text),
		                  Column('date', TIMESTAMP),
		                  Column('title', Text),
		                  Column('resume', Text),
		                  Column('links', Text),
		                  Column('news', Text),
		                  Column('category', Text),
		                  Column('agency', Text),
		                  extend_existing=True,
		                  autoload_with=engine)
		return table_small if engine == smi and table_name == 'news' else table_big

	@staticmethod
	def is_not_empty(table_name):
		q = f'SELECT * FROM {table_name} LIMIT 1'
		result = DataBaseMixin.get(q, smi)
		return True if result != [] else False

	@staticmethod
	def get(query, engine):
		"""Принимает запрос в БД и возвращает результат его исполнения"""
		with engine.begin() as conn:
			query_text = text(query)
			result_set = conn.execute(query_text)
			results_as_dict = result_set.mappings().all()
			return results_as_dict

	@staticmethod
	def record(engine, table_name, data):
		"""Принимает запрос на запись списка кортежей в БД и производит запись"""
		try:
			table = DataBaseMixin.get_table(engine, table_name)
			with engine.begin() as conn:
				ins = insert(table)
				conn.execute(ins, data)
		except Exception:
			filename = table_name + '-' + str(dt.datetime.now()).split()[0] + '-' + \
			           str(dt.datetime.now()).split()[-1].split('.')[-1]
			with open(f'pkl/{filename}.pkl', 'wb') as f:
				pickle.dump(data, f)
			logger.error(
				f'Отказ записи в {table_name}. Ваши данные сохранены в файл {filename}.pkl. Запишите их вручную')

	@staticmethod
	def erase(table_name):
		"""Принимает запрос в БД и возвращает результат его исполнения"""
		try:
			table = DataBaseMixin.get_table(smi, table_name)
			with smi.begin() as conn:
				del_query = table.delete()
				conn.execute(del_query)
			logger.info(f'Временная база данных {table_name} очищена')
		except Exception:
			logger.error(f'Ошибка очистки временной базы данных {table_name}. Проведите очистку вручную.')

	@staticmethod
	def move(table_from, table_to, data):
		"""Перемещает данные в новую таблицу, очищая данные в прежней. Сама обработка данных происходит во вне"""
		engine = smi if table_to == 'final' else asmi
		DataBaseMixin.record(engine, table_to, data)
		DataBaseMixin.erase(table_from)


class Query(DataBaseMixin):
	"""Универсальные и базовые запросы к базам данных, используемые в основном коде"""

	@staticmethod
	def get_monocategory_dict() -> dict:
		"""Формирует из базы словарь узкоспециализированных каналов, которые являются поставщиком одной категории новостей"""
		query_mono_category = "SELECT telegram, mono_category FROM agencies WHERE is_parsing = True and not mono_category " \
		                      "= 'None'"
		mono_category_alchemy = DataBaseMixin.get(query_mono_category, asmi)
		mono_dict = {el['telegram']: el['mono_category'] for el in mono_category_alchemy}

		return mono_dict

	@staticmethod
	def get_last_news_id():
		"""Формирует словарь последних id-новостей для каждого агентства"""
		last_agencies_url_query = "WITH t1 as (SELECT DISTINCT agency, max(date) OVER (PARTITION BY agency) as date FROM " \
		                          "news) SELECT t1.agency, url FROM t1 JOIN news USING(date) WHERE t1.agency = news.agency"
		all_active_agencies_query = "SELECT telegram FROM agencies WHERE is_parsing is True"

		last_url_list = DataBaseMixin.get(last_agencies_url_query, asmi)
		all_agencies_list = DataBaseMixin.get(all_active_agencies_query, asmi)

		last_url_dict = {el['agency']: int(el['url'].split('/')[-1]) for el in last_url_list}
		present_smi = [el['telegram'] for el in all_agencies_list]

		result_dict = {}
		for channel_name in present_smi:
			channel_link = 'https://t.me/s/' + channel_name
			if channel_name in last_url_dict:
				result_dict[channel_link] = last_url_dict[channel_name]
			else:
				result_dict[channel_link] = 0
		return result_dict

	@staticmethod
	def get_all_articles_dict(engine) -> dict:
		"""Формирует словарь всех существующих id-стотей в разрезе каждого агенства"""
		base_to = 'final' if engine == smi else 'news'
		all_agencies_articles = {}
		query = f"SELECT agency, url FROM {base_to}"
		query_result = DataBaseMixin.get(query, engine)
		all_articles = [dict(fresh_news) for fresh_news in query_result]

		all_active_agencies_query = "SELECT telegram FROM agencies WHERE is_parsing is True"
		all_agencies_list = DataBaseMixin.get(all_active_agencies_query, asmi)

		for agency in all_agencies_list:
			articles_tuple = tuple(
				el['url'].split('/')[-1] for el in all_articles if el['agency'] == agency['telegram'])
			all_agencies_articles[agency['telegram']] = articles_tuple
		return all_agencies_articles
