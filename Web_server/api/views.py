import os
import json
import logging
import face_recognition
from django.shortcuts import render
from rest_framework.permissions import AllowAny ,IsAuthenticated ,IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework import status, permissions
from django.db import connection
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from login.models import User, FaceEncoding, Group, UserGroup, Device, AccessControl, AccessLog
from .serializers import (
    UserSerializer, FaceEncodingSerializer, GroupSerializer, 
    UserGroupSerializer, DeviceSerializer, AccessControlSerializer, AccessLogSerializer
)



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class FaceEncodingViewSet(viewsets.ModelViewSet):
    queryset = FaceEncoding.objects.all()
    serializer_class = FaceEncodingSerializer
    permission_classes = [IsAdminUser]

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminUser]

class UserGroupViewSet(viewsets.ModelViewSet):
    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer
    permission_classes = [IsAdminUser]

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAdminUser]

class AccessControlViewSet(viewsets.ModelViewSet):
    queryset = AccessControl.objects.all()
    serializer_class = AccessControlSerializer
    permission_classes = [IsAdminUser]
    # เพิ่ม Custom Action สำหรับสลับค่า swit
    @action(detail=True, methods=['patch'])
    def toggle_swit(self, request, pk=None):
        print(f"toggle_swit called with pk={pk}")
        try:
            access_control = self.get_object()  # ดึง object จาก pk
            access_control.swit = "1" if access_control.swit == "0" else "0" # สลับค่า swit
                                        
            access_control.save()  # บันทึกการเปลี่ยนแปลง
            return Response({"status": "success", "swit": access_control.swit}, status=status.HTTP_200_OK)
        except AccessControl.DoesNotExist:
            return Response({"status": "error", "message": "AccessControl not found"}, status=status.HTTP_404_NOT_FOUND)

class AccessLogViewSet(viewsets.ModelViewSet):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAdminUser]


User = get_user_model()

class UploadFaceView(APIView):
    permission_classes = [IsAdminUser]  

    def post(self, request):
        email = request.POST.get('email')
        image_file = request.FILES.get('image')

        logging.info(f" Received email: {email}")
        print(f" Received email: {email}")

        if not email or not image_file:
            logging.warning(" Email or image is missing in the request")
            return Response({'error': 'Email and image are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # ตรวจสอบว่าผู้ใช้มีอยู่หรือไม่
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, email FROM Users WHERE email = %s", [email])
                user_data = cursor.fetchone()

            if user_data:
                user_id, user_email = user_data
                logging.info(f" User found: ID={user_id}, Email={user_email}")
                print(f" User found: ID={user_id}, Email={user_email}")
            else:
                logging.warning(f" User not found for email: {email}")
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            # บันทึกรูปภาพชั่วคราว
            filename = default_storage.save(f"uploads/{image_file.name}", image_file)
            filepath = default_storage.path(filename)
            logging.info(f" Image saved temporarily at: {filepath}")

            # โหลดรูปภาพและเข้ารหัสใบหน้า
            image = face_recognition.load_image_file(filepath)
            encodings = face_recognition.face_encodings(image)

            if len(encodings) == 0:
                logging.warning(" No face detected in the image")
                return Response({'error': 'No face detected in the image'}, status=status.HTTP_400_BAD_REQUEST)

            face_encoding = json.dumps(encodings[0].tolist())

            # บันทึกข้อมูลใบหน้าลงฐานข้อมูล
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO FaceEncodings (user_id, face_encoding, created_at)
                    VALUES (%s, %s, NOW())
                """, [user_id, face_encoding])
                cursor.execute("SELECT LAST_INSERT_ID()")
                face_id = cursor.fetchone()[0]

                # อัปเดตข้อมูลใน accesscontrol
                cursor.execute("""
                    UPDATE AccessControl 
                    SET face_id = %s, face_encoding = %s 
                    WHERE user_id = %s
                """, [face_id, face_encoding, user_id])

            logging.info(f" Face encoding saved successfully for user_id={user_id}")
            return Response({'message': 'Face encoding saved and AccessControl updated successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f" Error processing the request: {str(e)}")
            return Response({'error': f'Error processing image: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
                logging.info(f" Temporary file removed: {filepath}")


class UpdateFaceView(APIView):
    permission_classes = [IsAdminUser]  

    def put(self, request):
        email = request.POST.get('email')
        image_file = request.FILES.get('image')

        logging.info(f" Received email for update: {email}")
        print(f" Received email for update: {email}")

        if not email or not image_file:
            logging.warning(" Email or image is missing in the update request")
            return Response({'error': 'Email and image are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # ✅ ตรวจสอบว่าผู้ใช้มีอยู่หรือไม่
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, email FROM Users WHERE email = %s", [email])
                user_data = cursor.fetchone()

            if user_data:
                user_id, user_email = user_data
                logging.info(f" User found: ID={user_id}, Email={user_email}")
                print(f" User found: ID={user_id}, Email={user_email}")
            else:
                logging.warning(f" User not found for email: {email}")
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            # ✅ ตรวจสอบว่า user นี้มี face_id ใน AccessControl หรือไม่
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT face_id FROM AccessControl WHERE user_id = %s
                """, [user_id])
                face_record = cursor.fetchone()

            if not face_record or not face_record[0]:
                logging.warning(f" No existing face encoding found for user_id={user_id}")
                return Response({'error': 'No existing face encoding found. Please create one first.'}, status=status.HTTP_404_NOT_FOUND)

            face_id = face_record[0]
            logging.info(f" Existing face_id found: {face_id}")

            # ✅ บันทึกรูปภาพชั่วคราว
            filename = default_storage.save(f"uploads/{image_file.name}", image_file)
            filepath = default_storage.path(filename)
            logging.info(f" Image saved temporarily at: {filepath}")

            # ✅ โหลดรูปภาพและเข้ารหัสใบหน้า
            image = face_recognition.load_image_file(filepath)
            face_locations = face_recognition.face_locations(image, model="hog")
            encodings = face_recognition.face_encodings(image, face_locations)


            if len(encodings) == 0:
                
                logging.warning(" No face detected in the image")
                return Response({'error': 'No face detected in the image'}, status=status.HTTP_400_BAD_REQUEST)

            face_encoding = json.dumps(encodings[0].tolist())

            # ✅ อัปเดตข้อมูลใบหน้าใน FaceEncodings table
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE FaceEncodings
                    SET face_encoding = %s, created_at = NOW()
                    WHERE id = %s AND user_id = %s
                """, [face_encoding, face_id, user_id])

                # ✅ อัปเดตข้อมูลใน AccessControl table ด้วย face_encoding ล่าสุด
                cursor.execute("""
                    UPDATE AccessControl
                    SET face_encoding = %s
                    WHERE user_id = %s
                """, [face_encoding, user_id])

            logging.info(f" Face encoding updated successfully for user_id={user_id}")
            return Response({'message': 'Face encoding updated successfully!'}, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f" Error processing the update request: {str(e)}")
            return Response({'error': f'Error processing update: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
                logging.info(f" Temporary file removed: {filepath}")

