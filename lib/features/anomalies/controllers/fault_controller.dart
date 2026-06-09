import 'dart:async';
import 'package:get/get.dart';
import '../models/fault_model.dart';
import '../repositories/fault_repository.dart';

class FaultController extends GetxController {
  final FaultRepository _repository = FaultRepository();

  var isLoading = true.obs;
  var errorMessage = ''.obs;

  // Fault lists and summaries
  var activeFaults = <FaultModel>[].obs;
  var historicalFaults = <FaultModel>[].obs;
  var summary = Rxn<FaultDashboardSummary>();
  var timelinePoints = <FaultTimelinePoint>[].obs;

  // Search states
  var searchQuery = ''.obs;

  // Filtered active faults based on search query
  List<FaultModel> get filteredActiveFaults {
    if (searchQuery.value.isEmpty) {
      return activeFaults;
    }
    final query = searchQuery.value.toLowerCase();
    return activeFaults.where((f) {
      return f.faultType.toLowerCase().contains(query) ||
          f.assetName.toLowerCase().contains(query) ||
          f.faultId.toLowerCase().contains(query);
    }).toList();
  }

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
    if (activeFaults.isEmpty && historicalFaults.isEmpty) {
      isLoading.value = true;
    }
    errorMessage.value = '';

    try {
      final activeList = await _repository.getActiveFaults();
      final historyList = await _repository.getHistoricalFaults();
      final summaryResult = await _repository.getDashboardSummary();
      final timelineResult = await _repository.getTimeline();

      activeFaults.value = activeList;
      historicalFaults.value = historyList;
      timelinePoints.value = timelineResult;
      if (summaryResult != null) {
        summary.value = summaryResult;
      }
    } catch (e) {
      errorMessage.value = 'Failed to sync fault detection diagnostics';
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

  Future<FaultModel?> getFaultDetails(String id) async {
    try {
      return await _repository.getFaultDetails(id);
    } catch (e) {
      return null;
    }
  }
}
