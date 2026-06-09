import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:guvnl_project/core/api/api_client.dart';
import '../models/system_health_model.dart';

class SystemHealthApiService {
  final ApiClient _apiClient = ApiClient();

  Future<SystemHealthModel?> fetchSystemHealth() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/system/health');
      if (response.statusCode == 200 && response.data != null) {
        return SystemHealthModel.fromJson(response.data);
      }
      return null;
    } on DioException catch (e) {
      debugPrint("SystemHealth API DioError: $e");
      return null;
    } catch (e) {
      debugPrint("SystemHealth API Error: $e");
      return null;
    }
  }
}
