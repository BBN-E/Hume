import re
import time
from datetime import datetime
from datetime import date
from datetime import timedelta
from calendar import monthrange

class TimeMatcher:
    def __init__(self):
        pass

    def match_time(self, tval):
        startDate = None
        endTime = None

        ychk = re.compile('^\d{4}')
        mval = ychk.match(tval)
        if (mval):
            yearV = (int)(mval.group(0))
            # don't process
            if ((yearV < 1000) or (yearV > 2100)):
                return startDate, endTime

        fnorm = re.compile('^(\d{4})-\d{2}-\d{2}(?!T)')
        mval = fnorm.match(tval)
        if (mval):
            try:
                startDate = datetime.strptime(mval.group(0), "%Y-%m-%d")
            except ValueError:
                return startDate, endTime

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = startDate + timeToAdd
            return startDate, endTime

        fmonth = re.compile('^(\d{4})-(\d{2})$')
        mval = fmonth.match(tval)
        if (mval):
            try:
                startDate = datetime.strptime(mval.group(0), "%Y-%m")
            except ValueError:
                return startDate, endTime

            howManyDays = monthrange((int)(mval.group(1)), (int)(mval.group(2)))
            timeToAdd = timedelta(days=(howManyDays[1] - 1), hours=23, minutes=59, seconds=59)
            endTime = startDate + timeToAdd
            return startDate, endTime

        fyear = re.compile('^\\b\d{4}(?!-)\\b')
        mval = fyear.match(tval)
        if (mval):
            try:
                startDate = datetime.strptime(mval.group(0), "%Y")
            except ValueError:
                return startDate, endTime
            # check if we're leapyear
            howManyDays = monthrange((int)(mval.group(0)), 2)
            timeToAdd = timedelta(days=(336 + howManyDays[1]), hours=23, minutes=59, seconds=59)
            endTime = startDate + timeToAdd
            return startDate, endTime

        # ('^\d{4}-FA')
        fallm = re.compile('^(\d{4})-FA')
        mval = fallm.match(tval)
        if (mval):
            try:
                startDate = datetime((int)(mval.group(1)), 9, 1)
            except ValueError:
                return startDate, endTime

            endDate = datetime((int)(mval.group(1)), 11, 30)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = endDate + timeToAdd
            return startDate, endTime

        sall = re.compile('^(\d{4})-SU')
        mval = sall.match(tval)
        if (mval):
            try:
                startDate = datetime((int)(mval.group(1)), 6, 1)
            except ValueError:
                return startDate, endTime
            endDate = datetime((int)(mval.group(1)), 8, 31)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = endDate + timeToAdd
            return startDate, endTime

        spm = re.compile('^(\d{4})-SP')
        mval = spm.match(tval)
        if (mval):
            startDate = datetime((int)(mval.group(1)), 3, 1)
            endDate = datetime((int)(mval.group(1)), 5, 31)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = endDate + timeToAdd
            return startDate, endTime

        wim = re.compile('^(\d{4})-WI')
        mval = wim.match(tval)
        if (mval):
            startDate = datetime((int)(mval.group(1)), 12, 1)
            endDate = datetime((int)(mval.group(1)) + 1, 2, 28)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = endDate + timeToAdd
            return startDate, endTime

        q1m = re.compile('^(\d{4})-Q1')
        mval = q1m.match(tval)
        if (mval):
            startDate = datetime((int)(mval.group(1)), 1, 1)
            endDate = datetime((int)(mval.group(1)), 3, 31)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = endDate + timeToAdd
            return startDate, endTime

        q2m = re.compile('^(\d{4})-Q2')
        mval = q2m.match(tval)
        if (mval):
            startDate = datetime((int)(mval.group(1)), 4, 1)
            endDate = datetime((int)(mval.group(1)), 6, 30)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = endDate + timeToAdd
            return startDate, endTime

        q3m = re.compile('^(\d{4})-Q3')
        mval = q3m.match(tval)
        if (mval):
            startDate = datetime((int)(mval.group(1)), 7, 1)
            endDate = datetime((int)(mval.group(1)), 9, 30)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = endDate + timeToAdd
            return startDate, endTime

        q4m = re.compile('^(\d{4})-Q4')
        mval = q4m.match(tval)
        if (mval):
            startDate = datetime((int)(mval.group(1)), 10, 1)
            endDate = datetime((int)(mval.group(1)), 12, 31)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = endDate + timeToAdd
            return startDate, endTime

        h1y = re.compile('^(\d{4})-H1')
        mval = h1y.match(tval)
        if (mval):
            startDate = datetime((int)(mval.group(1)), 1, 1)
            endDate = datetime((int)(mval.group(1)), 6, 30)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = endDate + timeToAdd
            return startDate, endTime

        h2y = re.compile('^(\d{4})-H2')
        mval = h2y.match(tval)
        if (mval):
            startDate = datetime((int)(mval.group(1)), 7, 1)
            endDate = datetime((int)(mval.group(1)), 12, 31)
            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = endDate + timeToAdd
            return startDate, endTime

        # deal with T values
        mval = re.match('^((\d{4})-\d{2}-\d{2})TMO', tval)
        if (mval):
            try:
                startDate = datetime.strptime(mval.group(1), "%Y-%m-%d")
            except ValueError:
                return startDate, endTime

            timeToAdd = timedelta(hours=11, minutes=59, seconds=59)

            endTime = startDate + timeToAdd
            return startDate, endTime

        mval = re.match('^((\d{4})-\d{2}-\d{2})TAF', tval)
        if (mval):
            try:
                startDate = datetime.strptime(mval.group(1), "%Y-%m-%d")
            except ValueError:
                return startDate, endTime
            timeToAdd = timedelta(hours=12)
            startDate = startDate + timeToAdd

            timeToAdd = timedelta(hours=5, minutes=59, seconds=59)
            endTime = startDate + timeToAdd
            return startDate, endTime

        mval = re.match('^((\d{4})-\d{2}-\d{2})TNI', tval)
        if (mval):
            try:
                startDate = datetime.strptime(mval.group(1), "%Y-%m-%d")
            except ValueError:
                return startDate, endTime

            endTime = startDate
            timeToAdd = timedelta(hours=18)
            startDate = startDate + timeToAdd

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            endTime = endTime + timeToAdd
            return startDate, endTime

        mval = re.match('^((\d{4})-\d{2}-\d{2})TEV', tval)
        if (mval):
            try:
                startDate = datetime.strptime(mval.group(1), "%Y-%m-%d")
            except ValueError:
                return startDate, endTime

            endTime = startDate
            timeToAdd = timedelta(hours=18)
            startDate = startDate + timeToAdd

            timeToAdd = timedelta(hours=21, minutes=59, seconds=59)
            endTime = endTime + timeToAdd
            return startDate, endTime

        # @hqiu from wm_m12_hackathon:
        mval = re.match(r'^(\d{4})-W(\d{2})',tval)
        if (mval):
            try:
                startDate = datetime.strptime(mval.group(0),"%Y-W%U")
            except ValueError:
                return startDate, endTime
            endTime = startDate + timedelta(days=6,hours=23,minutes=59, seconds=59)
            return startDate,endTime

        mval = re.match(r'^(\d{4})-(\d{2})T(\d{2}:\d{2})',tval)
        if (mval):
            try:
                startDate = datetime.strptime(mval.group(0),"%Y-%mT%H:%M")
            except ValueError:
                return startDate, endTime
            endTime = startDate + timedelta(seconds=59)
            return startDate,endTime


        return None, None