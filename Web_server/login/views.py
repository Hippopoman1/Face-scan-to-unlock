from django.contrib import messages  # นำเข้า message framework
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse
from login.models import User,Device,AccessLog,Group,UserGroup,AccessControl
from .forms import add_user_form,ProfileForm ,UploadFileForm,add_admin_form, add_group_form ,add_door
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
import pandas as pd
from django.views.generic import ListView,UpdateView
from django.urls import reverse_lazy


def Home_view(request):  
    
    user_email = request.user.email
    if not User.objects.filter(email=user_email).exists():
        auth_logout(request)
        messages.error(request, "อีเมลของคุณไม่ได้รับอนุญาตให้เข้าสู่ระบบ")
        return redirect('login')

    if not user_email.endswith('@ubu.ac.th'):
        auth_logout(request)
        messages.error(request, "ตรวจสอบว่าอีเมลลงท้ายด้วย @ubu.ac.th")
        return redirect('login')

    user = User.objects.get(email=user_email)
    if user.role != 'admin':  
        auth_logout(request)
        messages.error(request, "สิทธิ์เฉพาะ admin")
        return redirect('login')

    User_count = User.objects.count()
    Admin_count = User.objects.filter(role='admin').count()
    Door_count = Device.objects.count()
    Log_count = AccessLog.objects.count()
    profile_img = User.objects.filter(email=request.user.email)
   

    return render(request, 'home.html', {'Admin_count': Admin_count, 'User_count': User_count , 'Door_count' : Door_count , 'Log_count' : Log_count,'profile_img':profile_img})



def logout_views(request):
    auth_logout(request)
    messages.success(request, "ออกจากระบบสำเร็จ")
    return redirect('login')  

def login(request):
    return render(request, "login.html")

def user_view(request):

    if request.method == 'POST':
        selected_users = request.POST.getlist('selected_users')  # ดึงรายการ ID ของผู้ใช้ที่เลือก
        if selected_users:
            User.objects.filter(id__in=selected_users).delete()  # ลบผู้ใช้ที่เลือก
            messages.success(request, "ลบผู้ใช้สำเร็จ")
        else:
            messages.error(request, "กรุณาเลือกผู้ใช้ก่อนทำการลบ")
        return redirect('user')  # โหลดหน้าซ้ำหลังลบ

    user_queryset  = User.objects.filter(role='user')
    paginator = Paginator(user_queryset, 10)  # แบ่งข้อมูลเป็น 10 ต่อหน้า
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    profile_img = User.objects.filter(email=request.user.email)
    return render(request, 'user.html', {'users': users,'profile_img':profile_img})
 

