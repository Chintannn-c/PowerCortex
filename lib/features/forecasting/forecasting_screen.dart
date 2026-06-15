import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:get/get.dart';
import 'package:syncfusion_flutter_charts/charts.dart';
import '../../core/utils/responsive.dart';
import '../../core/theme/app_colors.dart';
import '../../widgets/chart_container.dart';
import '../../widgets/confidence_badge.dart';
import 'controllers/forecast_controller.dart';
import 'forecasting_skeleton.dart';
import 'models/renewable_forecast_model.dart';

class ForecastingScreen extends StatefulWidget {
  const ForecastingScreen({super.key});

  @override
  State<ForecastingScreen> createState() => _ForecastingScreenState();
}

class _ForecastingScreenState extends State<ForecastingScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final ForecastController controller = Get.put(ForecastController());

  double _tempSlider = 34.0;
  double _humiditySlider = 65.0;
  double _windSpeedSlider = 13.0;
  double _cloudCoverSlider = 50.0;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Obx(() {
      if (controller.isLoading.value) {
        return const ForecastingSkeleton();
      }

      if (controller.errorMessage.value.isNotEmpty && controller.summary.value == null) {
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

      return Column(
        children: [
          // Tab bar
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
                Tab(text: 'Demand'),
                Tab(text: 'Renewables'),
              ],
            ),
          ),
          context.sh(8),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildDemandTab(context, isDark),
                _buildRenewableTab(context, isDark),
              ],
            ),
          ),
        ],
      );
    });
  }

  Widget _buildDemandTab(BuildContext context, bool isDark) {
    final summaryData = controller.summary.value;
    if (summaryData == null) {
      return const SizedBox.shrink();
    }

    return RefreshIndicator(
      onRefresh: controller.fetchData,
      color: AppColors.primaryBlue,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Forecast KPI Grid
            LayoutBuilder(
              builder: (context, constraints) {
                final crossCount = constraints.maxWidth > 700 ? 4 : 2;
                return GridView.count(
                  crossAxisCount: crossCount,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  mainAxisSpacing: 10,
                  crossAxisSpacing: 10,
                  childAspectRatio: 1.6,
                  children: [
                    _forecastKpi(context, 'Current Demand', '${summaryData.currentDemand.toStringAsFixed(0)} MW', summaryData.nextHourConfidence),
                    _forecastKpi(context, 'Next Hour', '${summaryData.nextHour.toStringAsFixed(0)} MW', summaryData.nextHourConfidence),
                    _forecastKpi(context, 'Next Day Peak', '${summaryData.nextDay.toStringAsFixed(0)} MW', summaryData.nextDayConfidence),
                    _forecastKpi(context, 'Next Week Avg', '${summaryData.nextWeek.toStringAsFixed(0)} MW', summaryData.nextWeekConfidence),
                  ],
                );
              },
            ),
            context.sh(20),

            // Actual vs Predicted Chart
            _buildDemandChart(isDark),
            context.sh(16),

            // Statistics Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Expanded(
                      child: _statItem(context, 'Peak Time', summaryData.peakTime, Icons.access_time),
                    ),
                    _divider(context),
                    Expanded(
                      child: _statItem(context, 'MAE', '${summaryData.mae.toStringAsFixed(1)} MW', Icons.analytics),
                    ),
                    _divider(context),
                    Expanded(
                      child: _statItem(context, 'RMSE', '${summaryData.rmse.toStringAsFixed(1)} MW', Icons.bar_chart),
                    ),
                    _divider(context),
                    Expanded(
                      child: _statItem(context, 'MAPE', '${summaryData.mape.toStringAsFixed(2)}%', Icons.percent),
                    ),
                  ],
                ),
              ),
            ),
            context.sh(20),

            // AI Insights & Action Section
            _buildInsightsSection(context, isDark),
            context.sh(20),
          ],
        ),
      ),
    );
  }

  Widget _buildDemandChart(bool isDark) {
    if (controller.chartPoints.isEmpty) {
      return const ChartContainer(
        title: 'Historical vs Predicted Load',
        subtitle: 'No data points available',
        chart: Center(child: Text('Empty Chart Data')),
      );
    }

    // Determine min/max values for charting axes dynamically to prevent clipping
    final minX = 0.0;
    final maxX = (controller.chartPoints.length - 1).toDouble();

    double minY = controller.chartPoints.map((p) => p.actual).fold(
        1500.0, (min, val) => val < min ? val : min);
    double maxY = controller.chartPoints.map((p) => p.actual).fold(
        1000.0, (max, val) => val > max ? val : max);

    // Add pad to prevent edge clipping
    minY = (minY - 100.0).clamp(0.0, double.infinity);
    maxY = maxY + 100.0;

    return ChartContainer(
      title: 'Historical vs Predicted Load',
      subtitle: 'Actual demand overlaid with LSTM Deep Learning prediction',
      actions: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _legendItem('Actual', AppColors.primaryBlue, isDashed: false),
            const SizedBox(width: 12),
            _legendItem('Predicted', AppColors.warning, isDashed: true),
          ],
        )
      ],
      chart: LineChart(
        LineChartData(
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            getDrawingHorizontalLine: (value) => FlLine(
              color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
              strokeWidth: 1,
            ),
          ),
          titlesData: FlTitlesData(
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 42,
                getTitlesWidget: (v, m) => Text(
                  '${v.toInt()}',
                  style: TextStyle(
                    fontSize: 9,
                    color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                  ),
                ),
              ),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 22,
                getTitlesWidget: (v, m) {
                  final index = v.toInt();
                  if (index >= 0 && index < controller.chartPoints.length && index % 4 == 0) {
                    final time = controller.chartPoints[index].timestamp;
                    return Text(
                      '${time.hour.toString().padLeft(2, '0')}:00',
                      style: TextStyle(
                        fontSize: 9,
                        color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
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
          minX: minX,
          maxX: maxX,
          minY: minY,
          maxY: maxY,
          lineBarsData: [
            // Actual load curve
            LineChartBarData(
              spots: controller.chartPoints.asMap().entries.map((entry) {
                return FlSpot(entry.key.toDouble(), entry.value.actual);
              }).toList(),
              isCurved: true,
              color: AppColors.primaryBlue,
              barWidth: 2.5,
              dotData: const FlDotData(show: false),
            ),
            // Predicted load curve
            LineChartBarData(
              spots: controller.chartPoints.asMap().entries.map((entry) {
                return FlSpot(entry.key.toDouble(), entry.value.predicted);
              }).toList(),
              isCurved: true,
              color: AppColors.warning,
              barWidth: 2,
              dashArray: [6, 4],
              dotData: const FlDotData(show: false),
              belowBarData: BarAreaData(
                show: true,
                color: AppColors.warning.withOpacity(0.06),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _legendItem(String label, Color color, {required bool isDashed}) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (isDashed)
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(width: 5, height: 2.5, color: color),
              const SizedBox(width: 3),
              Container(width: 5, height: 2.5, color: color),
            ],
          )
        else
          Container(
            width: 13,
            height: 2.5,
            color: color,
          ),
        const SizedBox(width: 6),
        Text(
          label,
          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
        ),
      ],
    );
  }

  Widget _buildInsightsSection(BuildContext context, bool isDark) {
    final theme = Theme.of(context);
    final insights = controller.summary.value?.insights ?? [];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.lightbulb_outline_rounded, color: AppColors.warning, size: 22),
                const SizedBox(width: 10),
                Text(
                  'AI Insights Engine',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (insights.isEmpty)
              const Text('No warnings or insights generated.')
            else
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: insights.length,
                itemBuilder: (context, index) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8.0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Padding(
                          padding: EdgeInsets.only(top: 4.0),
                          child: Icon(Icons.circle, size: 6, color: AppColors.primaryBlue),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            insights[index],
                            style: const TextStyle(fontSize: 13, height: 1.4),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 8),
            // Actions
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Expanded(
                  child: Text(
                    'Demand Forecast Actions',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                ),
                const SizedBox(width: 8),
                SizedBox(
                  height: 36,
                  child: ElevatedButton.icon(
                    onPressed: controller.isGenerating.value
                        ? null
                        : () => controller.runManualForecast('hourly'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primaryBlue,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      elevation: 0,
                    ),
                    icon: controller.isGenerating.value
                        ? const SizedBox(
                            width: 14,
                            height: 14,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                          )
                        : const Icon(Icons.flash_on, size: 14),
                    label: const Text(
                      'Run Forecast',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRenewableTab(BuildContext context, bool isDark) {
    final theme = Theme.of(context);
    final current = controller.currentRenewable.value;
    final double solar = current?.solarGeneration ?? 742.6;
    final double wind = current?.windGeneration ?? 312.4;
    final double total = current?.renewableTotal ?? 1055.0;

    final List<_DoughnutData> doughnutData = [
      _DoughnutData('Solar', solar, AppColors.warning),
      _DoughnutData('Wind', wind, AppColors.info),
    ];

    final history = controller.renewableHistory.reversed.toList();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // KPI Grid
          Text('Renewable Forecast KPIs', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          context.sh(10),
          LayoutBuilder(
            builder: (context, constraints) {
              final crossCount = constraints.maxWidth > 700 ? 4 : 2;
              return GridView.count(
                crossAxisCount: crossCount,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 10,
                crossAxisSpacing: 10,
                childAspectRatio: 1.6,
                children: [
                  _forecastKpi(context, 'Current Solar Output', '${solar.toStringAsFixed(1)} MW', 95.1),
                  _forecastKpi(context, 'Current Wind Output', '${wind.toStringAsFixed(1)} MW', 91.4),
                  _forecastKpi(context, 'Total Generation', '${total.toStringAsFixed(1)} MW', 93.3),
                  _forecastKpi(context, 'Renewable Contribution %', '${(total / 41134.0 * 100).toStringAsFixed(1)}%', 95.1),
                ],
              );
            },
          ),
          context.sh(20),

          // Charts
          Text('Generation Trend & Mix Analysis', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          context.sh(10),
          
          // Solar Chart
          Card(
            color: isDark ? AppColors.darkCard : AppColors.lightCard,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: SizedBox(
                height: 200,
                child: SfCartesianChart(
                  title: ChartTitle(text: 'Solar Output Forecast (MW)', textStyle: theme.textTheme.bodySmall),
                  tooltipBehavior: TooltipBehavior(enable: true),
                  primaryXAxis: const CategoryAxis(),
                  series: <CartesianSeries<RenewableForecastModel, String>>[
                    LineSeries<RenewableForecastModel, String>(
                      name: 'Solar Output',
                      dataSource: history,
                      xValueMapper: (RenewableForecastModel m, _) => '${m.timestamp.hour.toString().padLeft(2, '0')}:00',
                      yValueMapper: (RenewableForecastModel m, _) => m.solarGeneration,
                      color: AppColors.warning,
                      width: 3,
                      markerSettings: const MarkerSettings(isVisible: true),
                    )
                  ],
                ),
              ),
            ),
          ),
          context.sh(12),

          // Wind Chart
          Card(
            color: isDark ? AppColors.darkCard : AppColors.lightCard,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: SizedBox(
                height: 200,
                child: SfCartesianChart(
                  title: ChartTitle(text: 'Wind Output Forecast (MW)', textStyle: theme.textTheme.bodySmall),
                  tooltipBehavior: TooltipBehavior(enable: true),
                  primaryXAxis: const CategoryAxis(),
                  series: <CartesianSeries<RenewableForecastModel, String>>[
                    LineSeries<RenewableForecastModel, String>(
                      name: 'Wind Output',
                      dataSource: history,
                      xValueMapper: (RenewableForecastModel m, _) => '${m.timestamp.hour.toString().padLeft(2, '0')}:00',
                      yValueMapper: (RenewableForecastModel m, _) => m.windGeneration,
                      color: AppColors.info,
                      width: 3,
                      markerSettings: const MarkerSettings(isVisible: true),
                    )
                  ],
                ),
              ),
            ),
          ),
          context.sh(12),

          // Donut Chart
          Card(
            color: isDark ? AppColors.darkCard : AppColors.lightCard,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: SizedBox(
                height: 200,
                child: SfCircularChart(
                  title: ChartTitle(text: 'Renewable Fuel Mix', textStyle: theme.textTheme.bodySmall),
                  legend: const Legend(isVisible: true, position: LegendPosition.right),
                  series: <CircularSeries<_DoughnutData, String>>[
                    DoughnutSeries<_DoughnutData, String>(
                      dataSource: doughnutData,
                      xValueMapper: (_DoughnutData data, _) => data.x,
                      yValueMapper: (_DoughnutData data, _) => data.y,
                      pointColorMapper: (_DoughnutData data, _) => data.color,
                      dataLabelMapper: (_DoughnutData data, _) => '${data.y.toStringAsFixed(1)} MW',
                      dataLabelSettings: const DataLabelSettings(
                        isVisible: true,
                        labelPosition: ChartDataLabelPosition.outside,
                        connectorLineSettings: ConnectorLineSettings(
                          type: ConnectorType.curve,
                        ),
                        textStyle: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      innerRadius: '65%',
                    )
                  ],
                ),
              ),
            ),
          ),
          context.sh(24),

          // Interactive Weather Simulation Sliders
          Card(
            color: isDark ? AppColors.darkCard : AppColors.lightCard,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: AppColors.primaryBlue.withOpacity(0.3), width: 1.5),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.thermostat, color: AppColors.primaryBlue),
                      const SizedBox(width: 8),
                      Text(
                        'Weather Telemetry Simulation',
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  context.sh(12),
                  _buildSliderRow('Temperature', '${_tempSlider.toStringAsFixed(1)} °C', _tempSlider, 10.0, 45.0, (val) {
                    setState(() => _tempSlider = val);
                  }),
                  _buildSliderRow('Humidity', '${_humiditySlider.toStringAsFixed(0)} %', _humiditySlider, 10.0, 100.0, (val) {
                    setState(() => _humiditySlider = val);
                  }),
                  _buildSliderRow('Wind Speed', '${_windSpeedSlider.toStringAsFixed(1)} m/s', _windSpeedSlider, 0.0, 25.0, (val) {
                    setState(() => _windSpeedSlider = val);
                  }),
                  _buildSliderRow('Cloud Cover', '${_cloudCoverSlider.toStringAsFixed(0)} %', _cloudCoverSlider, 0.0, 100.0, (val) {
                    setState(() => _cloudCoverSlider = val);
                  }),
                  context.sh(16),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primaryBlue,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      onPressed: controller.isPredicting.value
                          ? null
                          : () {
                              controller.triggerManualPrediction(
                                temperature: _tempSlider,
                                humidity: _humiditySlider,
                                windSpeed: _windSpeedSlider,
                                cloudCover: _cloudCoverSlider,
                              );
                            },
                      icon: controller.isPredicting.value
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5),
                            )
                          : const Icon(Icons.bolt),
                      label: const Text('Run DL Prediction', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSliderRow(String label, String displayVal, double currentVal, double minVal, double maxVal, ValueChanged<double> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
              Text(displayVal, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            ],
          ),
          Slider(
            value: currentVal,
            min: minVal,
            max: maxVal,
            onChanged: onChanged,
            activeColor: AppColors.primaryBlue,
          ),
        ],
      ),
    );
  }

  Widget _forecastKpi(BuildContext context, String title, String value, double confidence) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                      fontSize: 11,
                    ),
                  ),
                ),
                ConfidenceBadge(score: confidence),
              ],
            ),
            context.sh(6),
            Text(
              value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _statItem(BuildContext context, String label, String value, IconData icon) {
    final theme = Theme.of(context);
    final isMobile = context.isMobile;
    return Column(
      children: [
        Icon(icon, size: isMobile ? 16 : 18, color: AppColors.primaryBlue),
        context.sh(6),
        FittedBox(
          fit: BoxFit.scaleDown,
          child: Text(
            value,
            style: theme.textTheme.labelLarge?.copyWith(fontSize: isMobile ? 12 : 14),
          ),
        ),
        context.sh(2),
        FittedBox(
          fit: BoxFit.scaleDown,
          child: Text(
            label,
            style: theme.textTheme.bodySmall?.copyWith(fontSize: isMobile ? 9 : 11),
          ),
        ),
      ],
    );
  }

  Widget _divider(BuildContext context) {
    return Container(
      width: 1,
      height: 40,
      color: Theme.of(context).dividerColor,
      margin: const EdgeInsets.symmetric(horizontal: 4),
    );
  }
}

class _DoughnutData {
  _DoughnutData(this.x, this.y, this.color);
  final String x;
  final double y;
  final Color color;
}
