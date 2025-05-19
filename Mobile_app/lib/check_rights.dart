import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class CheckRights extends StatefulWidget {
  const CheckRights({Key? key}) : super(key: key);

  @override
  _CheckRightsState createState() => _CheckRightsState();
}

class _CheckRightsState extends State<CheckRights> {
  List<dynamic> rights = [];
  bool isLoading = true;

  // ✅ ใส่ Token ตรงนี้
  final String token = '69046e79dbf663ac70876fea57bb07e8bab0daf9';

  @override
  void initState() {
    super.initState();
    fetchRights();
  }

  Future<void> fetchRights() async {
    try {
      final currentUser = FirebaseAuth.instance.currentUser;
      final email = currentUser?.email;

      if (email == null) {
        throw Exception("ไม่พบข้อมูลผู้ใช้ กรุณา Login ก่อน");
      }

      final response = await http.get(
        Uri.parse("http://192.168.0.104:8000/api/access-controls/"),
        headers: {
          'Authorization': 'Token $token', // ✅ เพิ่ม Token ตรงนี้
          'Accept': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        // ✅ กรองข้อมูลเฉพาะสิทธิ์ที่ตรงกับ email ของผู้ใช้ที่ล็อกอิน
        final filteredRights = data.where((item) => item['email'] == email).toList();

        setState(() {
          rights = filteredRights;
          isLoading = false;
        });
      } else {
        throw Exception('ไม่สามารถโหลดข้อมูลสิทธิ์ได้ (${response.statusCode})');
      }
    } catch (e) {
      setState(() {
        isLoading = false;
      });

      // ✅ แจ้งเตือน Error ให้ผู้ใช้รู้
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('เกิดข้อผิดพลาด: $e'),
          backgroundColor: Colors.redAccent,
        ),
      );

      print('Error fetching rights: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentUser = FirebaseAuth.instance.currentUser;
    final userName = currentUser?.displayName ?? 'คุณผู้ใช้';

    return Scaffold(
      appBar: AppBar(
        title: const Text("ตรวจสอบสิทธิ์การเข้าถึง"),
        centerTitle: true,
        backgroundColor: const Color(0xFFF7F7F7),
      ),
      body: RefreshIndicator(
        onRefresh: fetchRights, // ✅ ดึงข้อมูลใหม่ด้วย Pull-to-refresh
        child: Padding(
          padding: const EdgeInsets.only(top: 32),
          child: isLoading
              ? const Center(
                  child: CircularProgressIndicator(),
                )
              : rights.isEmpty
                  ? const Center(
                      child: Text(
                        'ไม่พบสิทธิ์การเข้าใช้งาน',
                        style: TextStyle(fontSize: 16),
                      ),
                    )
                  : ListView.builder(
                      itemCount: rights.length,
                      itemBuilder: (context, index) {
                        final right = rights[index];
                        final roomName = right['room_name'] ?? 'ไม่ทราบชื่อห้อง';
                        // final detail = right['detail'] ?? 'ไม่มีรายละเอียดเพิ่มเติม';
                        

                        return Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                          child: Container(
                            decoration: BoxDecoration(
                              color: Colors.lightBlue.shade100,
                              borderRadius: BorderRadius.circular(12),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.grey.withOpacity(0.3),
                                  spreadRadius: 1,
                                  blurRadius: 4,
                                  offset: const Offset(0, 2),
                                ),
                              ],
                            ),
                            padding: const EdgeInsets.all(16.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '👤 $userName',
                                  style: const TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  'มีสิทธิ์เข้าห้อง: $roomName',
                                  style: const TextStyle(
                                    fontSize: 16,
                                  ),
                                ),
                                // const SizedBox(height: 4),
                                // Text(
                                //   'รายละเอียด: $detail',
                                //   style: const TextStyle(
                                //     fontSize: 14,
                                //     color: Colors.black87,
                                //   ),
                                // ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
        ),
      ),
      backgroundColor: const Color(0xFFF7F7F7),
    );
  }
}
