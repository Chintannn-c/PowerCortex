import 'package:dio/dio.dart';
import 'package:guvnl_project/core/api/api_client.dart';
import 'package:flutter/foundation.dart';
import '../models/validation_dashboard_model.dart';

class ValidationApiService {
  final ApiClient _apiClient = ApiClient();

  Future<ValidationDashboardModel?> fetchValidationDashboard() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/validation/dashboard');
      if (response.statusCode == 200 && response.data != null) {
        return ValidationDashboardModel.fromJson(response.data);
      }
      return null;
    } on DioException catch (e) {
      debugPrint("Validation API DioError: $e");
      return null;
    } catch (e) {
      debugPrint("Validation API Error: $e");
      return null;
    }
  }
}
