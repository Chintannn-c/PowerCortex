import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:get/get.dart';
import '../../core/utils/responsive.dart';
import '../../core/theme/app_colors.dart';
import 'auth_controller.dart';
import '../../core/api/api_client.dart';


class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> with TickerProviderStateMixin {
  final _signInFormKey = GlobalKey<FormState>();
  final _signUpFormKey = GlobalKey<FormState>();
  
  // Login Controllers
  final _signInEmailController = TextEditingController();
  final _signInPasswordController = TextEditingController();
  
  // Sign Up Controllers
  final _signUpNameController = TextEditingController();
  final _signUpEmailController = TextEditingController();
  final _signUpPasswordController = TextEditingController();
  final _signUpConfirmPasswordController = TextEditingController();

  // Instantiate GetX AuthController
  final AuthController _authController = Get.put(AuthController());
  
  late PageController _pageController;
  bool _initialized = false;
  
  late AnimationController _logoController;
  late Animation<double> _logoScale;
  late Animation<double> _logoGlow;

  @override
  void initState() {
    super.initState();
    _logoController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat(reverse: true);
    
    _logoScale = Tween<double>(begin: 0.95, end: 1.05).animate(
      CurvedAnimation(parent: _logoController, curve: Curves.easeInOut),
    );
    
    _logoGlow = Tween<double>(begin: 0.2, end: 0.6).animate(
      CurvedAnimation(parent: _logoController, curve: Curves.easeInOut),
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_initialized) {
      final routeName = ModalRoute.of(context)?.settings.name;
      if (routeName == '/register') {
        _pageController = PageController(initialPage: 1);
        _authController.currentPage.value = 1;
      } else {
        _pageController = PageController(initialPage: 0);
        _authController.currentPage.value = 0;
      }
      _initialized = true;
    }
  }

  @override
  void dispose() {
    _signInEmailController.dispose();
    _signInPasswordController.dispose();
    _signUpNameController.dispose();
    _signUpEmailController.dispose();
    _signUpPasswordController.dispose();
    _signUpConfirmPasswordController.dispose();
    _logoController.dispose();
    _pageController.dispose();
    super.dispose();
  }

