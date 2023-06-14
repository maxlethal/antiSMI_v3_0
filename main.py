from shop import *
from cook import *
from apscheduler.schedulers.background import BlockingScheduler


def shopping():
    """agency telegram channel -> temp.db, table.news"""
    go_shopping()


def cooking():
    """temp.db, table.news -> temp.db, table.final"""
    cook_and_move_to_smi()


def serving():
    """temp.db, table.final -> antiSMI"""
    check_and_move_to_asmi()


if __name__ == '__main__':
    try:
        scheduler = BlockingScheduler()
        scheduler.add_job(shopping, 'cron', hour='*', minute=55, id='shopper', max_instances=10, misfire_grace_time=600)
        scheduler.add_job(cooking, 'cron', hour='7-23/2', id='cooker', max_instances=10, misfire_grace_time=600)
        scheduler.add_job(serving, 'cron', hour='9-21/4', minute=50, id='server', max_instances=10,
                          misfire_grace_time=600)
        scheduler.start()
        # shopping()
        # cooking()
        # serving()

    except Exception as e:
        logger.exception(e)
