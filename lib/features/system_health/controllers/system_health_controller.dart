import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:get/get.dart';
import '../models/system_health_model.dart';
import '../models/validation_dashboard_model.dart';
import '../services/system_health_api_service.dart';
import '../services/validation_api_service.dart';

class SystemHealthController extends GetxController {
  final SystemHealthApiService _apiService = SystemHealthApiService();
  final ValidationApiService _validationService = ValidationApiService();

  var isLoading = true.obs;
  var isError = false.obs;
  var lastUpdated = Rxn<DateTime>();
  var healthData = Rxn<SystemHealthModel>();
  var validationData = Rxn<ValidationDashboardModel>();
  Timer? _pollingTimer;

  @override
  void onInit() {
    super.onInit();
    fetchHealth(showLoading: true);
    // Poll every 10 seconds
    _pollingTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      fetchHealth(showLoading: false);
    });
  }

  Future<void> fetchHealth({bool showLoading = false}) async {
    if (showLoading) {
      isLoading.value = true;
    }
    isError.value = false;
    try {
      final futures = await Future.wait([
        _apiService.fetchSystemHealth(),
        _validationService.fetchValidationDashboard(),
      ]);

      final health = futures[0] as SystemHealthModel?;
      final validation = futures[1] as ValidationDashboardModel?;

      if (health != null) {
        healthData.value = health;
      }
      if (validation != null) {
        validationData.value = validation;
      }
      
      lastUpdated.value = DateTime.now();
    } catch (e) {
      debugPrint("SystemHealth fetch error: $e");
      isError.value = true;
    } finally {
      if (showLoading) {
        isLoading.value = false;
      }
    }
  }

  @override
  void onClose() {
    _pollingTimer?.cancel();
    super.onClose();
  }
}
