import '../models/fault_model.dart';
import '../services/fault_api_service.dart';

class FaultRepository {
  final FaultApiService _apiService = FaultApiService();

  Future<List<FaultModel>> getActiveFaults() async {
    final result = await _apiService.getActiveFaults();
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => FaultModel.fromJson(item))
          .toList();
    }
    return [];
  }

  Future<List<FaultModel>> getHistoricalFaults() async {
    final result = await _apiService.getHistoricalFaults();
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => FaultModel.fromJson(item))
          .toList();
    }
    return [];
  }

  Future<FaultDashboardSummary?> getDashboardSummary() async {
    final result = await _apiService.getDashboardSummary();
    if (result['success'] == true) {
      return FaultDashboardSummary.fromJson(result);
    }
    return null;
  }

  Future<List<FaultTimelinePoint>> getTimeline() async {
    final result = await _apiService.getTimeline();
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => FaultTimelinePoint.fromJson(item))
          .toList();
    }
    return [];
  }

  Future<FaultModel?> getFaultDetails(String id) async {
    final result = await _apiService.getFaultDetails(id);
    if (result['success'] == true && result['data'] != null) {
      return FaultModel.fromJson(result['data']);
    }
    return null;
  }

  Future<FaultModel?> predictFault(Map<String, dynamic> telemetry) async {
    final result = await _apiService.predictFault(telemetry);
    if (result['success'] == true && result['data'] != null) {
      return FaultModel.fromJson(result['data']);
    }
    return null;
  }
}
