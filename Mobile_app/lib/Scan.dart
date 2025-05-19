import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'dart:convert';
import 'upload_face.dart';
import 'update_face.dart';

class Scan extends StatefulWidget {
  const Scan({super.key});

  @override
  _ScanState createState() => _ScanState();
}

class _ScanState extends State<Scan> {
  bool _isLoading = false;
  final String token = '69046e79dbf663ac70876fea57bb07e8bab0daf9';

  Future<void> _checkUserAndNavigate() async {
    setState(() {
      _isLoading = true;
    });

    final currentUser = FirebaseAuth.instance.currentUser;

    if (currentUser == null) {
      _showSnackBar('กรุณาเข้าสู่ระบบก่อนใช้งาน');
      Navigator.pop(context);
      return;
    }

    final email = currentUser.email;
    int? userId;

    try {
      // ✅ 1. ดึง users ทั้งหมดจาก API
      final usersResponse = await http.get(
        Uri.parse('http://192.168.0.104:8000/api/users/'),
        headers: {
          'Authorization': 'Token $token',
          'Accept': 'application/json',
        },
      );

      if (usersResponse.statusCode != 200) {
        _showSnackBar('ไม่สามารถดึงข้อมูลผู้ใช้ได้');
        setState(() => _isLoading = false);
        return;
      }

      final List<dynamic> users = json.decode(usersResponse.body);

      // ✅ 2. หา user ที่ตรงกับ email
      final user = users.firstWhere(
        (u) => u['email'] == email,
        orElse: () => null,
      );

      if (user == null) {
        _showSnackBar('ไม่พบข้อมูลผู้ใช้ในระบบ');
        Navigator.pop(context);
        return;
      }

      userId = user['id'];
      print('✅ User found: ID = $userId, Email = $email');

      // ✅ 3. ดึง face encodings ทั้งหมดจาก API
      final facesResponse = await http.get(
        Uri.parse('http://192.168.0.104:8000/api/face-encodings/'),
        headers: {
          'Authorization': 'Token $token',
          'Accept': 'application/json',
        },
      );

      if (facesResponse.statusCode != 200) {
        _showSnackBar('ไม่สามารถดึงข้อมูล face encodings ได้');
        setState(() => _isLoading = false);
        return;
      }

      final List<dynamic> faceEncodings = json.decode(facesResponse.body);

      // ✅ 4. เช็คว่ามี face encoding หรือไม่
      final face = faceEncodings.firstWhere(
        (f) => f['user'] == userId,
        orElse: () => null,
      );

      if (face != null) {
        print('✅ พบ face encoding → ไปหน้า Update');
        await Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => UpdateFacePage()),
        );
      } else {
        print('✅ ไม่พบ face encoding → ไปหน้า Upload');

        final result = await Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => UploadFacePage()),
        );

        if (result == true) {
          print("✅ อัปโหลดเสร็จ → เช็คใหม่อีกครั้ง");
          _checkUserAndNavigate(); // รีเช็คใหม่หลังอัปโหลด
        }
      }

    } catch (e) {
      print('❌ Error: $e');
      _showSnackBar('เกิดข้อผิดพลาดในการเชื่อมต่อ');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.redAccent,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("สแกน"),
        centerTitle: true,
        backgroundColor: const Color(0xFFF7F7F7),
      ),
      body: Center(
        child: _isLoading
            ? const CircularProgressIndicator()
            : Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Image.asset(
                    "assets/images/face_detection.png",
                    width: 200,
                    height: 200,
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'การจำแนกใบหน้า',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'โปรดถอดหมวก,แมสก์ หรือสิ่งที่อาจปิดบังใบหน้า',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: _checkUserAndNavigate,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.lightBlue,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(30),
                      ),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 80, vertical: 15),
                    ),
                    child: const Text(
                      'ดำเนินการต่อไป',
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
      ),
      backgroundColor: const Color(0xFFF7F7F7),
    );
  }
}
