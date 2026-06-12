from django import forms

from .models import Customer, CustomerDocument


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "first_name", "last_name", "email", "phone", "company", "position",
            "address", "city", "country", "status", "tags", "owner", "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "tags": forms.SelectMultiple(attrs={"size": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-select" if name in ("status", "tags", "owner") else "form-control"
            field.widget.attrs.setdefault("class", css)


class CustomerDocumentForm(forms.ModelForm):
    class Meta:
        model = CustomerDocument
        fields = ["name", "file"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
