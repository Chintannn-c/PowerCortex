import 'package:flutter/material.dart';
import 'login_screen.dart';

/// Legacy export wrapper for [LoginScreen] to guarantee backwards compatibility.
class RegisterScreen extends StatelessWidget {
  const RegisterScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const LoginScreen();
  }
}
