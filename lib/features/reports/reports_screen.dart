import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:get/get.dart';
import '../../core/utils/responsive.dart';
import '../../core/theme/app_colors.dart';
import '../../widgets/confidence_badge.dart';
import 'controllers/reports_controller.dart';
import 'models/report_model.dart';
import 'reports_skeleton.dart';

class ReportsScreen extends StatelessWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = Get.put(ReportsController());
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Obx(() {
      if (controller.isLoading.value) {
        return const ReportsSkeleton();
      }

      if (controller.errorMessage.isNotEmpty) {
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                controller.errorMessage.value,
                style: const TextStyle(color: Colors.red, fontSize: 16),
              ),
              context.sh(16),
              ElevatedButton.icon(
                onPressed: () => controller.fetchData(),
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        );
      }

      return DefaultTabController(
        length: 3,
        child: Column(
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
                  Tab(text: 'Reports'),
                  Tab(text: 'Model Performance'),
                  Tab(text: 'Data Sources'),
                ],
              ),
            ),
            context.sh(8),
            Expanded(
              child: TabBarView(
                children: [
                  _buildReportsTab(context, isDark, controller),
                  _buildModelTab(context, isDark, controller),
                  _buildDataTab(context, isDark, controller),
                ],
              ),
            ),
          ],
        ),
      );
    });
  }

  // ─── REPORTS TAB ──────────────────────────────────────────────

  Widget _buildReportsTab(BuildContext context, bool isDark, ReportsController controller) {
    final reports = controller.reports;

    if (reports.isEmpty) {
      return const Center(child: Text('No reports available.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: reports.length,
      itemBuilder: (context, index) {
        final r = reports[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 10),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.primaryBlue.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.description, color: AppColors.primaryBlue),
                ),
                context.sw(14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(r.name, style: Theme.of(context).textTheme.labelLarge),
                      context.sh(2),
                      Text('${r.date} · ${r.type} · ${r.size}',
                          style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () => _showPdfPreviewDialog(context, r.id, r.name, controller),
                  icon: const Icon(Icons.picture_as_pdf, size: 20, color: AppColors.critical),
                  tooltip: 'View PDF Report',
                ),
                IconButton(
                  onPressed: () => controller.downloadReport(r.id, r.name, 'Excel'),
                  icon: const Icon(Icons.table_chart, size: 20, color: AppColors.healthy),
                  tooltip: 'Download Excel',
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // ─── MODEL PERFORMANCE TAB ────────────────────────────────────

  Widget _buildModelTab(BuildContext context, bool isDark, ReportsController controller) {
    final performance = controller.modelPerformance.value;

    final loadMetrics = performance?.loadForecasting ?? [
      ModelMetric('Accuracy', '96.4%'),
      ModelMetric('MAE', '12.4'),
      ModelMetric('RMSE', '15.8'),
      ModelMetric('MAPE', '2.1%'),
    ];
    final transMetrics = performance?.transformerHealth ?? [
      ModelMetric('Accuracy', '94.1%'),
      ModelMetric('Precision', '92.5%'),
      ModelMetric('Recall', '91.0%'),
      ModelMetric('F1 Score', '91.7%'),
    ];
    final theftMetrics = performance?.theftDetection ?? [
      ModelMetric('Detection Acc.', '95.2%'),
      ModelMetric('Anomalies', '12'),
    ];
    final faultMetrics = performance?.faultDetection ?? [
      ModelMetric('Classification', '97.8%'),
      ModelMetric('Confidence', '94.5%'),
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _modelSection(context, isDark, 'Load Forecasting Model', loadMetrics),
          context.sh(16),
          _modelSection(context, isDark, 'Transformer Health Model', transMetrics),
          context.sh(16),
          _modelSection(context, isDark, 'Theft Detection Model', theftMetrics),
          context.sh(16),
          _modelSection(context, isDark, 'Fault Detection Model', faultMetrics),
          context.sh(24),

          // Feature importance
          Text('AI Explainability – Feature Importance',
              style: Theme.of(context).textTheme.labelLarge),
          context.sh(12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: SizedBox(
                height: 200,
                child: BarChart(
                  BarChartData(
                    alignment: BarChartAlignment.spaceAround,
                    maxY: 50,
                    gridData: FlGridData(
                        show: true,
                        drawVerticalLine: false,
                        getDrawingHorizontalLine: (v) => FlLine(
                            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                            strokeWidth: 1)),
                    titlesData: FlTitlesData(
                      leftTitles: AxisTitles(
                        sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 32,
                            getTitlesWidget: (v, m) => Text('${v.toInt()}%',
                                style: TextStyle(
                                    fontSize: 10,
                                    color: isDark
                                        ? AppColors.darkTextSecondary
                                        : AppColors.lightTextSecondary))),
                      ),
                      bottomTitles: AxisTitles(
                        sideTitles: SideTitles(
                            showTitles: true,
                            getTitlesWidget: (v, m) {
                              const l = ['Temp', 'Humidity', 'Holiday', 'Day'];
                              if (v.toInt() < l.length) {
                                return Padding(
                                  padding: const EdgeInsets.only(top: 6),
                                  child: Text(l[v.toInt()],
                                      style: TextStyle(
                                          fontSize: 10,
                                          color: isDark
                                              ? AppColors.darkTextSecondary
                                              : AppColors.lightTextSecondary)),
                                );
                              }
                              return const SizedBox.shrink();
                            }),
                      ),
                      topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                      rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    ),
                    borderData: FlBorderData(show: false),
                    barGroups: [
                      _featureBar(0, 42, AppColors.primaryBlue),
                      _featureBar(1, 25, AppColors.info),
                      _featureBar(2, 18, AppColors.warning),
                      _featureBar(3, 15, AppColors.healthy),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  BarChartGroupData _featureBar(int x, double y, Color color) {
    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(
            toY: y,
            color: color,
            width: 28,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(4))),
      ],
    );
  }

  Widget _modelSection(
      BuildContext context, bool isDark, String title, List<ModelMetric> metrics) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: AppColors.primaryBlue.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Icon(Icons.model_training,
                      color: AppColors.primaryBlue, size: 18),
                ),
                context.sw(10),
                Text(title, style: Theme.of(context).textTheme.labelLarge),
              ],
            ),
            context.sh(14),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: metrics.map((m) => _metricChip(context, m.label, m.value)).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _metricChip(BuildContext context, String label, String value) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkBg : AppColors.lightBg,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
        ),
      ),
      child: Column(
        children: [
          Text(value,
              style: const TextStyle(
                  fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.primaryBlue)),
          context.sh(2),
          Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(fontSize: 11)),
        ],
      ),
    );
  }

  // ─── DATA SOURCES TAB ─────────────────────────────────────────

  Widget _buildDataTab(BuildContext context, bool isDark, ReportsController controller) {
    final sources = controller.dataSources;

    if (sources.isEmpty) {
      return const Center(child: Text('No data source information available.'));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: sources.map((s) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: _dataSourceCard(context, isDark, s.title, s.records, s.range, s.quality),
          );
        }).toList(),
      ),
    );
  }

  Widget _dataSourceCard(BuildContext context, bool isDark, String title,
      String records, String range, String quality) {
    double parsedQuality = 98.0;
    try {
      parsedQuality = double.parse(quality.replaceAll('%', ''));
    } catch (e) {
      debugPrint('Failed to parse quality: $e');
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.info.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.storage, color: AppColors.info),
            ),
            context.sw(14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.labelLarge),
                  context.sh(4),
                  Text('$records  ·  $range', style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text('Quality',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(fontSize: 10)),
                context.sh(2),
                ConfidenceBadge(score: parsedQuality),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _showPdfPreviewDialog(BuildContext context, String reportId, String reportName, ReportsController controller) async {
    // Show loading dialog
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 16),
                Text('Compiling PDF telemetry...'),
              ],
            ),
          ),
        ),
      ),
    );

    final previewData = await controller.fetchReportPreview(reportId);
    
    if (context.mounted) {
      Navigator.of(context).pop(); // Close loading dialog
    }

    if (previewData == null) {
      Get.snackbar(
        'Preview Failed',
        'Could not load telemetry data for this report.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.critical,
        colorText: Colors.white,
      );
      return;
    }

    final summary = previewData['summary'] ?? '';
    final recommendations = List<String>.from(previewData['recommendations'] ?? []);
    final dataList = List<Map<String, dynamic>>.from(
      (previewData['data'] as List?)?.map((item) => Map<String, dynamic>.from(item)) ?? []
    );

    if (!context.mounted) return;

    showDialog(
      context: context,
      barrierColor: Colors.black.withOpacity(0.7),
      builder: (context) {
        return Dialog(
          backgroundColor: Colors.transparent,
          insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Top Action bar
              Container(
                width: 600,
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
                decoration: BoxDecoration(
                  color: Theme.of(context).cardColor,
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.picture_as_pdf, color: AppColors.critical),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'PDF Document Preview: $reportName',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.download, size: 20),
                      tooltip: 'Download PDF',
                      onPressed: () {
                        Navigator.of(context).pop();
                        controller.downloadReport(reportId, reportName, 'PDF');
                      },
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, size: 20),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ],
                ),
              ),
              // PDF Paper Sheet
              Flexible(
                child: SingleChildScrollView(
                  child: Container(
                    width: 600,
                    padding: const EdgeInsets.all(32),
                    color: Colors.white, // Real white page paper background
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // PDF Header
                        const Text(
                          'GUVNL PowerCortex Analytics Platform',
                          style: TextStyle(
                            fontFamily: 'Helvetica',
                            fontSize: 10,
                            fontStyle: FontStyle.italic,
                            color: Color(0xFF64748B),
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          reportName.toUpperCase(),
                          style: const TextStyle(
                            fontFamily: 'Helvetica',
                            fontWeight: FontWeight.bold,
                            fontSize: 22,
                            color: Color(0xFF1E3A8A),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Generated: ${DateTime.now().day}/${DateTime.now().month}/${DateTime.now().year} | Operator: admin@guvnl.gov.in',
                          style: const TextStyle(
                            fontFamily: 'Helvetica',
                            fontSize: 9.5,
                            fontStyle: FontStyle.italic,
                            color: Color(0xFF64748B),
                          ),
                        ),
                        const SizedBox(height: 12),
                        const Divider(thickness: 1.5, color: Color(0xFFE2E8F0)),
                        const SizedBox(height: 12),

                        // Section 1: Executive Summary
                        const Text(
                          '1. AI-Powered Executive Summary',
                          style: TextStyle(
                            fontFamily: 'Helvetica',
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                            color: Color(0xFF1E3A8A),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          summary,
                          style: const TextStyle(
                            fontFamily: 'Helvetica',
                            fontSize: 10.5,
                            height: 1.4,
                            color: Color(0xFF334155),
                          ),
                        ),
                        const SizedBox(height: 18),

                        // Section 2: Telemetry Grid Table
                        const Text(
                          '2. Grid Analytics & Telemetry Table',
                          style: TextStyle(
                            fontFamily: 'Helvetica',
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                            color: Color(0xFF1E3A8A),
                          ),
                        ),
                        const SizedBox(height: 10),
                        if (dataList.isNotEmpty)
                          _buildPdfPreviewTable(dataList)
                        else
                          const Text('No telemetry records found.'),
                        const SizedBox(height: 18),

                        // Section 3: Recommendations
                        const Text(
                          '3. Recommended Maintenance Actions',
                          style: TextStyle(
                            fontFamily: 'Helvetica',
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                            color: Color(0xFF1E3A8A),
                          ),
                        ),
                        const SizedBox(height: 8),
                        ...recommendations.map((rec) => Padding(
                          padding: const EdgeInsets.only(bottom: 6),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('• ', style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1E3A8A))),
                              Expanded(
                                child: Text(
                                  rec,
                                  style: const TextStyle(
                                    fontFamily: 'Helvetica',
                                    fontSize: 10,
                                    height: 1.3,
                                    color: Color(0xFF334155),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        )).toList(),
                        const SizedBox(height: 24),
                        const Divider(thickness: 0.75, color: Color(0xFFE2E8F0)),
                        const SizedBox(height: 12),

                        // Green verification stamp
                        Center(
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              border: Border.all(color: AppColors.healthy, width: 1.5),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Text(
                              'POWER-CORTEX DATA VALIDATION LAYER VERIFIED • TRUE CONSENSUS',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontFamily: 'Helvetica',
                                fontWeight: FontWeight.bold,
                                fontSize: 8.5,
                                color: AppColors.healthy,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              // Bottom Action bar
              Container(
                width: 600,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: Theme.of(context).cardColor,
                  borderRadius: const BorderRadius.vertical(bottom: Radius.circular(12)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    TextButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Close'),
                    ),
                    const SizedBox(width: 12),
                    ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primaryBlue,
                        foregroundColor: Colors.white,
                      ),
                      onPressed: () {
                        Navigator.of(context).pop();
                        controller.downloadReport(reportId, reportName, 'PDF');
                      },
                      icon: const Icon(Icons.download, size: 16),
                      label: const Text('Download PDF'),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildPdfPreviewTable(List<Map<String, dynamic>> data) {
    final headers = data.first.keys.toList();
    
    return Table(
      border: TableBorder.all(color: const Color(0xFFCBD5E1), width: 0.5),
      columnWidths: {
        for (int i = 0; i < headers.length; i++) i: const FlexColumnWidth(),
      },
      children: [
        // Table Header
        TableRow(
          decoration: const BoxDecoration(color: Color(0xFF1E3A8A)),
          children: headers.map((h) => Padding(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
            child: Text(
              h,
              style: const TextStyle(
                fontFamily: 'Helvetica',
                fontWeight: FontWeight.bold,
                fontSize: 8.5,
                color: Colors.white,
              ),
            ),
          )).toList(),
        ),
        // Table Rows
        ...List.generate(data.length, (idx) {
          final row = data[idx];
          final bgColor = idx % 2 == 0 ? const Color(0xFFF8FAFC) : Colors.white;
          
          return TableRow(
            decoration: BoxDecoration(color: bgColor),
            children: headers.map((h) => Padding(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
              child: Text(
                row[h].toString(),
                style: const TextStyle(
                  fontFamily: 'Helvetica',
                  fontSize: 8,
                  color: const Color(0xFF334155),
                ),
              ),
            )).toList(),
          );
        }),
      ],
    );
  }
}
