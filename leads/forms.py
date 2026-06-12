from django import forms

from .models import Lead, LeadNote


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["name", "email", "phone", "company", "source", "status", "assigned_to", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-select" if name in ("source", "status", "assigned_to") else "form-control"
            field.widget.attrs.setdefault("class", css)


class LeadNoteForm(forms.ModelForm):
    class Meta:
        model = LeadNote
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 2, "class": "form-control", "placeholder": "Add a note..."}
            )
        }
