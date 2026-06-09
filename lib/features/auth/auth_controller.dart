import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/theme/app_colors.dart';
import 'models/user_model.dart';
import 'repositories/auth_repository.dart';

class AuthController extends GetxController {
  final AuthRepository _authRepository = AuthRepository();
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  // Page states
  var currentPage = 0.obs;
  
  // Obscure text states
  var obscureSignInPassword = true.obs;
  var obscureSignUpPassword = true.obs;
  var obscureSignUpConfirmPassword = true.obs;
  
  // Custom states
  var rememberMe = false.obs;
  var isLoading = false.obs;
  
  // Submit validation triggers
  var signInSubmitted = false.obs;
  var signUpSubmitted = false.obs;

  // Real-time password strength indicators
  var passwordStrength = 'None'.obs;
  var strengthProgress = 0.0.obs;
  var strengthColor = Colors.transparent.obs;

  // Real-time email validation flag
  var isSignInEmailValid = false.obs;
  var isSignUpEmailValid = false.obs;

  // Current User
  Rx<UserModel?> currentUser = Rx<UserModel?>(null);


  void toggleSignInPassword() => obscureSignInPassword.toggle();
  void toggleSignUpPassword() => obscureSignUpPassword.toggle();
  void toggleSignUpConfirmPassword() => obscureSignUpConfirmPassword.toggle();
  void toggleRememberMe() => rememberMe.toggle();

  void validateSignInEmail(String value) {
    isSignInEmailValid.value = RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$').hasMatch(value.trim());
  }

  void validateSignUpEmail(String value) {
    isSignUpEmailValid.value = RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$').hasMatch(value.trim());
  }

  void updatePasswordStrength(String password) {
    if (password.isEmpty) {
      passwordStrength.value = 'None';
      strengthProgress.value = 0.0;
      strengthColor.value = Colors.transparent;
      return;
    }

    if (password.length < 6) {
      passwordStrength.value = 'Too Short';
      strengthProgress.value = 0.2;
      strengthColor.value = AppColors.critical;
      return;
    }

    int score = 0;
    if (RegExp(r'[a-z]').hasMatch(password)) score++;
    if (RegExp(r'[A-Z]').hasMatch(password)) score++;
    if (RegExp(r'[0-9]').hasMatch(password)) score++;
    if (RegExp(r'[!@#\$&*~]').hasMatch(password)) score++;

    if (score <= 1) {
      passwordStrength.value = 'Weak Grid Key';
      strengthProgress.value = 0.4;
      strengthColor.value = AppColors.critical;
    } else if (score == 2) {
      passwordStrength.value = 'Moderate Security';
      strengthProgress.value = 0.6;
      strengthColor.value = AppColors.warning;
    } else if (score == 3) {
      passwordStrength.value = 'High Integrity';
      strengthProgress.value = 0.8;
      strengthColor.value = AppColors.info;
    } else {
      passwordStrength.value = 'Grid Operator Strong';
      strengthProgress.value = 1.0;
      strengthColor.value = AppColors.healthy;
    }
  }

  Future<void> checkAuthStatus() async {
    final token = await _secureStorage.read(key: 'access_token');
    if (token != null) {
      final res = await _authRepository.getCurrentUser();
      if (res['success'] == true) {
        currentUser.value = UserModel.fromJson(res['data']);
        Get.offAllNamed('/home');
        return;
      } else {
        await _secureStorage.deleteAll();
      }
    }
    Get.offAllNamed('/login');
  }