def add_user(request):

    if request.method == 'POST':
        form = add_user_form(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password('defaultpassword')  # แฮชรหัสผ่าน
            user.save()
            return redirect('user')  # เปลี่ยนเป็นหน้าแสดงรายการผู้ใช้
    else:
        form = add_user_form()
    profile_img = User.objects.filter(email=request.user.email)
    return render(request, 'add_user.html', {'form': form,'profile_img':profile_img})

def upload_users(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # อ่านไฟล์ Excel
                df = pd.read_excel(file, engine='openpyxl')  # เพิ่ม engine='openpyxl'
                
                # วนลูปเพื่อบันทึกข้อมูลในฐานข้อมูล
                for _, row in df.iterrows():
                    user_instance, created = User.objects.update_or_create(
                        id_student=row['id_student'],  # ต้องตรงกับชื่อคอลัมน์ใน Excel
                        defaults={
                            'name': row['name'],
                            'email': row['email'],
                            'role': row['role'],
                            'password': 'defaultpassword123'  # กำหนดรหัสผ่านเริ่มต้น
                        }
                    )
                    if created:
                        messages.success(request, f"เพิ่มผู้ใช้ {row['name']} สำเร็จ")
                    else:
                        messages.info(request, f"มีผู้ใช้ในระบบแล้ว {row['name']} สำเร็จ")

                return redirect('upload_users')
            except Exception as e:
                messages.error(request, f"เกิดข้อผิดพลาด:รูปแบบไฟล์ไม่ถูกต้อง{e}")
    else:
        form = UploadFileForm()
    profile_img = User.objects.filter(email=request.user.email)
    return render(request, 'upload_users.html', {'form': form,'profile_img':profile_img})




def profile(request):

    user = get_object_or_404(User, email=request.user.email)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "อัปเดตข้อมูลโปรไฟล์สำเร็จ")
            return redirect('profile')  # กลับไปหน้าโปรไฟล์
    else:
        form = ProfileForm(instance=user)  # สร้างฟอร์มพร้อมข้อมูลปัจจุบัน
    profile_img = User.objects.filter(email=request.user.email)
    return render(request, 'profile.html', {'form': form,'profile_img':profile_img})


def door_view(request):
    card_door = Device.objects.all()
    profile_img = User.objects.filter(email=request.user.email)
    return render(request, "door.html",{'card_door':card_door,'profile_img':profile_img})

def add_doors(request):
    if request.method == 'POST':
        form = add_door(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return redirect('door')
    else :
        form = add_door()
    profile_img = User.objects.filter(email=request.user.email)
    return render(request,'add_doors.html',{'form':form,'profile_img':profile_img})


def add_users_to_door(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    groups = Group.objects.all()  # ดึงกลุ่มทั้งหมด

    # ตรวจสอบว่าเลือกกลุ่มหรือยัง
    group_id = request.GET.get('group_id')
    users = User.objects.none()  # กำหนดให้เริ่มต้นเป็น user ที่ไม่มีข้อมูล

    if group_id:
        # กรอง user ตาม group ที่เลือก โดยดึงจาก UserGroup
        group = get_object_or_404(Group, id=group_id)
        users = User.objects.filter(usergroup__group=group)  # ใช้การเชื่อมโยงกับ UserGroup

    if request.method == "POST":
        selected_users = request.POST.getlist('user_ids')
        for user_id in selected_users:
            user = User.objects.get(id=user_id)
            # ใช้ 'device' แทน 'door'
            AccessControl.objects.get_or_create(user=user, device=device)
        return redirect('door')  # เปลี่ยน URL ให้ตรงตามที่คุณต้องการ
    profile_img = User.objects.filter(email=request.user.email)
    return render(request, 'add_user_to_door.html', {'device': device,'users': users,'groups': groups,'profile_img':profile_img})


def delete_user_to_door(request, device_id):
    # ดึงข้อมูลอุปกรณ์ที่ต้องการ
    device = get_object_or_404(Device, id=device_id)

    if request.method == "POST":
        # รับ user_ids ที่เลือกจาก form
        selected_users = request.POST.getlist('user_ids')
        
        # ลบผู้ใช้ที่เกี่ยวข้องกับอุปกรณ์นี้ใน AccessControl
        AccessControl.objects.filter(user_id__in=selected_users, device=device).delete()

        return redirect('door')  # เปลี่ยน URL ให้ตรงกับเส้นทางที่คุณต้องการ

    # ดึงผู้ใช้ที่สัมพันธ์กับอุปกรณ์นี้ (เช่น ผู้ใช้ที่สามารถควบคุมอุปกรณ์นี้)
    users = AccessControl.objects.filter(device=device).select_related('user')

    # สำหรับ profile_img ของผู้ใช้ปัจจุบัน
    profile_img = User.objects.filter(email=request.user.email)

    # ส่งข้อมูลไปยัง template
    return render(request, 'delete_user_to_door.html', {
        'device': device,
        'users': users,
        'profile_img': profile_img
    })

def delete_door(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        device.delete()
        return JsonResponse({'status': 'success', 'message': 'Door deleted successfully!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)



def admin_view(request):
    if request.method == 'POST':
        selected_users = request.POST.getlist('selected_users')  # ดึงรายการ ID ของผู้ใช้ที่เลือก
        if selected_users:
            User.objects.filter(id__in=selected_users).delete()  # ลบผู้ใช้ที่เลือก
            messages.success(request, "ลบผู้ใช้สำเร็จ")
        else:
            messages.error(request, "กรุณาเลือกผู้ใช้ก่อนทำการลบ")
        return redirect('admin')  
    admin_queryset = User.objects.filter(role = 'admin')
    paginator = Paginator(admin_queryset, 10)  # แบ่งข้อมูลเป็น 10 ต่อหน้า
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    profile_img = User.objects.filter(email=request.user.email)
    return render(request, "admin.html",{'admin_queryset':admin_queryset,'users':users,'profile_img':profile_img})

def add_admin(request):
    if request.method == 'POST':
        form = add_admin_form(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin')
    else :
        form = add_admin_form()
    profile_img = User.objects.filter(email=request.user.email)
    return render(request,'add_admin.html',{'form':form,'profile_img':profile_img})


def log_view(request):
    user_queryset = AccessLog.objects.all()  # ดึงข้อมูลทั้งหมด
    paginator = Paginator(user_queryset, 9)  # แบ่งหน้า 9 รายการต่อหน้า
    page_number = request.GET.get('page')  # ดึงหมายเลขหน้าจาก URL
    users = paginator.get_page(page_number)  # ใช้ Paginator ดึงเฉพาะหน้าที่ต้องการ
    profile_img = User.objects.filter(email=request.user.email)
    return render(request, "log.html", {'users': users, 'profile_img': profile_img})



class search(ListView):
    model = AccessLog
    template_name = 'log.html'
    context_object_name = 'accesslog'
    fields = ['id_student', 'name', 'email', 'access_status', 'access_time', 'room_name']
    success_url = reverse_lazy('log')

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("search")

        if query:
            queryset = queryset.filter(id_student__icontains=query)
        return queryset


def group_view(request):
    groups = Group.objects.all()
    profile_img = User.objects.filter(email=request.user.email)
    return render(request, "group.html",{'groups':groups ,'profile_img':profile_img})

def add_group(request):
    if request.method == 'POST':
        form = add_group_form(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return redirect('group')
    else :
        form = add_group_form()
    profile_img = User.objects.filter(email=request.user.email)
    return render(request,'add_group.html',{'form':form,'profile_img':profile_img})


def add_users_to_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    users = User.objects.all()  # รายชื่อผู้ใช้ทั้งหมด

    if request.method == "POST":
        selected_users = request.POST.getlist('user_ids')  # รับรายการไอดีผู้ใช้จาก checkbox
        for user_id in selected_users:
            user = User.objects.get(id=user_id)
            # ตรวจสอบว่าผู้ใช้ถูกเพิ่มไปแล้วหรือไม่
            UserGroup.objects.get_or_create(user=user, group=group)
        return redirect('group')
    profile_img = User.objects.filter(email=request.user.email)
    return render(request, 'add_user_to_group.html', {'group': group, 'users': users,'profile_img':profile_img})

def delete_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        group.delete()
        return JsonResponse({'status': 'success', 'message': 'Group deleted successfully!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


class edit_group(UpdateView):
    model = Group
    template_name = 'edit_group.html'
    context_object_name = 'delete_group'
    fields = ['group_name','description']
    success_url = reverse_lazy('group')


#---------------------------------





# --------test---------------


