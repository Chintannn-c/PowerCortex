import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:get/get.dart';
import '../../core/utils/responsive.dart';
import '../../core/theme/app_colors.dart';
import '../../widgets/status_chip.dart';
import '../../widgets/confidence_badge.dart';
import 'controllers/fault_controller.dart';
import 'controllers/theft_controller.dart';
import 'models/fault_model.dart';
import 'models/theft_model.dart';
import 'fault_theft_skeleton.dart';

class FaultTheftScreen extends StatefulWidget {
  const FaultTheftScreen({super.key});

  @override
  State<FaultTheftScreen> createState() => _FaultTheftScreenState();
}

class _FaultTheftScreenState extends State<FaultTheftScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final FaultController controller = Get.put(FaultController());
  final TheftController theftController = Get.put(TheftController());
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _searchController.addListener(() {
      controller.searchQuery.value = _searchController.text;
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Column(
      children: [
        Container(
          margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          decoration: BoxDecoration(
            color: isDark ? AppColors.darkCard : AppColors.lightBg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
            ),
          ),
          child: TabBar(
            controller: _tabController,
            indicatorSize: TabBarIndicatorSize.tab,
            dividerColor: Colors.transparent,
            indicator: BoxDecoration(
              color: AppColors.primaryBlue,
              borderRadius: BorderRadius.circular(10),
            ),
            labelColor: Colors.white,
            unselectedLabelColor:
                isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
            labelStyle: theme.textTheme.labelLarge?.copyWith(fontSize: 13),
            tabs: const [
              Tab(text: 'Fault Detection'),
              Tab(text: 'Theft Detection'),
            ],
          ),
        ),
        context.sh(8),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              _buildFaultTab(isDark),
              _buildTheftTab(isDark),
            ],
          ),
        ),
      ],
    );
  }

  // ─── FAULT TAB ──────────────────────────────────────────────────

  Widget _buildFaultTab(bool isDark) {
    final theme = Theme.of(context);
    
    return Obx(() {
      if (controller.isLoading.value && controller.activeFaults.isEmpty) {
        return const FaultTheftSkeleton();
      }

      if (controller.errorMessage.value.isNotEmpty && controller.activeFaults.isEmpty) {
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
      final faults = controller.filteredActiveFaults;

      return RefreshIndicator(
        onRefresh: controller.fetchData,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Search field
              TextField(
                controller: _searchController,
                decoration: InputDecoration(
                  hintText: 'Search faults by type or asset...',
                  prefixIcon: const Icon(Icons.search, size: 20),
                  suffixIcon: _searchController.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear, size: 20),
                          onPressed: () {
                            _searchController.clear();
                            controller.searchQuery.value = '';
                          },
                        )
                      : null,
                ),
              ),
              context.sh(16),

              // KPI Row
              LayoutBuilder(
                builder: (context, constraints) {
                  final wide = constraints.maxWidth > 600;
                  return Row(
                    children: [
                      Expanded(child: _faultKpi('Active Faults', '${summary?.activeFaults ?? 0}', AppColors.critical)),
                      context.sw(10),
                      Expanded(child: _faultKpi('Resolved Today', '${summary?.resolvedToday ?? 0}', AppColors.healthy)),
                      if (wide) ...[
                        context.sw(10),
                        Expanded(child: _faultKpi('Critical Active', '${summary?.critical ?? 0}', AppColors.critical)),
                      ],
                    ],
                  );
                },
              ),
              context.sh(20),

              // Fault List
              Text('Active Faults', style: theme.textTheme.labelLarge),
              context.sh(10),
              if (faults.isEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Center(
                      child: Text(
                        'No active faults detected.',
                        style: TextStyle(
                          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                        ),
                      ),
                    ),
                  ),
                )
              else
                ...faults.map((f) => _faultListTile(f, isDark)),
              context.sh(20),

              // Timeline chart
              Text('Fault Timeline (History)', style: theme.textTheme.labelLarge),
              context.sh(10),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: SizedBox(
                    height: 180,
                    child: BarChart(
                      BarChartData(
                        gridData: FlGridData(
                          show: true,
                          drawVerticalLine: false,
                          getDrawingHorizontalLine: (v) => FlLine(
                            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                            strokeWidth: 1,
                          ),
                        ),
                        titlesData: FlTitlesData(
                          leftTitles: AxisTitles(
                            sideTitles: SideTitles(
                              showTitles: true,
                              reservedSize: 28,
                              getTitlesWidget: (v, m) => Text(
                                '${v.toInt()}',
                                style: TextStyle(
                                  fontSize: 10,
                                  color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                                ),
                              ),
                            ),
                          ),
                          bottomTitles: AxisTitles(
                            sideTitles: SideTitles(
                              showTitles: true,
                              getTitlesWidget: (v, m) {
                                final idx = v.toInt();
                                if (idx >= 0 && idx < controller.timelinePoints.length) {
                                  final dateStr = controller.timelinePoints[idx].date;
                                  try {
                                    final parts = dateStr.split('-');
                                    if (parts.length >= 3) {
                                      return Padding(
                                        padding: const EdgeInsets.only(top: 4.0),
                                        child: Text(
                                          '${parts[1]}/${parts[2]}',
                                          style: TextStyle(
                                            fontSize: 9,
                                            color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                                          ),
                                        ),
                                      );
                                    }
                                  } catch (e) {
                                      debugPrint('Failed to parse date for chart: $e');
                                    }
                                  return Padding(
                                    padding: const EdgeInsets.only(top: 4.0),
                                    child: Text(
                                      dateStr,
                                      style: TextStyle(
                                        fontSize: 9,
                                        color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                                      ),
                                    ),
                                  );
                                }
                                return const SizedBox.shrink();
                              },
                            ),
                          ),
                          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        ),
                        borderData: FlBorderData(show: false),
                        barGroups: _buildBarGroups(),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    });
  }

  List<BarChartGroupData> _buildBarGroups() {
    if (controller.timelinePoints.isEmpty) {
      return [
        _bar(0, 3, AppColors.critical),
        _bar(1, 5, AppColors.warning),
        _bar(2, 2, AppColors.critical),
        _bar(3, 7, AppColors.critical),
        _bar(4, 1, AppColors.info),
        _bar(5, 4, AppColors.warning),
        _bar(6, 2, AppColors.info),
      ];
    }
    
    final List<BarChartGroupData> list = [];
    for (int i = 0; i < controller.timelinePoints.length; i++) {
      final p = controller.timelinePoints[i];
      final count = p.count.toDouble();
      final color = count > 5 ? AppColors.critical : (count > 2 ? AppColors.warning : AppColors.info);
      list.add(_bar(i, count, color));
    }
    return list;
  }

  BarChartGroupData _bar(int x, double y, Color color) {
    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(
          toY: y,
          color: color,
          width: 16,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
        ),
      ],
    );
  }

  Widget _faultKpi(String label, String value, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          children: [
            Text(
              value,
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color),
            ),
            context.sh(4),
            Text(label, style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }

  Widget _faultListTile(FaultModel f, bool isDark) {
    final color = f.severity == StatusType.critical
        ? AppColors.critical
        : f.severity == StatusType.warning
            ? AppColors.warning
            : f.severity == StatusType.healthy
                ? AppColors.healthy
                : AppColors.info;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => Get.toNamed('/fault-details', arguments: f.faultId),
        child: IntrinsicHeight(
          child: Row(
            children: [
              Container(
                width: 4,
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(12),
                    bottomLeft: Radius.circular(12),
                  ),
                ),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: color.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(Icons.warning_amber, color: color, size: 20),
                      ),
                      context.sw(12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(f.faultType, style: Theme.of(context).textTheme.labelLarge),
                            context.sh(2),
                            Text(f.assetName, style: Theme.of(context).textTheme.bodySmall),
                          ],
                        ),
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          StatusChip(
                            status: f.severity,
                            label: f.severity == StatusType.healthy ? 'Medium' : (f.severity == StatusType.info ? 'Low' : null),
                          ),
                          context.sh(6),
                          ConfidenceBadge(score: f.probability),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ─── THEFT TAB ──────────────────────────────────────────────────

  Widget _buildTheftTab(bool isDark) {
    return Obx(() {
      if (theftController.isLoading.value && theftController.suspiciousConsumers.isEmpty) {
        return const FaultTheftSkeleton();
      }

      if (theftController.errorMessage.value.isNotEmpty && theftController.suspiciousConsumers.isEmpty) {
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: AppColors.critical),
              const SizedBox(height: 16),
              Text(
                theftController.errorMessage.value,
                style: const TextStyle(color: AppColors.critical),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: theftController.fetchData,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        );
      }

      final summary = theftController.dashboardSummary.value;
      final consumers = theftController.suspiciousConsumers;

      return RefreshIndicator(
        onRefresh: theftController.fetchData,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // KPI Row
              Row(
                children: [
                  Expanded(child: _faultKpi('Suspicious', '${summary?.suspiciousCount ?? 0}', AppColors.warning)),
                  context.sw(10),
                  Expanded(child: _faultKpi('High Risk', '${summary?.highRiskCount ?? 0}', AppColors.critical)),
                  context.sw(10),
                  Expanded(child: _faultKpi('Resolved', '${summary?.resolvedCount ?? 0}', AppColors.healthy)),
                ],
              ),
              context.sh(20),

              Text('Suspicious Consumers', style: Theme.of(context).textTheme.labelLarge),
              context.sh(10),
              if (consumers.isEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Center(
                      child: Text(
                        'No suspicious consumers detected.',
                        style: TextStyle(
                          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                        ),
                      ),
                    ),
                  ),
                )
              else
                ...consumers.map((c) => _theftConsumerCard(c, isDark)),
            ],
          ),
        ),
      );
    });
  }

  Widget _theftConsumerCard(TheftAlertModel t, bool isDark) {
    Color color;
    switch (t.riskLevel) {
      case 'High Risk':
        color = AppColors.critical;
        break;
      case 'Medium Risk':
        color = AppColors.warning;
        break;
      case 'Low Risk':
        color = Colors.amber;
        break;
      default:
        color = AppColors.healthy;
        break;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => Get.toNamed('/consumer-investigation', arguments: t.consumerId),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(Icons.person_search, color: color, size: 20),
                  ),
                  context.sw(12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('${t.consumerId} (${t.consumerName})', style: Theme.of(context).textTheme.labelLarge),
                        Text('${t.sector}, ${t.city}', style: Theme.of(context).textTheme.bodySmall),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: color.withOpacity(0.3)),
                    ),
                    child: Text(
                      t.riskLevel,
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: color),
                    ),
                  ),
                ],
              ),
              context.sh(12),
              Row(
                children: [
                  _theftMetric('Theft Prob.', '${t.theftProbability.toStringAsFixed(1)}%', color),
                  context.sw(16),
                  _theftMetric('Deviation', '${t.deviationPercentage.toStringAsFixed(1)}%', AppColors.critical),
                  const Spacer(),
                  ConfidenceBadge(score: t.theftProbability),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _theftMetric(String label, String value, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(fontSize: 10)),
        Text(value,
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }
}
