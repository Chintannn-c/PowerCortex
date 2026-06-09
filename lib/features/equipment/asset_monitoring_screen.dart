import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../core/utils/responsive.dart';
import '../../core/theme/app_colors.dart';
import '../../widgets/asset_card.dart';
import '../../widgets/status_chip.dart';
import '../../widgets/confidence_badge.dart';
import 'controllers/transformer_controller.dart';
import 'models/transformer_model.dart';
import 'asset_monitoring_skeleton.dart';

class AssetMonitoringScreen extends StatefulWidget {
  const AssetMonitoringScreen({super.key});

  @override
  State<AssetMonitoringScreen> createState() => _AssetMonitoringScreenState();
}

class _AssetMonitoringScreenState extends State<AssetMonitoringScreen>
    with SingleTickerProviderStateMixin {
  final TransformerController controller = Get.put(TransformerController());
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _searchController.addListener(() {
      controller.searchQuery.value = _searchController.text;
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  String _getUpdatedAgo(DateTime dateTime) {
    final difference = DateTime.now().difference(dateTime);
    if (difference.inSeconds < 60) {
      return 'Just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes} min ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours} hours ago';
    } else {
      return '${difference.inDays} days ago';
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Obx(() {
      if (controller.isLoading.value && controller.allAssets.isEmpty) {
        return const AssetMonitoringSkeleton();
      }

      if (controller.errorMessage.value.isNotEmpty && controller.allAssets.isEmpty) {
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: AppColors.critical),
              const SizedBox(height: 16),
              Text(
                controller.errorMessage.value,
                style: const TextStyle(color: AppColors.critical),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: controller.fetchData,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        );
      }

      final summary = controller.summary.value;
      final assets = controller.filteredAssets;

      return Column(
        children: [
          // Search
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search equipment by name or ID...',
                prefixIcon: const Icon(Icons.search, size: 20),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.tune, size: 20),
                  onPressed: () {},
                ),
              ),
            ),
          ),
          context.sh(12),

          // Tabs
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 16),
            height: 40,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                _filterChip('All', controller.selectedFilterTab.value == 'All'),
                _filterChip('Transformers', controller.selectedFilterTab.value == 'Transformers'),
                _filterChip('Feeders', controller.selectedFilterTab.value == 'Feeders'),
                _filterChip('Distribution', controller.selectedFilterTab.value == 'Distribution'),
                _filterChip('Transmission', controller.selectedFilterTab.value == 'Transmission'),
              ],
            ),
          ),
          context.sh(12),

          // Summary
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                _summaryBadge('Total: ${summary?.total ?? 0}', AppColors.primaryBlue),
                context.sw(8),
                _summaryBadge('Healthy: ${summary?.healthy ?? 0}', AppColors.healthy),
                context.sw(8),
                _summaryBadge('Warning: ${summary?.warning ?? 0}', AppColors.warning),
                context.sw(8),
                _summaryBadge('Critical: ${summary?.critical ?? 0}', AppColors.critical),
              ],
            ),
          ),
          context.sh(12),

          // Asset list
          Expanded(
            child: RefreshIndicator(
              onRefresh: controller.fetchData,
              child: assets.isEmpty
                  ? Center(
                      child: Text(
                        'No equipment matching search criteria.',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                        ),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      itemCount: assets.length,
                      itemBuilder: (context, index) {
                        final a = assets[index];
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: AssetCard(
                            name: a.name,
                            type: a.type,
                            healthScore: a.healthScore,
                            status: a.status,
                            lastUpdated: _getUpdatedAgo(a.lastUpdated),
                            onTap: () => _showAssetDetails(context, a),
                          ),
                        );
                      },
                    ),
            ),
          ),
        ],
      );
    });
  }

  Widget _filterChip(String label, bool selected) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: selected ? Colors.white : null,
          ),
        ),
        selected: selected,
        onSelected: (_) {
          controller.selectedFilterTab.value = label;
        },
        selectedColor: AppColors.primaryBlue,
        checkmarkColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
    );
  }

  Widget _summaryBadge(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color),
      ),
    );
  }

  void _showAssetDetails(BuildContext context, TransformerModel asset) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: isDark ? AppColors.darkCard : AppColors.lightCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Obx(() {
          // Re-fetch reactive item inside Obx to automatically reflect real-time changes
          final currentAsset = controller.allAssets.firstWhere(
            (a) => a.assetId == asset.assetId,
            orElse: () => asset,
          );

          // Calculate dynamic confidence score based on risk
          final confidenceScore = 95.0 - (currentAsset.riskScore * 0.05);

          // Get recommendation details
          String recommendationText = 'Transformer operating normally.';
          IconData recIcon = Icons.check_circle_outline;
          Color recColor = AppColors.healthy;

          if (currentAsset.healthScore < 50) {
            recommendationText = 'Immediate maintenance recommended. High risk of failure.';
            recIcon = Icons.warning;
            recColor = AppColors.critical;
          } else if (currentAsset.healthScore < 80) {
            recommendationText = 'Schedule inspection within 7 days. Fluid levels and load balance check suggested.';
            recIcon = Icons.lightbulb_outline;
            recColor = AppColors.warning;
          }

          return DraggableScrollableSheet(
            initialChildSize: 0.75,
            minChildSize: 0.5,
            maxChildSize: 0.95,
            expand: false,
            builder: (context, scrollController) {
              return SingleChildScrollView(
                controller: scrollController,
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 40,
                        height: 4,
                        decoration: BoxDecoration(
                          color: Colors.grey.withOpacity(0.3),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    context.sh(20),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.primaryBlue.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(
                            Icons.electrical_services,
                            color: AppColors.primaryBlue,
                            size: 28,
                          ),
                        ),
                        context.sw(16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(currentAsset.name, style: theme.textTheme.headlineSmall),
                              Text(currentAsset.type, style: theme.textTheme.bodySmall),
                            ],
                          ),
                        ),
                        StatusChip(status: currentAsset.status),
                      ],
                    ),
                    context.sh(24),

                    // Telemetry values
                    Text('Telemetry', style: theme.textTheme.labelLarge),
                    context.sh(12),
                    _telemetryRow('Temperature', '${currentAsset.temperature.toStringAsFixed(1)} °C', Icons.thermostat),
                    _telemetryRow('Voltage', '${currentAsset.voltage.toStringAsFixed(1)} kV', Icons.bolt),
                    _telemetryRow('Current', '${currentAsset.current.toStringAsFixed(0)} A', Icons.electric_meter),
                    _telemetryRow('Oil Level', '${currentAsset.oilLevel.toStringAsFixed(1)}%', Icons.water_drop),
                    _telemetryRow('Load Percentage', '${currentAsset.loadPercentage.toStringAsFixed(1)}%', Icons.speed),
                    context.sh(24),

                    // AI metrics
                    Text('AI Health Analysis', style: theme.textTheme.labelLarge),
                    context.sh(12),
                    Row(
                      children: [
                        Expanded(
                          child: _metricTile(
                            'Health Score',
                            '${currentAsset.healthScore.toStringAsFixed(0)}%',
                            currentAsset.healthScore >= 80
                                ? AppColors.healthy
                                : currentAsset.healthScore >= 50
                                    ? AppColors.warning
                                    : AppColors.critical,
                          ),
                        ),
                        context.sw(10),
                        Expanded(
                          child: _metricTile(
                            'Risk Score',
                            '${currentAsset.riskScore.toStringAsFixed(0)}%',
                            currentAsset.riskScore < 20
                                ? AppColors.healthy
                                : currentAsset.riskScore < 50
                                    ? AppColors.warning
                                    : AppColors.critical,
                          ),
                        ),
                        context.sw(10),
                        Expanded(
                          child: _metricTile(
                            'Failure Prob.',
                            '${currentAsset.failureProbability.toStringAsFixed(0)}%',
                            currentAsset.failureProbability < 20
                                ? AppColors.healthy
                                : currentAsset.failureProbability < 50
                                    ? AppColors.warning
                                    : AppColors.critical,
                          ),
                        ),
                      ],
                    ),
                    context.sh(8),
                    Row(
                      children: [
                        const Text('Prediction Confidence: ', style: TextStyle(fontSize: 12)),
                        ConfidenceBadge(score: confidenceScore),
                      ],
                    ),
                    context.sh(24),

                    // Recommendation
                    Text('AI Recommendation', style: theme.textTheme.labelLarge),
                    context.sh(8),
                    Card(
                      color: recColor.withOpacity(0.08),
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Row(
                          children: [
                            Icon(recIcon, color: recColor, size: 20),
                            context.sw(12),
                            Expanded(
                              child: Text(
                                recommendationText,
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: isDark ? AppColors.darkText : AppColors.lightText,
                                  height: 1.5,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    context.sh(20),

                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () => _showTelemetrySimulationDialog(context, currentAsset),
                            icon: const Icon(Icons.settings_suggest, size: 16),
                            label: const Text('Simulate Telemetry'),
                          ),
                        ),
                        context.sw(10),
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: () {},
                            icon: const Icon(Icons.smart_toy, size: 16),
                            label: const Text('Ask AI'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            },
          );
        });
      },
    );
  }

  Widget _telemetryRow(String label, String value, IconData icon) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.primaryBlue),
          context.sw(12),
          Text(label, style: theme.textTheme.bodyMedium),
          const Spacer(),
          Text(value, style: theme.textTheme.labelLarge),
        ],
      ),
    );
  }

  Widget _metricTile(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color),
          ),
          context.sh(4),
          Text(label, style: TextStyle(fontSize: 11, color: color)),
        ],
      ),
    );
  }

  void _showTelemetrySimulationDialog(BuildContext context, TransformerModel asset) {
    final tempController = TextEditingController(text: asset.temperature.toStringAsFixed(1));
    final voltController = TextEditingController(text: asset.voltage.toStringAsFixed(1));
    final currController = TextEditingController(text: asset.current.toStringAsFixed(0));
    final oilController = TextEditingController(text: asset.oilLevel.toStringAsFixed(1));
    final loadController = TextEditingController(text: asset.loadPercentage.toStringAsFixed(1));

    showDialog(
      context: context,
      builder: (dialogCtx) {
        return AlertDialog(
          title: Text('Simulate Telemetry: ${asset.assetId}'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _dialogTextField('Temperature (°C)', tempController, TextInputType.number),
                _dialogTextField('Voltage (kV)', voltController, TextInputType.number),
                _dialogTextField('Current (A)', currController, TextInputType.number),
                _dialogTextField('Oil Level (%)', oilController, TextInputType.number),
                _dialogTextField('Load Percentage (%)', loadController, TextInputType.number),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogCtx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final temp = double.tryParse(tempController.text) ?? asset.temperature;
                final volt = double.tryParse(voltController.text) ?? asset.voltage;
                final curr = double.tryParse(currController.text) ?? asset.current;
                final oil = double.tryParse(oilController.text) ?? asset.oilLevel;
                final load = double.tryParse(loadController.text) ?? asset.loadPercentage;

                Navigator.pop(dialogCtx);

                // Show dynamic loading indicator using a snackbar
                Get.showSnackbar(
                  const GetSnackBar(
                    message: 'Submitting telemetry to ML Predictor...',
                    duration: Duration(seconds: 1),
                    showProgressIndicator: true,
                    snackPosition: SnackPosition.BOTTOM,
                  ),
                );

                await controller.updateTelemetry(asset.assetId, {
                  'temperature': temp,
                  'voltage': volt,
                  'current': curr,
                  'oil_level': oil,
                  'load_percentage': load,
                });

                Get.snackbar(
                  'Simulation Success',
                  'Transformer ${asset.assetId} diagnostics updated via RF model.',
                  snackPosition: SnackPosition.BOTTOM,
                  backgroundColor: AppColors.healthy,
                  colorText: Colors.white,
                  duration: const Duration(seconds: 3),
                );
              },
              child: const Text('Update'),
            ),
          ],
        );
      },
    );
  }

  Widget _dialogTextField(String label, TextEditingController textController, TextInputType keyboardType) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: TextField(
        controller: textController,
        keyboardType: keyboardType,
        decoration: InputDecoration(
          labelText: label,
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          border: const OutlineInputBorder(),
        ),
      ),
    );
  }
}
