import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:syncfusion_flutter_charts/charts.dart';
import '../../core/theme/app_colors.dart';
import '../../core/utils/responsive.dart';
import '../../widgets/confidence_badge.dart';
import 'controllers/theft_controller.dart';
import 'models/theft_model.dart';
import 'consumer_investigation_skeleton.dart';

class ConsumerInvestigationScreen extends StatefulWidget {
  const ConsumerInvestigationScreen({super.key});

  @override
  State<ConsumerInvestigationScreen> createState() => _ConsumerInvestigationScreenState();
}

class _ConsumerInvestigationScreenState extends State<ConsumerInvestigationScreen> {
  final TheftController controller = Get.find<TheftController>();
  late String consumerId;
  final TextEditingController _notesController = TextEditingController();

  @override
  void initState() {
    super.initState();
    consumerId = Get.arguments as String? ?? 'CN-88029';
    // Fetch details on init
    controller.fetchConsumerInvestigation(consumerId).then((_) {
      if (controller.selectedInvestigation.value != null) {
        _notesController.text = controller.selectedInvestigation.value!.investigationNotes;
      }
    });
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  Color _getRiskColor(String risk) {
    switch (risk) {
      case 'High Risk':
        return AppColors.critical;
      case 'Medium Risk':
        return AppColors.warning;
      case 'Low Risk':
        return Colors.amber;
      default:
        return AppColors.healthy;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Consumer Investigation'),
      ),
      body: Obx(() {
        if (controller.isDetailsLoading.value) {
          return const ConsumerInvestigationSkeleton();
        }

        final alert = controller.selectedInvestigation.value;
        if (alert == null) {
          return const Center(
            child: Text('Failed to load consumer details'),
          );
        }

        final riskColor = _getRiskColor(alert.riskLevel);
        final trendPoints = controller.selectedTrend;

        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header Consumer Profile Card
              Card(
                color: isDark ? AppColors.darkCard : AppColors.lightCard,
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: BorderSide(
                    color: riskColor.withOpacity(0.5),
                    width: 1.5,
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  alert.consumerName,
                                  style: theme.textTheme.titleLarge?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                context.sh(4),
                                Text(
                                  '${alert.consumerId} │ ${alert.sector}, ${alert.city}',
                                  style: theme.textTheme.bodyMedium?.copyWith(
                                    color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 12),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: riskColor.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: riskColor.withOpacity(0.3)),
                            ),
                            child: Text(
                              alert.riskLevel,
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.bold,
                                color: riskColor,
                              ),
                            ),
                          ),
                        ],
                      ),
                      context.sh(16),
                      const Divider(),
                      context.sh(12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          _buildProfileStat('Current Usage', '${alert.currentConsumption.toStringAsFixed(0)} kWh', riskColor),
                          _buildProfileStat('Avg Usage', '${alert.avgConsumption.toStringAsFixed(0)} kWh', isDark ? AppColors.darkText : AppColors.lightText),
                          _buildProfileStat('Power Factor', alert.powerFactor.toStringAsFixed(2), alert.powerFactor < 0.85 ? AppColors.warning : AppColors.healthy),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              context.sh(16),

              // AI Explanation Card
              Card(
                color: riskColor.withOpacity(0.04),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(
                    color: riskColor.withOpacity(0.2),
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.psychology, color: riskColor),
                          context.sw(8),
                          Text(
                            'AI Diagnostic Summary',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: riskColor,
                            ),
                          ),
                          const Spacer(),
                          ConfidenceBadge(score: alert.theftProbability),
                        ],
                      ),
                      context.sh(12),
                      Text(
                        alert.aiExplanation,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              context.sh(20),

              // Consumption History Line Chart
              Text('Consumption History Trend', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              context.sh(8),
              Card(
                color: isDark ? AppColors.darkCard : AppColors.lightCard,
                child: Padding(
                  padding: const EdgeInsets.all(8),
                  child: SizedBox(
                    height: 220,
                    child: SfCartesianChart(
                      legend: const Legend(isVisible: true, position: LegendPosition.top),
                      tooltipBehavior: TooltipBehavior(enable: true),
                      primaryXAxis: const CategoryAxis(
                        majorGridLines: MajorGridLines(width: 0),
                      ),
                      primaryYAxis: const NumericAxis(
                        axisLine: AxisLine(width: 0),
                        majorTickLines: MajorTickLines(size: 0),
                      ),
                      series: <CartesianSeries<TheftTrendPoint, String>>[
                        LineSeries<TheftTrendPoint, String>(
                          name: 'Actual Usage',
                          dataSource: trendPoints,
                          xValueMapper: (TheftTrendPoint t, _) => t.month,
                          yValueMapper: (TheftTrendPoint t, _) => t.actual,
                          color: riskColor,
                          width: 3,
                          markerSettings: const MarkerSettings(isVisible: true),
                        ),
                        LineSeries<TheftTrendPoint, String>(
                          name: 'Expected Usage',
                          dataSource: trendPoints,
                          xValueMapper: (TheftTrendPoint t, _) => t.month,
                          yValueMapper: (TheftTrendPoint t, _) => t.expected,
                          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                          width: 2,
                          dashArray: const <double>[5, 5],
                          markerSettings: const MarkerSettings(isVisible: true),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              context.sh(20),

              // Pie Chart: Overall Risk Distribution
              Text('Overall Risk Distribution', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              context.sh(8),
              Card(
                color: isDark ? AppColors.darkCard : AppColors.lightCard,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: SizedBox(
                    height: 200,
                    child: SfCircularChart(
                      legend: const Legend(isVisible: true, position: LegendPosition.right),
                      series: <CircularSeries<TheftDistributionPoint, String>>[
                        PieSeries<TheftDistributionPoint, String>(
                          dataSource: controller.riskDistribution,
                          xValueMapper: (TheftDistributionPoint data, _) => data.name,
                          yValueMapper: (TheftDistributionPoint data, _) => data.value,
                          dataLabelSettings: const DataLabelSettings(isVisible: true),
                          pointColorMapper: (TheftDistributionPoint data, _) {
                            return _getRiskColor(data.name);
                          },
                        )
                      ],
                    ),
                  ),
                ),
              ),
              context.sh(20),

              // Investigation Notes
              Text('Investigation Notes', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              context.sh(8),
              TextField(
                controller: _notesController,
                maxLines: 4,
                decoration: InputDecoration(
                  hintText: 'Add notes about site checks, physical seals status, action items...',
                  fillColor: isDark ? AppColors.darkCard : AppColors.lightCard,
                  filled: true,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              context.sh(20),

              // Action buttons
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      onPressed: () => Get.back(),
                      child: const Text('Cancel'),
                    ),
                  ),
                  context.sw(12),
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primaryBlue,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      onPressed: () {
                        // Normally save notes to database, mock success here
                        Get.back();
                        Get.snackbar(
                          'Notes Saved',
                          'Investigation notes updated successfully for consumer $consumerId',
                          backgroundColor: AppColors.healthy.withOpacity(0.9),
                          colorText: Colors.white,
                        );
                      },
                      child: const Text('Save Notes'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      }),
    );
  }

  Widget _buildProfileStat(String label, String value, Color color) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            fontSize: 10,
            color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
          ),
        ),
        context.sh(4),
        Text(
          value,
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }
}
