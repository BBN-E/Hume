import re
import time
from datetime import datetime
from datetime import date
from datetime import timedelta
from calendar import monthrange

class TimeMatcher:
    def __init__(self):
        pass

    def match_time(self, tval, time_text, doc_date_str):
        earliestStartTime = None
        earliestEndTime = None
        latestStartTime = None
        latestEndTime = None
        
        earliestTime = None
        latestTime = None

        documentDate = None
        if doc_date_str is not None:
            try:
                documentDate = datetime.strptime(doc_date_str, "%Y-%m-%d")
            except ValueError:
                pass

        time_text = time_text.lower()

        ychk = re.compile('^\d{4}')
        mval = ychk.match(tval)
        if (mval):
            yearV = (int)(mval.group(0))
            # don't process
            if ((yearV < 1000) or (yearV > 2100)):
                return earliestTime, earliestTime, latestTime, latestTime

        fnorm = re.compile('^(\d{4})-\d{2}-\d{2}(?!T)')
        mval = fnorm.match(tval)
        if (mval):
            try:
                earliestTime = datetime.strptime(mval.group(0), "%Y-%m-%d")
            except ValueError:
                return earliestTime, earliestTime, latestTime, latestTime

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = earliestTime + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        fmonth = re.compile('^(\d{4})-(\d{2})$')
        mval = fmonth.match(tval)
        if (mval):
            try:
                earliestTime = datetime.strptime(mval.group(0), "%Y-%m")
            except ValueError:
                return earliestTime, earliestTime, latestTime, latestTime

            howManyDays = monthrange((int)(mval.group(1)), (int)(mval.group(2)))
            timeToAdd = timedelta(days=(howManyDays[1] - 1), hours=23, minutes=59, seconds=59)
            latestTime = earliestTime + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        fyear = re.compile('^\\b\d{4}(?!-)\\b')
        mval = fyear.match(tval)
        if (mval):
            try:
                earliestTime = datetime.strptime(mval.group(0), "%Y")
            except ValueError:
                return earliestTime, earliestTime, latestTime, latestTime
            # check if we're leapyear
            howManyDays = monthrange((int)(mval.group(0)), 2)
            timeToAdd = timedelta(days=(336 + howManyDays[1]), hours=23, minutes=59, seconds=59)
            latestTime = earliestTime + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        # ('^\d{4}-FA')
        fallm = re.compile('^(\d{4})-FA')
        mval = fallm.match(tval)
        if (mval):
            try:
                earliestTime = datetime((int)(mval.group(1)), 9, 1)
            except ValueError:
                return earliestTime, earliestTime, latestTime, latestTime

            endDate = datetime((int)(mval.group(1)), 11, 30)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = endDate + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        sall = re.compile('^(\d{4})-SU')
        mval = sall.match(tval)
        if (mval):
            try:
                earliestTime = datetime((int)(mval.group(1)), 6, 1)
            except ValueError:
                return earliestTime, earliestTime, latestTime, latestTime
            endDate = datetime((int)(mval.group(1)), 8, 31)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = endDate + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        spm = re.compile('^(\d{4})-SP')
        mval = spm.match(tval)
        if (mval):
            earliestTime = datetime((int)(mval.group(1)), 3, 1)
            endDate = datetime((int)(mval.group(1)), 5, 31)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = endDate + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        wim = re.compile('^(\d{4})-WI')
        mval = wim.match(tval)
        if (mval):
            earliestTime = datetime((int)(mval.group(1)), 12, 1)
            endDate = datetime((int)(mval.group(1)) + 1, 2, 28)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = endDate + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        q1m = re.compile('^(\d{4})-Q1')
        mval = q1m.match(tval)
        if (mval):
            earliestTime = datetime((int)(mval.group(1)), 1, 1)
            endDate = datetime((int)(mval.group(1)), 3, 31)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = endDate + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        q2m = re.compile('^(\d{4})-Q2')
        mval = q2m.match(tval)
        if (mval):
            earliestTime = datetime((int)(mval.group(1)), 4, 1)
            endDate = datetime((int)(mval.group(1)), 6, 30)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = endDate + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        q3m = re.compile('^(\d{4})-Q3')
        mval = q3m.match(tval)
        if (mval):
            earliestTime = datetime((int)(mval.group(1)), 7, 1)
            endDate = datetime((int)(mval.group(1)), 9, 30)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = endDate + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        q4m = re.compile('^(\d{4})-Q4')
        mval = q4m.match(tval)
        if (mval):
            earliestTime = datetime((int)(mval.group(1)), 10, 1)
            endDate = datetime((int)(mval.group(1)), 12, 31)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = endDate + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        h1y = re.compile('^(\d{4})-H1')
        mval = h1y.match(tval)
        if (mval):
            earliestTime = datetime((int)(mval.group(1)), 1, 1)
            endDate = datetime((int)(mval.group(1)), 6, 30)

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = endDate + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        h2y = re.compile('^(\d{4})-H2')
        mval = h2y.match(tval)
        if (mval):
            earliestTime = datetime((int)(mval.group(1)), 7, 1)
            endDate = datetime((int)(mval.group(1)), 12, 31)
            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = endDate + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        # deal with T values
        mval = re.match('^((\d{4})-\d{2}-\d{2})TMO', tval)
        if (mval):
            try:
                earliestTime = datetime.strptime(mval.group(1), "%Y-%m-%d")
            except ValueError:
                return earliestTime, earliestTime, latestTime, latestTime

            timeToAdd = timedelta(hours=11, minutes=59, seconds=59)

            latestTime = earliestTime + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        mval = re.match('^((\d{4})-\d{2}-\d{2})TAF', tval)
        if (mval):
            try:
                earliestTime = datetime.strptime(mval.group(1), "%Y-%m-%d")
            except ValueError:
                return earliestTime, earliestTime, latestTime, latestTime
            timeToAdd = timedelta(hours=12)
            earliestTime = earliestTime + timeToAdd

            timeToAdd = timedelta(hours=5, minutes=59, seconds=59)
            latestTime = earliestTime + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        mval = re.match('^((\d{4})-\d{2}-\d{2})TNI', tval)
        if (mval):
            try:
                earliestTime = datetime.strptime(mval.group(1), "%Y-%m-%d")
            except ValueError:
                return earliestTime, earliestTime, latestTime, latestTime

            latestTime = earliestTime
            timeToAdd = timedelta(hours=18)
            earliestTime = earliestTime + timeToAdd

            timeToAdd = timedelta(hours=23, minutes=59, seconds=59)
            latestTime = latestTime + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        mval = re.match('^((\d{4})-\d{2}-\d{2})TEV', tval)
        if (mval):
            try:
                earliestTime = datetime.strptime(mval.group(1), "%Y-%m-%d")
            except ValueError:
                return earliestTime, earliestTime, latestTime, latestTime

            latestTime = earliestTime
            timeToAdd = timedelta(hours=18)
            earliestTime = earliestTime + timeToAdd

            timeToAdd = timedelta(hours=21, minutes=59, seconds=59)
            latestTime = latestTime + timeToAdd
            return earliestTime, earliestTime, latestTime, latestTime

        # @hqiu from wm_m12_hackathon:
        mval = re.match(r'^(\d{4})-W(\d{2})',tval)
        if (mval):
            try:
                earliestTime = datetime.strptime(mval.group(0),"%Y-W%U")
            except ValueError:
                return earliestTime, earliestTime, latestTime, latestTime
            latestTime = earliestTime + timedelta(days=6,hours=23,minutes=59, seconds=59)
            return earliestTime, earliestTime, latestTime, latestTime

        mval = re.match(r'^(\d{4})-(\d{2})T(\d{2}:\d{2})',tval)
        if (mval):
            try:
                earliestTime = datetime.strptime(mval.group(0),"%Y-%mT%H:%M")
            except ValueError:
                return earliestTime, earliestTime, latestTime, latestTime
            latestTime = earliestTime + timedelta(seconds=59)
            return earliestTime, earliestTime, latestTime, latestTime

        if documentDate is not None and tval == "PAST_REF":
            latestTime = documentDate - timedelta(seconds=1)
            return None, None, latestTime, latestTime

        if documentDate is not None and tval == "FUTURE_REF":
            earliestTime = documentDate + timedelta(days=1)
            return earliestTime, earliestTime, None, None

        if documentDate is not None and tval == "PRESENT_REF":
            if (time_text.startswith("current") or
                time_text.startswith("modern") or
                time_text.startswith("present") or
                time_text.startswith("lately")):
                
                latestStartTime = documentDate - timedelta(seconds=1)
                return None, None, latestStartTime, None
            
            if (time_text == "now" or
                time_text == "right now" or
                time_text == "now immediately" or
                time_text.startswith("immediate")):

                latestStartTime = documentDate + timedelta(hours=23,minutes=59, seconds=59)
                return None, None, latestStartTime, None

            latestStartTime = documentDate + timedelta(hours=23,minutes=59, seconds=59)
            return None, None, latestStartTime, None

        return None, None, None, None
