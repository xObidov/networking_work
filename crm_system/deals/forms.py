from django import forms

from .models import Deal


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ["name", "customer", "value", "stage", "expected_close_date", "owner", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "expected_close_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-select" if name in ("customer", "stage", "owner") else "form-control"
            field.widget.attrs.setdefault("class", css)
