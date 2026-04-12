from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import ACCESS_END_TIME, ACCESS_START_TIME, Booking, Resource, UserProfile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    department = forms.CharField(max_length=120, required=True)
    phone = forms.CharField(max_length=20, required=True)
    role = forms.ChoiceField(choices=UserProfile.Role.choices, initial=UserProfile.Role.STUDENT)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "department",
            "phone",
            "role",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["role"].widget.attrs["class"] = "form-select"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        role = self.cleaned_data["role"]
        user.is_staff = role in {UserProfile.Role.STAFF, UserProfile.Role.ADMIN}
        if commit:
            user.save()
            profile = user.userprofile
            profile.role = role
            profile.department = self.cleaned_data["department"]
            profile.phone = self.cleaned_data["phone"]
            profile.save()
        return user


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = [
            "name",
            "resource_type",
            "building",
            "floor",
            "location_detail",
            "capacity",
            "features",
            "description",
            "source_name",
            "source_url",
            "hourly_cost",
            "requires_approval",
            "available_from",
            "available_until",
            "status",
        ]
        widgets = {
            "features": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "source_url": forms.URLInput(attrs={"placeholder": "https://example.com/resource-page"}),
            "available_from": forms.TimeInput(attrs={"type": "time"}),
            "available_until": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["resource_type"].widget.attrs["class"] = "form-select"
        self.fields["status"].widget.attrs["class"] = "form-select"
        self.fields["requires_approval"].widget.attrs["class"] = "form-check-input"
        self.fields["available_from"].widget.attrs["min"] = ACCESS_START_TIME.strftime("%H:%M")
        self.fields["available_from"].widget.attrs["max"] = ACCESS_END_TIME.strftime("%H:%M")
        self.fields["available_until"].widget.attrs["min"] = ACCESS_START_TIME.strftime("%H:%M")
        self.fields["available_until"].widget.attrs["max"] = ACCESS_END_TIME.strftime("%H:%M")


class BookingForm(forms.ModelForm):
    requested_start = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    requested_end = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Booking
        fields = [
            "resource",
            "title",
            "purpose",
            "attendees",
            "requested_start",
            "requested_end",
            "priority",
        ]
        widgets = {
            "purpose": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resource"].queryset = Resource.objects.filter(status=Resource.Status.ACTIVE)
        current_local = timezone.localtime().replace(second=0, microsecond=0)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["resource"].widget.attrs["class"] = "form-select"
        self.fields["priority"].widget.attrs["class"] = "form-select"
        self.fields["requested_start"].widget.attrs["min"] = current_local.strftime("%Y-%m-%dT%H:%M")
        self.fields["requested_end"].widget.attrs["min"] = current_local.strftime("%Y-%m-%dT%H:%M")
        self.fields["requested_start"].widget.attrs["step"] = 60
        self.fields["requested_end"].widget.attrs["step"] = 60
        if self.instance.pk:
            self.initial["requested_start"] = self.instance.requested_start.strftime("%Y-%m-%dT%H:%M")
            self.initial["requested_end"] = self.instance.requested_end.strftime("%Y-%m-%dT%H:%M")

    def clean(self):
        cleaned_data = super().clean()
        resource = cleaned_data.get("resource")
        start = cleaned_data.get("requested_start")
        end = cleaned_data.get("requested_end")

        if resource and start and end:
            booking = self.instance if self.instance.pk else Booking(user=User())
            booking.resource = resource
            booking.requested_start = start
            booking.requested_end = end
            booking.attendees = cleaned_data.get("attendees") or 1
            booking.title = cleaned_data.get("title") or "Draft booking"
            booking.purpose = cleaned_data.get("purpose") or "Draft purpose"
            booking.priority = cleaned_data.get("priority") or Booking.Priority.MEDIUM
            booking.status = self.instance.status if self.instance.pk else Booking.Status.PENDING
            try:
                booking.clean()
            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field, messages in exc.message_dict.items():
                        if field in self.fields:
                            for message in messages:
                                self.add_error(field, message)
                        else:
                            for message in messages:
                                self.add_error(None, message)
                else:
                    self.add_error(None, exc)
        return cleaned_data
