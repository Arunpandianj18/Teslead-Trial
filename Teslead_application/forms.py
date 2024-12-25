from django import forms
# from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        # model = Product
        fields = [
            'product_id', 'product_name', 'product_description', 'size', 'class_field', 'type_field',
            'hshell_set_pressure', 'hshell_set_holding_time', 'hshell_set_duration',
            'hseat_set_pressure', 'hseat_set_holding_time', 'hseat_set_duration',
            'ashell_set_pressure', 'ashell_set_holding_time', 'ashell_set_duration',
            'aseat_set_pressure', 'aseat_set_holding_time', 'aseat_set_duration'
        ]

class AlarmForm(forms.Form):
    alarm_id = forms.CharField(max_length=100)  # Adjust max_length as needed
    alarm_name = forms.CharField(max_length=100)  # Adjust max_length as needed