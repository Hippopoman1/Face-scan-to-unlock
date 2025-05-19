import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'dart:convert';

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Device Controller',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        fontFamily: 'Kanit',
      ),
      debugShowCheckedModeBanner: false,
      home: ToggleSwitScreen(),
    );
  }
}

class ToggleSwitScreen extends StatefulWidget {
  @override
  _ToggleSwitScreenState createState() => _ToggleSwitScreenState();
}

class _ToggleSwitScreenState extends State<ToggleSwitScreen> {
  bool _isLoading = false;
  String _switStatus = "0";
  List<Map<String, dynamic>> _userDevices = [];
  String? _selectedDevice;
  int? _switId;

  final String token = '69046e79dbf663ac70876fea57bb07e8bab0daf9';

  @override
  void initState() {
    super.initState();
    _fetchUserDevices();
  }

  Future<void> _fetchUserDevices() async {
    final url = Uri.parse('http://192.168.0.104:8000/api/access-controls/');

    try {
      setState(() => _isLoading = true);

      final response = await http.get(url, headers: {
        'Authorization': 'Token $token',
        'Accept': 'application/json',
      });

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        final currentUser = FirebaseAuth.instance.currentUser;
        final email = currentUser?.email;

        if (email == null) throw Exception('ไม่พบ email ของผู้ใช้');

        final userDevices = data.where((item) => item["email"] == email).toList();

        if (userDevices.isNotEmpty) {
          setState(() {
            _userDevices = List<Map<String, dynamic>>.from(userDevices);
            _selectedDevice = userDevices.first["device"].toString();
            _switId = userDevices.first["id"];
            _switStatus = userDevices.first["swit"] ?? "0";
          });
        } else {
          _showSnackBar("ไม่พบอุปกรณ์ของผู้ใช้", Colors.orange);
        }
      } else {
        _showSnackBar("โหลดข้อมูลไม่สำเร็จ (${response.statusCode})", Colors.red);
      }
    } catch (e) {
      _showSnackBar("เกิดข้อผิดพลาด: $e", Colors.red);
    } finally {
      setState(() => _isLoading = false);
    }
  }

Future<void> _notifyPiToRefreshSwitch() async {
  final String raspberryPiUrl = 'http://192.168.0.104:9000/refresh_swit'; // ✅ เปลี่ยนเป็น IP ของ Raspberry Pi
  
  try {
    final response = await http.post(Uri.parse(raspberryPiUrl));

    if (response.statusCode == 200) {
      _showSnackBar("Raspberry Pi โหลดข้อมูลหม่สำเร็จ", Colors.green);
    } else {
      _showSnackBar("⚠️ ไม่สามารถแจ้ง Raspberry Pi ได้ (${response.statusCode})", Colors.red);
    }
  } catch (e) {
    _showSnackBar("⚠️ เกิดข้อผิดพลาดในการเชื่อมต่อ Raspberry Pi: $e", Colors.red);
  }
}

  Future<void> _toggleSwit() async {
    if (_switId == null) {
      _showSnackBar("กรุณาเลือกอุปกรณ์ก่อน", Colors.orange);
      return;
    }

    setState(() => _isLoading = true);

    final url = Uri.parse('http://192.168.0.104:8000/api/access-controls/$_switId/toggle_swit/');

    try {
      final response = await http.patch(
        url,
        headers: {
          'Authorization': 'Token $token',
          'Accept': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        setState(() {
          _switStatus = data["swit"] ?? "0";
        });

        _showSnackBar(
          "สถานะ: ${_switStatus == "1" ? "ปลดล็อค (Unlock)" : "ล็อค (Lock)"}",
          Colors.green,
        );
        await _notifyPiToRefreshSwitch();
      } else {
        _showSnackBar("อัปเดตไม่สำเร็จ (${response.statusCode})", Colors.red);
      }
    } catch (e) {
      _showSnackBar("เกิดข้อผิดพลาด: $e", Colors.red);
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showSnackBar(String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: color,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("ควบคุมอุปกรณ์"),
        centerTitle: true,
        backgroundColor: const Color(0xFFF7F7F7),
      ),
      body: Container(
        color: const Color(0xFFF1F4F8),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _userDevices.isEmpty
                ? const Center(
                    child: Text(
                      'ไม่พบอุปกรณ์ที่สามารถควบคุมได้',
                      style: TextStyle(fontSize: 16),
                    ),
                  )
                : SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Card(
                          color: Colors.white,
                          elevation: 4,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'เลือกอุปกรณ์',
                                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                                ),
                                const SizedBox(height: 12),
                                DropdownButton<String>(
                                  isExpanded: true,
                                  value: _selectedDevice,
                                  icon: const Icon(Icons.arrow_drop_down),
                                  onChanged: (String? newValue) {
                                    final selected = _userDevices.firstWhere(
                                      (device) => device["device"].toString() == newValue,
                                    );

                                    setState(() {
                                      _selectedDevice = newValue;
                                      _switId = selected["id"];
                                      _switStatus = selected["swit"] ?? "0";
                                    });
                                  },
                                  items: _userDevices.map<DropdownMenuItem<String>>((device) {
                                    return DropdownMenuItem<String>(
                                      value: device["device"].toString(),
                                      child: Text('อุปกรณ์ ${device["device"]}'),
                                    );
                                  }).toList(),
                                ),
                                const SizedBox(height: 20),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    const Text(
                                      'สถานะรีเลย์',
                                      style: TextStyle(fontSize: 16),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                      decoration: BoxDecoration(
                                        color: _switStatus == "1" ? Colors.green : Colors.red,
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      // child: Text(
                                      //   _switStatus == "1" ? "ปลดล็อค (Unlock)" : "ล็อค (Lock)",
                                      //   style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                                      // ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 30),
                                SizedBox(
                                  width: double.infinity,
                                  child: ElevatedButton.icon(
                                    onPressed: _toggleSwit,
                                    icon: const Icon(Icons.lock_open_rounded),
                                    label: const Text('สั่งเปิด / ปิด รีเลย์'),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: const Color(0xFFF7F7F7),
                                      padding: const EdgeInsets.symmetric(vertical: 14),
                                      textStyle: const TextStyle(fontSize: 16),
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  
      ),
    );
  }
}
