from django import forms
from .models import User, Group ,UserGroup,Device

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'profile_picture']  # ฟิลด์ที่อนุญาตให้แก้ไข
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class add_user_form(forms.ModelForm):
    class Meta:
        model = User
        fields = ['id_student','name','email','profile_picture']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.role = 'User'  # กำหนดค่า role เป็น admin
        if commit:
            instance.save()
        return instance


class add_group_form(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['group_name','description']


class add_admin_form(forms.ModelForm):
    class Meta:
        model = User
        fields = ['id_student', 'name', 'email', 'profile_picture']

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.role = 'admin'  # กำหนดค่า role เป็น admin
        if commit:
            instance.save()
        return instance


class UploadFileForm(forms.Form):
    file = forms.FileField()



class add_group(forms.ModelForm):
    class Meta:
        fields = ['group_name']


class add_user_to_Group_Form(forms.ModelForm):
    class Meta:
        model = UserGroup
        fields = ['user', 'group']


class add_door(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['door_name','room_name','detail']