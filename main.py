from parse import *

from apscheduler.schedulers.background import BlockingScheduler
import datetime as dt
import time


def main():
	total_news = 0
	start_time = dt.datetime.now()

	agencies_ids = AgenciesID()
	agencies_ids.set_ids
	for channel, ids_tuple in agencies_ids.get_ids.items():
		channel = Parser(channel, ids_tuple)
		channel.set_news
		if len(channel):
			DataBaseMixin.record(smi, 'news', channel.get_news)
			logger.info(f'{channel.channel}: собрано {len(channel)} новостей')
		total_news += len(channel)
		channel.del_news
		time.sleep(random.randint(1, 3))
	agencies_ids.del_ids
	# del(agencies_ids)

	result_time = dt.datetime.now() - start_time
	logger.info(
		f'Сбор завершен успешно.Получено {total_news} новостей за {round(result_time.seconds / 60, 2)} минут '
		f'со скоростью {round(result_time.seconds / total_news, 2)}  новостей в секунду\n')


if __name__ == '__main__':
	try:
		# main()
		scheduler = BlockingScheduler()
		scheduler.add_job(main, 'interval', hours=1, next_run_time=dt.datetime(2023, 6, 8, 19, 55, 0))
		scheduler.start()
	except Exception as e:
		logger.exception('Незадокументированное исключение')
