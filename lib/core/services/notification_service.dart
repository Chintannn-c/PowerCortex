import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:guvnl_project/core/api/api_client.dart';
import '../config/app_config.dart';
import '../../features/home/home_shell.dart';
import '../../main.dart' show firebaseAvailable;

class NotificationModel {
  final String id;
  final String title;
  final String message;
  final String type;
  final String screen;
  final String? entityId;
  final bool isRead;
  final String createdAt;

  NotificationModel({
    required this.id,
    required this.title,
    required this.message,
    required this.type,
    required this.screen,
    this.entityId,
    required this.isRead,
    required this.createdAt,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: json['_id'] ?? json['id'] ?? '',
      title: json['title'] ?? '',
      message: json['message'] ?? '',
      type: json['type'] ?? '',
      screen: json['screen'] ?? '',
      entityId: json['entity_id'],
      isRead: json['is_read'] ?? false,
      createdAt: json['created_at'] ?? '',
    );
  }
}

@pragma('vm:entry-point')
void notificationTapBackground(NotificationResponse notificationResponse) {
  debugPrint("Background tap on local notification: ${notificationResponse.actionId}");
}

class NotificationService extends GetxController {
  final _api = ApiClient().dio;
  final _secureStorage = const FlutterSecureStorage();
  final FlutterLocalNotificationsPlugin _localNotifications = FlutterLocalNotificationsPlugin();

  final RxList<NotificationModel> notifications = <NotificationModel>[].obs;
  final RxInt unreadCount = 0.obs;
  final RxBool isLoading = false.obs;

  WebSocketChannel? _wsChannel;
  bool _isConnecting = false;

  /// Exponential backoff state for WebSocket reconnection
  int _wsReconnectAttempts = 0;
  static const int _wsMaxReconnectAttempts = 10;
  static const int _wsBaseDelaySeconds = 2;
  static const int _wsMaxDelaySeconds = 30;

  /// Track recently processed notification IDs to prevent duplicates
  final Set<String> _processedNotificationIds = {};

  @override
  void onInit() {
    super.onInit();
    fetchNotifications();
    initLocalNotifications();
    if (firebaseAvailable) {
      initFirebaseMessaging();
    }
    connectWebSocket();
  }

  Future<void> initLocalNotifications() async {
    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const DarwinInitializationSettings initializationSettingsDarwin =
        DarwinInitializationSettings();
    const InitializationSettings initializationSettings = InitializationSettings(
      android: initializationSettingsAndroid,
      iOS: initializationSettingsDarwin,
    );

    await _localNotifications.initialize(
      initializationSettings,
      onDidReceiveNotificationResponse: onDidReceiveNotificationResponse,
      onDidReceiveBackgroundNotificationResponse: notificationTapBackground,
    );
  }

  Future<void> initFirebaseMessaging() async {
    // Request notification permission
    await FirebaseMessaging.instance.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      criticalAlert: true,
    );

    // Retrieve FCM Device token
    try {
      String? token = await FirebaseMessaging.instance.getToken();
      if (token != null) {
        debugPrint("FCM Device Token: $token");
        await registerFcmToken(token);
      }
    } catch (e) {
      debugPrint("Error getting FCM token: $e");
    }

    // Handle foreground notifications
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint("Foreground FCM message received: ${message.messageId}");
      
      final String notifId = message.data['id'] ?? '';
      final title = message.notification?.title ?? "Grid Alert";
      final body = message.notification?.body ?? "";

      // Deduplicate notifications
      if (notifId.isNotEmpty) {
        if (_processedNotificationIds.contains(notifId)) {
          debugPrint("FCM: Notification $notifId already processed. Skipping duplicate.");
          return;
        }
        _processedNotificationIds.add(notifId);
      }

      // Skip displaying empty notifications
      if (title.trim().isEmpty || body.trim().isEmpty) {
        debugPrint("FCM: Skipping notification because title or body is empty. Title: '$title', Body: '$body'");
        return;
      }