  void _showForgotPasswordDialog() {
    final emailDialogController = TextEditingController(text: _signInEmailController.text);
    final dialogFormKey = GlobalKey<FormState>();
    
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          title: Text(
            'Reset Password',
            style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
          ),
          content: Form(
            key: dialogFormKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Enter your registered email address to receive a 6-digit verification code.',
                    style: GoogleFonts.poppins(fontSize: 13, color: AppColors.lightTextSecondary),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: emailDialogController,
                    keyboardType: TextInputType.emailAddress,
                    decoration: const InputDecoration(
                      labelText: 'Email Address',
                      prefixIcon: Icon(Icons.email_outlined, size: 20),
                    ),
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return 'Please enter your email';
                      }
                      if (!RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$').hasMatch(value.trim())) {
                        return 'Please enter a valid email';
                      }
                      return null;
                    },
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(
                'Cancel',
                style: GoogleFonts.poppins(color: AppColors.lightTextSecondary),
              ),
            ),
            ElevatedButton(
              onPressed: () async {
                if (dialogFormKey.currentState!.validate()) {
                  final email = emailDialogController.text.trim();
                  Navigator.pop(context); // Close email dialog
                  
                  // Show loading dialog/overlay
                  Get.dialog(
                    const Center(
                      child: CircularProgressIndicator(
                        valueColor: AlwaysStoppedAnimation<Color>(AppColors.primaryBlue),
                      ),
                    ),
                    barrierDismissible: false,
                  );
                  
                  final result = await _authController.forgotPassword(email);
                  
                  if (Get.isDialogOpen == true) {
                    Get.back(); // Dismiss the loading dialog
                  }
                  
                  if (result['success'] == true) {
                    Get.snackbar(
                      'Code Sent',
                      'A 6-digit verification code has been sent to $email.',
                      snackPosition: SnackPosition.BOTTOM,
                      backgroundColor: AppColors.healthy,
                      colorText: Colors.white,
                      borderRadius: 10,
                      margin: const EdgeInsets.all(16),
                      icon: const Icon(Icons.check_circle_outline, color: Colors.white),
                    );
                    _showVerifyCodeDialog(email); // Proceed to verification
                  } else {
                    Get.snackbar(
                      'Request Failed',
                      result['message'] ?? 'Failed to request password reset.',
                      snackPosition: SnackPosition.BOTTOM,
                      backgroundColor: AppColors.critical,
                      colorText: Colors.white,
                      borderRadius: 10,
                      margin: const EdgeInsets.all(16),
                      icon: const Icon(Icons.error_outline, color: Colors.white),
                    );
                  }
                }
              },
              child: Text(
                'Send Code',
                style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
              ),
            ),
          ],
        );
      },
    );
  }

  void _showVerifyCodeDialog(String email) {
    final codeController = TextEditingController();
    final dialogFormKey = GlobalKey<FormState>();
    
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          title: Text(
            'Enter Reset Code',
            style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
          ),
          content: Form(
            key: dialogFormKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Please enter the 6-digit verification code sent to $email.',
                    style: GoogleFonts.poppins(fontSize: 13, color: AppColors.lightTextSecondary),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: codeController,
                    keyboardType: TextInputType.number,
                    maxLength: 6,
                    textAlign: TextAlign.center,
                    style: GoogleFonts.poppins(fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 8),
                    decoration: const InputDecoration(
                      labelText: 'Verification Code',
                      counterText: '',
                      prefixIcon: Icon(Icons.security_outlined, size: 20),
                    ),
                    validator: (value) {
                      if (value == null || value.trim().length != 6) {
                        return 'Please enter the 6-digit code';
                      }
                      if (!RegExp(r'^[0-9]+$').hasMatch(value.trim())) {
                        return 'Code must contain digits only';
                      }
                      return null;
                    },
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(
                'Cancel',
                style: GoogleFonts.poppins(color: AppColors.lightTextSecondary),
              ),
            ),
            ElevatedButton(
              onPressed: () async {
                if (dialogFormKey.currentState!.validate()) {
                  final code = codeController.text.trim();
                  Navigator.pop(context); // Close verification dialog
                  
                  // Show loading dialog/overlay
                  Get.dialog(
                    const Center(
                      child: CircularProgressIndicator(
                        valueColor: AlwaysStoppedAnimation<Color>(AppColors.primaryBlue),
                      ),
                    ),
                    barrierDismissible: false,
                  );
                  
                  final isCodeValid = await _authController.verifyResetCode(code);
                  
                  if (Get.isDialogOpen == true) {
                    Get.back(); // Dismiss the loading dialog
                  }
                  
                  if (isCodeValid) {
                    _showNewPasswordDialog(email, code); // Proceed to password setup
                  } else {
                    _showVerifyCodeDialog(email); // Let user try again
                  }
                }
              },
              child: Text(
                'Verify Code',
                style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
              ),
            ),
          ],
        );
      },
    );
  }

  void _showNewPasswordDialog(String email, String code) {
    final passwordController = TextEditingController();
    final confirmPasswordController = TextEditingController();
    final dialogFormKey = GlobalKey<FormState>();
    final showPassword = false.obs;
    
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          title: Text(
            'New Password',
            style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
          ),
          content: Obx(() => Form(
            key: dialogFormKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Enter a strong new password for your account.',
                    style: GoogleFonts.poppins(fontSize: 13, color: AppColors.lightTextSecondary),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: passwordController,
                    obscureText: !showPassword.value,
                    decoration: InputDecoration(
                      labelText: 'New Password',
                      prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20),
                      suffixIcon: IconButton(
                        icon: Icon(
                          showPassword.value
                              ? Icons.visibility_outlined
                              : Icons.visibility_off_outlined,
                          size: 20,
                        ),
                        onPressed: () => showPassword.toggle(),
                      ),
                    ),
                    validator: (value) {
                      if (value == null || value.length < 8) {
                        return 'Password must be at least 8 characters';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: confirmPasswordController,
                    obscureText: !showPassword.value,
                    decoration: const InputDecoration(
                      labelText: 'Confirm Password',
                      prefixIcon: Icon(Icons.lock_outline_rounded, size: 20),
                    ),
                    validator: (value) {
                      if (value != passwordController.text) {
                        return 'Passwords do not match';
                      }
                      return null;
                    },
                  ),
                ],
              ),
            ),
          )),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(
                'Cancel',
                style: GoogleFonts.poppins(color: AppColors.lightTextSecondary),
              ),
            ),
            ElevatedButton(
              onPressed: () async {
                if (dialogFormKey.currentState!.validate()) {
                  final newPassword = passwordController.text;
                  Navigator.pop(context); // Close new password dialog
                  
                  // Show loading dialog/overlay
                  Get.dialog(
                    const Center(
                      child: CircularProgressIndicator(
                        valueColor: AlwaysStoppedAnimation<Color>(AppColors.primaryBlue),
                      ),
                    ),
                    barrierDismissible: false,
                  );
                  
                  final success = await _authController.resetPassword(code, newPassword);
                  
                  if (Get.isDialogOpen == true) {
                    Get.back(); // Dismiss the loading dialog
                  }
                  
                  if (!success) {
                    _showNewPasswordDialog(email, code); // Let user try again on failure
                  }
                }
              },
              child: Text(
                'Reset Password',
                style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
              ),
            ),
          ],
        );
      },
    );
  }

  void _showServerConfigDialog() {
    final configController = TextEditingController(text: ApiClient.baseUrl);
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(
            'Server Configuration',
            style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Configure the backend API URL for this physical device:',
                style: GoogleFonts.poppins(fontSize: 13, color: AppColors.lightTextSecondary),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: configController,
                decoration: const InputDecoration(
                  labelText: 'API Base URL',
                  hintText: 'http://192.168.1.5:8000',
                  prefixIcon: Icon(Icons.dns_outlined, size: 20),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(
                'Cancel',
                style: GoogleFonts.poppins(color: AppColors.lightTextSecondary),
              ),
            ),
            ElevatedButton(
              onPressed: () {
                final newUrl = configController.text.trim();
                if (newUrl.isNotEmpty) {
                  ApiClient.customBaseUrl = newUrl;
                  Navigator.pop(context);
                  Get.snackbar(
                    'Server Updated',
                    'Connecting to: $newUrl',
                    snackPosition: SnackPosition.BOTTOM,
                    backgroundColor: AppColors.healthy,
                    colorText: Colors.white,
                  );
                }
              },
              child: Text(
                'Save',
                style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
              ),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final isWide = size.width > 800;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      body: Stack(
        children: [
          Row(
            children: [
          // Left branding panel (desktop/tablet only)
          if (isWide)
            Expanded(
              flex: 5,
              child: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [AppColors.darkBlue, AppColors.primaryBlue],
                  ),
                ),
                child: Stack(
                  children: [
                    Positioned.fill(
                      child: Opacity(
                        opacity: 0.05,
                        child: CustomPaint(
                          painter: GridPainter(),
                        ),
                      ),
                    ),
                    Center(
                      child: Padding(
                        padding: const EdgeInsets.all(48),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            AnimatedBuilder(
                              animation: _logoController,
                              builder: (context, child) {
                                return Transform.scale(
                                  scale: _logoScale.value,
                                  child: Container(
                                    padding: const EdgeInsets.all(24),
                                    decoration: BoxDecoration(
                                      color: Colors.white.withOpacity(0.08),
                                      shape: BoxShape.circle,
                                      boxShadow: [
                                        BoxShadow(
                                          color: Colors.yellow.withOpacity(_logoGlow.value),
                                          blurRadius: 30,
                                          spreadRadius: 5,
                                        ),
                                      ],
                                      border: Border.all(
                                        color: Colors.white.withOpacity(0.2),
                                        width: 1.5,
                                      ),
                                    ),
                                    child: ClipRRect(
                                      borderRadius: BorderRadius.circular(12),
                                      child: Image.asset(
                                        'assets/images/logo.png',
                                        width: 64,
                                        height: 64,
                                        fit: BoxFit.contain,
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                            context.sh(28),
                            Text(
                              'PowerCortex',
                              style: GoogleFonts.poppins(
                                fontSize: 40,
                                fontWeight: FontWeight.bold,
                                color: const Color.fromARGB(255, 209, 183, 183),
                                letterSpacing: 3,
                              ),
                            ),
                            context.sh(12),
                            Text(
                              'Next-Gen Power Network Analytics',
                              textAlign: TextAlign.center,
                              style: GoogleFonts.poppins(
                                fontSize: 16,
                                fontWeight: FontWeight.w300,
                                color: Colors.white.withOpacity(0.75),
                                letterSpacing: 0.5,
                              ),
                            ),
                            context.sh(48),
                            Wrap(
                              spacing: 12,
                              runSpacing: 12,
                              alignment: WrapAlignment.center,
                              children: [
                                _featurePill(Icons.analytics_outlined, 'Smart Load Forecasting'),
                                _featurePill(Icons.monitor_heart_outlined, 'Live Asset Monitoring'),
                                _featurePill(Icons.warning_amber_rounded, 'Real-time Fault Detection'),
                                _featurePill(Icons.smart_toy_outlined, 'PowerCortex AI Assistant'),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          
          // Right/Center Auth panel containing swipable forms
          Expanded(
            flex: 4,
            child: Container(
              color: isDark ? AppColors.darkBg : AppColors.lightBg,
              child: SafeArea(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Top spacing and branding for mobile
                    if (!isWide) ...[
                      context.sh(20),
                      Center(
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.primaryBlue.withOpacity(0.1),
                            shape: BoxShape.circle,
                          ),
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: Image.asset(
                              'assets/images/logo.png',
                              width: 32,
                              height: 32,
                              fit: BoxFit.contain,
                            ),
                          ),
                        ),
                      ),
                      context.sh(8),
                      Center(
                        child: Text(
                          'PowerCortex',
                          style: GoogleFonts.poppins(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: AppColors.primaryBlue,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ),
                    ],
                    
                    context.sh(20),
                    
                    // Sliding Tab bar controller with GetX reactive slider state
                    Center(
                      child: Container(
                        width: 320,
                        height: 48,
                        decoration: BoxDecoration(
                          color: isDark ? AppColors.darkBorder : Colors.grey.shade200,
                          borderRadius: BorderRadius.circular(24),
                        ),
                        child: Stack(
                          children: [
                            Obx(() => AnimatedAlign(
                              duration: const Duration(milliseconds: 250),
                              curve: Curves.easeInOut,
                              alignment: _authController.currentPage.value == 0 ? Alignment.centerLeft : Alignment.centerRight,
                              child: Container(
                                width: 154,
                                margin: const EdgeInsets.all(4),
                                decoration: BoxDecoration(
                                  color: AppColors.primaryBlue,
                                  borderRadius: BorderRadius.circular(20),
                                  boxShadow: [
                                    BoxShadow(
                                      color: AppColors.primaryBlue.withOpacity(0.3),
                                      blurRadius: 6,
                                      offset: const Offset(0, 2),
                                    ),
                                  ],
                                ),
                              ),
                            )),
                            Row(
                              children: [
                                Expanded(
                                  child: GestureDetector(
                                    onTap: () {
                                      _pageController.animateToPage(
                                        0,
                                        duration: const Duration(milliseconds: 300),
                                        curve: Curves.easeInOut,
                                      );
                                    },
                                    child: Container(
                                      color: Colors.transparent,
                                      alignment: Alignment.center,
                                      child: Obx(() => Text(
                                        'Login',
                                        style: GoogleFonts.poppins(
                                          fontSize: 14,
                                          fontWeight: FontWeight.bold,
                                          color: _authController.currentPage.value == 0 
                                              ? Colors.white 
                                              : (isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary),
                                        ),
                                      )),
                                    ),
                                  ),
                                ),
                                Expanded(
                                  child: GestureDetector(
                                    onTap: () {
                                      _pageController.animateToPage(
                                        1,
                                        duration: const Duration(milliseconds: 300),
                                        curve: Curves.easeInOut,
                                      );
                                    },
                                    child: Container(
                                      color: Colors.transparent,
                                      alignment: Alignment.center,
                                      child: Obx(() => Text(
                                        'Register',
                                        style: GoogleFonts.poppins(
                                          fontSize: 14,
                                          fontWeight: FontWeight.bold,
                                          color: _authController.currentPage.value == 1 
                                              ? Colors.white 
                                              : (isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary),
                                        ),
                                      )),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                    
                    context.sh(12),
                    
                    // Native Swipable PageView
                    Expanded(
                      child: PageView(
                        controller: _pageController,
                        onPageChanged: (index) {
                          _authController.currentPage.value = index;
                        },
                        children: [
                          _buildSignInView(context, isDark),
                          _buildSignUpView(context, isDark),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          )],
          ),
          Positioned(
            top: 16,
            right: 16,
            child: SafeArea(
              child: Container(
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkBorder.withOpacity(0.5) : Colors.grey.shade200.withOpacity(0.5),
                  shape: BoxShape.circle,
                ),
                child: IconButton(
                  icon: const Icon(Icons.dns_outlined, color: AppColors.primaryBlue),
                  tooltip: 'Server Config',
                  onPressed: _showServerConfigDialog,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSignInView(BuildContext context, bool isDark) {
    return SingleChildScrollView(
      padding: const EdgeInsets.only(left: 36, right: 36, top: 16, bottom: 48),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Obx(() => Form(
            key: _signInFormKey,
            autovalidateMode: _authController.signInSubmitted.value 
                ? AutovalidateMode.onUserInteraction 
                : AutovalidateMode.disabled,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                context.sh(8),
                
                // Email field
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Email Address',
                      style: GoogleFonts.poppins(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: isDark ? AppColors.darkText : AppColors.lightText,
                      ),
                    ),
                    Obx(() => _authController.isSignInEmailValid.value && _signInEmailController.text.isNotEmpty
                        ? const Text('✓ Valid Grid ID', style: TextStyle(fontSize: 10, color: AppColors.healthy, fontWeight: FontWeight.bold))
                        : const SizedBox.shrink()),
                  ],
                ),
                context.sh(8),
                TextFormField(
                  controller: _signInEmailController,
                  keyboardType: TextInputType.emailAddress,
                  style: GoogleFonts.poppins(fontSize: 14),
                  onChanged: (val) => _authController.validateSignInEmail(val),
                  decoration: InputDecoration(
                    hintText: 'operator@powercortex.in',
                    hintStyle: TextStyle(color: isDark ? Colors.white24 : Colors.black26),
                    prefixIcon: const Icon(Icons.email_outlined, size: 20),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Email address is required';
                    }
                    if (!RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$').hasMatch(value.trim())) {
                      return 'Please enter a valid email address';
                    }
                    return null;
                  },
                ),
                context.sh(20),
                
                // Password field
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Password',
                      style: GoogleFonts.poppins(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: isDark ? AppColors.darkText : AppColors.lightText,
                      ),
                    ),
                    GestureDetector(
                      onTap: _showForgotPasswordDialog,
                      child: Text(
                        'Forgot Password?',
                        style: GoogleFonts.poppins(
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                          color: AppColors.primaryBlue,
                        ),
                      ),
                    ),
                  ],
                ),
                context.sh(8),
                Obx(() => TextFormField(
                  controller: _signInPasswordController,
                  obscureText: _authController.obscureSignInPassword.value,
                  style: GoogleFonts.poppins(fontSize: 14),
                  decoration: InputDecoration(
                    hintText: '••••••••',
                    hintStyle: TextStyle(color: isDark ? Colors.white24 : Colors.black26),
                    prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _authController.obscureSignInPassword.value
                            ? Icons.visibility_off_outlined
                            : Icons.visibility_outlined,
                        size: 20,
                      ),
                      onPressed: _authController.toggleSignInPassword,
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Password is required';
                    }
                    if (value.length < 6) {
                      return 'Password must be at least 6 characters';
                    }
                    return null;
                  },
                )),
                context.sh(14),
                
                // Remember Me Checkbox
                Row(
                  children: [
                    SizedBox(
                      height: 24,
                      width: 24,
                      child: Checkbox(
                        value: _authController.rememberMe.value,
                        activeColor: AppColors.primaryBlue,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                        onChanged: (val) {
                          _authController.rememberMe.value = val ?? false;
                        },
                      ),
                    ),
                    const SizedBox(width: 10),
                    Text(
                      'Keep me logged in',
                      style: GoogleFonts.poppins(
                        fontSize: 13,
                        color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                      ),
                    ),
                  ],
                ),
                context.sh(28),
                
                // Login Button
                SizedBox(
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _authController.isLoading.value 
                        ? null 
                        : () => _authController.submitSignIn(_signInFormKey, context, _signInEmailController.text, _signInPasswordController.text),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primaryBlue,
                      foregroundColor: Colors.white,
                      elevation: 1,
                      shadowColor: AppColors.primaryBlue.withOpacity(0.3),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: _authController.isLoading.value
                        ? const SizedBox(
                            height: 22,
                            width: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: Colors.white,
                            ),
                          )
                        : Text(
                            'Login',
                            style: GoogleFonts.poppins(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                  ),
                ),
                context.sh(20),
                
                // Bottom hint helper
                Center(
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'Swipe left or tap Register above to sign up ',
                        style: GoogleFonts.poppins(
                          fontSize: 12,
                          color: isDark ? AppColors.darkTextSecondary.withOpacity(0.7) : AppColors.lightTextSecondary.withOpacity(0.7),
                        ),
                      ),
                      Icon(
                        Icons.arrow_forward_rounded,
                        size: 14,
                        color: AppColors.primaryBlue.withOpacity(0.6),
                      ),
                    ],
                  ),
                ),
                context.sh(24),
              ],
            ),
          )),
        ),
      ),
    );
  }

  Widget _buildSignUpView(BuildContext context, bool isDark) {
    return SingleChildScrollView(
      padding: const EdgeInsets.only(left: 36, right: 36, top: 16, bottom: 48),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Obx(() => Form(
            key: _signUpFormKey,
            autovalidateMode: _authController.signUpSubmitted.value 
                ? AutovalidateMode.onUserInteraction 
                : AutovalidateMode.disabled,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                context.sh(8),
                
                // Full Name field
                Text(
                  'Full Name',
                  style: GoogleFonts.poppins(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: isDark ? AppColors.darkText : AppColors.lightText,
                  ),
                ),
                context.sh(8),
                TextFormField(
                  controller: _signUpNameController,
                  keyboardType: TextInputType.name,
                  style: GoogleFonts.poppins(fontSize: 14),
                  decoration: InputDecoration(
                    hintText: 'Arjun Sharma',
                    hintStyle: TextStyle(color: isDark ? Colors.white24 : Colors.black26),
                    prefixIcon: const Icon(Icons.person_outline_rounded, size: 20),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Full name is required';
                    }
                    if (value.trim().length < 2) {
                      return 'Please enter your full name';
                    }
                    return null;
                  },
                ),
                context.sh(16),
                
                // Email field
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Email Address',
                      style: GoogleFonts.poppins(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: isDark ? AppColors.darkText : AppColors.lightText,
                      ),
                    ),
                    Obx(() => _authController.isSignUpEmailValid.value && _signUpEmailController.text.isNotEmpty
                        ? const Text('✓ Valid Grid ID', style: TextStyle(fontSize: 10, color: AppColors.healthy, fontWeight: FontWeight.bold))
                        : const SizedBox.shrink()),
                  ],
                ),
                context.sh(8),
                TextFormField(
                  controller: _signUpEmailController,
                  keyboardType: TextInputType.emailAddress,
                  style: GoogleFonts.poppins(fontSize: 14),
                  onChanged: (val) => _authController.validateSignUpEmail(val),
                  decoration: InputDecoration(
                    hintText: 'operator@powercortex.in',
                    hintStyle: TextStyle(color: isDark ? Colors.white24 : Colors.black26),
                    prefixIcon: const Icon(Icons.email_outlined, size: 20),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Email address is required';
                    }
                    if (!RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$').hasMatch(value.trim())) {
                      return 'Please enter a valid email address';
                    }
                    return null;
                  },
                ),
                context.sh(16),
                
                // Password field
                Text(
                  'Password',
                  style: GoogleFonts.poppins(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: isDark ? AppColors.darkText : AppColors.lightText,
                  ),
                ),
                context.sh(8),
                TextFormField(
                  controller: _signUpPasswordController,
                  obscureText: _authController.obscureSignUpPassword.value,
                  style: GoogleFonts.poppins(fontSize: 14),
                  onChanged: (val) => _authController.updatePasswordStrength(val),
                  decoration: InputDecoration(
                    hintText: '••••••••',
                    hintStyle: TextStyle(color: isDark ? Colors.white24 : Colors.black26),
                    prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _authController.obscureSignUpPassword.value
                            ? Icons.visibility_off_outlined
                            : Icons.visibility_outlined,
                        size: 20,
                      ),
                      onPressed: _authController.toggleSignUpPassword,
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Password is required';
                    }
                    if (value.length < 8) {
                      return 'Password must be at least 8 characters';
                    }
                    return null;
                  },
                ),
                
                // Reactive GetX Password Strength Bar
                Obx(() {
                  if (_authController.passwordStrength.value == 'None') {
                    return const SizedBox.shrink();
                  }
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 8),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(2),
                        child: LinearProgressIndicator(
                          value: _authController.strengthProgress.value,
                          backgroundColor: isDark ? AppColors.darkBorder : Colors.grey.shade200,
                          valueColor: AlwaysStoppedAnimation<Color>(_authController.strengthColor.value),
                          minHeight: 4,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Strength: ${_authController.passwordStrength.value}',
                            style: GoogleFonts.poppins(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: _authController.strengthColor.value,
                            ),
                          ),
                          if (_authController.strengthProgress.value >= 0.8)
                            Text(
                              '🔐 Secure Operator Standard',
                              style: GoogleFonts.poppins(
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                                color: AppColors.healthy,
                              ),
                            ),
                        ],
                      ),
                    ],
                  );
                }),
                
                context.sh(16),
                
                // Confirm Password field
                Text(
                  'Confirm Password',
                  style: GoogleFonts.poppins(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: isDark ? AppColors.darkText : AppColors.lightText,
                  ),
                ),
                context.sh(8),
                TextFormField(
                  controller: _signUpConfirmPasswordController,
                  obscureText: _authController.obscureSignUpConfirmPassword.value,
                  style: GoogleFonts.poppins(fontSize: 14),
                  decoration: InputDecoration(
                    hintText: '••••••••',
                    hintStyle: TextStyle(color: isDark ? Colors.white24 : Colors.black26),
                    prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _authController.obscureSignUpConfirmPassword.value
                            ? Icons.visibility_off_outlined
                            : Icons.visibility_outlined,
                        size: 20,
                      ),
                      onPressed: _authController.toggleSignUpConfirmPassword,
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please confirm your password';
                    }
                    if (value != _signUpPasswordController.text) {
                      return 'Passwords do not match';
                    }
                    return null;
                  },
                ),
                context.sh(28),
                
                // Sign Up Button
                SizedBox(
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _authController.isLoading.value 
                        ? null 
                        : () => _authController.submitSignUp(_signUpFormKey, context, _signUpNameController.text, _signUpEmailController.text, _signUpPasswordController.text, 'General'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primaryBlue,
                      foregroundColor: Colors.white,
                      elevation: 1,
                      shadowColor: AppColors.primaryBlue.withOpacity(0.3),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: _authController.isLoading.value
                        ? const SizedBox(
                            height: 22,
                            width: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: Colors.white,
                            ),
                          )
                        : Text(
                            'Register Account',
                            style: GoogleFonts.poppins(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                  ),
                ),
                context.sh(20),
                
                // Bottom hint helper
                Center(
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.arrow_back_rounded,
                        size: 14,
                        color: AppColors.primaryBlue.withOpacity(0.6),
                      ),
                      Text(
                        ' Swipe right or tap Login above to log in',
                        style: GoogleFonts.poppins(
                          fontSize: 12,
                          color: isDark ? AppColors.darkTextSecondary.withOpacity(0.7) : AppColors.lightTextSecondary.withOpacity(0.7),
                        ),
                      ),
                    ],
                  ),
                ),
                context.sh(24),
              ],
            ),
          )),
        ),
      ),
    );
  }

  Widget _featurePill(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.06),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: Colors.white.withOpacity(0.12)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: Colors.yellow.shade700),
          const SizedBox(width: 8),
          Text(
            label,
            style: GoogleFonts.poppins(
              fontSize: 12.5,
              fontWeight: FontWeight.w500,
              color: Colors.white.withOpacity(0.9),
            ),
          ),
        ],
      ),
    );
  }
}

class GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white
      ..strokeWidth = 1.0;

    const spacing = 40.0;
    for (double x = 0; x < size.width; x += spacing) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += spacing) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
