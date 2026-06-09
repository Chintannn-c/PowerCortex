import '../models/transformer_model.dart';
import '../services/transformer_api_service.dart';

class TransformerRepository {
  final TransformerApiService _apiService = TransformerApiService();

  Future<List<TransformerModel>> getAllTransformers() async {
    final result = await _apiService.getAllTransformers();
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => TransformerModel.fromJson(item))
          .toList();
    }
    return [];
  }

  Future<TransformerDashboardSummary?> getDashboardSummary() async {
    final result = await _apiService.getDashboardSummary();
    if (result['success'] == true) {
      return TransformerDashboardSummary.fromJson(result);
    }
    return null;
  }

  Future<List<TransformerModel>> getCriticalTransformers() async {
    final result = await _apiService.getCriticalTransformers();
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => TransformerModel.fromJson(item))
          .toList();
    }
    return [];
  }

  Future<List<TransformerModel>> getWarningTransformers() async {
    final result = await _apiService.getWarningTransformers();
    if (result['success'] == true && result['data'] != null) {
      return (result['data'] as List)
          .map((item) => TransformerModel.fromJson(item))
          .toList();
    }
    return [];
  }

  Future<TransformerModel?> getTransformerDetails(String id) async {
    final result = await _apiService.getTransformerDetails(id);
    if (result['success'] == true && result['data'] != null) {
      return TransformerModel.fromJson(result['data']);
    }
    return null;
  }

  Future<TransformerModel?> updateTelemetry(String id, Map<String, dynamic> telemetry) async {
    final result = await _apiService.updateTelemetry(id, telemetry);
    if (result['success'] == true && result['data'] != null) {
      return TransformerModel.fromJson(result['data']);
    }
    return null;
  }
}
