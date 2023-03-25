import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    current_year = int(datetime.datetime.now().strftime("%Y"))
    return {
        'year': current_year
    }