      final payloadData = {
        'id': notifId,
        'screen': message.data['screen'] ?? '',
        'entity_id': message.data['entity_id'] ?? '',
        'type': message.data['type'] ?? '',
      };
      showLocalNotification(
        id: message.hashCode,
        title: title,
        body: body,
        payload: jsonEncode(payloadData),
      );
    });

    // Handle background notification clicks when app is in background (but not terminated)
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      debugPrint("FCM message clicked: ${message.messageId}");
      _handleFcmMessageTap(message);
    });

    // Check if app was opened from a terminated state via a notification
    FirebaseMessaging.instance.getInitialMessage().then((RemoteMessage? message) {
      if (message != null) {
        debugPrint("FCM initial message received: ${message.messageId}");
        _handleFcmMessageTap(message);
      }
    });
  }

  void _handleFcmMessageTap(RemoteMessage message) async {
    final String? notificationId = message.data['id'];
    if (notificationId != null && notificationId.isNotEmpty) {
      if (notifications.isEmpty) {
        await fetchNotifications();
      }
      final index = notifications.indexWhere((n) => n.id == notificationId);
      if (index != -1) {
        handleNotificationTap(notifications[index]);
      } else {
        // Fallback using data payload directly
        final screen = message.data['screen'] ?? '';
        final entityId = message.data['entity_id'] ?? '';
        final type = message.data['type'] ?? '';
        final dummyNotif = NotificationModel(
          id: notificationId,
          title: message.notification?.title ?? '',
          message: message.notification?.body ?? '',
          type: type,
          screen: screen,
          entityId: entityId,
          isRead: false,
          createdAt: DateTime.now().toIso8601String(),
        );
        handleNotificationTap(dummyNotif);
      }
    }
  }

  Future<void> showLocalNotification({
    required int id,
    required String title,
    required String body,
    required String payload,
  }) async {
    // Skip empty notifications
    if (title.trim().isEmpty || body.trim().isEmpty) {
      debugPrint("Skipping local notification because title or body is empty. Title: '$title', Body: '$body'");
      return;
    }
    const List<AndroidNotificationAction> actions = [
      AndroidNotificationAction('acknowledge', 'Acknowledge', showsUserInterface: true),
      AndroidNotificationAction('dispatch', 'Dispatch Crew', showsUserInterface: true),
      AndroidNotificationAction('snooze', 'Snooze 1h', showsUserInterface: true),
    ];

    const AndroidNotificationDetails androidDetails = AndroidNotificationDetails(
      'critical_alarms_channel',
      'Critical Grid Alarms',
      channelDescription: 'High priority alerts for grid emergencies. Bypasses DND.',
      importance: Importance.max,
      priority: Priority.high,
      playSound: true,
      enableVibration: true,
      actions: actions,
      channelShowBadge: true,
      category: AndroidNotificationCategory.alarm,
    );

    const NotificationDetails details = NotificationDetails(
      android: androidDetails,
      iOS: DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
        sound: 'default',
      ),
    );

    await _localNotifications.show(id, title, body, details, payload: payload);
  }

  Future<void> connectWebSocket() async {
    if (_isConnecting) return;
    _isConnecting = true;

    try {
      final token = await _secureStorage.read(key: 'access_token');
      if (token == null) {
        _isConnecting = false;
        // Retry connection in case they log in later
        Future.delayed(const Duration(seconds: 5), connectWebSocket);
        return;
      }

      String baseUrl = _api.options.baseUrl;
      if (baseUrl.isEmpty) {
        baseUrl = AppConfig.apiBaseUrl;
      }

      final uri = Uri.parse(baseUrl);
      final wsScheme = uri.scheme == 'https' ? 'wss' : 'ws';
      final hostPort = (uri.port == 80 || uri.port == 443 || uri.port == 0)
          ? uri.host
          : "${uri.host}:${uri.port}";

      final wsUri = Uri.parse("$wsScheme://$hostPort/api/v1/notifications/ws?token=$token");
      debugPrint("Connecting to WebSocket: $wsUri");
      _wsChannel = WebSocketChannel.connect(wsUri);
      _isConnecting = false;
      _wsReconnectAttempts = 0; // Reset backoff on successful connection

      _wsChannel!.stream.listen(
        (message) {
          debugPrint("WebSocket message received: $message");
          try {
            final data = jsonDecode(message);
            final notif = NotificationModel.fromJson(data);
            
            // Skip empty notifications
            if (notif.title.trim().isEmpty || notif.message.trim().isEmpty) {
              debugPrint("WebSocket: Skipping empty notification. Title: '${notif.title}', Message: '${notif.message}'");
              return;
            }

            // Deduplicate notifications
            if (notif.id.isNotEmpty) {
              if (_processedNotificationIds.contains(notif.id)) {
                debugPrint("WebSocket: Notification ${notif.id} already processed. Skipping duplicate.");
                return;
              }
              _processedNotificationIds.add(notif.id);
            }

            // Insert into the local reactive notifications list (avoiding duplicate UI entries)
            if (!notifications.any((n) => n.id == notif.id)) {
              notifications.insert(0, notif);
              _updateUnreadCount();
            }

             // Display dynamic local alert with action buttons
            showLocalNotification(
              id: notif.id.hashCode,
              title: notif.title,
              body: notif.message,
              payload: jsonEncode({
                'id': notif.id,
                'screen': notif.screen,
                'entity_id': notif.entityId,
                'type': notif.type,
              }),
            );
          } catch (e) {
            debugPrint("Error decoding websocket message: $e");
          }
        },
        onError: (error) {
          debugPrint("WebSocket error: $error");
          _reconnectWebSocket();
        },
        onDone: () {
          debugPrint("WebSocket connection closed.");
          _reconnectWebSocket();
        },
      );
    } catch (e) {
      debugPrint("WebSocket connection error: $e");
      _isConnecting = false;
      _reconnectWebSocket();
    }
  }

  void _reconnectWebSocket() {
    _wsChannel = null;
    _wsReconnectAttempts++;

    if (_wsReconnectAttempts > _wsMaxReconnectAttempts) {
      debugPrint("WebSocket: Max reconnect attempts ($_wsMaxReconnectAttempts) reached. Giving up.");
      return;
    }

    // Exponential backoff: 2s, 4s, 8s, 16s, 30s (capped)
    final delay = (_wsBaseDelaySeconds * (1 << (_wsReconnectAttempts - 1)))
        .clamp(1, _wsMaxDelaySeconds);
    debugPrint("WebSocket: Reconnecting in ${delay}s (attempt $_wsReconnectAttempts/$_wsMaxReconnectAttempts)");
    Future.delayed(Duration(seconds: delay), connectWebSocket);
  }

  Future<void> fetchNotifications({int retryCount = 0}) async {
    isLoading.value = true;
    try {
      final response = await _api.get('/api/v1/notifications/');
      if (response.statusCode == 200) {
        final List data = response.data;
        notifications.value = data
            .map((e) => NotificationModel.fromJson(e))
            .where((n) => n.title.trim().isNotEmpty && n.message.trim().isNotEmpty)
            .toList();
        _updateUnreadCount();
      }
    } catch (e) {
      debugPrint('Error fetching notifications (attempt ${retryCount + 1}): $e');
      // Retry up to 3 times with increasing delay
      if (retryCount < 3) {
        await Future.delayed(Duration(seconds: 2 * (retryCount + 1)));
        return fetchNotifications(retryCount: retryCount + 1);
      }
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> markAsRead(String id) async {
    try {
      await _api.put('/api/v1/notifications/$id/read');
      final index = notifications.indexWhere((n) => n.id == id);
      if (index != -1) {
        final old = notifications[index];
        notifications[index] = NotificationModel(
          id: old.id,
          title: old.title,
          message: old.message,
          type: old.type,
          screen: old.screen,
          entityId: old.entityId,
          isRead: true,
          createdAt: old.createdAt,
        );
        _updateUnreadCount();
      }
    } catch (e) {
      debugPrint('Error marking notification read: $e');
    }
  }

  void _updateUnreadCount() {
    unreadCount.value = notifications.where((n) => !n.isRead).length;
  }

  Future<void> deleteNotification(String id) async {
    try {
      final response = await _api.delete('/api/v1/notifications/$id');
      if (response.statusCode == 200) {
        notifications.removeWhere((n) => n.id == id);
        _updateUnreadCount();
        Get.snackbar(
          "Notification Removed",
          "Notification deleted successfully.",
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.red.withOpacity(0.8),
          colorText: Colors.white,
          margin: const EdgeInsets.all(16),
          borderRadius: 10,
        );
      }
    } catch (e) {
      debugPrint('Error deleting notification: $e');
      Get.snackbar(
        "Error",
        "Failed to delete notification.",
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.red.withOpacity(0.8),
        colorText: Colors.white,
        margin: const EdgeInsets.all(16),
        borderRadius: 10,
      );
    }
  }

  Future<void> clearAllNotifications() async {
    try {
      final response = await _api.delete('/api/v1/notifications/');
      if (response.statusCode == 200) {
        notifications.clear();
        _updateUnreadCount();
        Get.snackbar(
          "All Cleared",
          "All notifications cleared successfully.",
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.blue.withOpacity(0.8),
          colorText: Colors.white,
          margin: const EdgeInsets.all(16),
          borderRadius: 10,
        );
      }
    } catch (e) {
      debugPrint('Error clearing notifications: $e');
      Get.snackbar(
        "Error",
        "Failed to clear notifications.",
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.red.withOpacity(0.8),
        colorText: Colors.white,
        margin: const EdgeInsets.all(16),
        borderRadius: 10,
      );
    }
  }

  void handleNotificationTap(NotificationModel notification) {
    if (!notification.isRead) markAsRead(notification.id);
    
    // Close notifications drawer dialog if open
    if (Get.isDialogOpen ?? false) {
      Get.back();
    }

    // Check if we have an entity ID to deep link to
    if (notification.entityId != null && notification.entityId!.isNotEmpty) {
      if (notification.type == 'fault' || notification.screen == 'fault_detection') {
        Get.toNamed('/fault-details', arguments: notification.entityId);
        return;
      } else if (notification.type == 'theft' || notification.screen == 'theft_detection') {
        Get.toNamed('/consumer-investigation', arguments: notification.entityId);
        return;
      }
    }

    int tabIndex = 0;
    switch (notification.screen) {
      case 'dashboard': tabIndex = 0; break;
      case 'forecasting': tabIndex = 1; break;
      case 'asset_monitoring': tabIndex = 2; break;
      case 'fault_detection': tabIndex = 3; break;
      case 'ai_assistant': tabIndex = 4; break;
      case 'reports': tabIndex = 5; break;
      case 'system_health': tabIndex = 6; break;
      case 'settings': tabIndex = 7; break;
    }

    if (Get.currentRoute == '/home') {
      if (Get.isRegistered<HomeShellState>()) {
        Get.find<HomeShellState>().navigateTo(tabIndex);
      }
    } else {
      Get.offAllNamed('/home', arguments: tabIndex);
    }
  }

  Future<void> registerFcmToken(String token) async {
    try {
      await _api.post('/api/v1/notifications/fcm-token', data: {'fcm_token': token});
    } catch (e) {
      debugPrint('Error registering FCM token: $e');
    }
  }

  Future<void> acknowledgeAlert(String notificationId) async {
    try {
      final response = await _api.post('/api/v1/notifications/$notificationId/acknowledge');
      if (response.statusCode == 200) {
        Get.snackbar(
          "Alert Acknowledged",
          "Alarm marked resolved successfully.",
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.green.withOpacity(0.8),
          colorText: Colors.white,
        );
        await fetchNotifications();
      }
    } catch (e) {
      Get.snackbar("Error", "Failed to acknowledge notification.");
    }
  }

  Future<void> dispatchCrewAlert(String notificationId) async {
    try {
      final response = await _api.post('/api/v1/notifications/$notificationId/dispatch');
      if (response.statusCode == 200) {
        Get.snackbar(
          "Crew Dispatched",
          "Assigned field maintenance crew to ticket.",
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.blue.withOpacity(0.8),
          colorText: Colors.white,
        );
        await fetchNotifications();
      }
    } catch (e) {
      Get.snackbar("Error", "Failed to dispatch maintenance crew.");
    }
  }

  Future<void> snoozeAlert(String notificationId) async {
    try {
      final response = await _api.post('/api/v1/notifications/$notificationId/snooze');
      if (response.statusCode == 200) {
        Get.snackbar(
          "Notifications Snoozed",
          "Muted alerts for this asset for 1 hour.",
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.orange.withOpacity(0.8),
          colorText: Colors.white,
        );
        await fetchNotifications();
      }
    } catch (e) {
      Get.snackbar("Error", "Failed to snooze asset notifications.");
    }
  }

  void onDidReceiveNotificationResponse(NotificationResponse response) async {
    final String? actionId = response.actionId;
    final String? payload = response.payload;
    if (payload == null) return;

    // Try parsing the payload as JSON (our new format) or fallback to raw ID
    String notificationId = payload;
    String screen = '';
    String entityId = '';
    String type = '';

    try {
      final decoded = jsonDecode(payload);
      if (decoded is Map) {
        notificationId = decoded['id'] ?? '';
        screen = decoded['screen'] ?? '';
        entityId = decoded['entity_id'] ?? '';
        type = decoded['type'] ?? '';
      }
    } catch (e) {
      debugPrint('Payload is not JSON, treating as raw ID: $e');
    }

    if (actionId == 'acknowledge') {
      await acknowledgeAlert(notificationId);
    } else if (actionId == 'dispatch') {
      await dispatchCrewAlert(notificationId);
    } else if (actionId == 'snooze') {
      await snoozeAlert(notificationId);
    } else {
      if (notifications.isEmpty) {
        await fetchNotifications();
      }
      final index = notifications.indexWhere((n) => n.id == notificationId);
      if (index != -1) {
        handleNotificationTap(notifications[index]);
      } else {
        // Fallback: construct a dummy model with parsed info
        final dummy = NotificationModel(
          id: notificationId,
          title: '',
          message: '',
          type: type,
          screen: screen,
          entityId: entityId,
          isRead: false,
          createdAt: DateTime.now().toIso8601String(),
        );
        handleNotificationTap(dummy);
      }
    }
  }
}
