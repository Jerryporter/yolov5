resultList = []
finishOnePic = False


def finishProcOnePic():
    global finishOnePic,resultList
    if not resultList:
        pass
    else:
        finishOnePic = True


def startProcOnePic():
    global finishOnePic, resultList
    resultList.clear()
    finishOnePic = False
