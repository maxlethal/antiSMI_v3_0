import time

from db import *
import datetime as dt

from apscheduler.schedulers.background import BlockingScheduler

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, T5ForConditionalGeneration
import warnings
import fasttext as fasttext

warnings.filterwarnings("ignore")
fasttext.FastText.eprint = lambda x: None
model_class = fasttext.load_model("models//cat_model.ftz")

tokenizer_resume = AutoTokenizer.from_pretrained("IlyaGusev/mbart_ru_sum_gazeta")
model_resume = AutoModelForSeq2SeqLM.from_pretrained("IlyaGusev/mbart_ru_sum_gazeta")

tokenizer_title = AutoTokenizer.from_pretrained("IlyaGusev/rut5_base_headline_gen_telegram")
model_title = T5ForConditionalGeneration.from_pretrained("IlyaGusev/rut5_base_headline_gen_telegram")

from loguru import logger

logger.add('debugging//debug.json', format="{time} {message}", level='INFO', rotation="1 week", compression="zip",
           serialize=True)


def article2resume(article_text: str) -> str:
	"""Делает краткое саммари из новости"""
	input_ids = tokenizer_resume(
		[article_text],
		max_length=600,
		padding="max_length",
		truncation=True,
		return_tensors="pt")["input_ids"]

	output_ids = model_resume.generate(
		input_ids=input_ids,
		no_repeat_ngram_size=4)[0]

	summary = tokenizer_resume.decode(output_ids, skip_special_tokens=True)

	return summary


def article2title(summary: str) -> str:
	"""Делает заголовок из краткой новости"""
	input_ids = tokenizer_title(
		[summary],
		max_length=600,
		add_special_tokens=True,
		padding="max_length",
		truncation=True,
		return_tensors="pt")["input_ids"]

	output_ids = model_title.generate(
		input_ids=input_ids,
		no_repeat_ngram_size=4)[0]

	title = tokenizer_title.decode(output_ids, skip_special_tokens=True)

	return title


def make_full_fresh_news_list() -> list:
	"""Забирает свежие новости из smi, получает из них резюме и формирует словарь свежих новостей для записи во
	вспомогательную базу данных smi"""

	if not DataBaseMixin.is_not_empty('news'):
		logger.error(
			f'Обработка новостей не может начаться, так как новости ещё не собраны')
		logger.info('Соберите новости с помощью модуля parse')

	mono_dict = Query.get_monocategory_dict()
	all_fresh_news_query = "SELECT * FROM news"
	all_fresh_news_alchemy = DataBaseMixin.get(all_fresh_news_query, smi)
	fresh_news_list = [dict(fresh_news) for fresh_news in all_fresh_news_alchemy if 'url' in dict(fresh_news).keys()]

	start_t = dt.datetime.now()
	logger.info(f'Начинается обработка новостей от {start_t}:\n')

	for news in fresh_news_list:
		start_time = dt.datetime.now()
		category = model_class.predict(news['news'])[0][0].split('__')[-1]
		if category == 'not_news':
			fresh_news_list.remove(news)
		else:
			news['category'] = mono_dict[news['agency']] if news['agency'] in mono_dict.keys() else category
			news['title'] = article2title(news['news'])
			news['resume'] = article2resume(news['news'])
		duration = (dt.datetime.now() - start_time).seconds
		logger_dict = {'agency': news["agency"], 'url': news["url"], 'duration': duration}
		logger_dict = {'duration': duration, 'url': news["url"]}
		logger.info(logger_dict)

	for news in fresh_news_list:
		if 'category' not in news.keys():
			start_time = dt.datetime.now()
			news['category'] = mono_dict[news['agency']] if news['agency'] in mono_dict.keys() else \
				model_class.predict(news['news'])[0][0].split('__')[-1]
			news['title'] = article2title(news['news'])
			news['resume'] = article2resume(news['news'])
			duration = (dt.datetime.now() - start_time).seconds
			logger_dict = {'duration': duration, 'url': news["url"]}
			logger.info(logger_dict)

	result_time = dt.datetime.now() - start_t
	logger.info(f'Обработка {len(fresh_news_list)} новостей завершена за {round(result_time.seconds / 60, 2)} минут')
	logger.info(
		f'Среднее время обработки одной новости - {round(result_time.seconds / (len(fresh_news_list) + 0.01), 2)} секунд')

	filename = str(dt.datetime.now()).split()[0] + '-' + \
	           str(dt.datetime.now()).split()[-1].split('.')[-1]
	with open(f'{filename}.pkl', 'wb') as f:
		pickle.dump(fresh_news_list, f)

	return fresh_news_list


def cook_and_move_to_smi():
	fresh_news_list = make_full_fresh_news_list()
	DataBaseMixin.move('news', 'final', fresh_news_list)


def check_and_move_to_asmi():
	exist_asmi_url = Query.get_all_articles_dict(asmi)
	q = 'select * from final'
	final_news = DataBaseMixin.get(q, smi)
	for news in final_news:
		if 'category' not in news.keys():
			news_id = news['url'].split('/')[-1]
			exist_agency_urls = exist_asmi_url[news['agency']]
			if news_id in exist_agency_urls:
				final_news.remove(news)
				logger.info(f"{news_id} из {news['agency']} уже имеется в AntiSMI, новость не будет записана")
	DataBaseMixin.move('final', 'news', final_news)


def main():
	cook_and_move_to_smi()
	time.sleep(3)
	check_and_move_to_asmi()


if __name__ == '__main__':
	"""Организация и запуск планировщика для выполения двух типов задач: обработки новостей и записи их в AntiSMI"""
	# scheduler = BlockingScheduler()
	#
	# scheduler.add_job(main, 'cron', max_instances=10, misfire_grace_time=600, hour=5,
	#                   minute=00)
	# scheduler.add_job(main, 'cron', max_instances=10, misfire_grace_time=600, hour=7,
	#                   minute=00)
	# scheduler.add_job(main, 'cron', max_instances=10, misfire_grace_time=600, hour=9,
	#                   minute=16)
	# scheduler.add_job(main, 'cron', max_instances=10, misfire_grace_time=600, hour=12,
	#                   minute=00)
	# scheduler.add_job(main, 'cron', max_instances=10, misfire_grace_time=600, hour=15,
	#                   minute=00)
	# scheduler.add_job(main, 'cron', max_instances=10, misfire_grace_time=600, hour=17,
	#                   minute=00)
	# scheduler.add_job(main, 'cron', max_instances=10, misfire_grace_time=600, hour=20,
	#                   minute=00)
	# scheduler.add_job(main, 'cron', max_instances=10, misfire_grace_time=600, hour=21,
	#                   minute=00)
	#
	# scheduler.start()
	main()