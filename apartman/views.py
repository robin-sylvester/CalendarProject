from django.shortcuts import render
from django.views.generic.edit import View
from .forms import UploadFileApartmanForm, UploadURLApartmanForm
from .models import Apartman, Customer
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Min, Max
from django.http import JsonResponse
import json
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from CalendarProject.decorators import contains_jwt

from icalendar import Calendar, Event
from datetime import date, datetime, timedelta
from django.contrib import messages
import pytz
import jwt
from pytz import UTC
import uuid
import requests
from pathlib import Path
import validators
import pandas as pd
import numpy as np


def importURLs(calendar, apartman):
    for component in calendar.walk():
        if component.name == "VEVENT":
            customer = Customer(uid=str(component.get('uid')), name=component.get('summary'),
                                begin_date=component.get('dtstart').dt, end_date=component.get('dtend').dt,
                                apartman=apartman)
            customer.save()


@method_decorator(contains_jwt, name='dispatch')
class ApartmanIcsView(View):
    form_class = UploadFileApartmanForm

    def get(self, request):
        form = UploadFileApartmanForm
        return render(request, 'apartman/upload_ics.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = UploadFileApartmanForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']

            calendar = Calendar.from_ical(file.read())
            apartman = Apartman(url=file)
            apartman.save()

            importURLs(calendar, apartman)
            messages.add_message(self.request, messages.SUCCESS, 'Calendar imported')

            return HttpResponseRedirect('/')
        else:
            messages.add_message(self.request, messages.ERROR, 'Calendar with that name was already imported')
            return HttpResponseRedirect('/')


@method_decorator(contains_jwt, name='dispatch')
class ApartmanUrlView(View):
    form_class = UploadURLApartmanForm

    def get(self, request):
        form = UploadURLApartmanForm
        return render(request, 'apartman/upload_url.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = UploadURLApartmanForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']

            calendar = Calendar.from_ical(requests.get(url).text)
            apartman = Apartman(url=url)
            apartman.save()

            importURLs(calendar, apartman)
            messages.add_message(self.request, messages.SUCCESS, 'Calendar imported')

            return HttpResponseRedirect('/')
        else:
            messages.add_message(self.request, messages.ERROR, 'That URL was already imported')
            return HttpResponseRedirect('/')


# cron job
def refreshURLs():
    apartmans = Apartman.objects.all()
    for apartman in apartmans:
        if validators.url(apartman.url):
            url = apartman.url
            calendar = Calendar.from_ical(requests.get(url).text)

            customers = Customer.objects.filter(apartman_id=apartman.id)
            for customer in customers:
                customer.delete()

            importURLs(calendar, apartman)
    print("Succesful cron job")


@method_decorator(contains_jwt, name='dispatch')
class ExportApartman(View):

    def get(self, request):
        calendars = Apartman.objects.all()
        return render(request, 'apartman/export.html', {'calendars': calendars})


@method_decorator(contains_jwt, name='dispatch')
class ExportApartmanByID(View):

    def get(self, request, pk):

        apartman_id = self.kwargs['pk']

        cal = Calendar()
        cal.add('attendee', 'MAILTO:abc@example.com')
        cal.add('attendee', 'MAILTO:xyz@example.com')

        customers = Customer.objects.filter(apartman_id=apartman_id)
        for customer in customers:
            event = Event()
            event.add('summary', customer.name)
            event.add('dtstart', date(customer.begin_date.year, customer.begin_date.month, customer.begin_date.day))
            event.add('dtend', date(customer.end_date.year, customer.end_date.month, customer.end_date.day))
            event.add('uid', customer.uid)
            cal.add_component(event)

        if cal.to_ical():
            response = HttpResponse(cal.to_ical(), content_type='text/calendar')
            response['Content-Disposition'] = 'attachment; filename=calendar_' + str(apartman_id) + '.ics'
            return response
        else:
            messages.add_message(self.request, messages.ERROR, 'Unable to export calendar')
            return HttpResponseRedirect('/')


def fill_dictionary(begin, end, apartman_id, calendars):

    min_date, max_date = margin_dates()

    customers = Customer.objects.filter(apartman_id=apartman_id).filter(begin_date__range=[min_date,end]).filter(end_date__range=[begin, max_date]).order_by('begin_date')
    num_of_days = (end - begin).days

    for single_date in (begin + timedelta(n) for n in range(num_of_days + 1)):
        calendars[single_date.strftime("%Y-%m-%d")] = "-"

    for customer in customers:

        if customer.begin_date < begin:
            pass
        else:
            if "IZLAZAK" in calendars[customer.begin_date.strftime("%Y-%m-%d")]:
                calendars[customer.begin_date.strftime("%Y-%m-%d")] = "IZLAZAK/ULAZAK"
            else:
                calendars[customer.begin_date.strftime("%Y-%m-%d")] = "ULAZAK"

        if customer.end_date > end:
            pass
        else:
            calendars[customer.end_date.strftime("%Y-%m-%d")] = "IZLAZAK"

        num_of_days = (customer.end_date - customer.begin_date).days
        for single_date in (customer.begin_date + timedelta(n + 1) for n in range(num_of_days - 1)):
            if single_date >= begin and single_date <= end:
                calendars[single_date.strftime("%Y-%m-%d")] = "ZAUZETO"

    return calendars


