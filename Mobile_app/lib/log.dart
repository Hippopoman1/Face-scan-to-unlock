import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class Log extends StatefulWidget {
  const Log({Key? key}) : super(key: key);

  @override
  _LogScreenState createState() => _LogScreenState();
}

class _LogScreenState extends State<Log> {
  List<dynamic> logs = [];
  bool isLoading = true;

  // ✅ Token Auth
  final String token = '69046e79dbf663ac70876fea57bb07e8bab0daf9';

  @override
  void initState() {
    super.initState();
    fetchLogs();
  }

  Future<void> fetchLogs() async {
    setState(() => isLoading = true);

    try {
      final currentUser = FirebaseAuth.instance.currentUser;
      final email = currentUser?.email;

      if (email == null) {
        throw Exception('กรุณาเข้าสู่ระบบก่อน');
      }

      final response = await http.get(
        Uri.parse("http://192.168.0.104:8000/api/access-logs/"),
        headers: {
          'Authorization': 'Token $token',
          'Accept': 'application/json',
        },
      ).timeout(const Duration(seconds: 10)); // ✅ เพิ่ม timeout ป้องกันค้าง

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final filteredLogs = data.where((log) => log['email'] == email).toList();

        setState(() {
          logs = filteredLogs;
          isLoading = false;
        });
      } else {
        throw Exception('โหลดข้อมูลไม่สำเร็จ (${response.statusCode})');
      }
    } catch (e) {
      setState(() => isLoading = false);
      showError('เกิดข้อผิดพลาด: $e');
    }
  }

  void showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.redAccent,
      ),
    );
  }

  String formatDateTime(String dateTimeString) {
    try {
      final dateTime = DateTime.parse(dateTimeString);
      return '${dateTime.day}/${dateTime.month}/${dateTime.year} ${dateTime.hour}:${dateTime.minute}';
    } catch (e) {
      return dateTimeString;
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentUser = FirebaseAuth.instance.currentUser;
    final photoURL = currentUser?.photoURL ?? 'https://via.placeholder.com/150';

    return Scaffold(
      appBar: AppBar(
        title: const Text("ประวัติการใช้งาน"),
        centerTitle: true,
        backgroundColor: const Color(0xFFF7F7F7),
      ),
      body: RefreshIndicator(
        onRefresh: fetchLogs,
        child: Container(
          color: const Color(0xFFF7F7F7),
          child: isLoading
              ? const Center(child: CircularProgressIndicator())
              : logs.isEmpty
                  ? const Center(
                      child: Text(
                        'ไม่มีข้อมูลการเข้าใช้งาน',
                        style: TextStyle(fontSize: 16),
                      ),
                    )
                  : ListView.builder(
                      physics: const AlwaysScrollableScrollPhysics(),
                      itemCount: logs.length,
                      itemBuilder: (context, index) {
                        final log = logs[index];
                        return Card(
                          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          elevation: 3,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: ListTile(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            leading: CircleAvatar(
                              backgroundImage: NetworkImage(photoURL),
                              radius: 28,
                            ),
                            title: Text(
                              log['name'] ?? 'ไม่ทราบชื่อ',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                            ),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const SizedBox(height: 4),
                                Text('รหัสนักศึกษา: ${log['id_student'] ?? '-'}', style: const TextStyle(fontSize: 14)),
                                const SizedBox(height: 2),
                                Text('สถานะ: ${log['access_status'] ?? '-'}', style: const TextStyle(fontSize: 14)),
                                const SizedBox(height: 2),
                                Text('เวลา: ${formatDateTime(log['access_time'] ?? '')}', style: const TextStyle(fontSize: 14)),
                                const SizedBox(height: 2),
                                Text('ห้อง: ${log['room_name'] ?? '-'}', style: const TextStyle(fontSize: 14)),
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
