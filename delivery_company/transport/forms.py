from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *


class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('клиент', 'Клиент'),
        ('водитель', 'Водитель'),
    ]

    # Переопределяем стандартные поля
    username = forms.CharField(label='Имя пользователя (Логин)', help_text='Только буквы, цифры и символы @/./+/-/_')

    # Общие поля
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Роль')
    phone = forms.CharField(max_length=20, required=True, label='Телефон')
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, label='Имя')
    last_name = forms.CharField(required=True, label='Фамилия')
    patronymic = forms.CharField(required=False, label='Отчество')

    # Поля водителя
    driving_license = forms.CharField(required=False, label='Водительские права')
    experience_years = forms.IntegerField(required=False, label='Стаж вождения (лет)', min_value=0)

    # Новое поле: Выбор автомобиля
    fleet_choice = forms.ChoiceField(label='Транспортное средство', required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'patronymic', 'phone', 'role',
                  'driving_license', 'experience_years', 'fleet_choice')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Формируем список выбора автомобиля
        fleet_choices = [('own', 'Свой автомобиль')]

        try:
            # ИЗМЕНЕНИЕ ЗДЕСЬ: ищем машины со статусом 'на стоянке'
            available_fleets = Fleet.objects.filter(status='на стоянке')
            for car in available_fleets:
                fleet_choices.append((str(car.id), str(car)))
        except Exception:
            pass

        self.fields['fleet_choice'].choices = fleet_choices
        self.fields['fleet_choice'].widget.attrs.update({'class': 'form-select'})

        self.fields['fleet_choice'].choices = fleet_choices
        # Добавляем класс bootstrap
        self.fields['fleet_choice'].widget.attrs.update({'class': 'form-select'})

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        if role == 'водитель':
            if not cleaned_data.get('driving_license'):
                self.add_error('driving_license', 'Для водителя обязательно указать права.')
            if cleaned_data.get('experience_years') is None:
                self.add_error('experience_years', 'Для водителя обязательно указать стаж.')
            # Проверяем, что водитель выбрал хоть что-то в списке машин
            if not cleaned_data.get('fleet_choice'):
                self.add_error('fleet_choice', 'Выберите транспортное средство.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            role = self.cleaned_data['role']
            phone = self.cleaned_data['phone']

            # Получаем общие данные (они теперь есть в форме для всех)
            patronymic = self.cleaned_data.get('patronymic', '')
            last_name = self.cleaned_data['last_name']
            first_name = self.cleaned_data['first_name']

            if role == 'клиент':
                Client.objects.create(
                    user=user,
                    phone=phone,
                    # Добавляем сохранение полей в модель Client
                    last_name=last_name,
                    first_name=first_name,
                    patronymic=patronymic
                )

            elif role == 'водитель':
                # ... код для водителя остается прежним ...
                # (код с fleet_choice и созданием Driver)
                # ...
                choice = self.cleaned_data.get('fleet_choice')
                assigned_fleet = None

                if choice and choice != 'own':
                    try:
                        assigned_fleet = Fleet.objects.get(id=int(choice))
                    except Fleet.DoesNotExist:
                        assigned_fleet = None

                Driver.objects.create(
                    user=user,
                    phone=phone,
                    last_name=last_name,
                    first_name=first_name,
                    patronymic=patronymic,
                    driving_license=self.cleaned_data.get('driving_license', ''),
                    experience_years=self.cleaned_data.get('experience_years', 0),
                    status='свободен',
                    fleet=assigned_fleet
                )
        return user


# Остальные формы (DeliveryForm, CargoForm, RouteForm) без изменений
class DeliveryForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = ['delivery_type']
        widgets = {
            'delivery_type': forms.Select(attrs={'class': 'form-control'}),
        }


class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ['name', 'weight']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = [
            'departure_city', 'departure_street', 'departure_house',
            'arrival_city', 'arrival_street', 'arrival_house',
            'distance'
        ]
        widgets = {
            'departure_city': forms.TextInput(attrs={'class': 'form-control'}),
            'departure_street': forms.TextInput(attrs={'class': 'form-control'}),
            'departure_house': forms.TextInput(attrs={'class': 'form-control'}),
            'arrival_city': forms.TextInput(attrs={'class': 'form-control'}),
            'arrival_street': forms.TextInput(attrs={'class': 'form-control'}),
            'arrival_house': forms.TextInput(attrs={'class': 'form-control'}),
            'distance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['content']
        labels = {
            'content': 'Ваш отзыв',
        }
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Напишите, как прошла доставка...'
            }),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['method']
        labels = {
            'method': 'Способ оплаты'
        }
        widgets = {
            'method': forms.Select(attrs={'class': 'form-select'}),
        }


class RefuelingForm(forms.ModelForm):
    class Meta:
        model = Refueling
        fields = ['fuel_type', 'liters', 'cost_per_liter']
        labels = {
            'fuel_type': 'Вид топлива',
            'liters': 'Количество литров',
            'cost_per_liter': 'Цена за литр (руб)',
        }
        widgets = {
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'liters': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Например: 45.5'}),
            'cost_per_liter': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Например: 55.00'}),
        }