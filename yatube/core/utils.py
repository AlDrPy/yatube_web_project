from django.core.paginator import Paginator


def add_paginator(request, obj_list, number_of_obj):
    paginator = Paginator(obj_list, number_of_obj)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
