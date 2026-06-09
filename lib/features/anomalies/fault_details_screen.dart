import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../core/theme/app_colors.dart';
import '../../widgets/status_chip.dart';
import '../../widgets/confidence_badge.dart';
import 'controllers/fault_controller.dart';
import 'models/fault_model.dart';
import 'fault_details_skeleton.dart';

class FaultDetailsScreen extends StatefulWidget {
  const FaultDetailsScreen({super.key});

  @override
  State<FaultDetailsScreen> createState() => _FaultDetailsScreenState();
}

class _FaultDetailsScreenState extends State<FaultDetailsScreen> {
  final FaultController _controller = Get.find<FaultController>();
  FaultModel? _fault;
  bool _isLoading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _loadFaultDetails();
  }

  Future<void> _loadFaultDetails() async {
    final String? id = Get.arguments as String?;
    if (id == null) {
      setState(() {
        _isLoading = false;
        _error = 'No fault ID provided';
      });
      return;
    }

    final faultData = await _controller.getFaultDetails(id);
    if (faultData != null) {
      setState(() {
        _fault = faultData;
        _isLoading = false;
      });
    } else {
      // Look up in loaded lists as fallback
      final localFault = _controller.activeFaults.firstWhereOrNull((f) => f.faultId == id) ??
                          _controller.historicalFaults.firstWhereOrNull((f) => f.faultId == id);
      if (localFault != null) {
        setState(() {
          _fault = localFault;
          _isLoading = false;
        });
      } else {
        setState(() {
          _isLoading = false;
          _error = 'Fault details not found';
        });
      }
    }
  }

  String _getAIRecommendation(FaultModel f) {
    final probStr = '${f.probability.toStringAsFixed(1)}%';
    switch (f.faultType) {
      case 'Voltage Sag':
        return 'Immediate inspection required. Voltage dropped to ${f.voltage.toStringAsFixed(1)} V (below nominal threshold) and fault probability is $probStr.';
      case 'Voltage Swell':
        return 'Grid overvoltage protection check required. Voltage rose to ${f.voltage.toStringAsFixed(1)} V, posing damage risks. Fault probability is $probStr.';
      case 'Overload':
        return 'Load redistribution required immediately. Line current reached ${f.current.toStringAsFixed(1)} A, exceeding safety ratings. Fault probability is $probStr.';
      case 'Line Fault':
        return 'Physical line scan suggested. Impedance changes detected on the phase lines. Fault probability is $probStr.';
      case 'Transformer Fault':
        return 'Fluid level and temperature check required. Transformer showing high thermal and loading stress. Fault probability is $probStr.';
      case 'Frequency Deviation':
        return 'Generator governor response tuning required. Grid frequency fluctuated to ${f.frequency.toStringAsFixed(1)} Hz. Fault probability is $probStr.';
      case 'Short Circuit':
        return 'Crew dispatch needed. Low voltage and severe current spike suggest active short circuit. Fault probability is $probStr.';
      default:
        return 'Inspection required. Telemetry metrics show unusual patterns. Fault probability is $probStr.';
    }
  }

  String _formatDateTime(DateTime dt) {
    return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    Widget body;
    if (_isLoading) {
      body = const FaultDetailsSkeleton();
    } else if (_error.isNotEmpty) {
      body = Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: AppColors.critical),
            const SizedBox(height: 16),
            Text(_error, style: const TextStyle(color: AppColors.critical)),
          ],
        ),
      );
    } else {
      final f = _fault!;
      final color = f.severity == StatusType.critical
          ? AppColors.critical
          : f.severity == StatusType.warning
              ? AppColors.warning
              : f.severity == StatusType.healthy
                  ? AppColors.healthy
                  : AppColors.info;

      body = SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status and ID Row
            Row(
              children: [
                Text(
                  'Fault ID: ${f.faultId}',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                  ),
                ),
                const Spacer(),
                StatusChip(status: f.severity, label: f.severity == StatusType.healthy ? 'Medium' : (f.severity == StatusType.info ? 'Low' : null)),
              ],
            ),
            const SizedBox(height: 16),
            // Fault Type Title
            Text(
              f.faultType,
              style: theme.textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: isDark ? AppColors.darkText : AppColors.lightText,
              ),
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(Icons.location_on_outlined, size: 16, color: isDark ? Colors.grey : Colors.black54),
                const SizedBox(width: 4),
                Text(
                  f.assetName,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // AI Recommendation Card
            Card(
              elevation: 0,
              color: color.withOpacity(0.08),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: BorderSide(color: color.withOpacity(0.25), width: 1.5),
              ),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.psychology, color: color, size: 24),
                        const SizedBox(width: 8),
                        Text(
                          'AI Recommendation',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: color,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _getAIRecommendation(f),
                      style: theme.textTheme.bodyMedium?.copyWith(
                        height: 1.5,
                        color: isDark ? AppColors.darkText : AppColors.lightText,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Telemetry values grid
            Text(
              'Telemetry Metrics',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.4,
              children: [
                _metricTile('Voltage', '${f.voltage.toStringAsFixed(1)} V', Icons.flash_on, AppColors.primaryBlue, isDark),
                _metricTile('Current', '${f.current.toStringAsFixed(1)} A', Icons.bolt, AppColors.warning, isDark),
                _metricTile('Frequency', '${f.frequency.toStringAsFixed(1)} Hz', Icons.waves, AppColors.healthy, isDark),
                _metricTile(
                  'Confidence',
                  '${f.probability.toStringAsFixed(1)}%',
                  Icons.verified_user_outlined,
                  AppColors.info,
                  isDark,
                  child: ConfidenceBadge(score: f.probability),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Diagnostic information
            Text(
              'Diagnostic Details',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            _detailRow('Detection Time', _formatDateTime(f.detectedAt), isDark),
            _detailRow('Fault Status', f.status, isDark, valueColor: f.status == 'Active' ? AppColors.critical : AppColors.healthy),
            _detailRow('Asset Link', f.assetName, isDark),
          ],
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Fault Details'),
      ),
      body: body,
    );
  }

  Widget _metricTile(String label, String value, IconData icon, Color color, bool isDark, {Widget? child}) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                Icon(icon, color: color, size: 20),
              ],
            ),
            if (child != null)
              child
            else
              Text(
                value,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
          ],
        ),
      ),
    );
  }

  Widget _detailRow(String label, String value, bool isDark, {Color? valueColor}) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: isDark ? AppColors.darkBorder.withOpacity(0.5) : AppColors.lightBorder.withOpacity(0.5),
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.w600,
              color: valueColor ?? (isDark ? AppColors.darkText : AppColors.lightText),
            ),
          ),
        ],
      ),
    );
  }
}
