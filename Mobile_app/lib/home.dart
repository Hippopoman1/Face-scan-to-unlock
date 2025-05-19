import 'swit.dart';
import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'Scan.dart';
import 'check_rights.dart';
import 'log.dart';

class HomeScreen extends StatelessWidget {
  final User user;

  HomeScreen({required this.user});

  Future<void> _logout(BuildContext context) async {
  try {
    // Logout จาก Firebase
    await FirebaseAuth.instance.signOut();

    // Logout จาก Google Sign-In
    await GoogleSignIn().signOut();

    // กลับไปหน้าล็อกอิน
    Navigator.pushReplacementNamed(context, '/');
  } catch (e) {
    print("Error during logout: $e");
  }
}


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("หน้าหลัก"),
        centerTitle: true,
        backgroundColor: const Color(0xFFF7F7F7),
      ),
      body: Container(
        padding: const EdgeInsets.only(top: 32),
        color: const Color(0xFFF7F7F7),
        child: Column(
          children: [
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: ListView(
                  children: [
                    buildMenuItem(
                      imagePath: 'assets/images/face_scan.png',
                      text: 'Scan',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const Scan(),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 16),
                    buildMenuItem(
                      imagePath: 'assets/images/open_door.png',
                      text: 'Open the door',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>  ToggleSwitScreen(),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 16),
                    buildMenuItem(
                      imagePath: 'assets/images/access_right.png',
                      text: 'Access rights',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const CheckRights(),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 16),
                    buildMenuItem(
                      imagePath: 'assets/images/check_list.png',
                      text: 'Log',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const Log(),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: ElevatedButton(
                onPressed: () => _logout(context),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.lightBlue,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 15),
                ),
                child: const Text(
                  'Logout',
                  style: TextStyle(fontSize: 16, color: Colors.white),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget buildMenuItem({
    String? imagePath,
    required String text,
    VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(30),
          boxShadow: [
            BoxShadow(
              color: Colors.grey.withOpacity(0.3),
              spreadRadius: 2,
              blurRadius: 10,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
        child: Row(
          children: [
            if (imagePath != null)
              Image.asset(
                imagePath,
                width: 50,
                height: 50,
              ),
            const SizedBox(width: 16),
            Text(
              text,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
