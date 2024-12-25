from datetime import datetime
from django.db import models

class Cell(models.Model):
    cell_id = models.IntegerField()

    def __str__(self):
        return str(self.cell_id)

class OPRToken(models.Model):
    opr_token = models.CharField(max_length=6)

    def __str__(self):
        return self.opr_token

class FirstName(models.Model):
    first_name = models.CharField(max_length=20)

    def __str__(self):
        return self.first_name

class LastName(models.Model):
    last_name = models.CharField(max_length=20)

    def __str__(self):
        return self.last_name
    
class Operator(models.Model):
    cell_id = models.CharField(max_length=10)
    opr_token = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100, default="Unknown")  # Default value added
    last_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'operator_tbl'

class PressureAnalysis(models.Model):
    valve_serial_number = models.CharField(max_length=100)
    valve_status = models.CharField(max_length=50)
    set_pressure = models.DecimalField(max_digits=10, decimal_places=2)
    set_time = models.IntegerField()  # Change to IntegerField if it’s a timestamp

    @property
    def formatted_set_time(self):
        return datetime.fromtimestamp(self.set_time) if isinstance(self.set_time, int) else self.set_time

    class Meta:
        db_table = 'pressure_analysis'

class AlarmDetails(models.Model):
    alarm_id = models.CharField(max_length=100)
    alarm_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'alarm_details'