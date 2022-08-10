from datetime import datetime, timedelta
import time
from ground_station import apscheduler_worker
import logging

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

def test_job(arg):
    print('job start')
    for i in range(15):
        print(f'do job {i}...')
        time.sleep(1)
    print('job finish', arg)
    time.sleep(1)
    print('go out')


if __name__ == '__main__':
    apscheduler_worker.scheduler_worker.start()
    time.sleep(2)
    apscheduler_worker.scheduler_worker.add_job(test_job, 'date', args=[1], run_date=datetime.now() + timedelta(seconds=2))
    job = apscheduler_worker.scheduler_worker.get_jobs()
    apscheduler_worker.scheduler_worker.pause_job(job_id=job[0].id)
    time.sleep(4)
    apscheduler_worker.scheduler_worker.resume_job(job_id=job[0].id)
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        apscheduler_worker.shutdown()
        print('Shutting down...')