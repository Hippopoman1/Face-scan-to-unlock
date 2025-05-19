import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'dart:io';
import 'dart:convert';

class UpdateFacePage extends StatefulWidget {
  @override
  _UpdateFacePageState createState() => _UpdateFacePageState();
}

class _UpdateFacePageState extends State<UpdateFacePage> {
  File? _image;
  final ImagePicker _picker = ImagePicker();
  List<Face> _faces = [];
  bool _isProcessing = false;
  bool _isUploading = false;

  final String token = '69046e79dbf663ac70876fea57bb07e8bab0daf9';
  String? _userEmail;

  @override
  void initState() {
    super.initState();
    checkLoginStatus();
  }

  void checkLoginStatus() {
    final currentUser = FirebaseAuth.instance.currentUser;

    if (currentUser == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('กรุณาเข้าสู่ระบบก่อนใช้งาน')),
      );
      Navigator.of(context).pop(); // กลับหน้าเดิม
    } else {
      setState(() {
        _userEmail = currentUser.email;
      });
    }
  }

  Future<void> _notifyPiToRefresh() async {
  final uri = Uri.parse('http://192.168.0.104:9000/refresh_faces'); // เปลี่ยน IP ให้ตรงกับ Raspberry Pi
  try {
    final response = await http.post(uri);
    if (response.statusCode == 200) {
      print("📡 แจ้ง Raspberry Pi ให้โหลดข้อมูลใบหน้าใหม่สำเร็จ");
    } else {
      print("⚠️ ไม่สามารถแจ้ง Raspberry Pi ได้ (${response.statusCode})");
    }
  } catch (e) {
    print("⚠️ เกิดข้อผิดพลาดในการเชื่อมต่อ Raspberry Pi: $e");
  }
}


  Future<void> _pickImage(ImageSource source) async {
    try {
      final pickedFile = await _picker.pickImage(source: source);

      if (pickedFile != null) {
        setState(() {
          _image = File(pickedFile.path);
          _isProcessing = true;
        });
        await _detectFaces(_image!);
      }
    } catch (e) {
      print("Error picking image: $e");
      _showSnackBar("ไม่สามารถเลือกรูปภาพได้");
    }
  }

  Future<void> _detectFaces(File imageFile) async {
    final inputImage = InputImage.fromFile(imageFile);
    final options = FaceDetectorOptions(
      performanceMode: FaceDetectorMode.accurate,
    );
    final faceDetector = FaceDetector(options: options);

    try {
      final faces = await faceDetector.processImage(inputImage);
      setState(() {
        _faces = faces;
        _isProcessing = false;
      });

      if (_faces.isEmpty) {
        _showSnackBar('ไม่พบใบหน้าในรูปภาพ');
      }
    } catch (e) {
      print("Error detecting faces: $e");
      _showSnackBar('ตรวจจับใบหน้าไม่สำเร็จ');
      setState(() {
        _isProcessing = false;
      });
    } finally {
      faceDetector.close();
    }
  }

  Future<File?> _cropFace(File imageFile, Rect boundingBox) async {
    try {
      final croppedFile = await ImageCropper().cropImage(
        sourcePath: imageFile.path,
        aspectRatio: CropAspectRatio(ratioX: 1, ratioY: 1),
        uiSettings: [
          AndroidUiSettings(
            toolbarTitle: 'Crop Face',
            lockAspectRatio: true,
          ),
          IOSUiSettings(
            title: 'Crop Face',
          ),
        ],
      );

      if (croppedFile != null) {
        return File(croppedFile.path);
      }
    } catch (e) {
      print("Error cropping image: $e");
      _showSnackBar('ตัดรูปภาพไม่สำเร็จ');
    }
    return null;
  }

  Future<void> _updateFace(File faceImage, String email) async {
  setState(() {
    _isUploading = true;
  });

  final uri = Uri.parse('http://192.168.0.104:8000/api/update/'); // เปลี่ยน URL ตาม IP ของ API Django

  final request = http.MultipartRequest('PUT', uri)
    ..fields['email'] = email
    ..files.add(await http.MultipartFile.fromPath('image', faceImage.path));

  request.headers['Authorization'] = 'Token $token';
  request.headers['Accept'] = 'application/json';

  try {
    final response = await request.send();

    if (response.statusCode == 200) {
      final responseBody = await response.stream.bytesToString();
      final data = jsonDecode(responseBody);

      print('✅ Update Success: $data');
      _showSnackBar('อัปเดตใบหน้าสำเร็จ! 🎉');

      // 🔥 แจ้ง Raspberry Pi ให้โหลดข้อมูลใบหน้าใหม่
      await _notifyPiToRefresh();

      Navigator.pop(context);
    } else {
      final errorMsg = 'อัปเดตใบหน้าไม่สำเร็จ (${response.statusCode})';
      print(errorMsg);
      _showSnackBar(errorMsg);
    }
  } catch (e) {
    print("Error updating face: $e");
    _showSnackBar('เกิดข้อผิดพลาดในการอัปเดตใบหน้า');
  } finally {
    setState(() {
      _isUploading = false;
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

  Future<void> _confirmUpdate() async {
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('ยืนยันการอัปเดตใบหน้า'),
        content: const Text('คุณต้องการอัปเดตใบหน้าหรือไม่?'),
        actions: [
          TextButton(
            child: const Text('ยกเลิก'),
            onPressed: () => Navigator.of(context).pop(false),
          ),
          ElevatedButton(
            child: const Text('ยืนยัน'),
            onPressed: () => Navigator.of(context).pop(true),
          ),
        ],
      ),
    );

    if (result == true) {
      if (_faces.isNotEmpty) {
        final croppedFace = await _cropFace(_image!, _faces.first.boundingBox);
        if (croppedFace != null && _userEmail != null) {
          await _updateFace(croppedFace, _userEmail!);
        } else {
          _showSnackBar('ไม่สามารถตัดรูปใบหน้าได้');
        }
      } else {
        _showSnackBar('กรุณาเลือกรูปภาพที่มีใบหน้าก่อน');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("อัปเดตใบหน้า"),
        centerTitle: true,
        backgroundColor: const Color(0xFFF7F7F7),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Expanded(
              child: _image == null
                  ? const Center(child: Text("ยังไม่ได้เลือกรูปภาพ"))
                  : Stack(
                      children: [
                        Image.file(_image!),
                        ..._faces.map((face) {
                          return Positioned(
                            left: face.boundingBox.left,
                            top: face.boundingBox.top,
                            width: face.boundingBox.width,
                            height: face.boundingBox.height,
                            child: Container(
                              decoration: BoxDecoration(
                                border: Border.all(color: Colors.red, width: 2),
                              ),
                            ),
                          );
                        }).toList(),
                      ],
                    ),
            ),
            if (_isProcessing || _isUploading)
              const Padding(
                padding: EdgeInsets.all(8.0),
                child: CircularProgressIndicator(),
              )
            else
              Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      ElevatedButton.icon(
                        onPressed: () => _pickImage(ImageSource.camera),
                        icon: const Icon(Icons.camera_alt),
                        label: const Text("ถ่ายรูปใหม่"),
                      ),
                      ElevatedButton.icon(
                        onPressed: () => _pickImage(ImageSource.gallery),
                        icon: const Icon(Icons.photo_library),
                        label: const Text("เลือกรูปใหม่"),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  if (_faces.isNotEmpty)
                    ElevatedButton(
                      onPressed: _confirmUpdate,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.orange,
                      ),
                      child: const Text("อัปเดตใบหน้า"),
                    ),
                ],
              ),
          ],
        ),
      ),
      backgroundColor: const Color(0xFFF7F7F7),
    );
  }
}
