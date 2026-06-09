import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import '../../core/theme/app_colors.dart';
import 'auth_controller.dart';

class TwoFactorSetupController extends GetxController {
  final AuthController _authController = Get.find<AuthController>();

  var isLoading = true.obs;
  var isVerifying = false.obs;
  var isSuccess = false.obs;
  
  var qrData = ''.obs;
  var secretKey = ''.obs;
  var errorMessage = ''.obs;
  var codeLength = 0.obs;
  var isNotifying = false.obs;
  
  // Timer and active code states
  var secondsRemaining = 45.obs;
  var activeCode = '748291'.obs; // Default fallback code matching user's spec
  Timer? _timer;

  final TextEditingController codeController = TextEditingController();
  final FocusNode otpFocusNode = FocusNode();

  @override
  void onInit() {
    super.onInit();
    codeController.addListener(() {
      codeLength.value = codeController.text.length;
      if (errorMessage.value.isNotEmpty) {
        errorMessage.value = '';
      }
    });
    _fetchSetupData();
  }

  @override
  void onClose() {
    _timer?.cancel();
    codeController.dispose();
    otpFocusNode.dispose();
    super.onClose();
  }

  Future<void> _fetchSetupData() async {
    isLoading.value = true;
    errorMessage.value = '';
    
    final result = await _authController.setup2FA();
    
    if (result['success'] == true) {
      qrData.value = result['uri'] ?? '';
      secretKey.value = result['secret'] ?? '';
      
      // Fetch current TOTP code from backend to display in the simulated notification
      final codeResult = await _authController.get2FACode();
      if (codeResult['success'] == true) {
        activeCode.value = codeResult['code'] ?? '748291';
        
        // Show notification toast with code immediately on load
        _showNotificationToast(activeCode.value);
      }
      
      startTimer();
    } else {
      errorMessage.value = result['message'] ?? 'Failed to load 2FA setup.';
    }
    
    isLoading.value = false;
  }

  void _showNotificationToast(String code) {
    Get.snackbar(
      '🔔 Security Alert',
      'Your verification code is: $code',
      snackPosition: SnackPosition.TOP,
      backgroundColor: AppColors.primaryBlue.withOpacity(0.95),
      colorText: Colors.white,
      duration: const Duration(seconds: 12),
      margin: const EdgeInsets.all(16),
      borderRadius: 12,
      boxShadows: [
        BoxShadow(
          color: Colors.black.withOpacity(0.25),
          blurRadius: 10,
          offset: const Offset(0, 4),
        )
      ],
      icon: const Icon(Icons.security_rounded, color: Colors.white),
      mainButton: TextButton(
        onPressed: () {
          codeController.text = code;
          codeLength.value = code.length;
          if (Get.isSnackbarOpen) {
            Get.back();
          }
          verifyAndEnable();
        },
        style: TextButton.styleFrom(
          foregroundColor: Colors.white,
          backgroundColor: Colors.white24,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        ),
        child: const Text(
          'Autofill',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  void startTimer() {
    _timer?.cancel();
    secondsRemaining.value = 45;
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (secondsRemaining.value > 0) {
        secondsRemaining.value--;
      } else {
        _timer?.cancel();
      }
    });
  }

  void copySecretKey() {
    if (secretKey.value.isNotEmpty) {
      Clipboard.setData(ClipboardData(text: secretKey.value));
      Get.snackbar(
        'Copied',
        'Manual setup key copied to clipboard.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.info,
        colorText: Colors.white,
        margin: const EdgeInsets.all(16),
        duration: const Duration(seconds: 2),
      );
    }
  }

  Future<void> resendNotification() async {
    if (secondsRemaining.value > 0) return;
    
    isNotifying.value = true;
    errorMessage.value = '';
    
    final result = await _authController.get2FACode();
    isNotifying.value = false;
    
    if (result['success'] == true) {
      activeCode.value = result['code'] as String;
      codeController.clear();
      startTimer();
      
      // Fire simulated system notification
      _showNotificationToast(activeCode.value);
    } else {
      errorMessage.value = result['message'] ?? 'Failed to generate code.';
      Get.snackbar(
        'Error',
        errorMessage.value,
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.critical,
        colorText: Colors.white,
        margin: const EdgeInsets.all(16),
      );
    }
  }

  Future<void> verifyAndEnable() async {
    final code = codeController.text.trim();
    if (code.length != 6) {
      errorMessage.value = 'Code must be 6 digits.';
      return;
      }

    isVerifying.value = true;
    errorMessage.value = '';

    final result = await _authController.verify2FA(code);
    
    isVerifying.value = false;

    if (result['success'] == true) {
      isSuccess.value = true;
      // After success, wait 2 seconds and navigate back to settings
      Future.delayed(const Duration(seconds: 2), () {
        if (Get.isDialogOpen ?? false) Get.back();
        Get.back();
      });
    } else {
      errorMessage.value = '⚠ Incorrect or expired verification code';
      codeController.clear();
      otpFocusNode.requestFocus();
    }
  }

  void refreshSetup() {
    _fetchSetupData();
  }
}
