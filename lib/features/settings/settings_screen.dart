import 'package:flutter/material.dart';
import '../../core/utils/responsive.dart';
import '../../core/theme/app_colors.dart';
import 'package:get/get.dart';
import '../auth/auth_controller.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../main.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _isDarkMode = false;
  bool _pushNotifications = true;
  bool _emailAlerts = false;

  @override
  void initState() {
    super.initState();
    _isDarkMode = Get.isDarkMode;
    _loadSettings();
  }

  void _loadSettings() {
    final user = Get.find<AuthController>().currentUser.value;
    setState(() {
      if (user != null) {
        _pushNotifications = user.pushNotifications;
        _emailAlerts = user.emailAlerts;
      }
    });
  }

  void _toggleDarkMode(bool value) async {
    setState(() => _isDarkMode = value);
    if (Get.isRegistered<ThemeController>()) {
      Get.find<ThemeController>().changeTheme(value ? ThemeMode.dark : ThemeMode.light);
    } else {
      Get.changeThemeMode(value ? ThemeMode.dark : ThemeMode.light);
    }
    const storage = FlutterSecureStorage();
    await storage.write(key: 'theme_mode', value: value ? 'dark' : 'light');
  }

  void _showEditProfileDialog() {
    final user = Get.find<AuthController>().currentUser.value;
    if (user == null) return;
    
    final nameController = TextEditingController(text: user.fullName);
    final deptController = TextEditingController(text: user.department);
    
    Get.defaultDialog(
      title: 'Edit Profile',
      content: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: const InputDecoration(
                labelText: 'Full Name',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: deptController,
              decoration: const InputDecoration(
                labelText: 'Department',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
      ),
      textConfirm: 'Save',
      textCancel: 'Cancel',
      confirmTextColor: Colors.white,
      buttonColor: AppColors.primaryBlue,
      cancelTextColor: AppColors.primaryBlue,
      onConfirm: () {
        Get.find<AuthController>().updateProfile(
          nameController.text.trim(), 
          deptController.text.trim(),
        );
        Get.back();
      },
    );
  }

  void _showChangePasswordDialog() {
    final currentController = TextEditingController();
    final newController = TextEditingController();
    
    Get.defaultDialog(
      title: 'Change Password',
      content: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: currentController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Current Password',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: newController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'New Password',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
      ),
      textConfirm: 'Save',
      textCancel: 'Cancel',
      confirmTextColor: Colors.white,
      buttonColor: AppColors.primaryBlue,
      cancelTextColor: AppColors.primaryBlue,
      onConfirm: () {
        Get.find<AuthController>().changePassword(
          currentController.text, 
          newController.text,
        );
        Get.back();
      },
    );
  }

  void _showDisable2FADialog() {
    Get.defaultDialog(
      title: 'Disable Two-Step Verification?',
      content: const Padding(
        padding: EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
        child: Text(
          'Are you sure you want to disable two-step verification? This will make your grid operator profile less secure.',
          textAlign: TextAlign.center,
        ),
      ),
      textConfirm: 'Disable',
      textCancel: 'Cancel',
      confirmTextColor: Colors.white,
      buttonColor: AppColors.critical,
      cancelTextColor: AppColors.primaryBlue,
      onConfirm: () async {
        Get.back(); // close dialog
        final result = await Get.find<AuthController>().disable2FA();
        if (result['success'] == true) {
          Get.snackbar(
            'Verification Disabled',
            'Two-step verification has been successfully disabled.',
            snackPosition: SnackPosition.BOTTOM,
            backgroundColor: AppColors.warning,
            colorText: Colors.white,
            margin: const EdgeInsets.all(16),
            borderRadius: 10,
            icon: const Icon(Icons.warning_amber_rounded, color: Colors.white),
          );
        } else {
          Get.snackbar(
            'Error',
            result['message'] ?? 'Failed to disable verification.',
            snackPosition: SnackPosition.BOTTOM,
            backgroundColor: AppColors.critical,
            colorText: Colors.white,
            margin: const EdgeInsets.all(16),
            borderRadius: 10,
            icon: const Icon(Icons.error_outline, color: Colors.white),
          );
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Profile Card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 32,
                    backgroundColor: AppColors.primaryBlue.withOpacity(0.15),
                    child: const Icon(Icons.person, size: 32, color: AppColors.primaryBlue),
                  ),
                  context.sw(16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Obx(() => Text(
                          Get.find<AuthController>().currentUser.value?.fullName ?? 'User', 
                          style: theme.textTheme.headlineSmall
                        )),
                        context.sh(2),
                        Obx(() => Text(
                          Get.find<AuthController>().currentUser.value?.department ?? 'Operator',
                          style: theme.textTheme.bodySmall
                        )),
                        context.sh(2),
                        Obx(() => Text(
                          Get.find<AuthController>().currentUser.value?.email ?? 'user@powercortex.in',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: AppColors.primaryBlue,
                          )
                        )),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: _showEditProfileDialog,
                    icon: const Icon(Icons.edit_outlined, size: 20),
                  ),
                ],
              ),
            ),
          ),
          context.sh(24),

          // Appearance
          _sectionLabel(context, 'Appearance'),
          context.sh(8),
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  title: const Text('Dark Mode'),
                  subtitle: const Text('Switch to dark theme'),
                  secondary: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppColors.primaryBlue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.dark_mode, color: AppColors.primaryBlue, size: 20),
                  ),
                  value: _isDarkMode,
                  onChanged: _toggleDarkMode,
                  activeColor: AppColors.primaryBlue,
                ),
              ],
            ),
          ),
          context.sh(20),

          // Notifications
          _sectionLabel(context, 'Notifications'),
          context.sh(8),
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  title: const Text('Push Notifications'),
                  subtitle: const Text('Receive real-time alerts'),
                  secondary: _iconBox(Icons.notifications_active),
                  value: _pushNotifications,
                  onChanged: (v) {
                    setState(() => _pushNotifications = v);
                    Get.find<AuthController>().updatePreferences(v, _emailAlerts);
                  },
                  activeColor: AppColors.primaryBlue,
                ),
                const Divider(height: 1),
                SwitchListTile(
                  title: const Text('Email Alerts'),
                  subtitle: const Text('Daily summary emails'),
                  secondary: _iconBox(Icons.email),
                  value: _emailAlerts,
                  onChanged: (v) {
                    setState(() => _emailAlerts = v);
                    Get.find<AuthController>().updatePreferences(_pushNotifications, v);
                  },
                  activeColor: AppColors.primaryBlue,
                ),
              ],
            ),
          ),
          context.sh(20),

          // Security
          _sectionLabel(context, 'Security'),
          context.sh(8),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: _iconBox(Icons.lock_outline),
                  title: const Text('Change Password'),
                  trailing: const Icon(Icons.chevron_right, size: 20),
                  onTap: _showChangePasswordDialog,
                ),
                const Divider(height: 1),
                Obx(() {
                  final is2FAEnabled = Get.find<AuthController>().currentUser.value?.twoFactorEnabled ?? false;
                  return ListTile(
                    leading: _iconBox(Icons.security),
                    title: const Text('Two-Step Verification'),
                    subtitle: Text(
                      is2FAEnabled
                          ? 'Enabled • Tap to configure or disable'
                          : 'Require an authenticator code to log in',
                    ),
                    trailing: is2FAEnabled
                        ? const Icon(Icons.check_circle, color: AppColors.healthy, size: 20)
                        : const Icon(Icons.chevron_right, size: 20),
                    onTap: () {
                      if (is2FAEnabled) {
                        _showDisable2FADialog();
                      } else {
                        Get.toNamed('/settings/2fa');
                      }
                    },
                  );
                }),
              ],
            ),
          ),
          context.sh(20),

          // System
          _sectionLabel(context, 'System'),
          context.sh(8),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: _iconBox(Icons.info_outline),
                  title: const Text('App Version'),
                  trailing: Text('v1.0.0',
                      style: theme.textTheme.bodySmall?.copyWith(
                        fontWeight: FontWeight.w600,
                      )),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: _iconBox(Icons.help_outline),
                  title: const Text('Help & Support'),
                  trailing: const Icon(Icons.chevron_right, size: 20),
                  onTap: () {
                    Get.toNamed('/settings/help');
                  },
                ),
                const Divider(height: 1),
                ListTile(
                  leading: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppColors.critical.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.logout, color: AppColors.critical, size: 20),
                  ),
                  title: const Text('Logout',
                      style: TextStyle(color: AppColors.critical)),
                  onTap: () {
                    Get.find<AuthController>().logout();
                  },
                ),
              ],
            ),
          ),
          context.sh(24),
        ],
      ),
    );
  }

  Widget _sectionLabel(BuildContext context, String label) {
    return Text(label, style: Theme.of(context).textTheme.labelLarge);
  }

  Widget _iconBox(IconData icon) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: AppColors.primaryBlue.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(icon, color: AppColors.primaryBlue, size: 20),
    );
  }
}
