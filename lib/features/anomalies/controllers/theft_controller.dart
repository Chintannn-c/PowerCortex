import 'dart:async';
import 'package:get/get.dart';
import '../models/theft_model.dart';
import '../repositories/theft_repository.dart';

class TheftController extends GetxController {
  final TheftRepository _repository = TheftRepository();

  var isLoading = true.obs;
  var isDetailsLoading = false.obs;
  var errorMessage = ''.obs;

  // Reactives for list, metrics, and chart
  var suspiciousConsumers = <TheftAlertModel>[].obs;
  var dashboardSummary = Rxn<TheftDashboardModel>();
  var riskDistribution = <TheftDistributionPoint>[].obs;

  // Investigation details reactive states
  var selectedInvestigation = Rxn<ConsumerInvestigationModel>();
  var selectedTrend = <TheftTrendPoint>[].obs;

  Timer? _refreshTimer;

  @override
  void onInit() {
    super.onInit();
    fetchData();
    _startAutoRefresh();
  }

  @override
  void onClose() {
    _refreshTimer?.cancel();
    super.onClose();
  }

  Future<void> fetchData() async {
    if (suspiciousConsumers.isEmpty) {
      isLoading.value = true;
    }
    errorMessage.value = '';

    try {
      final list = await _repository.getSuspiciousConsumers();
      final summary = await _repository.getDashboardSummary();
      final dist = await _repository.getRiskDistribution();

      suspiciousConsumers.value = list;
      riskDistribution.value = dist;
      if (summary != null) {
        dashboardSummary.value = summary;
      }
    } catch (e) {
      errorMessage.value = 'Failed to sync power theft diagnostics';
    } finally {
      isLoading.value = false;
    }
  }

  void _startAutoRefresh() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(const Duration(seconds: 15), (timer) {
      fetchData();
    });
  }

  Future<void> fetchConsumerInvestigation(String consumerId) async {
    isDetailsLoading.value = true;
    try {
      final details = await _repository.getConsumerDetails(consumerId);
      final trend = await _repository.getConsumptionTrend(consumerId);
      
      selectedInvestigation.value = details;
      selectedTrend.value = trend;
    } catch (e) {
      // Handle details fetch error
    } finally {
      isDetailsLoading.value = false;
    }
  }

  Future<bool> triggerTheftPrediction(String consumerId, {double? current, double? average, double? pf}) async {
    try {
      final Map<String, dynamic> body = {
        'consumer_id': consumerId,
      };
      if (current != null) body['current_consumption'] = current;
      if (average != null) body['avg_consumption'] = average;
      if (pf != null) body['power_factor'] = pf;
      final result = await _repository.predictTheft(body);
      if (result != null) {
        await fetchData(); // Refresh local list and KPIs
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }
}
