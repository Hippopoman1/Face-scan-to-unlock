import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'home.dart';

class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();

  Future<User?> _signInWithGoogle() async {
  try {
    // ตรวจสอบว่ามีผู้ใช้ Google Sign-In อยู่หรือไม่
    if (await _googleSignIn.isSignedIn()) {
      await _googleSignIn.signOut(); // Sign out ก่อน
    }

    final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
    if (googleUser == null) {
      return null; // ผู้ใช้ยกเลิกการล็อกอิน
    }

    final GoogleSignInAuthentication googleAuth =
        await googleUser.authentication;

    final AuthCredential credential = GoogleAuthProvider.credential(
      accessToken: googleAuth.accessToken,
      idToken: googleAuth.idToken,
    );

    final UserCredential userCredential =
        await _auth.signInWithCredential(credential);

    return userCredential.user;
  } catch (e) {
    print("Error during Google Sign-In: $e");
    return null;
  }
}


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Login',
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color.fromARGB(255, 255, 255, 255),
        elevation: 0,
        centerTitle: true,
      ),
      body: Center(
        child: ElevatedButton(
          onPressed: () async {
            User? user = await _signInWithGoogle();
            if (user != null) {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(
                  builder: (context) => HomeScreen(user: user),
                ),
              );
            }
          },
          child: Text('Login with Google'),
        ),
      ),
      backgroundColor: const Color(0xFFF7F7F7),
    );
  }
}
