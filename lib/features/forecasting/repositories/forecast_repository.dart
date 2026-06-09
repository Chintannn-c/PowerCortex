import '../models/forecast_model.dart';
import '../models/renewable_forecast_model.dart';
import '../services/forecast_api_service.dart';

class ForecastRepository {
  final ForecastApiService _apiService = ForecastApiService();

  Future<ForecastInfo?> getForecast(String type) async {
    Map<String, dynamic> result;
    if (type == 'hourly') {
      result = await _apiService.getHourlyForecast();
    } else if (type == 'daily') {
      result = await _apiService.getDailyForecast();
    } else {
      result = await _apiService.getWeeklyForecast();
    }

    if (result['success'] == true && result['forecast'] != null) {
      return ForecastInfo.fromJson(result['forecast']);
    }
    return null;
  }

  Future<List<ChartPoint>> getChartData() async {
    final result = await _apiService.getChartData();
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => ChartPoint.fromJson(item))
          .toList();
    }
    return [];
  }

  Future<DashboardSummary?> getDashboardSummary() async {
    final result = await _apiService.getDashboardSummary();
    if (result['success'] == true) {
      return DashboardSummary.fromJson(result);
    }
    return null;
  }

  Future<bool> generateForecast(String type) async {
    final result = await _apiService.triggerForecastGeneration(type);
    return result['success'] == true;
  }

  Future<List<ForecastDocument>> getHistory({String? type}) async {
    final result = await _apiService.getForecastHistory(type: type);
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => ForecastDocument.fromJson(item))
          .toList();
    }
    return [];
  }

  Future<RenewableForecastModel?> getCurrentRenewables() async {
    final result = await _apiService.getCurrentRenewables();
    if (result['solar_generation'] != null || result['wind_generation'] != null) {
      return RenewableForecastModel.fromJson(result);
    }
    return null;
  }

  Future<RenewableForecastModel?> predictRenewables({
    required double temperature,
    required double humidity,
    required double windSpeed,
    required double cloudCover,
  }) async {
    final result = await _apiService.predictRenewables(
      temperature: temperature,
      humidity: humidity,
      windSpeed: windSpeed,
      cloudCover: cloudCover,
    );
    if (result['solar_generation'] != null || result['wind_generation'] != null) {
      return RenewableForecastModel.fromJson(result);
    }
    return null;
  }

  Future<List<RenewableForecastModel>> getRenewablesHistory({int limit = 24}) async {
    final result = await _apiService.getRenewablesHistory(limit: limit);
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => RenewableForecastModel.fromJson(item))
          .toList();
    }
    return [];
  }
}