  Future<void> submitSignIn(GlobalKey<FormState> formKey, BuildContext context, String email, String password) async {
    signInSubmitted.value = true;
    if (formKey.currentState!.validate()) {
      isLoading.value = true;
      
      final result = await _authRepository.login(email.trim(), password);
      
      isLoading.value = false;

      if (result['requires_2fa'] == true) {
        final tempToken = result['temp_token'];
        _show2FADialog(tempToken);
        return;
      }

      if (result['success'] == true) {
        final data = result['data'];
        await _secureStorage.write(key: 'access_token', value: data['access_token']);
        await _secureStorage.write(key: 'refresh_token', value: data['refresh_token']);
        currentUser.value = UserModel.fromJson(data['user']);

        Get.snackbar(
          'Login Successful',
          'Welcome back, ${currentUser.value?.fullName ?? email.split('@').first}!',
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: AppColors.healthy,
          colorText: Colors.white,
          borderRadius: 10,
          margin: const EdgeInsets.all(16),
          icon: const Icon(Icons.check_circle_outline, color: Colors.white),
        );
        
        Get.offAllNamed('/home');
      } else {
        Get.snackbar(
          'Login Failed',
          result['message'] ?? 'Invalid credentials',
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: AppColors.critical,
          colorText: Colors.white,
          borderRadius: 10,
          margin: const EdgeInsets.all(16),
          icon: const Icon(Icons.error_outline, color: Colors.white),
        );
      }
    }
  }

