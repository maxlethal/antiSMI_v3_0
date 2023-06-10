from imports_cook import *

logger.add('debugging//debug_cook.json', format="{time} {message}", level='INFO', rotation="1 week", compression="zip",
           serialize=True)


def article2resume(article_text: str) -> str:
	"""Делает саммари полной новости"""
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

	return fresh_news_list


def cook_and_move_to_smi():
	fresh_news_list = make_full_fresh_news_list()
	try:
		DataBaseMixin.move('news', 'final', fresh_news_list)
	except:
		filename = str(dt.datetime.now()).split()[0] + '-' + \
		           str(dt.datetime.now()).split()[-1].split('.')[-1]
		with open(f'pkl/{filename}.pkl', 'wb') as f:
			pickle.dump(fresh_news_list, f)
		logger.error(f'Не удалось записать обработанные новости в final, файл {filename} сохранён для ручной обработки')


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
	try:
		DataBaseMixin.move('final', 'news', final_news)
		os.remove("".join(glob.glob("pkl/*")))
	except Exception as e:
		logger.exception(f'Не смог обработать из-за ошибки {e}')
