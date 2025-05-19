from django.db import models


class User(models.Model):
    id_student = models.CharField(max_length=20)
    email = models.CharField(max_length=255, unique=True)  # Unique Email
    name = models.CharField(max_length=255)
    password = models.CharField(max_length=128,default="16as5d5awf")
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    profile_picture = models.ImageField(upload_to='profile_pictures/',default="profile_pictures/02.jpeg" ,blank=True, null=True)  # Profile picture
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Users'


class FaceEncoding(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Foreign Key to Users
    face_encoding = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'FaceEncodings'


class Group(models.Model):
   
    group_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Groups'


class UserGroup(models.Model):
 
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Foreign Key to Users
    group = models.ForeignKey(Group, on_delete=models.CASCADE)  # Foreign Key to Groups
    created_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        db_table = 'UserGroups'


class Device(models.Model):
  
    door_name = models.CharField(max_length=255)
    room_name = models.CharField(max_length=255)  # Room name associated with the device
    detail = models.TextField(null=True, blank=True)  # Additional details about the device
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Devices'


class AccessControl(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    face = models.ForeignKey(FaceEncoding, null=True, blank=True, on_delete=models.CASCADE)  # เพิ่ม ForeignKey
    
    # Other fields
    name = models.CharField(max_length=255, null=True, blank=True)
    face_encoding = models.TextField(null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    room_name = models.CharField(max_length=255, null=True, blank=True)
    detail = models.TextField(null=True, blank=True)
    swit = models.CharField(max_length=2,blank=True,default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Populate user-related fields
        if self.user:
            self.name = self.user.name
            self.email = self.user.email
            # If face is not set, try to fetch the first FaceEncoding
            if not self.face:
                face_encoding_instance = FaceEncoding.objects.filter(user=self.user).first()
                if face_encoding_instance:
                    self.face = face_encoding_instance
                    self.face_encoding = face_encoding_instance.face_encoding

        # Populate device-related fields
        if self.device:
            self.room_name = self.device.room_name
            self.detail = self.device.detail

        super(AccessControl, self).save(*args, **kwargs)

    class Meta:
        db_table = 'AccessControl'


class AccessLog(models.Model):
    id_student = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    access_status = models.CharField(
        max_length=20, 
        choices=[('in', 'เข้าประตู'), ('out', 'ออกประตู')]
    )
    access_time = models.DateTimeField(auto_now_add=True)
    room_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'AccessLogs'