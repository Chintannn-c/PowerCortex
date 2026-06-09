import 'package:flutter/material.dart';
import '../core/utils/responsive.dart';
import '../core/theme/app_colors.dart';
import 'status_chip.dart';

class AssetCard extends StatelessWidget {
  final String name;
  final String type;
  final double healthScore;
  final StatusType status;
  final String lastUpdated;
  final VoidCallback? onTap;

  const AssetCard({
    super.key,
    required this.name,
    required this.type,
    required this.healthScore,
    required this.status,
    required this.lastUpdated,
    this.onTap,
  });

  Color get _healthColor {
    if (healthScore >= 80) return AppColors.healthy;
    if (healthScore >= 60) return AppColors.warning;
    return AppColors.critical;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppColors.primaryBlue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(
                      Icons.electrical_services,
                      color: AppColors.primaryBlue,
                      size: 22,
                    ),
                  ),
                  context.sw(12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(name, style: theme.textTheme.labelLarge),
                        Text(type, style: theme.textTheme.bodySmall),
                      ],
                    ),
                  ),
                  StatusChip(status: status),
                ],
              ),
              context.sh(16),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Health Score',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: isDark
                                ? AppColors.darkTextSecondary
                                : AppColors.lightTextSecondary,
                          ),
                        ),
                        context.sh(6),
                        Row(
                          children: [
                            Expanded(
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(4),
                                child: LinearProgressIndicator(
                                  value: healthScore / 100,
                                  backgroundColor: _healthColor.withOpacity(0.15),
                                  valueColor:
                                      AlwaysStoppedAnimation<Color>(_healthColor),
                                  minHeight: 6,
                                ),
                              ),
                            ),
                            context.sw(8),
                            Text(
                              '${healthScore.toInt()}%',
                              style: theme.textTheme.labelMedium?.copyWith(
                                color: _healthColor,
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
              context.sh(10),
              Row(
                children: [
                  Icon(
                    Icons.access_time,
                    size: 13,
                    color: isDark
                        ? AppColors.darkTextSecondary
                        : AppColors.lightTextSecondary,
                  ),
                  context.sw(4),
                  Text(
                    'Updated $lastUpdated',
                    style: theme.textTheme.bodySmall?.copyWith(fontSize: 11),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