def margin_dates():
    customers = Customer.objects.all()
    min_date = customers.aggregate(Min('begin_date'))['begin_date__min']
    max_date = customers.aggregate(Max('end_date'))['end_date__max']
    return min_date, max_date


def date_algorithm(min_date, max_date):

    calendars = {}
    dates = set()

    apartmans = Apartman.objects.values('id')
    num_of_apartmans = apartmans.count()

    for apartman in apartmans:
        calendars[apartman['id']] = {}
        calendars[apartman['id']] = fill_dictionary(min_date, max_date, apartman['id'], calendars[apartman['id']])

    pandas = pd.DataFrame(calendars)
    pandas = pandas.replace(to_replace=["IZLAZAK/ULAZAK", "IZLAZAK", "ULAZAK", "-"], value=True)
    pandas = pandas.replace(to_replace="ZAUZETO", value=False)

    min_edge, max_edge = margin_dates()

    if min_edge == min_date:
        pandas = pandas.drop([min_date.strftime("%Y-%m-%d")])
    if max_edge == max_date:
        pandas = pandas.drop([max_date.strftime("%Y-%m-%d")])

    def dates_recursive(pd_dataframe, result_dates, nbr_of_apartmans):

        count_dict = {}
        for index, row in pd_dataframe.iterrows():
            try:
                count_dict[index] = int(row.value_counts()[True])
            except KeyError:
                count_dict[index] = 0
            finally:
                if count_dict[index] == nbr_of_apartmans:
                    result_dates.add(index)
                    return result_dates

        chosen_date = max(count_dict, key=count_dict.get)
        result_dates.add(chosen_date)
        chosen_series = pd_dataframe.loc[chosen_date, :]
        pd_dataframe = pd_dataframe.drop([chosen_date])

        for index, row in pd_dataframe.iterrows():
            first_array = np.array(chosen_series)
            second_array = row.values

            ser = np.array([])
            for i in np.arange(nbr_of_apartmans):
                temp = first_array[i] or second_array[i]
                ser = np.append(ser, temp)

            is_all_true = np.all((ser == True))
            if is_all_true:
                result_dates.add(index)
                return result_dates

        for index, element in chosen_series.items():
            if element:
                pd_dataframe = pd_dataframe.drop([index], axis=1)
                nbr_of_apartmans = nbr_of_apartmans - 1

        remain_index = pd_dataframe.index
        number_of_rows = len(remain_index)

        if number_of_rows == 1:
            result_dates.add(remain_index.values[0])
            return result_dates
        else:
            return dates_recursive(pd_dataframe, result_dates, nbr_of_apartmans)

    result = dates_recursive(pandas, dates, num_of_apartmans)
    return result, calendars


@contains_jwt
def get_dynamic_data(request):
    min_date_str = request.GET.get('begin_date')[1:-1]
    min_datetime = datetime.strptime(min_date_str, '%Y-%m-%d')
    min_date = min_datetime.date()

    max_date_str = request.GET.get('end_date')[1:-1]
    max_datetime = datetime.strptime(max_date_str, '%Y-%m-%d')
    max_date = max_datetime.date()

    if min_date == max_date:
        data = json.dumps({})
        return JsonResponse(data, safe=False)

    result, calendars = date_algorithm(min_date, max_date)

    temp_dict = {
        'calendar': calendars,
        'dates': list(result)
    }

    data = json.dumps(temp_dict)
    return JsonResponse(data, safe=False)


@method_decorator(contains_jwt, name='dispatch')
class Schedule(View):

    def get(self, request):

        apartmans = Apartman.objects.values('id')

        if not apartmans:
            return render(request, 'apartman/schedule.html', {'calendars': {}})

        min_date, max_date = margin_dates()
        result, calendars = date_algorithm(min_date, max_date)

        context = {
            'calendar': calendars,
            'dates': list(result)
        }

        return render(request, 'apartman/apartman_schedule.html', context)


@method_decorator(contains_jwt, name='dispatch')
class EmptyDatabase(View):
    def get(self, request):

        customers = Customer.objects.all()
        for customer in customers:
            customer.delete()

        apartmans = Apartman.objects.all()
        for apartman in apartmans:
            apartman.delete()

        messages.add_message(self.request, messages.SUCCESS, 'Database emptied')

        return HttpResponseRedirect('/')

