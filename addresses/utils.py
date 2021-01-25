from datetime import datetime, timedelta
from calendar import HTMLCalendar
from .models import DeliveryFrequency, BillingProfile

class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    def formatday(self, day, events):
        events_per_day = events.filter(delivery_start__day=day)
        d = ''
        for event in events_per_day:
            d += f'<li class="calendar_list"> {event.get_html_url} </li>'
        if day != 0:
            return f"<td><span class='date'>{day}</span><ul> {d} </ul></td>"
        return '<td></td>'

    def formatweek(self, theweek, events):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f'<tr> {week} </tr>'

    def formatmonth(self, withyear=True):
        events = DeliveryFrequency.objects.filter(delivery_start__year=self.year, delivery_start__month=self.month)
        cal = f'<table class="table calendar" border="0" cellpadding="0" cellspacing="0">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, events)}\n'
        cal += '</table>'
        return cal


class MyCalendar(HTMLCalendar):
    def __init__(self, billing_profile, year=None, month=None):
        super(MyCalendar, self).__init__()
        self.year = year
        self.month = month
        self.billing_profile = billing_profile
        print(self.billing_profile, "2")

    def formatday(self, day, events):
        events_per_day = events.filter(delivery_start__day=day)
        d = ''
        for event in events_per_day:
            # d += f'<li class="calendar_list"> {event.get_html_url} </li>'
            d += f'<span class="maroon-text"> {event.get_html_url} </span>'
        if day != 0:
            return f"<td><span class='date'>{day}</span> {d} </td>"
        return '<td></td>'

    def formatweek(self, theweek, events):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f'<tr> {week} </tr>'

    def formatmonth(self, withyear=True):
        events = DeliveryFrequency.objects.filter(delivery_start__year=self.year, delivery_start__month=self.month, billing_profile=self.billing_profile)
        print(events)
        cal = f'<table class="table table-sm calendar" border="0" cellpadding="0" cellspacing="0">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, events)}\n'
        cal += '</table>'
        return cal