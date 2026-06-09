import '../models/theft_model.dart';
import '../services/theft_api_service.dart';

class TheftRepository {
  final TheftApiService _apiService = TheftApiService();

  Future<List<TheftAlertModel>> getSuspiciousConsumers() async {
    final result = await _apiService.getSuspiciousConsumers();
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => TheftAlertModel.fromJson(item))
          .toList();
    }
    return [];
  }

  Future<TheftDashboardModel?> getDashboardSummary() async {
    final result = await _apiService.getDashboardSummary();
    if (result['success'] == true) {
      return TheftDashboardModel.fromJson(result);
    }
    return null;
  }

  Future<ConsumerInvestigationModel?> getConsumerDetails(String consumerId) async {
    final result = await _apiService.getConsumerDetails(consumerId);
    if (result['success'] == true && result['data'] != null) {
      return ConsumerInvestigationModel.fromJson(result['data']);
    }
    return null;
  }

  Future<List<TheftDistributionPoint>> getRiskDistribution() async {
    final result = await _apiService.getRiskDistribution();
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => TheftDistributionPoint.fromJson(item))
          .toList();
    }
    return [];
  }

  Future<List<TheftTrendPoint>> getConsumptionTrend(String consumerId) async {
    final result = await _apiService.getConsumptionTrend(consumerId);
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => TheftTrendPoint.fromJson(item))
          .toList();
    }
    return [];
  }

  Future<TheftAlertModel?> predictTheft(Map<String, dynamic> body) async {
    final result = await _apiService.predictTheft(body);
    if (result['success'] == true && result['data'] != null) {
      return TheftAlertModel.fromJson(result['data']);
    }
    return null;
  }
}
