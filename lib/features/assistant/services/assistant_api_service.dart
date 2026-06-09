import 'package:dio/dio.dart';
import 'package:guvnl_project/core/api/api_client.dart';

class AssistantApiService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> sendChatMessage(String message, List<Map<String, String>> history) async {
    try {
      final response = await _apiClient.dio.post(
        '/api/v1/assistant/chat',
        data: {
          'message': message,
          'history': history,
        },
      );
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return Map<String, dynamic>.from(e.response!.data);
      }
      return {'success': false, 'reply': 'Network error. Please check your connection.'};
    }
  }

  Future<Map<String, dynamic>> querySmartSearch(String query) async {
    try {
      final response = await _apiClient.dio.post(
        '/api/v1/assistant/search',
        data: {
          'query': query,
        },
      );
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return Map<String, dynamic>.from(e.response!.data);
      }
      return {
        'success': false,
        'intent': 'filter',
        'tab': 2,
        'query': query,
        'text': 'Network error. Defaulting to local filter.'
      };
    }
  }
}

