import 'package:dio/dio.dart';
import 'package:guvnl_project/core/api/api_client.dart';

class TransformerApiService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> getAllTransformers() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/transformers');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getDashboardSummary() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/transformers/dashboard');
      // The backend returns {total: 8, healthy: 4, warning: 3, critical: 1} directly or wrapped.
      // Looking at the response_model TransformerDashboardResponse: it is direct.
      // So we can wrap it as {"success": true, ...response.data} for uniformity.
      if (response.data is Map<String, dynamic>) {
        return {'success': true, ...response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getCriticalTransformers() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/transformers/critical');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getWarningTransformers() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/transformers/warning');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getTransformerDetails(String id) async {
    try {
      final response = await _apiClient.dio.get('/api/v1/transformers/$id');
      if (response.data is Map<String, dynamic>) {
        return {'success': true, 'data': response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> submitPredict(Map<String, dynamic> telemetry) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/transformers/predict', data: telemetry);
      if (response.data is Map<String, dynamic>) {
        return {'success': true, 'data': response.data};
      }
      return {'success': false, 'message': 'Invalid response format'};
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> updateTelemetry(String id, Map<String, dynamic> telemetry) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/transformers/$id/telemetry', data: telemetry);
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
