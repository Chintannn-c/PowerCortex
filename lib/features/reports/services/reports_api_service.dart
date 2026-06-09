import 'package:dio/dio.dart';
import 'package:guvnl_project/core/api/api_client.dart';

class ReportsApiService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> getReports() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/reports');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getModelPerformance() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/reports/model-performance');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getDataSources() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/reports/data-sources');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Response> downloadReportFile(String reportId, String format) async {
    // Return the raw Dio response containing the file bytes
    return await _apiClient.dio.get(
      '/api/v1/reports/download/$reportId/$format',
      options: Options(responseType: ResponseType.bytes),
    );
  }

  Future<Map<String, dynamic>> getReportPreview(String reportId) async {
    try {
      final response = await _apiClient.dio.get('/api/v1/reports/preview/$reportId');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Map<String, dynamic> _handleError(DioException error) {
    return {
      'success': false,
      'message': error.response?.data?['detail'] ?? 'Connection error. Please try again.'
    };
  }
}
