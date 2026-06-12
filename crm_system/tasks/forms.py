from django import forms

from .models import Task, TaskAttachment, TaskComment


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "assigned_to", "priority", "status", "due_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-select" if name in ("assigned_to", "priority", "status") else "form-control"
            field.widget.attrs.setdefault("class", css)


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 2, "class": "form-control", "placeholder": "Write a comment..."}
            )
        }


class TaskAttachmentForm(forms.ModelForm):
    class Meta:
        model = TaskAttachment
        fields = ["file"]
        widgets = {"file": forms.ClearableFileInput(attrs={"class": "form-control"})}
