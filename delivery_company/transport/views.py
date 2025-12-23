from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import *
from decimal import Decimal


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # После регистрации сразу перенаправляем в нужный дашборд
                return home(request)
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def home(request):
    if request.user.is_authenticated:
        # Сразу перенаправляем в соответствующий дашборд
        if hasattr(request.user, 'client'):
            return redirect('client_dashboard')
        elif hasattr(request.user, 'driver'):
            return redirect('driver_dashboard')
        elif request.user.is_staff:
            return redirect('/admin/')
            # Если не авторизован - показываем логин
    return redirect('login')


@login_required
def dashboard(request):
    # А эту функцию используем для перенаправления по ролям
    if hasattr(request.user, 'client'):
        return redirect('client_dashboard')
    elif hasattr(request.user, 'driver'):
        return redirect('driver_dashboard')
    elif request.user.is_staff:
        return redirect('/admin/')
    return redirect('home')


# Клиентские представления
@login_required
def client_dashboard(request):
    if not hasattr(request.user, 'client'):
        return HttpResponseForbidden("Доступ запрещен")

    client = request.user.client
    deliveries = Delivery.objects.filter(client=client).order_by('-created_at')

    context = {
        'client': client,
        'deliveries': deliveries,
    }
    return render(request, 'client/dashboard.html', context)


@login_required
def create_delivery(request):
    if not hasattr(request.user, 'client'):
        return HttpResponseForbidden("Доступ запрещен")

    client = request.user.client
    calculated_price = None  # Переменная для цены

    if request.method == 'POST':
        delivery_form = DeliveryForm(request.POST)
        cargo_form = CargoForm(request.POST)
        route_form = RouteForm(request.POST)

        # Получаем действие (какая кнопка нажата)
        action = request.POST.get('action')

        if all([delivery_form.is_valid(), cargo_form.is_valid(), route_form.is_valid()]):
            # 1. Логика расчета цены (для отображения)
            weight = cargo_form.cleaned_data.get('weight', 0)
            distance = route_form.cleaned_data.get('distance', 0)

            # Формула: 50 руб/км + 10 руб/кг (минимум 500)
            price = (distance * Decimal('50.00')) + (weight * Decimal('10.00'))
            if price < 500:
                price = Decimal('500.00')

            calculated_price = price

            # 2. Если нажата кнопка "Подтвердить" (create), сохраняем в БД
            if action == 'create':
                cargo = cargo_form.save()

                delivery = delivery_form.save(commit=False)
                delivery.client = client
                delivery.cargo = cargo
                delivery.status = 'оформлен'
                delivery.save()

                route = route_form.save(commit=False)
                route.delivery = delivery
                route.save()

                return redirect('client_dashboard')

            # Если action == 'calculate', код просто пойдет дальше и отобразит страницу с calculated_price

    else:
        delivery_form = DeliveryForm()
        cargo_form = CargoForm()
        route_form = RouteForm()

    context = {
        'delivery_form': delivery_form,
        'cargo_form': cargo_form,
        'route_form': route_form,
        'calculated_price': calculated_price,  # Передаем цену в шаблон
    }
    return render(request, 'client/create_delivery.html', context)


@login_required
def delete_delivery(request, delivery_id):
    if not hasattr(request.user, 'client'):
        return HttpResponseForbidden("Доступ запрещен")

    client = request.user.client
    delivery = get_object_or_404(Delivery, id=delivery_id, client=client)

    if delivery.status == 'оформлен' and delivery.driver is None:
        delivery.status = 'отменён'
        delivery.save()

    return redirect('client_dashboard')


@login_required
def client_profile(request):
    if not hasattr(request.user, 'client'):
        return HttpResponseForbidden("Доступ запрещен")

    client = request.user.client
    total_deliveries = Delivery.objects.filter(client=client).count()
    completed_deliveries = Delivery.objects.filter(client=client, status='доставлен').count()
    active_deliveries = Delivery.objects.filter(client=client).exclude(status__in=['доставлен', 'отменён']).count()

    context = {
        'client': client,
        'total_deliveries': total_deliveries,
        'completed_deliveries': completed_deliveries,
        'active_deliveries': active_deliveries,
    }
    return render(request, 'client/profile.html', context)


# Водительские представления
@login_required
def driver_dashboard(request):
    if not hasattr(request.user, 'driver'):
        return HttpResponseForbidden("Доступ запрещен")

    driver = request.user.driver
    current_deliveries = Delivery.objects.filter(driver=driver).exclude(status__in=['доставлен', 'отменён'])

    context = {
        'driver': driver,
        'current_deliveries': current_deliveries,
    }
    return render(request, 'driver/dashboard.html', context)


@login_required
def available_deliveries(request):
    if not hasattr(request.user, 'driver'):
        return HttpResponseForbidden("Доступ запрещен")

    driver = request.user.driver
    available_deliveries = Delivery.objects.filter(
        status='оформлен',
        driver__isnull=True
    ).select_related('cargo', 'client', 'route')

    context = {
        'driver': driver,
        'available_deliveries': available_deliveries,
    }
    return render(request, 'driver/available_deliveries.html', context)


