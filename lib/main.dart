import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'core/theme/app_theme.dart';
import 'features/splash/splash_screen.dart';
import 'features/auth/login_screen.dart';
import 'features/auth/register_screen.dart';
import 'features/home/home_shell.dart';
import 'features/auth/screens/two_factor_setup_screen.dart';
import 'features/anomalies/fault_details_screen.dart';
import 'features/anomalies/consumer_investigation_screen.dart';
import 'features/settings/help_support_screen.dart';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  debugPrint("Handling background message: ${message.messageId}");
}

/// Global flag indicating whether Firebase was successfully initialized.
/// NotificationService and other Firebase-dependent features should check
/// this before attempting to use Firebase APIs.
bool firebaseAvailable = false;

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    await Firebase.initializeApp(
      options: const FirebaseOptions(
        apiKey: String.fromEnvironment('FIREBASE_API_KEY', defaultValue: ''),
        appId: String.fromEnvironment('FIREBASE_APP_ID', defaultValue: ''),
        messagingSenderId: String.fromEnvironment('FIREBASE_SENDER_ID', defaultValue: ''),
        projectId: String.fromEnvironment('FIREBASE_PROJECT_ID', defaultValue: ''),
      ),
    );
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
    firebaseAvailable = true;
  } catch (e) {
    debugPrint("Firebase initialization failed: $e — push notifications disabled.");
    firebaseAvailable = false;
  }
  const storage = FlutterSecureStorage();
  final themeStr = await storage.read(key: 'theme_mode');
  
  ThemeMode initialThemeMode = ThemeMode.system;
  if (themeStr == 'dark') {
    initialThemeMode = ThemeMode.dark;
  } else if (themeStr == 'light') {
    initialThemeMode = ThemeMode.light;
  }

  runApp(PowerCortexApp(initialThemeMode: initialThemeMode));
}

class ThemeController extends GetxController {
  final Rx<ThemeMode> themeMode;
  ThemeController(ThemeMode initial) : themeMode = initial.obs;

  void changeTheme(ThemeMode mode) {
    themeMode.value = mode;
    Get.changeThemeMode(mode);
  }
}

class PowerCortexApp extends StatelessWidget {
  final ThemeMode initialThemeMode;

  const PowerCortexApp({super.key, this.initialThemeMode = ThemeMode.system});

  @override
  Widget build(BuildContext context) {
    // Initialize global services
    final themeController = Get.put(ThemeController(initialThemeMode), permanent: true);

    return Obx(() => GetMaterialApp(
      title: 'PowerCortex',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeController.themeMode.value,
      initialRoute: '/',
      routes: {
        '/': (context) => const SplashScreen(),
        '/login': (context) => const LoginScreen(),
        '/signin': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/home': (context) => const HomeShell(),
        '/settings/2fa': (context) => TwoFactorSetupScreen(),
        '/settings/help': (context) => const HelpSupportScreen(),
        '/fault-details': (context) => const FaultDetailsScreen(),
        '/consumer-investigation': (context) => const ConsumerInvestigationScreen(),
      },
    ));
  }
}