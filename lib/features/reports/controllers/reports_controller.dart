import 'package:get/get.dart';
import 'package:flutter/material.dart';
import '../models/report_model.dart';
import '../repositories/reports_repository.dart';
import '../../../core/theme/app_colors.dart';

class ReportsController extends GetxController {
  final ReportsRepository _repository = ReportsRepository();

  var isLoading = true.obs;
  var isDownloading = false.obs;
  var errorMessage = ''.obs;

  var reports = <ReportModel>[].obs;
  var modelPerformance = Rxn<ModelPerformanceData>();
  var dataSources = <DataSourceModel>[].obs;

  @override
  void onInit() {
    super.onInit();
    fetchData();
  }

  Future<void> fetchData() async {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      final reportsRes = await _repository.getReports();
      final performanceRes = await _repository.getModelPerformance();
      final dataSourcesRes = await _repository.getDataSources();

      reports.value = reportsRes;
      modelPerformance.value = performanceRes;
      dataSources.value = dataSourcesRes;
    } catch (e) {
      errorMessage.value = 'Failed to load report data';
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> downloadReport(String reportId, String reportName, String format) async {
    isDownloading.value = true;
    // Show visual status dialog
    Get.dialog(
      const Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 16),
                Text('Generating report...'),
              ],
            ),
          ),
        ),
      ),
      barrierDismissible: false,
    );

    try {
      final success = await _repository.downloadReport(reportId, format);
      Get.back(); // close loading dialog
      
      if (success) {
        final ext = format.toLowerCase() == 'excel' ? 'xlsx' : 'csv';
        Get.snackbar(
          'Download Completed',
          'Successfully downloaded "$reportName" as $format ($ext) to system downloads.',
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: AppColors.healthy,
          colorText: Colors.white,
          borderRadius: 8,
          margin: const EdgeInsets.all(16),
          icon: const Icon(Icons.check_circle_outline, color: Colors.white),
          duration: const Duration(seconds: 4),
        );
      } else {
        Get.snackbar(
          'Download Failed',
          'Could not generate report file on server.',
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: AppColors.critical,
          colorText: Colors.white,
          borderRadius: 8,
          margin: const EdgeInsets.all(16),
          icon: const Icon(Icons.error_outline, color: Colors.white),
        );
      }
    } catch (e) {
      Get.back(); // close dialog if open
      Get.snackbar(
        'Download Error',
        'An error occurred while downloading the report.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.critical,
        colorText: Colors.white,
        borderRadius: 8,
        margin: const EdgeInsets.all(16),
      );
    } finally {
      isDownloading.value = false;
    }
  }

  Future<Map<String, dynamic>?> fetchReportPreview(String reportId) async {
    return await _repository.getReportPreview(reportId);
  }
}
