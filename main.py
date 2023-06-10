from shop import *
from cook import *
from apscheduler.schedulers.background import BlockingScheduler


def shopping():
	go_shopping()


def cooking():
	cook_and_move_to_smi()


def serving():
	check_and_move_to_asmi()


if __name__ == '__main__':
	try:
		scheduler = BlockingScheduler()
		# Исключил параметры max_instances = 10, misfire_grace_time = 600 -> проконтролировать поведение
		scheduler.add_job(shopping, 'cron', hour='*', minute=55, id='shopping')
		scheduler.add_job(cooking, 'cron', hour='7-23/2', id='cooking')
		scheduler.add_job(serving, 'cron', hour='9-21/4', minute=50, id='serving')
		scheduler.start()
	except Exception as e:
		logger.exception('Непредусмотренное исключение')
