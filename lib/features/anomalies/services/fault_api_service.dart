import 'package:dio/dio.dart';
import 'package:guvnl_project/core/api/api_client.dart';

class FaultApiService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> getActiveFaults() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/faults/active');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getHistoricalFaults() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/faults/history');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getDashboardSummary() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/faults/dashboard');
      if (response.data is Map<String, dynamic>) {
        return {'success': true, ...response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getTimeline() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/faults/timeline');
      if (response.data is List) {
        return {'success': true, 'data': response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getFaultDetails(String id) async {
    try {
      final response = await _apiClient.dio.get('/api/v1/faults/$id');
      if (response.data is Map<String, dynamic>) {
        return {'success': true, 'data': response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> predictFault(Map<String, dynamic> telemetry) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/faults/predict', data: telemetry);
      if (response.data is Map<String, dynamic>) {
        return {'success': true, 'data': response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
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
