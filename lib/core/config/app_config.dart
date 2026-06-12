import 'package:flutter/foundation.dart';

class AppConfig {
  /// The base URL for the PowerCortex backend API.
  /// 
  /// Override at build time using:
  ///   flutter run --dart-define=API_BASE_URL=https://api.powercortex.com
  ///   flutter build apk --dart-define=API_BASE_URL=https://api.powercortex.com
  static String get apiBaseUrl {
    // Check for build-time environment variable first
    const envUrl = String.fromEnvironment('API_BASE_URL');
    if (envUrl.isNotEmpty) return envUrl;

    // Development fallbacks
    if (kIsWeb) return 'http://127.0.0.1:8000';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://127.0.0.1:8000';
  }

  /// WebSocket base URL derived from the API base URL.
  static String get wsBaseUrl {
    final uri = Uri.parse(apiBaseUrl);
    final scheme = uri.scheme == 'https' ? 'wss' : 'ws';
    return '$scheme://${uri.host}:${uri.port}';
  }

  /// Timeout for API requests
  static const Duration apiTimeout = Duration(seconds: 15);
}

