import 'package:flutter/foundation.dart';
import '../models/report_model.dart';
import '../services/reports_api_service.dart';

class ReportsRepository {
  final ReportsApiService _apiService = ReportsApiService();

  Future<List<ReportModel>> getReports() async {
    final response = await _apiService.getReports();
    if (response['success'] == true && response['data'] is List) {
      final list = response['data'] as List;
      return list.map((item) => ReportModel.fromJson(item)).toList();
    }
    return [];
  }

  Future<ModelPerformanceData?> getModelPerformance() async {
    final response = await _apiService.getModelPerformance();
    if (response['success'] == true && response['data'] != null) {
      return ModelPerformanceData.fromJson(response['data']);
    }
    return null;
  }

  Future<List<DataSourceModel>> getDataSources() async {
    final response = await _apiService.getDataSources();
    if (response['success'] == true && response['data'] is Map) {
      final map = response['data'] as Map<String, dynamic>;
      final sources = <DataSourceModel>[];
      
      if (map.containsKey('load_dataset')) {
        sources.add(DataSourceModel.fromJson('Historical Load Dataset', map['load_dataset']));
      }
      if (map.containsKey('weather_dataset')) {
        sources.add(DataSourceModel.fromJson('Weather Dataset', map['weather_dataset']));
      }
      if (map.containsKey('renewable_dataset')) {
        sources.add(DataSourceModel.fromJson('Renewable Energy Dataset', map['renewable_dataset']));
      }
      if (map.containsKey('training_dataset')) {
        sources.add(DataSourceModel.fromJson('Training Dataset', map['training_dataset']));
      }
      return sources;
    }
    return [];
  }

  Future<bool> downloadReport(String reportId, String format) async {
    try {
      final response = await _apiService.downloadReportFile(reportId, format);
      // Returns true if we fetched bytes successfully (status code 200)
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<Map<String, dynamic>?> getReportPreview(String reportId) async {
    try {
      final response = await _apiService.getReportPreview(reportId);
      if (response['success'] == true) {
        return response;
      }
      return null;
    } catch (e) {
      debugPrint("Error fetching report preview: $e");
      return null;
    }
  }
}
