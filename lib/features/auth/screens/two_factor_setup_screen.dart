import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import '../../../core/theme/app_colors.dart';
import '../two_factor_setup_controller.dart';

class TwoFactorSetupScreen extends StatelessWidget {
  TwoFactorSetupScreen({super.key});

  final TwoFactorSetupController controller = Get.put(TwoFactorSetupController());

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBg : AppColors.lightBg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, 
            color: isDark ? Colors.white : Colors.black, 
            size: 20
          ),
          onPressed: () => Get.back(),
        ),
        title: Text(
          'Security',
          style: TextStyle(
            color: isDark ? Colors.white : Colors.black,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
                child: Obx(() {
                  if (controller.isSuccess.value) {
                    return _buildSuccessState(context);
                  }

                  if (controller.isLoading.value) {
                    return const Center(
                      child: Padding(
                        padding: EdgeInsets.all(40.0),
                        child: CircularProgressIndicator(color: AppColors.primaryBlue),
                      ),
                    );
                  }

                  return _buildVerificationForm(context);
                }),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildVerificationForm(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Title
        const Text(
          'Two-Step Verification',
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.5,
          ),
        ),
        const SizedBox(height: 12),

        // Description
        Text(
          'To help keep your account secure, we\'ve sent a verification code to your registered device.',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 14,
            color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
            height: 1.4,
          ),
        ),
        const SizedBox(height: 28),

        // Notification Preview
        _buildNotificationPreview(context),
        const SizedBox(height: 28),

        Align(
          alignment: Alignment.centerLeft,
          child: Padding(
            padding: const EdgeInsets.only(left: 4.0, bottom: 8.0),
            child: Text(
              'ENTER CODE',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                letterSpacing: 0.5,
              ),
            ),
          ),
        ),

        // OTP Section
        _buildOtpBoxes(context),
        const SizedBox(height: 12),

        // Error message if any
        if (controller.errorMessage.value.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 12.0),
            child: Text(
              controller.errorMessage.value,
              style: const TextStyle(
                color: AppColors.critical,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),

        // Timer
        _buildTimerText(context),
        const SizedBox(height: 24),

        // Security Information Card
        _buildSecurityInfoCard(context),
        const SizedBox(height: 32),

        // Action Buttons
        _buildActionButtons(context),
        const SizedBox(height: 20),

        // Text Links
        _buildTextLinks(context),
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildNotificationPreview(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return GestureDetector(
      onTap: () {
        // Tapping autofills and validates
        final code = controller.activeCode.value;
        controller.codeController.text = code;
        controller.codeLength.value = code.length;
        controller.verifyAndEnable();
      },
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isDark ? AppColors.darkCard : Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(isDark ? 0.2 : 0.04),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppColors.primaryBlue.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.notifications_active,
                color: AppColors.primaryBlue,
                size: 20,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        '🔔 Security Alert',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                      Text(
                        'Just Now',
                        style: TextStyle(
                          fontSize: 11,
                          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Your verification code is:',
                    style: TextStyle(fontSize: 13, height: 1.3),
                  ),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.primaryBlue.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Text(
                      '••••••',
                      style: TextStyle(
                        fontFamily: 'monospace',
                        fontWeight: FontWeight.w800,
                        fontSize: 18,
                        letterSpacing: 4.0,
                        color: AppColors.primaryBlue,
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Expires in 5 minutes.',
                    style: TextStyle(
                      fontSize: 11,
                      color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOtpBoxes(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return GestureDetector(
      onTap: () {
        controller.otpFocusNode.requestFocus();
      },
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Hidden transparent TextField to capture text input/pasting
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
                  if (val.length == 6) {
                    controller.verifyAndEnable();
                  }
                },
              ),
            ),
          ),
          // 6 Separate OTP Boxes
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(6, (index) {
              String char = "";
              if (controller.codeController.text.length > index) {
                char = controller.codeController.text[index];
              }

              bool isFocused = controller.codeController.text.length == index &&
                  controller.otpFocusNode.hasFocus;

              return Container(
                width: 48,
                height: 56,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkCard : Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isFocused
                        ? AppColors.primaryBlue
                        : (isDark ? AppColors.darkBorder : AppColors.lightBorder),
                    width: isFocused ? 2.2 : 1.0,
                  ),
                  boxShadow: isFocused
                      ? [
                          BoxShadow(
                            color: AppColors.primaryBlue.withOpacity(0.15),
                            blurRadius: 8,
                            offset: const Offset(0, 3),
                          )
                        ]
                      : [],
                ),
                child: Text(
                  char,
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: isDark ? Colors.white : AppColors.darkBlue,
                  ),
                ),
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildTimerText(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final seconds = controller.secondsRemaining.value;
    final formattedSec = seconds.toString().padLeft(2, '0');

    if (seconds > 0) {
      return Text(
        'Resend code in 00:$formattedSec',
        style: TextStyle(
          fontSize: 13,
          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
          fontWeight: FontWeight.w500,
        ),
      );
    } else {
      return Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.check_circle_outline, color: AppColors.healthy, size: 14),
          const SizedBox(width: 4),
          Text(
            'Ready to resend notification',
            style: TextStyle(
              fontSize: 13,
              color: AppColors.healthy,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      );
    }
  }

  Widget _buildSecurityInfoCard(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard.withOpacity(0.4) : AppColors.lightBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.info_outline_rounded,
                size: 16,
                color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
              ),
              const SizedBox(width: 8),
              Text(
                'LOGIN METADATA',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                  color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _buildMetadataRow('Device', 'Chrome on Windows', context),
          const Divider(height: 16),
          _buildMetadataRow('Location', 'New Device Login', context),
          const Divider(height: 16),
          _buildMetadataRow('Time', 'Just Now', context),
        ],
      ),
    );
  }

  Widget _buildMetadataRow(String label, String value, BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 13,
            color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
          ),
        ),
        Text(
          value,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  Widget _buildActionButtons(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isTimerActive = controller.secondsRemaining.value > 0;

    return Column(
      children: [
        // Primary Button
        SizedBox(
          width: double.infinity,
          height: 50,
          child: ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primaryBlue,
              foregroundColor: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            onPressed: (controller.isVerifying.value || controller.codeLength.value < 6)
                ? null
                : () => controller.verifyAndEnable(),
            child: controller.isVerifying.value
                ? const SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5),
                  )
                : const Text(
                    'Verify Code',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
          ),
        ),
        const SizedBox(height: 12),

        // Secondary Button
        SizedBox(
          width: double.infinity,
          height: 50,
          child: OutlinedButton(
            style: OutlinedButton.styleFrom(
              foregroundColor: isDark ? Colors.white : AppColors.darkBlue,
              side: BorderSide(
                color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            onPressed: (isTimerActive || controller.isNotifying.value)
                ? null
                : () => controller.resendNotification(),
            child: controller.isNotifying.value
                ? const SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(color: AppColors.primaryBlue, strokeWidth: 2),
                  )
                : Text(
                    'Resend Notification',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      color: isTimerActive 
                        ? (isDark ? Colors.white24 : Colors.black26) 
                        : (isDark ? Colors.white : AppColors.darkBlue),
                    ),
                  ),
          ),
        ),
      ],
    );
  }

  Widget _buildTextLinks(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        TextButton(
          onPressed: () {
            Get.snackbar(
              'Security Flow',
              'Alternative verification methods are currently restricted by security policy.',
              snackPosition: SnackPosition.BOTTOM,
              backgroundColor: isDark ? AppColors.darkCard : Colors.white,
              colorText: isDark ? Colors.white : AppColors.darkBlue,
            );
          },
          child: const Text(
            'Use Another Method',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppColors.primaryBlue,
            ),
          ),
        ),
        Container(
          width: 4,
          height: 4,
          decoration: BoxDecoration(
            color: isDark ? Colors.white24 : Colors.black26,
            shape: BoxShape.circle,
          ),
        ),
        TextButton(
          onPressed: () {
            Get.snackbar(
              'Device Security',
              'This device has been flagged as trusted for the next 30 days.',
              snackPosition: SnackPosition.BOTTOM,
              backgroundColor: AppColors.healthy,
              colorText: Colors.white,
            );
          },
          child: const Text(
            'Trust This Device',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppColors.primaryBlue,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSuccessState(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 90,
            height: 90,
            decoration: BoxDecoration(
              color: AppColors.healthy.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.check_circle_rounded,
              color: AppColors.healthy,
              size: 56,
            ),
          ),
          const SizedBox(height: 28),
          const Text(
            '✓ Verification Successful',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Your device has been verified and Two-Step Verification is active.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 36),
          const SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(
              color: AppColors.healthy,
              strokeWidth: 2,
            ),
          ),
        ],
      ),
    );
  }
}
