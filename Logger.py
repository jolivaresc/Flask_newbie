from time import strftime
def Logger(msg,app):
    logger = open('logger.dat','a+')
    logger.write('['+strftime("%c")+'] '+ msg +'\n')
    app.logger.info(msg)
    logger.close()
