import 'package:get/get.dart';
import 'package:flutter/material.dart';
import '../services/assistant_api_service.dart';

class ChatMessageModel {
  final String text;
  final bool isUser;
  final String time;

  ChatMessageModel({
    required this.text,
    required this.isUser,
    required this.time,
  });

  Map<String, String> toMap() {
    return {
      'role': isUser ? 'user' : 'assistant',
      'content': text,
    };
  }
}

class AssistantController extends GetxController {
  final AssistantApiService _apiService = AssistantApiService();

  var isLoading = false.obs;
  var messages = <ChatMessageModel>[].obs;

  @override
  void onInit() {
    super.onInit();
    // Seed the greeting message
    messages.add(
      ChatMessageModel(
        text: 'Hello! I\'m PowerCortex AI Assistant. I can help you with:\n'
            '• Demand and renewable forecasting\n'
            '• Transformer health analysis\n'
            '• Fault root cause explanations\n'
            '• Maintenance recommendations\n'
            '• Report generation\n\n'
            'How can I assist you today?',
        isUser: false,
        time: _currentTime(),
      ),
    );
  }

  String _currentTime() {
    final now = TimeOfDay.now();
    final hour = now.hourOfPeriod == 0 ? 12 : now.hourOfPeriod;
    final minute = now.minute.toString().padLeft(2, '0');
    final period = now.period == DayPeriod.am ? 'AM' : 'PM';
    return '$hour:$minute $period';
  }

  Future<void> sendChatMessage(String text) async {
    if (text.trim().isEmpty) return;

    // Add user message
    messages.add(
      ChatMessageModel(
        text: text,
        isUser: true,
        time: _currentTime(),
      ),
    );

    isLoading.value = true;

    try {
      // Map history (excluding greeting and current user message which is sent separately)
      final List<Map<String, String>> history = messages.length > 2
          ? messages.sublist(1, messages.length - 1).map((m) => m.toMap()).toList()
          : [];

      final result = await _apiService.sendChatMessage(text, history);
      
      final reply = result['reply'] ?? 'Sorry, I encountered an issue processing that query.';
      
      messages.add(
        ChatMessageModel(
          text: reply,
          isUser: false,
          time: _currentTime(),
        ),
      );
    } catch (e) {
      messages.add(
        ChatMessageModel(
          text: 'An unexpected connection error occurred.',
          isUser: false,
          time: _currentTime(),
        ),
      );
    } finally {
      isLoading.value = false;
    }
  }
}
