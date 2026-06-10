import 'package:flutter/foundation.dart';
import 'dart:convert';
import 'package:get/get.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:guvnl_project/core/api/api_client.dart';

class InsightsController extends GetxController {
  final ApiClient _apiClient = ApiClient();
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  WebSocketChannel? _channel;
  
  var isLoading = true.obs;
  var aggregatedInsights = <Map<String, dynamic>>[].obs;
  var errorMessage = ''.obs;

  @override
  void onInit() {
    super.onInit();
    _connectWebSocket();
  }

  @override
  void onClose() {
    _channel?.sink.close();
    super.onClose();
  }

  Future<void> _connectWebSocket() async {
    try {
      isLoading.value = true;
      // Get base URL from API Client (strip http/https and replace with ws/wss)
      final String baseUrl = _apiClient.dio.options.baseUrl;
      final token = await _secureStorage.read(key: 'access_token') ?? '';
      final String wsUrl = baseUrl.replaceAll(RegExp(r'^http'), 'ws') + '/api/v1/insights/ws?token=$token';
      
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      
      _channel!.stream.listen(
        (message) {
          isLoading.value = false;
          errorMessage.value = '';
          try {
            final responseData = jsonDecode(message);
            if (responseData['success'] == true) {
              final List<dynamic> data = responseData['data'] ?? [];
              final parsed = data.map((e) {
                return {
                  'text': e['text'] ?? '',
                  'type': e['type'] ?? '',
                  'timestamp': DateTime.tryParse(e['timestamp'] ?? '') ?? DateTime.now(),
                  'source': e['source'] ?? '',
                };
              }).toList();
              
              aggregatedInsights.value = parsed;
            }
          } catch (e) {
            debugPrint("Error parsing websocket message: $e");
          }
        },
        onError: (error) {
          isLoading.value = false;
          errorMessage.value = 'Live stream disconnected: $error';
        },
        onDone: () {
          // Reconnect logic could be added here if needed
          debugPrint("WebSocket disconnected.");
        },
      );
    } catch (e) {
      isLoading.value = false;
      errorMessage.value = 'Failed to connect to live insights: $e';
    }
  }
}
