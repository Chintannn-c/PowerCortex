import 'dart:async';
import 'package:get/get.dart';
import '../models/transformer_model.dart';
import '../repositories/transformer_repository.dart';

class TransformerController extends GetxController {
  final TransformerRepository _repository = TransformerRepository();

  var isLoading = true.obs;
  var errorMessage = ''.obs;

  // Raw assets and summary
  var allAssets = <TransformerModel>[].obs;
  var summary = Rxn<TransformerDashboardSummary>();

  // Filter & Search states
  var selectedFilterTab = 'All'.obs;
  var searchQuery = ''.obs;

  // Filtered list derived from allAssets, selectedFilterTab, and searchQuery
  List<TransformerModel> get filteredAssets {
    return allAssets.where((asset) {
      // 1. Tab filter logic
      bool matchesTab = true;
      final typeLower = asset.type.toLowerCase();
      
      switch (selectedFilterTab.value) {
        case 'Transformers':
          matchesTab = typeLower.contains('transformer');
          break;
        case 'Feeders':
          matchesTab = typeLower.contains('feeder');
          break;
        case 'Distribution':
          matchesTab = typeLower.contains('distribution') || typeLower.contains('substation');
          break;
        case 'Transmission':
          matchesTab = typeLower.contains('transmission') || typeLower.contains('line');
          break;
        case 'All':
        default:
          matchesTab = true;
          break;
      }

      // 2. Search query logic
      bool matchesSearch = true;
      if (searchQuery.value.isNotEmpty) {
        final query = searchQuery.value.toLowerCase();
        matchesSearch = asset.name.toLowerCase().contains(query) ||
            asset.assetId.toLowerCase().contains(query) ||
            asset.type.toLowerCase().contains(query);
      }

      return matchesTab && matchesSearch;
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
    if (allAssets.isEmpty) {
      isLoading.value = true;
    }
    errorMessage.value = '';

    try {
      final assetsResult = await _repository.getAllTransformers();
      final summaryResult = await _repository.getDashboardSummary();

      allAssets.value = assetsResult;
      if (summaryResult != null) {
        summary.value = summaryResult;
      }
    } catch (e) {
      errorMessage.value = 'Failed to sync asset health diagnostics';
    } finally {
      isLoading.value = false;
    }
  }

  void _startAutoRefresh() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
      fetchData();
    });
  }

  Future<void> updateTelemetry(String assetId, Map<String, dynamic> telemetry) async {
    try {
      final updatedAsset = await _repository.updateTelemetry(assetId, telemetry);
      if (updatedAsset != null) {
        final index = allAssets.indexWhere((a) => a.assetId == assetId);
        if (index != -1) {
          allAssets[index] = updatedAsset;
        }
        final summaryResult = await _repository.getDashboardSummary();
        if (summaryResult != null) {
          summary.value = summaryResult;
        }
      }
    } catch (e) {
      // Handle or log error
    }
  }
}
