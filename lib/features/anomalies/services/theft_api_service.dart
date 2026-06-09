import 'package:dio/dio.dart';
import 'package:guvnl_project/core/api/api_client.dart';

class TheftApiService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> getSuspiciousConsumers() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/theft/suspicious');
      if (response.data is List) {
        return {'success': true, 'data': response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getDashboardSummary() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/theft/dashboard');
      if (response.data is Map<String, dynamic>) {
        return {'success': true, ...response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getConsumerDetails(String consumerId) async {
    try {
      final response = await _apiClient.dio.get('/api/v1/theft/consumer/$consumerId');
      if (response.data is Map<String, dynamic>) {
        return {'success': true, 'data': response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getRiskDistribution() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/theft/distribution');
      if (response.data is List) {
        return {'success': true, 'data': response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getConsumptionTrend(String consumerId) async {
    try {
      final response = await _apiClient.dio.get('/api/v1/theft/trend/$consumerId');
      if (response.data is List) {
        return {'success': true, 'data': response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> predictTheft(Map<String, dynamic> body) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/theft/predict', data: body);
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Map<String, dynamic> _handleError(DioException e) {
    if (e.response != null && e.response?.data is Map) {
      return Map<String, dynamic>.from(e.response!.data);
    }
    return {'success': false, 'message': 'Network error. Please try again.'};
  }
}
