import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'dart:convert';

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Toggle Swit',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
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

  // ฟังก์ชันดึงข้อมูลจาก API
  Future<Map<String, dynamic>?> _fetchUserAccess() async {
    final url = Uri.parse('http://192.168.0.107:8000/api/access-controls/');
    try {
      final response = await http.get(url, headers: {"Content-Type": "application/json"});
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        final currentUser = FirebaseAuth.instance.currentUser;
        final email = currentUser?.email;

        // ค้นหาข้อมูลอีเมลที่ตรงกัน
        final userAccess = data.firstWhere(
          (item) => item["email"] == email,
          orElse: () => null,
        );
        return userAccess;
      } else {
        throw Exception('Failed to fetch user access data');
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error fetching user access: $e")),
      );
      return null;
    }
  }

  // ฟังก์ชันสำหรับสลับค่า swit
  Future<void> _toggleSwit() async {
    setState(() {
      _isLoading = true;
    });

    final userAccess = await _fetchUserAccess();
    if (userAccess == null) {
      setState(() {
        _isLoading = false;
      });
      return;
    }

    final switId = userAccess["id"];
    final url = Uri.parse('http://192.168.0.107:8000/api/access-controls/$switId/toggle_swit/');

    try {
      final response = await http.patch(
        url,
        headers: {"Content-Type": "application/json"},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _switStatus = data["swit"];
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Swit is now ${data["swit"]}")),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Failed to toggle swit")),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error toggling swit: $e")),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Toggle Swit'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'Swit Status: $_switStatus',
              style: TextStyle(fontSize: 24),
            ),
            SizedBox(height: 20),
            _isLoading
                ? CircularProgressIndicator()
                : ElevatedButton(
                    onPressed: _toggleSwit,
                    child: Text('Toggle Swit'),
                  ),
          ],
        ),
      ),
    );
  }
}

void main() {
  runApp(MyApp());
}