  void _show2FADialog(String tempToken) {
    final codeController = TextEditingController();
    Get.defaultDialog(
      title: 'Two-Step Verification',
      content: Column(
        children: [
          const Text('Please enter the 6-digit code from your authenticator app.'),
          const SizedBox(height: 16),
          TextField(
            controller: codeController,
            keyboardType: TextInputType.number,
            maxLength: 6,
            decoration: const InputDecoration(
              labelText: '6-digit code',
              border: OutlineInputBorder(),
            ),
          ),
        ],
      ),
      textConfirm: 'Verify',
      confirmTextColor: Colors.white,
      onConfirm: () async {
        final code = codeController.text.trim();
        if (code.length == 6) {
          Get.back(); // close dialog
          await _submit2FALogin(tempToken, code);
        } else {
          Get.snackbar('Error', 'Code must be 6 digits.', backgroundColor: AppColors.critical, colorText: Colors.white);
        }
      },
    );

    // Fetch the code to simulate mock email delivery to the user's email inbox
    get2FACodeForLogin(tempToken).then((result) {
      if (result['success'] == true) {
        final code = result['code'] as String;
        final email = result['email'] as String;
        
        Get.snackbar(
          'Email Received: PowerCortex',
          'Your 2FA login code is $code',
          snackPosition: SnackPosition.TOP,
          backgroundColor: AppColors.primaryBlue.withOpacity(0.95),
          colorText: Colors.white,
          duration: const Duration(seconds: 15),
          margin: const EdgeInsets.all(16),
          borderRadius: 12,
          boxShadows: [
            BoxShadow(
              color: Colors.black.withOpacity(0.2),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
          icon: Container(
            padding: const EdgeInsets.all(8),
            decoration: const BoxDecoration(
              color: Colors.white24,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.email_outlined,
              color: Colors.white,
              size: 24,
            ),
          ),
          messageText: Text(
            'We sent a 2FA verification code to $email. Code: $code',
            style: const TextStyle(color: Colors.white70, fontSize: 13),
          ),
          mainButton: TextButton(
            onPressed: () {
              codeController.text = code;
              if (Get.isSnackbarOpen) {
                Get.back();
              }
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
    });
  }

  Future<void> _submit2FALogin(String tempToken, String code) async {
    isLoading.value = true;
    final result = await _authRepository.loginWith2FA(tempToken, code);
    isLoading.value = false;

    if (result['success'] == true) {
      final data = result['data'];
      await _secureStorage.write(key: 'access_token', value: data['access_token']);
      await _secureStorage.write(key: 'refresh_token', value: data['refresh_token']);
      currentUser.value = UserModel.fromJson(data['user']);

      Get.snackbar(
        'Login Successful',
        'Welcome back!',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.healthy,
        colorText: Colors.white,
        margin: const EdgeInsets.all(16),
      );
      Get.offAllNamed('/home');
    } else {
      Get.snackbar(
        'Login Failed',
        result['message'] ?? 'Invalid 2FA code.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.critical,
        colorText: Colors.white,
        margin: const EdgeInsets.all(16),
      );
    }
  }

  Future<void> submitSignUp(GlobalKey<FormState> formKey, BuildContext context, String name, String email, String password, String department) async {
    signUpSubmitted.value = true;
    if (formKey.currentState!.validate()) {
      isLoading.value = true;
      
      final result = await _authRepository.register(name.trim(), email.trim(), password, department.trim());
      
      if (result['success'] == true) {
        // Auto-login after successful registration
        final loginResult = await _authRepository.login(email.trim(), password);
        isLoading.value = false;

        if (loginResult['success'] == true) {
          final data = loginResult['data'];
          await _secureStorage.write(key: 'access_token', value: data['access_token']);
          await _secureStorage.write(key: 'refresh_token', value: data['refresh_token']);
          currentUser.value = UserModel.fromJson(data['user']);

          Get.snackbar(
            'Account Registered',
            'Logging in as grid operator $name...',
            snackPosition: SnackPosition.BOTTOM,
            backgroundColor: AppColors.healthy,
            colorText: Colors.white,
            borderRadius: 10,
            margin: const EdgeInsets.all(16),
            icon: const Icon(Icons.stars_rounded, color: Colors.white),
          );
          
          Get.offAllNamed('/home');
        } else {
          Get.offAllNamed('/login'); // If login fails somehow after register
        }
      } else {
        isLoading.value = false;
        String errorMessage = result['message'] ?? 'Registration failed';
        if (result['errors'] != null && (result['errors'] as List).isNotEmpty) {
           errorMessage = (result['errors'] as List).first.toString();
        }
        
        Get.snackbar(
          'Registration Failed',
          errorMessage,
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: AppColors.critical,
          colorText: Colors.white,
          borderRadius: 10,
          margin: const EdgeInsets.all(16),
          icon: const Icon(Icons.error_outline, color: Colors.white),
        );
      }
    }
  }

  void logoutLocally() {
    currentUser.value = null;
    Get.offAllNamed('/login');
  }

  Future<void> logout() async {
    final refreshToken = await _secureStorage.read(key: 'refresh_token');
    if (refreshToken != null) {
      await _authRepository.logout(refreshToken);
    }
    await _secureStorage.deleteAll();
    logoutLocally();
  }
  Future<void> updateProfile(String fullName, String department) async {
    final user = currentUser.value;
    if (user == null) return;

    isLoading.value = true;
    final result = await _authRepository.updateUser(user.id, {
      'full_name': fullName,
      'department': department,
    });
    isLoading.value = false;

    if (result['success'] == true) {
      // Refresh current user data
      await checkAuthStatus();
      Get.snackbar(
        'Profile Updated',
        'Your profile has been successfully updated.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.healthy,
        colorText: Colors.white,
        margin: const EdgeInsets.all(16),
      );
    } else {
      Get.snackbar(
        'Update Failed',
        result['message'] ?? 'Failed to update profile.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.critical,
        colorText: Colors.white,
        margin: const EdgeInsets.all(16),
      );
    }
  }

  Future<void> changePassword(String currentPassword, String newPassword) async {
    isLoading.value = true;
    final result = await _authRepository.changePassword(currentPassword, newPassword);
    isLoading.value = false;

    if (result['success'] == true) {
      Get.snackbar(
        'Password Changed',
        'Your password has been successfully updated.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.healthy,
        colorText: Colors.white,
        margin: const EdgeInsets.all(16),
      );
    } else {
      Get.snackbar(
        'Change Failed',
        result['message'] ?? 'Failed to change password.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.critical,
        colorText: Colors.white,
        margin: const EdgeInsets.all(16),
      );
    }
  }

  Future<Map<String, dynamic>> setup2FA() async {
    isLoading.value = true;
    final result = await _authRepository.setup2FA();
    isLoading.value = false;
    return result;
  }

  Future<Map<String, dynamic>> verify2FA(String code) async {
    isLoading.value = true;
    final result = await _authRepository.verify2FA(code);
    isLoading.value = false;
    return result;
  }

  Future<Map<String, dynamic>> get2FACode() async {
    isLoading.value = true;
    final result = await _authRepository.get2FACode();
    isLoading.value = false;
    return result;
  }

  Future<Map<String, dynamic>> disable2FA() async {
    isLoading.value = true;
    final result = await _authRepository.disable2FA();
    isLoading.value = false;
    if (result['success'] == true) {
      await checkAuthStatus();
    }
    return result;
  }

  Future<Map<String, dynamic>> get2FACodeForLogin(String tempToken) async {
    return await _authRepository.get2FACodeForLogin(tempToken);
  }
}
