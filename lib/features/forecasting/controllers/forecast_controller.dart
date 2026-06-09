import 'package:get/get.dart';
import 'package:flutter/material.dart';
import '../models/forecast_model.dart';
import '../models/renewable_forecast_model.dart';
import '../repositories/forecast_repository.dart';
import '../../../core/theme/app_colors.dart';

class ForecastController extends GetxController {
  final ForecastRepository _repository = ForecastRepository();

  var isLoading = true.obs;
  var isGenerating = false.obs;
  var isPredicting = false.obs;
  var errorMessage = ''.obs;

  // Demand Forecasting states
  var summary = Rxn<DashboardSummary>();
  var chartPoints = <ChartPoint>[].obs;
  var history = <ForecastDocument>[].obs;

  // Renewable Forecasting states
  var currentRenewable = Rxn<RenewableForecastModel>();
  var renewableHistory = <RenewableForecastModel>[].obs;

  // Selected tab (0 = Demand Forecasting, 1 = Renewable Forecasting)
  var activeTab = 0.obs;

  @override
  void onInit() {
    super.onInit();
    fetchData();
  }

  Future<void> fetchData() async {
    isLoading.value = true;
    errorMessage.value = '';

    try {
      // Fetch demand forecasting data
      final summaryResult = await _repository.getDashboardSummary();
      final chartResult = await _repository.getChartData();
      final historyResult = await _repository.getHistory();

      if (summaryResult != null) {
        summary.value = summaryResult;
      } else {
        errorMessage.value = 'Failed to load forecast KPIs';
      }

      chartPoints.value = chartResult;
      history.value = historyResult;

      // Fetch renewable forecasting data
      await fetchRenewableData();
    } catch (e) {
      errorMessage.value = 'Error connecting to forecasting servers';
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> fetchRenewableData() async {
    try {
      final currentRes = await _repository.getCurrentRenewables();
      if (currentRes != null) {
        currentRenewable.value = currentRes;
      }
      final historyRes = await _repository.getRenewablesHistory();
      renewableHistory.value = historyRes;
    } catch (e) {
      debugPrint("Error fetching renewable forecast data: $e");
    }
  }

  Future<void> triggerManualPrediction({
    required double temperature,
    required double humidity,
    required double windSpeed,
    required double cloudCover,
  }) async {
    isPredicting.value = true;
    try {
      final result = await _repository.predictRenewables(
        temperature: temperature,
        humidity: humidity,
        windSpeed: windSpeed,
        cloudCover: cloudCover,
      );

      if (result != null) {
        currentRenewable.value = result;
        await fetchRenewableData(); // refresh history
        Get.snackbar(
          'Prediction Successful',
          'Solar: ${result.solarGeneration} MW, Wind: ${result.windGeneration} MW generated.',
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: AppColors.healthy,
          colorText: Colors.white,
          borderRadius: 8,
          margin: const EdgeInsets.all(16),
          icon: const Icon(Icons.check_circle_outline, color: Colors.white),
        );
      } else {
        Get.snackbar(
          'Prediction Failed',
          'Could not execute DL model prediction on current inputs.',
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: AppColors.critical,
          colorText: Colors.white,
          borderRadius: 8,
          margin: const EdgeInsets.all(16),
          icon: const Icon(Icons.error_outline, color: Colors.white),
        );
      }
    } catch (e) {
      Get.snackbar(
        'Error',
        'Failed to connect to forecasting server.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.critical,
        colorText: Colors.white,
        borderRadius: 8,
        margin: const EdgeInsets.all(16),
      );
    } finally {
      isPredicting.value = false;
    }
  }

  Future<void> runManualForecast(String type) async {
    isGenerating.value = true;
    errorMessage.value = '';

    try {
      final success = await _repository.generateForecast(type);
      if (success) {
        Get.snackbar(
          'Run Complete',
          'Successfully generated new $type forecast metrics.',
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: AppColors.healthy,
          colorText: Colors.white,
          borderRadius: 8,
          margin: const EdgeInsets.all(16),
          icon: const Icon(Icons.check_circle_outline, color: Colors.white),
        );
        await fetchData();
      } else {
        Get.snackbar(
          'Run Failed',
          'Forecast model failed to generate. Please check weather feeds.',
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: AppColors.critical,
          colorText: Colors.white,
          borderRadius: 8,
          margin: const EdgeInsets.all(16),
          icon: const Icon(Icons.error_outline, color: Colors.white),
        );
      }
    } catch (e) {
      Get.snackbar(
        'Error',
        'Could not communicate with forecasting server.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.critical,
        colorText: Colors.white,
        borderRadius: 8,
        margin: const EdgeInsets.all(16),
      );
    } finally {
      isGenerating.value = false;
    }
  }
}
