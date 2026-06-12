from django import forms

from .models import Invoice


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["customer", "deal", "amount", "tax_rate", "status", "due_date"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-select" if name in ("customer", "deal", "status") else "form-control"
            field.widget.attrs.setdefault("class", css)
