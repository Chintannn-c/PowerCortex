import 'package:dio/dio.dart';
import 'package:guvnl_project/core/api/api_client.dart';

class ForecastApiService {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> getHourlyForecast() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/forecast/hour');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getDailyForecast() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/forecast/day');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getWeeklyForecast() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/forecast/week');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getChartData() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/forecast/chart');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getDashboardSummary() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/forecast/dashboard');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> triggerForecastGeneration(String forecastType) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/forecast/generate', data: {
        'forecast_type': forecastType,
      });
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getForecastHistory({String? type, int limit = 20}) async {
    try {
      final queryParams = <String, dynamic>{'limit': limit};
      if (type != null) {
        queryParams['forecast_type'] = type;
      }
      final response = await _apiClient.dio.get('/api/v1/forecast/history', queryParameters: queryParams);
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getCurrentRenewables() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/renewables/current');
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> predictRenewables({
    required double temperature,
    required double humidity,
    required double windSpeed,
    required double cloudCover,
  }) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/renewables/predict', data: {
        'temperature': temperature,
        'humidity': humidity,
        'wind_speed': windSpeed,
        'cloud_cover': cloudCover,
      });
      return response.data;
    } on DioException catch (e) {
      return _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getRenewablesHistory({int limit = 24}) async {
    try {
      final response = await _apiClient.dio.get('/api/v1/renewables/history', queryParameters: {'limit': limit});
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