@login_required
def accept_delivery(request, delivery_id):
    if not hasattr(request.user, 'driver'):
        return HttpResponseForbidden("Доступ запрещен")

    driver = request.user.driver
    delivery = get_object_or_404(Delivery, id=delivery_id, status='оформлен', driver__isnull=True)

    if driver.status == 'свободен':
        # 1. Обновляем доставку
        delivery.driver = driver
        delivery.status = 'в пути'
        delivery.save()

        # 2. Обновляем водителя
        driver.status = 'в пути'
        driver.save()

        # 3. Обновляем статус машины (если она есть)
        if driver.fleet:
            driver.fleet.status = 'используется'
            driver.fleet.save()

    return redirect('driver_dashboard')


@login_required
def cancel_delivery(request, delivery_id):
    if not hasattr(request.user, 'driver'):
        return HttpResponseForbidden("Доступ запрещен")

    driver = request.user.driver
    delivery = get_object_or_404(Delivery, id=delivery_id, driver=driver, status='в пути')

    # 1. Сбрасываем доставку
    delivery.driver = None
    delivery.status = 'оформлен'
    delivery.save()

    # 2. Освобождаем водителя
    driver.status = 'свободен'
    driver.save()

    # 3. Освобождаем машину (возвращаем на стоянку)
    if driver.fleet:
        driver.fleet.status = 'на стоянке'
        driver.fleet.save()

    return redirect('driver_dashboard')


@login_required
def complete_delivery(request, delivery_id):
    if not hasattr(request.user, 'driver'):
        return HttpResponseForbidden("Доступ запрещен")

    driver = request.user.driver
    delivery = get_object_or_404(Delivery, id=delivery_id, driver=driver, status='в пути')

    # 1. Завершаем доставку
    delivery.status = 'доставлен'
    delivery.save()

    # 2. Освобождаем водителя
    driver.status = 'свободен'
    driver.save()

    # 3. Освобождаем машину (возвращаем на стоянку)
    if driver.fleet:
        driver.fleet.status = 'на стоянке'
        driver.fleet.save()

    return redirect('driver_dashboard')


@login_required
def driver_profile(request):
    if not hasattr(request.user, 'driver'):
        return HttpResponseForbidden("Доступ запрещен")

    driver = request.user.driver
    total_deliveries = Delivery.objects.filter(driver=driver).count()
    completed_deliveries = Delivery.objects.filter(driver=driver, status='доставлен').count()
    current_deliveries = Delivery.objects.filter(driver=driver).exclude(status__in=['доставлен', 'отменён']).count()

    context = {
        'driver': driver,
        'total_deliveries': total_deliveries,
        'completed_deliveries': completed_deliveries,
        'current_deliveries': current_deliveries,
    }
    return render(request, 'driver/profile.html', context)


@login_required
def leave_feedback(request, delivery_id):
    if not hasattr(request.user, 'client'):
        return HttpResponseForbidden("Доступ запрещен")

    client = request.user.client
    # Получаем доставку, которая завершена и принадлежит этому клиенту
    delivery = get_object_or_404(Delivery, id=delivery_id, client=client, status='доставлен')

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            # Проверяем, нет ли уже отзыва на эту доставку
            if Feedback.objects.filter(delivery=delivery).exists():
                # Если отзыв уже есть, просто обновляем страницу (или можно вывести сообщение)
                return redirect('client_dashboard')

            feedback = form.save(commit=False)
            feedback.delivery = delivery
            feedback.client = client
            feedback.save()

    return redirect('client_dashboard')


@login_required
def make_payment(request, delivery_id):
    if not hasattr(request.user, 'client'):
        return HttpResponseForbidden("Доступ запрещен")

    client = request.user.client
    delivery = get_object_or_404(Delivery, id=delivery_id, client=client, status='доставлен')

    if delivery.payment_set.exists():
        return redirect('client_dashboard')

    # ИСПОЛЬЗУЕМ НОВЫЙ МЕТОД МОДЕЛИ
    calculated_amount = delivery.get_price()

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.delivery = delivery
            payment.amount = calculated_amount
            payment.status = 'проведён'
            payment.save()
            return redirect('client_dashboard')

    return redirect('client_dashboard')


@login_required
def add_refueling(request):
    if not hasattr(request.user, 'driver'):
        return HttpResponseForbidden("Доступ запрещен")

    driver = request.user.driver

    # Проверка: есть ли у водителя служебное авто
    if not driver.fleet:
        # Можно вывести ошибку или просто перенаправить
        return render(request, 'driver/error_no_fleet.html', {
            'message': 'Заправка доступна только для служебных автомобилей парка.'
        })

    if request.method == 'POST':
        form = RefuelingForm(request.POST)
        if form.is_valid():
            refueling = form.save(commit=False)
            refueling.driver = driver
            refueling.fleet = driver.fleet
            # total_cost посчитается автоматически в методе save() модели
            refueling.save()
            return redirect('driver_dashboard')
    else:
        form = RefuelingForm()

    return render(request, 'driver/add_refueling.html', {'form': form})