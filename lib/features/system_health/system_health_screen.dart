import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../core/utils/responsive.dart';
import '../../core/theme/app_colors.dart';
import '../../widgets/status_chip.dart';
import 'controllers/system_health_controller.dart';
import 'system_health_skeleton.dart';

class SystemHealthScreen extends StatelessWidget {
  const SystemHealthScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final controller = Get.put(SystemHealthController());
    final RxInt selectedTab = 0.obs;

    return Obx(() {
      if (controller.isLoading.value && controller.healthData.value == null) {
        return const SystemHealthSkeleton();
      }

      if (controller.healthData.value == null) {
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: AppColors.critical),
              context.sh(16),
              const Text('Failed to load system health metrics.'),
              context.sh(16),
              ElevatedButton(
                onPressed: () => controller.fetchHealth(showLoading: true),
                child: const Text('Retry'),
              ),
            ],
          ),
        );
      }

      final health = controller.healthData.value!;
      final validation = controller.validationData.value;

      return SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Sliding Tab Selector (Infrastructure vs Data Validation)
            Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: isDark ? Colors.white.withValues(alpha: 0.05) : Colors.black.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: isDark ? Colors.white.withValues(alpha: 0.1) : Colors.black.withValues(alpha: 0.05),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: GestureDetector(
                      onTap: () => selectedTab.value = 0,
                      child: Obx(() => Container(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        decoration: BoxDecoration(
                          color: selectedTab.value == 0
                              ? (isDark ? AppColors.primaryBlue : AppColors.primaryBlue.withValues(alpha: 0.15))
                              : Colors.transparent,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Center(
                          child: Text(
                            'System Infrastructure',
                            style: theme.textTheme.labelMedium?.copyWith(
                              color: selectedTab.value == 0
                                  ? (isDark ? Colors.white : AppColors.primaryBlue)
                                  : (isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary),
                              fontWeight: selectedTab.value == 0 ? FontWeight.bold : FontWeight.normal,
                            ),
                          ),
                        ),
                      )),
                    ),
                  ),
                  Expanded(
                    child: GestureDetector(
                      onTap: () => selectedTab.value = 1,
                      child: Obx(() => Container(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        decoration: BoxDecoration(
                          color: selectedTab.value == 1
                              ? (isDark ? AppColors.primaryBlue : AppColors.primaryBlue.withValues(alpha: 0.15))
                              : Colors.transparent,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Center(
                          child: Text(
                            'AI Data Validation',
                            style: theme.textTheme.labelMedium?.copyWith(
                              color: selectedTab.value == 1
                                  ? (isDark ? Colors.white : AppColors.primaryBlue)
                                  : (isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary),
                              fontWeight: selectedTab.value == 1 ? FontWeight.bold : FontWeight.normal,
                            ),
                          ),
                        ),
                      )),
                    ),
                  ),
                ],
              ),
            ),
            context.sh(20),

            Obx(() {
              if (selectedTab.value == 0) {
                return _buildInfrastructureTab(context, health, isDark, theme, controller);
              } else {
                return _buildValidationTab(context, health, validation, isDark, theme, controller);
              }
            }),
          ],
        ),
      );
    });
  }

  // ── INFRASTRUCTURE TAB ─────────────────────────────────────────────
  Widget _buildInfrastructureTab(
      BuildContext context,
      dynamic health,
      bool isDark,
      ThemeData theme,
      SystemHealthController controller) {
    final isHealthy = health.overallStatus.toLowerCase() == 'healthy';
    final isWarning = health.overallStatus.toLowerCase() == 'warning';

    final bannerBgColor = isHealthy
        ? AppColors.healthy.withValues(alpha: 0.08)
        : (isWarning ? AppColors.warning.withValues(alpha: 0.08) : AppColors.critical.withValues(alpha: 0.08));

    final iconBgColor = isHealthy
        ? AppColors.healthy.withValues(alpha: 0.15)
        : (isWarning ? AppColors.warning.withValues(alpha: 0.15) : AppColors.critical.withValues(alpha: 0.15));

    final bannerColor = isHealthy
        ? AppColors.healthy
        : (isWarning ? AppColors.warning : AppColors.critical);

    final bannerIcon = isHealthy
        ? Icons.check_circle
        : (isWarning ? Icons.warning : Icons.error);

    final bannerText = isHealthy
        ? 'All Systems Operational'
        : (isWarning ? 'System Running with Warnings' : 'Critical System Failures Detected');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Overall status card
        Card(
          color: bannerBgColor,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(color: bannerColor.withValues(alpha: 0.2)),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: iconBgColor,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(bannerIcon, color: bannerColor, size: 28),
                ),
                context.sw(16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(bannerText,
                          style: theme.textTheme.labelLarge?.copyWith(color: bannerColor, fontWeight: FontWeight.bold)),
                      Text('System health model continuously evaluating telemetry',
                          style: theme.textTheme.bodySmall),
                    ],
                  ),
                ),
                OutlinedButton.icon(
                  onPressed: () => controller.fetchHealth(showLoading: true),
                  icon: const Icon(Icons.refresh, size: 16),
                  label: const Text('Refresh'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                ),
              ],
            ),
          ),
        ),
        context.sh(20),

        // Deep Learning prediction details
        Card(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.psychology, color: AppColors.primaryBlue),
                    context.sw(8),
                    Text('Deep Learning Health Evaluation', style: theme.textTheme.labelLarge?.copyWith(fontWeight: FontWeight.bold)),
                  ],
                ),
                context.sh(12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Predicted System Health', style: theme.textTheme.bodySmall),
                        Text('${health.overallHealthScore.toStringAsFixed(1)}%',
                            style: theme.textTheme.headlineMedium?.copyWith(
                                color: bannerColor, fontWeight: FontWeight.bold)),
                      ],
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text('Failure Probability', style: theme.textTheme.bodySmall),
                        Text('${health.failureProbability.toStringAsFixed(1)}%',
                            style: theme.textTheme.headlineMedium?.copyWith(
                                color: health.failureProbability > 30.0 ? AppColors.warning : AppColors.healthy,
                                fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ],
                ),
                context.sh(12),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: health.overallHealthScore / 100.0,
                    backgroundColor: bannerColor.withValues(alpha: 0.1),
                    valueColor: AlwaysStoppedAnimation<Color>(bannerColor),
                    minHeight: 8,
                  ),
                ),
              ],
            ),
          ),
        ),
        context.sh(20),

        // Backend
        _sectionTitle(context, 'Backend Services'),
        context.sh(10),
        _serviceCard(context, isDark, health.backend.name, 'Running on port 8000',
            health.backend.status.toLowerCase() == 'online' ? StatusType.healthy : StatusType.offline, [
              _Detail('Status', health.backend.status),
              _Detail('Uptime', health.backend.uptime),
              _Detail('Requests/min', health.backend.requestsPerMinute.toString()),
              _Detail('Avg Latency', '${health.backend.latencyMs.toStringAsFixed(0)} ms'),
              _Detail('CPU Usage', '${health.backend.cpuUsage.toStringAsFixed(1)}%'),
              _Detail('Memory Usage', '${health.backend.memoryUsage.toStringAsFixed(1)}%'),
            ]),
        context.sh(10),

        // Database
        _sectionTitle(context, 'Database'),
        context.sh(10),
        _serviceCard(context, isDark, health.database.name, 'Primary replica set',
            health.database.status.toLowerCase() == 'connected' ? StatusType.healthy : StatusType.offline, [
              _Detail('Status', health.database.status),
              _Detail('Storage', '${health.database.storageUsedGb} / ${health.database.storageTotalGb} GB'),
              _Detail('Collections', health.database.collections.toString()),
              _Detail('Read Ops/s', health.database.readOpsPerSecond.toString()),
              _Detail('Ping Latency', '${health.database.latencyMs.toStringAsFixed(1)} ms'),
            ]),
        context.sh(10),
        _storageBar(context, isDark, health.database.storageUsedGb, health.database.storageTotalGb),
        context.sh(20),

        // AI Services
        _sectionTitle(context, 'AI Services'),
        context.sh(10),
        _serviceCard(context, isDark, health.aiEngine.name, 'via OpenRouter API / Groq',
            health.aiEngine.status.toLowerCase() == 'online' ? StatusType.healthy : StatusType.offline, [
              _Detail('Status', health.aiEngine.status),
              _Detail('Avg Response', '${health.aiEngine.latencyMs.toStringAsFixed(0)} ms'),
              _Detail('Tokens/day', health.aiEngine.tokensToday.toString()),
            ]),
        context.sh(20),

        // ML Services
        _sectionTitle(context, 'ML Pipeline Services'),
        context.sh(10),
        _mlServiceRow(context, isDark, 'Load Forecasting', StatusType.healthy, '${health.mlPipeline.loadForecastingLatencyMs.toStringAsFixed(0)} ms'),
        context.sh(8),
        _mlServiceRow(context, isDark, 'Transformer Health', StatusType.healthy, '${health.mlPipeline.transformerHealthLatencyMs.toStringAsFixed(0)} ms'),
        context.sh(8),
        _mlServiceRow(context, isDark, 'Fault Detection', StatusType.healthy, '${health.mlPipeline.faultDetectionLatencyMs.toStringAsFixed(0)} ms'),
        context.sh(8),
        _mlServiceRow(context, isDark, 'Theft Detection', StatusType.healthy, '${health.mlPipeline.theftDetectionLatencyMs.toStringAsFixed(0)} ms'),
        context.sh(24),
      ],
    );
  }

  // ── DATA VALIDATION TAB ────────────────────────────────────────────
  Widget _buildValidationTab(
      BuildContext context,
      dynamic health,
      dynamic validation,
      bool isDark,
      ThemeData theme,
      SystemHealthController controller) {
    if (validation == null) {
      return Card(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
        ),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const CircularProgressIndicator(),
              context.sh(16),
              const Center(child: Text('Loading active prediction validation layer...')),
            ],
          ),
        ),
      );
    }

    final validationTime = DateTime.tryParse(validation.lastValidationTime)?.toLocal() ?? DateTime.now();
    final timeString = "${validationTime.hour.toString().padLeft(2, '0')}:${validationTime.minute.toString().padLeft(2, '0')}:${validationTime.second.toString().padLeft(2, '0')}";

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Glassmorphic Validation Banner Card
        _buildGlassmorphicContainer(
          isDark: isDark,
          borderRadius: 16,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.info.withValues(alpha: 0.15),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.shield_outlined, color: AppColors.info, size: 28),
                ),
                context.sw(16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Prediction Validation Layer Active',
                        style: theme.textTheme.labelLarge?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      Text(
                        'Consensus engine running multi-model validation checks. Last verified at $timeString.',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        context.sh(20),

        // Core validation stats dashboard
        _sectionTitle(context, 'Prediction Validation KPI'),
        context.sh(10),
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 3,
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          childAspectRatio: 0.9,
          children: [
            _buildStatMetricCard(
              context,
              'Prediction Confidence',
              '${validation.predictionConfidence.toStringAsFixed(1)}%',
              validation.predictionConfidence / 100.0,
              AppColors.healthy,
              isDark,
              theme,
            ),
            _buildStatMetricCard(
              context,
              'Data Quality Score',
              '${validation.dataQualityScore.toStringAsFixed(1)}%',
              validation.dataQualityScore / 100.0,
              AppColors.info,
              isDark,
              theme,
            ),
            _buildStatMetricCard(
              context,
              'Model Agreement',
              '${validation.modelAgreementScore.toStringAsFixed(1)}%',
              validation.modelAgreementScore / 100.0,
              AppColors.warning,
              isDark,
              theme,
            ),
          ],
        ),
        context.sh(20),

        // API Status Grid
        _sectionTitle(context, 'Verification API Heuristics'),
        context.sh(10),
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          childAspectRatio: 2.2,
          children: [
            _buildApiStatusCell(
              context,
              'OpenWeather API',
              validation.apiStatus['weather_api'] ?? 'Offline',
              Icons.cloud_queue,
              isDark,
            ),
            _buildApiStatusCell(
              context,
              'AI Consensus API',
              validation.apiStatus['ai_api'] ?? 'Offline',
              Icons.psychology,
              isDark,
            ),
            _buildApiStatusCell(
              context,
              'MongoDB validations',
              validation.apiStatus['database'] ?? 'Offline',
              Icons.storage,
              isDark,
            ),
            _buildApiStatusCell(
              context,
              'Validation Engine',
              validation.apiStatus['validation_engine'] ?? 'Active',
              Icons.verified_user,
              isDark,
            ),
          ],
        ),
        context.sh(20),

        // Engineering Verification Rules Explorer
        _sectionTitle(context, 'Module Rules & Heuristics'),
        context.sh(10),
        _buildModuleValidationCard(
          context: context,
          isDark: isDark,
          theme: theme,
          title: 'Load Forecasting Validation',
          subtitle: 'XGBoost Load Forecaster',
          sources: const ['OpenWeather API', 'Historical Patterns', 'Seasonality Rules', 'Holiday Calendar'],
          rules: const [
            'Temperature anomaly check: flags AC demand load (> 30°C) or heater load (< 12°C)',
            'Historical Bounds: flags demand forecasting outside standard 30,000 to 46,000 MW limits',
            'Weekly / Holiday: lowers expected baseline on public holidays and Sundays by 3,000 - 5,000 MW'
          ],
          active: validation.moduleStatus['load_forecasting'] ?? true,
        ),
        context.sh(8),
        _buildModuleValidationCard(
          context: context,
          isDark: isDark,
          theme: theme,
          title: 'Renewable Forecast Validation',
          subtitle: 'XGBoost, LightGBM, LSTM Ensemble',
          sources: const ['OpenWeather API', 'Physical Generation Limits'],
          rules: const [
            'Solar Daylight check: automatically caps solar farm prediction to 0 MW outside 6 AM - 7 PM',
            'Cloud Cover cross-check: flags over-optimistic solar forecast during heavy cloud cover (> 80%)',
            'Wind Cut-in/Cut-out limits: caps wind forecast to 0 MW if speed < 3.0 m/s or > 25.0 m/s'
          ],
          active: validation.moduleStatus['renewable_forecasting'] ?? true,
        ),
        context.sh(8),
        _buildModuleValidationCard(
          context: context,
          isDark: isDark,
          theme: theme,
          title: 'Fault Detection Validation',
          subtitle: 'Multi-Model Consensus (XGBoost, RF, LightGBM)',
          sources: const ['Rule-Based Grid Physics', 'Consensus Engine'],
          rules: const [
            'Current Overload rule: flags anomaly if current > 25A engineering limit',
            'Voltage Swell / Sag check: flags swell if voltage > 245V, and sag if voltage < 195V',
            'Ensemble Agreement Check: downgrades alerts to Warning if XGBoost, RF, & LightGBM agreement < 80%'
          ],
          active: validation.moduleStatus['fault_detection'] ?? true,
        ),
        context.sh(8),
        _buildModuleValidationCard(
          context: context,
          isDark: isDark,
          theme: theme,
          title: 'Theft Detection Validation',
          subtitle: 'Isolation Forest + Consumption Rules',
          sources: const ['Historical Consumption', 'Neighbourhood Patterns', 'Power Factor'],
          rules: const [
            'Sudden Drop check: flags alert if consumption is > 40% below historical monthly average',
            'Inductive bypass tapping: checks power factor; flags severe alert if power factor drops < 0.75 PF',
            'False Alert Filter: overrides theft flag if consumption is above normal (+20%)'
          ],
          active: validation.moduleStatus['theft_detection'] ?? true,
        ),
        context.sh(8),
        _buildModuleValidationCard(
          context: context,
          isDark: isDark,
          theme: theme,
          title: 'Transformer Health Validation',
          subtitle: 'XGBoost & Random Forest Diagnostics',
          sources: const ['Thermal Engineering Rules', 'dielectric Oil Limits'],
          rules: const [
            'Winding Temperature limit: flags warning/overheating if transformer temp > 95°C',
            'Dielectric Oil Level: flags dielectric failure risk if oil level drops below 70%',
            'MVA Load percentage limits: warns if transformer load exceeds 100% rated design'
          ],
          active: validation.moduleStatus['transformer_health'] ?? true,
        ),
        context.sh(24),
      ],
    );
  }

  // ── CORE METRICS UI HELPERS ────────────────────────────────────────
  Widget _buildStatMetricCard(
      BuildContext context,
      String title,
      String value,
      double progressValue,
      Color color,
      bool isDark,
      ThemeData theme) {
    return _buildGlassmorphicContainer(
      isDark: isDark,
      borderRadius: 12,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 12.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Expanded(
              child: Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    width: 60,
                    height: 60,
                    child: CircularProgressIndicator(
                      value: progressValue.clamp(0.0, 1.0),
                      strokeWidth: 5,
                      backgroundColor: color.withValues(alpha: 0.1),
                      valueColor: AlwaysStoppedAnimation<Color>(color),
                    ),
                  ),
                  Text(
                    value,
                    style: theme.textTheme.labelLarge?.copyWith(fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                ],
              ),
            ),
            context.sh(8),
            Text(
              title,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall?.copyWith(fontSize: 10, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildApiStatusCell(
      BuildContext context,
      String title,
      String status,
      IconData icon,
      bool isDark) {
    final theme = Theme.of(context);
    final isOnline = status.toLowerCase() == 'online' ||
        status.toLowerCase() == 'connected' ||
        status.toLowerCase() == 'active';

    final indicatorColor = isOnline ? AppColors.healthy : AppColors.critical;

    return _buildGlassmorphicContainer(
      isDark: isDark,
      borderRadius: 12,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(icon, color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary, size: 20),
            context.sw(10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(title, style: theme.textTheme.labelMedium?.copyWith(fontSize: 12, fontWeight: FontWeight.bold)),
                  context.sh(2),
                  Row(
                    children: [
                      Container(
                        width: 6,
                        height: 6,
                        decoration: BoxDecoration(
                          color: indicatorColor,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: indicatorColor.withValues(alpha: 0.5),
                              blurRadius: 4,
                              spreadRadius: 1,
                            ),
                          ],
                        ),
                      ),
                      context.sw(6),
                      Text(
                        status,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: indicatorColor,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildModuleValidationCard({
    required BuildContext context,
    required bool isDark,
    required ThemeData theme,
    required String title,
    required String subtitle,
    required List<String> sources,
    required List<String> rules,
    required bool active,
  }) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Theme(
        data: theme.copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          title: Row(
            children: [
              Icon(
                Icons.check_circle_outline,
                color: active ? AppColors.healthy : AppColors.warning,
                size: 20,
              ),
              context.sw(12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: theme.textTheme.labelMedium?.copyWith(fontWeight: FontWeight.bold)),
                    Text(subtitle, style: theme.textTheme.bodySmall?.copyWith(fontSize: 11)),
                  ],
                ),
              ),
            ],
          ),
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Divider(),
                  context.sh(8),
                  Text('Validation Sources:', style: theme.textTheme.labelSmall?.copyWith(fontWeight: FontWeight.bold)),
                  context.sh(4),
                  Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    children: sources.map((src) {
                      return Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.primaryBlue.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          src,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: AppColors.primaryBlue,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                  context.sh(12),
                  Text('Active Verification Rules:', style: theme.textTheme.labelSmall?.copyWith(fontWeight: FontWeight.bold)),
                  context.sh(6),
                  ...rules.map((rule) => Padding(
                    padding: const EdgeInsets.only(bottom: 6.0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.arrow_right, color: AppColors.primaryBlue, size: 16),
                        context.sw(4),
                        Expanded(
                          child: Text(
                            rule,
                            style: theme.textTheme.bodySmall?.copyWith(fontSize: 11, height: 1.3),
                          ),
                        ),
                      ],
                    ),
                  )),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── GLASSMORPHIC WRAPPER ───────────────────────────────────────────
  Widget _buildGlassmorphicContainer({
    required bool isDark,
    required double borderRadius,
    required Widget child,
  }) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(
            color: isDark
                ? Colors.white.withValues(alpha: 0.05)
                : Colors.black.withValues(alpha: 0.02),
            borderRadius: BorderRadius.circular(borderRadius),
            border: Border.all(
              color: isDark
                  ? Colors.white.withValues(alpha: 0.08)
                  : Colors.black.withValues(alpha: 0.04),
              width: 1,
            ),
          ),
          child: child,
        ),
      ),
    );
  }

  // ── SECTION HEADER UI HELPERS ──────────────────────────────────────
  Widget _sectionTitle(BuildContext context, String title) {
    return Text(
      title,
      style: Theme.of(context).textTheme.labelLarge?.copyWith(fontWeight: FontWeight.bold),
    );
  }

  Widget _serviceCard(BuildContext context, bool isDark, String name,
      String subtitle, StatusType status, List<_Detail> details) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.primaryBlue.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.dns, color: AppColors.primaryBlue, size: 20),
                ),
                context.sw(12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(name, style: Theme.of(context).textTheme.labelLarge?.copyWith(fontWeight: FontWeight.bold)),
                      Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ),
                StatusChip(status: status),
              ],
            ),
            context.sh(14),
            Wrap(
              spacing: 20,
              runSpacing: 10,
              children: details
                  .map((d) => _detailItem(context, d.label, d.value))
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _detailItem(BuildContext context, String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(fontSize: 10)),
        context.sh(2),
        Text(value,
            style: Theme.of(context)
                .textTheme
                .labelLarge
                ?.copyWith(fontSize: 13, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _storageBar(BuildContext context, bool isDark, double used, double total) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text('Storage Usage',
                    style: Theme.of(context).textTheme.bodySmall),
                const Spacer(),
                Text('${used.toStringAsFixed(1)} / ${total.toInt()} GB',
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.bold)),
              ],
            ),
            context.sh(8),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: used / total,
                backgroundColor: AppColors.primaryBlue.withValues(alpha: 0.1),
                valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primaryBlue),
                minHeight: 8,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _mlServiceRow(
      BuildContext context, bool isDark, String name, StatusType status, String latency) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Icon(
              Icons.memory,
              size: 20,
              color: status == StatusType.healthy ? AppColors.healthy : AppColors.warning,
            ),
            context.sw(12),
            Expanded(
              child: Text(name, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.bold)),
            ),
            Text(latency, style: Theme.of(context).textTheme.bodySmall),
            context.sw(12),
            StatusChip(status: status),
          ],
        ),
      ),
    );
  }
}

class _Detail {
  final String label, value;
  _Detail(this.label, this.value);
}
