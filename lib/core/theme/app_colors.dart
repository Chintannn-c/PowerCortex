import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  // Primary Colors
  static const Color primaryBlue = Color(0xFF1E3A8A);
  static const Color darkBlue = Color(0xFF0F172A);
  static const Color lightBlue = Color(0xFFDBEAFE);

  // Status Colors
  static const Color healthy = Color(0xFF22C55E);
  static const Color warning = Color(0xFFF59E0B);
  static const Color critical = Color(0xFFEF4444);
  static const Color info = Color(0xFF3B82F6);

  // Light Mode
  static const Color lightBg = Color(0xFFF8FAFC);
  static const Color lightCard = Color(0xFFFFFFFF);
  static const Color lightText = Color(0xFF0F172A);
  static const Color lightTextSecondary = Color(0xFF475569);
  static const Color lightBorder = Color(0xFFE2E8F0);

  // Dark Mode
  static const Color darkBg = Color.fromARGB(255, 0, 0, 0);
  static const Color darkCard = Color(0xFF111827);
  static const Color darkText = Color(0xFFF8FAFC);
  static const Color darkTextSecondary = Color(0xFF94A3B8);
  static const Color darkBorder = Color(0xFF1E293B);
}
