# Initialize the scheduler only once, not in each worker
def on_starting(server):
    import atexit
    import os
    import time

    from apscheduler.schedulers.background import BackgroundScheduler

    from api import app, utils
    from api.schedules import status_worker, status_farm, status_plotting, \
        status_plots, status_challenges, status_wallets, status_blockchains, \
        status_connections, status_keys, status_alerts, status_controller, \
        status_plotnfts, status_pools, status_partials
    from api.schedules import stats_disk, stats_farm, nft_recover, plots_check, log_rotate, db_backup
    from common.config import globals

    scheduler = BackgroundScheduler()

    schedule_every_x_minutes = "?"
    try:
        schedule_every_x_minutes = app.config['STATUS_EVERY_X_MINUTES']
        JOB_FREQUENCY = 60 * int(schedule_every_x_minutes)
        JOB_JITTER = JOB_FREQUENCY / 2
    except:
        app.logger.info("Failed to configure job schedule frequency in minutes as setting was: '{0}'".format(schedule_every_x_minutes))
        JOB_FREQUENCY = 60 # once a minute
        JOB_JITTER = 30 # 30 seconds
    app.logger.info("Scheduler frequency will be once every {0} seconds.".format(JOB_FREQUENCY))

    # Every single container should report as a worker
    scheduler.add_job(func=status_worker.update, name="workers", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 

    # Collect disk stats from all modes where blockchain is chia, avoiding duplicate disks from multiple forks on same host
    if 'chia' in globals.enabled_blockchains():
        scheduler.add_job(func=stats_disk.collect, name="stats_disk", trigger='cron', minute="*/10") # Every 10 minutes
        
    # Status for both farmers and harvesters (includes fullnodes)
    if globals.farming_enabled() or globals.harvesting_enabled():
        scheduler.add_job(func=status_challenges.update, name="challenges", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
        scheduler.add_job(func=status_alerts.update, name="alerts", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=log_rotate.execute, name="log_rotate", trigger='cron', minute=0)  # Hourly

    # Status for plotters
    if globals.plotting_enabled():
        scheduler.add_job(func=status_plotting.update, name="plottings", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
          
    # Status for fullnodes, all different forks
    if utils.is_fullnode():
        scheduler.add_job(func=stats_farm.collect, name="stats_farm", trigger='cron', minute=0)  # Hourly
        scheduler.add_job(func=status_wallets.update, name="wallets", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=status_blockchains.update, name="blockchains", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=status_connections.update, name="connections", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=status_keys.update, name="keys", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
        scheduler.add_job(func=status_farm.update, name="farms", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=status_plots.update, name="plots", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
        scheduler.add_job(func=db_backup.execute, name="db_backup", trigger='cron', hour=0, jitter=(JOB_JITTER*3600))  # Daily
        scheduler.add_job(func=status_plotnfts.update, name="plotnfts", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=status_pools.update, name="pools", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
            
    # Status for single Machinaris controller only, should be blockchain=chia
    if utils.is_controller():
        scheduler.add_job(func=plots_check.execute, name="plot_checks", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=status_partials.update, name="partials", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
        scheduler.add_job(func=status_controller.update, name="controller", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=nft_recover.execute, name="nft_recover", trigger='interval', hours=12)

    # Testing only
    #scheduler.add_job(func=status_pools.update, trigger='interval', seconds=10) # Test immediately

    app.logger.debug("Starting background scheduler...")
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
