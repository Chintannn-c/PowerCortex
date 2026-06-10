import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:get/get.dart';
import '../../../core/theme/app_colors.dart';
import '../two_factor_setup_controller.dart';
import 'package:shimmer/shimmer.dart';

class TwoFactorSetupScreen extends StatelessWidget {
  TwoFactorSetupScreen({super.key});

  final TwoFactorSetupController controller = Get.put(TwoFactorSetupController());

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBg : AppColors.lightBg,
      appBar: AppBar(
        title: const Text('Security Verification'),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Obx(() {
              if (controller.isSuccess.value) {
                return SingleChildScrollView(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 36.0, vertical: 16.0),
                    child: _buildSuccessState(context, isDark),
                  ),
                );
              }

              if (controller.isLoading.value) {
                return SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 36.0, vertical: 32.0),
                  child: _buildSkeletonLoader(isDark),
                );
              }

              return Column(
                children: [
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.symmetric(horizontal: 36.0, vertical: 32.0),
                      child: _buildVerificationForm(context, isDark),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(36.0, 0, 36.0, 32.0),
                    child: _buildActionButtons(context, isDark),
                  ),
                ],
              );
            }),
          ),
        ),
      ),
    );
  }

  Widget _buildSkeletonLoader(bool isDark) {
    final baseColor = isDark ? Colors.grey[850]! : Colors.grey[300]!;
    final highlightColor = isDark ? Colors.grey[800]! : Colors.grey[100]!;
    
    return Shimmer.fromColors(
      baseColor: baseColor,
      highlightColor: highlightColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Title skeleton
          Center(
            child: Container(
              height: 28,
              width: 200,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          ),
          const SizedBox(height: 16),
          
          // Description skeleton (2 lines)
          Center(
            child: Container(
              height: 14,
              width: 280,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          ),
          const SizedBox(height: 6),
          Center(
            child: Container(
              height: 14,
              width: 220,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          ),
          const SizedBox(height: 32),
          
          // Subtitle skeleton
          Container(
            height: 14,
            width: 80,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
          const SizedBox(height: 8),
          
          // OTP Boxes skeleton
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(6, (index) {
              return Container(
                width: 45,
                height: 56,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                ),
              );
            }),
          ),
          const SizedBox(height: 24),
          
          // Timer skeleton
          Center(
            child: Container(
              height: 14,
              width: 140,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          ),
          const SizedBox(height: 48),
          
          // Buttons skeleton
          Container(
            height: 52,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
            ),
          ),
          const SizedBox(height: 16),
          Container(
            height: 52,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVerificationForm(BuildContext context, bool isDark) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Title
        Text(
          'Two-Step Verification',
          textAlign: TextAlign.center,
          style: GoogleFonts.poppins(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: isDark ? Colors.white : Colors.black,
          ),
        ),
        const SizedBox(height: 12),

        // Description
        Text(
          'To help keep your account secure, we\'ve sent a verification code to your registered device.',
          textAlign: TextAlign.center,
          style: GoogleFonts.poppins(
            fontSize: 14,
            color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
          ),
        ),
        const SizedBox(height: 32),

        Text(
          'Secure Code',
          style: GoogleFonts.poppins(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: isDark ? AppColors.darkText : AppColors.lightText,
          ),
        ),
        const SizedBox(height: 8),

        // OTP Section
        _buildOtpBoxes(context, isDark),
        const SizedBox(height: 16),

        // Error message if any
        if (controller.errorMessage.value.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 12.0),
            child: Text(
              controller.errorMessage.value,
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: AppColors.critical,
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),

        // Timer
        _buildTimerText(context, isDark),
      ],
    );
  }

  Widget _buildOtpBoxes(BuildContext context, bool isDark) {
    return GestureDetector(
      onTap: () {
        controller.otpFocusNode.requestFocus();
      },
      child: Stack(
        alignment: Alignment.center,
        children: [
          Opacity(
            opacity: 0.0,
            child: SizedBox(
              height: 56,
              child: TextField(
                controller: controller.codeController,
                focusNode: controller.otpFocusNode,
                keyboardType: TextInputType.number,
                maxLength: 6,
                autofocus: true,
                showCursor: false,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                ],
                onChanged: (val) {
                  controller.codeLength.value = val.length;
                  if (val.length == 6) {
                    controller.verifyAndEnable();
                  }
                },
              ),
            ),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(6, (index) {
              String char = "";
              if (controller.codeController.text.length > index) {
                char = controller.codeController.text[index];
              }

              bool isFocused = controller.codeController.text.length == index &&
                  controller.otpFocusNode.hasFocus;

              return AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: 45,
                height: 56,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkBg : AppColors.lightBg,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: isFocused
                        ? AppColors.primaryBlue
                        : (isDark ? AppColors.darkBorder : AppColors.lightBorder),
                    width: isFocused ? 2.0 : 1.0,
                  ),
                ),
                child: Text(
                  char,
                  style: GoogleFonts.poppins(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: isDark ? Colors.white : Colors.black,
                  ),
                ),
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildTimerText(BuildContext context, bool isDark) {
    final seconds = controller.secondsRemaining.value;
    final formattedSec = seconds.toString().padLeft(2, '0');

    if (seconds > 0) {
      return Center(
        child: Text(
          'Resend code in 00:$formattedSec',
          style: GoogleFonts.poppins(
            fontSize: 13,
            color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
            fontWeight: FontWeight.w500,
          ),
        ),
      );
    } else {
      return Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.check_circle_outline, color: AppColors.healthy, size: 16),
          const SizedBox(width: 6),
          Text(
            'Ready to resend notification',
            style: GoogleFonts.poppins(
              fontSize: 13,
              color: AppColors.healthy,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      );
    }
  }

  Widget _buildActionButtons(BuildContext context, bool isDark) {
    final isTimerActive = controller.secondsRemaining.value > 0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Primary Button
        SizedBox(
          height: 52,
          child: ElevatedButton(
            onPressed: (controller.isVerifying.value || controller.codeLength.value < 6)
                ? null
                : () => controller.verifyAndEnable(),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primaryBlue,
              foregroundColor: Colors.white,
              elevation: 1,
              shadowColor: AppColors.primaryBlue.withOpacity(0.3),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: controller.isVerifying.value
                ? const SizedBox(
                    height: 22,
                    width: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      color: Colors.white,
                    ),
                  )
                : Text(
                    'Verify Code',
                    style: GoogleFonts.poppins(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
          ),
        ),
        const SizedBox(height: 16),

        // Secondary Button
        SizedBox(
          height: 52,
          child: OutlinedButton(
            onPressed: (isTimerActive || controller.isNotifying.value)
                ? null
                : () => controller.resendNotification(),
            style: OutlinedButton.styleFrom(
              foregroundColor: isDark ? Colors.white : Colors.black,
              side: BorderSide(
                color: isTimerActive 
                  ? (isDark ? Colors.white24 : Colors.black26) 
                  : (isDark ? Colors.white54 : Colors.black54),
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: controller.isNotifying.value
                ? const SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(color: AppColors.primaryBlue, strokeWidth: 2),
                  )
                : Text(
                    'Resend Notification',
                    style: GoogleFonts.poppins(
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                      color: isTimerActive 
                        ? (isDark ? Colors.white38 : Colors.black38) 
                        : (isDark ? Colors.white : Colors.black),
                    ),
                  ),
          ),
        ),
      ],
    );
  }

  Widget _buildSuccessState(BuildContext context, bool isDark) {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: AppColors.healthy.withOpacity(0.15),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.shield_rounded,
              color: AppColors.healthy,
              size: 40,
            ),
          ),
          const SizedBox(height: 32),
          Text(
            'Security Verified',
            textAlign: TextAlign.center,
            style: GoogleFonts.poppins(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: isDark ? Colors.white : Colors.black,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Your device has been authenticated and grid access is now secured.',
            textAlign: TextAlign.center,
            style: GoogleFonts.poppins(
              fontSize: 14,
              color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 40),
          const Center(
            child: SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                color: AppColors.healthy,
                strokeWidth: 2.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
