from django import forms

from .models import Ticket, TicketReply


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["customer", "subject", "description", "priority", "status", "assigned_to"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-select" if name in ("customer", "priority", "status", "assigned_to") else "form-control"
            field.widget.attrs.setdefault("class", css)


class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 3, "class": "form-control", "placeholder": "Write a reply..."}
            )
        }
