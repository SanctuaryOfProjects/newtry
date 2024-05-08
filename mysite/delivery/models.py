from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from geopy.geocoders import ArcGIS
import osmnx as ox
import networkx as nx

class Establishment(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    photo = models.FileField(upload_to='est/', verbose_name="Фото")
    adress = models.CharField(max_length=120, verbose_name='Адрес')
    phone = models.CharField(max_length=11, verbose_name='Телефон')
    verification = models.BooleanField(default=False, verbose_name="Верификация")
    bin = models.CharField(max_length=20, verbose_name="БИН")
    work_schedule = models.CharField(max_length=100, verbose_name="График работы")
    legal_info = models.TextField(verbose_name="Юридическая информация")
    documentation = models.FileField(upload_to='documentation/', verbose_name="Документация")
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Заведение"
        verbose_name_plural = "Заведения"

class Courier(models.Model):
    fullname = models.CharField(max_length=100, verbose_name='ФИО')
    email = models.EmailField(verbose_name='Email')
    work_phone = models.CharField(max_length=11, verbose_name='Телефон')
    photo = models.FileField(upload_to='couriers/', verbose_name="Фото")
    username = models.CharField(max_length=50, unique=True, verbose_name="Логин")
    password = models.CharField(max_length=50, verbose_name="Пароль")
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь", blank=True, null=True)
    is_courier = models.BooleanField(default=True, verbose_name="Курьер")

    def __str__(self):
        return self.fullname
    
    
    class Meta:
        verbose_name = "Курьер"
        verbose_name_plural = "Курьеры"


class EstCouriers(models.Model):
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE, verbose_name='Заведение')
    courier = models.ForeignKey(Courier, on_delete=models.CASCADE, verbose_name='Курьер', related_name='establishments', null=True)
    def __str__(self):
        return f"{self.courier.fullname} - {self.establishment.name}"
    
    class Meta:
        verbose_name = "Курьеры заведения"
        verbose_name_plural = "Курьеры заведения"

class Order(models.Model):
    STATUS_CHOICES = [
        ('Обработан', 'Обработан'),
        ('Доставляется', 'Доставляется'),
        ('Доставлен', 'Доставлен'),
        ('Отменен', 'Отменен'),
    ]
    sender = models.ForeignKey(Establishment, on_delete=models.CASCADE, related_name='sent_orders', verbose_name="Отправитель")
    recipient = models.CharField(max_length=100, verbose_name="Получатель")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Обработан', verbose_name="Статус")
    origin = models.CharField(max_length=100, verbose_name="Точка отправления")
    destination = models.CharField(max_length=100, verbose_name="Точка назначения")
    route_link = models.URLField(blank=True, verbose_name="Ссылка на маршрут")
    courier = models.ForeignKey(Courier, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Курьер заказа")
    courier_latitude = models.FloatField(blank=True, null=True, verbose_name="Широта курьера")
    courier_longitude = models.FloatField(blank=True, null=True, verbose_name="Долгота курьера")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время заказа")
    comment = models.TextField(verbose_name="Комментарий", blank=True, null=True)

    def save(self, *args, **kwargs):
        geolocator = ArcGIS(timeout=5)
        location_origin = geolocator.geocode(self.origin)
        location_destination = geolocator.geocode(self.destination)

        G = ox.graph_from_place('Караганда, Карагандинская область, Казахстан', network_type='walk')
        node_origin = ox.distance.nearest_nodes(G, location_origin.longitude, location_origin.latitude)
        node_destination = ox.distance.nearest_nodes(G, location_destination.longitude, location_destination.latitude)
        shortest_path = nx.shortest_path(G, node_origin, node_destination, weight='length')

        """if self.courier is not None:
            location_courier = geolocator.geocode(self.courier.address)
            if location_courier:
                self.courier_latitude = location_courier.latitude
                self.courier_longitude = location_courier.longitude"""

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sender.name} - {self.date}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

class Penalty(models.Model):
    courier = models.ForeignKey(Courier, on_delete=models.CASCADE, verbose_name="Курьер")
    penalty_type = models.CharField(max_length=100, verbose_name="Тип штрафа")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    reason = models.TextField(verbose_name="Причина")
    def __str__(self):
        return f"{self.courier.user.username} - {self.penalty_type}"

    class Meta:
        verbose_name = "Штраф"
        verbose_name_plural = "Штрафы"

class Schedule(models.Model):
    courier = models.ForeignKey(Courier, on_delete=models.CASCADE, verbose_name="Курьер")
    est = models.ForeignKey(Establishment, on_delete=models.CASCADE, verbose_name="Заведение")
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Начало смены")
    end_time = models.TimeField(verbose_name="Конец смены")
    skip = models.BooleanField(default=False, blank=True , verbose_name="Пропуск" )
    def __str__(self):
        return f"{self.courier.fullname} - {self.date}"
    
    class Meta:
        verbose_name = "График работы"
        verbose_name_plural = "График работы"

class Salary(models.Model):
    courier = models.ForeignKey(Courier, on_delete=models.CASCADE, verbose_name="Курьер")
    working_hours = models.PositiveIntegerField(verbose_name="Часы работы")
    money_per_hour = models.PositiveIntegerField(verbose_name="З/П в час")
    def __str__(self):
        return self.courier.fullname
    
    class Meta:
            verbose_name = "Зарплата"
            verbose_name_plural = "Зарплата"