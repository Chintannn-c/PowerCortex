import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import '../../core/theme/app_colors.dart';
import 'insights_controller.dart';
import 'insights_skeleton.dart';
import '../home/home_shell.dart';
import '../anomalies/controllers/fault_controller.dart';
import '../equipment/controllers/transformer_controller.dart';

class InsightsScreen extends StatelessWidget {
  const InsightsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final InsightsController controller = Get.put(InsightsController());
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Obx(() {
      if (controller.isLoading.value) {
        return const InsightsSkeleton();
      }

      final insights = controller.aggregatedInsights;

      return Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: insights.isEmpty
                  ? Center(
                      child: Text(
                        'No insights available at the moment.',
                        style: TextStyle(
                          color: isDark ? Colors.white60 : Colors.black54,
                        ),
                      ),
                    )
                  : ListView.builder(
                      itemCount: insights.length,
                      itemBuilder: (context, index) {
                        final insight = insights[index];
                        return _buildInsightCard(context, insight, isDark);
                      },
                    ),
            ),
          ],
        ),
      );
    });
  }

  Widget _buildInsightCard(
    BuildContext context,
    Map<String, dynamic> insight,
    bool isDark,
  ) {
    final type = insight['type'] as String;
    final text = insight['text'] as String;
    final timestamp = insight['timestamp'] as DateTime;
    final source = insight['source'] as String;

    Color iconColor;
    IconData icon;

    if (type == 'Anomaly Alert' || type == 'Revenue Risk') {
      iconColor = AppColors.critical;
      icon = Icons.warning_amber_rounded;
    } else if (type == 'Equipment Warning') {
      iconColor = AppColors.warning;
      icon = Icons.electrical_services_rounded;
    } else if (type == 'Weather Impact') {
      iconColor = AppColors.info;
      icon = Icons.thermostat_rounded;
    } else {
      iconColor = AppColors.primaryBlue;
      icon = Icons.insights_rounded;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : AppColors.lightCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: (isDark ? Colors.white : Colors.black).withOpacity(0.05),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(isDark ? 0.2 : 0.05),
            blurRadius: 15,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => _handleInsightTap(context, text),
          child: IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Left severity accent bar
                Container(
                  width: 6,
                  decoration: BoxDecoration(
                    color: iconColor,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(16),
                      bottomLeft: Radius.circular(16),
                    ),
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 16,
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: iconColor.withOpacity(0.12),
                                shape: BoxShape.circle,
                              ),
                              child: Icon(icon, color: iconColor, size: 18),
                            ),
                            const SizedBox(width: 12),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 10,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: iconColor.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: iconColor.withOpacity(0.3),
                                ),
                              ),
                              child: Text(
                                type,
                                style: GoogleFonts.poppins(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: iconColor,
                                  letterSpacing: 0.3,
                                ),
                              ),
                            ),
                            const Spacer(),
                            Text(
                              DateFormat('hh:mm a').format(timestamp),
                              style: GoogleFonts.poppins(
                                fontSize: 12,
                                color: isDark ? Colors.white54 : Colors.black45,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 14),
                        Text(
                          text,
                          style: GoogleFonts.poppins(
                            fontSize: 14,
                            color: isDark
                                ? AppColors.darkText
                                : AppColors.lightText,
                            height: 1.6,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const SizedBox(height: 14),
                        Divider(
                          height: 1,
                          color: (isDark ? Colors.white : Colors.black)
                              .withOpacity(0.05),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Icon(
                              Icons.auto_awesome,
                              size: 14,
                              color: isDark ? Colors.white54 : Colors.black54,
                            ),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                'Source: $source',
                                style: GoogleFonts.poppins(
                                  fontSize: 12,
                                  color: isDark
                                      ? Colors.white54
                                      : Colors.black54,
                                  fontWeight: FontWeight.w500,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  'View Details',
                                  style: GoogleFonts.poppins(
                                    fontSize: 12,
                                    color: iconColor,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                const SizedBox(width: 4),
                                Icon(
                                  Icons.arrow_forward_ios,
                                  size: 10,
                                  color: iconColor,
                                ),
                              ],
                            ),
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
      ),
    );
  }

  void _handleInsightTap(BuildContext context, String text) {
    final faultRegex = RegExp(r'\bFLT-\d+\b', caseSensitive: false);
    final transRegex = RegExp(r'\bT-\d+\b', caseSensitive: false);

    if (faultRegex.hasMatch(text)) {
      final id = faultRegex.firstMatch(text)!.group(0)!.toUpperCase();
      if (Get.isRegistered<FaultController>()) {
        Get.find<FaultController>().searchQuery.value = id;
      }
      HomeShell.of(context)?.navigateTo(3); // Anomalies

      Get.snackbar(
        'Insight Redirect',
        'Navigated to Anomalies and filtered by $id',
        backgroundColor: AppColors.primaryBlue.withOpacity(0.9),
        colorText: Colors.white,
        snackPosition: SnackPosition.BOTTOM,
      );
    } else if (transRegex.hasMatch(text)) {
      final id = transRegex.firstMatch(text)!.group(0)!.toUpperCase();
      if (Get.isRegistered<TransformerController>()) {
        Get.find<TransformerController>().searchQuery.value = id;
      }
      HomeShell.of(context)?.navigateTo(2); // Diagnostics

      Get.snackbar(
        'Insight Redirect',
        'Navigated to Diagnostics and filtered by $id',
        backgroundColor: AppColors.primaryBlue.withOpacity(0.9),
        colorText: Colors.white,
        snackPosition: SnackPosition.BOTTOM,
      );
    } else {
      // General insight goes to Forecast
      HomeShell.of(context)?.navigateTo(1); // Forecasting
      Get.snackbar(
        'Insight Redirect',
        'Navigated to Forecast to view broader trends',
        backgroundColor: AppColors.primaryBlue.withOpacity(0.9),
        colorText: Colors.white,
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }
}
