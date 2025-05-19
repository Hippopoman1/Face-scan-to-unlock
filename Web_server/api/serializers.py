from rest_framework import serializers
from login.models import User, FaceEncoding, Group, UserGroup, Device, AccessControl, AccessLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class FaceEncodingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaceEncoding
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = '__all__'

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

class AccessControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessControl
        fields = '__all__'

class AccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessLog
        fields = '__all__'
