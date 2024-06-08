from django.forms import ModelForm, Form, FileField
from .models import *
from django.contrib.auth.forms import UserCreationForm


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'password1', 'password2']

class DriveForm(ModelForm):
    class Meta:
        model = Drives
        exclude = ['placement_officer', 'driveChat', 'created', 'updated']

class KYCForm(ModelForm):
    class Meta:
        model = KYC
        fields = '__all__'
        exclude = ['student', 'validation', 'comments']

class SPFForm(ModelForm):
    class Meta:
        model = SPF
        fields = '__all__'
        exclude = ['student', 'validation', 'comments']

class ChatRoomForm(ModelForm):
    class Meta:
        model = ChatRoom
        fields = '__all__'
        exclude = ['host', 'topic', 'participants', 'created', 'updated']

class TestForm(ModelForm):
    class Meta:
        model = Tests
        fields = '__all__'
        exclude = ['testType']

class SubTestForm(ModelForm):
    class Meta:
        model = SubTests
        fields = '__all__'
        exclude = ['test']

class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['avatar']

class UploadMarksForm(Form):
    csv_file = FileField()

    def clean_file(self):
        uploaded_file = self.cleaned_data['csv_file']
        
        if not uploaded_file.name.endswith('.csv'):
            raise ValidationError("The uploaded file must be a .csv file")
        
        if uploaded_file.content_type != 'text/csv':
            raise ValidationError("The uploaded file must be a CSV (text/csv)")

        return uploaded_file