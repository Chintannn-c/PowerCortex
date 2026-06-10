import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import 'package:shimmer/shimmer.dart';

class InsightsSkeleton extends StatelessWidget {
  const InsightsSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Shimmer.fromColors(
            baseColor: isDark ? Colors.white10 : Colors.black12,
            highlightColor: isDark ? Colors.white24 : Colors.black26,
            child: Container(
              height: 32,
              width: 250,
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkCard : AppColors.lightCard,
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Shimmer.fromColors(
            baseColor: isDark ? Colors.white10 : Colors.black12,
            highlightColor: isDark ? Colors.white24 : Colors.black26,
            child: Container(
              height: 16,
              width: 350,
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkCard : AppColors.lightCard,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          ),
          const SizedBox(height: 32),
          Expanded(
            child: ListView.builder(
              itemCount: 5,
              itemBuilder: (context, index) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 16.0),
                  child: Shimmer.fromColors(
                    baseColor: isDark ? Colors.white10 : Colors.black12,
                    highlightColor: isDark ? Colors.white24 : Colors.black26,
                    child: Container(
                      height: 120,
                      decoration: BoxDecoration(
                        color: isDark ? AppColors.darkCard : AppColors.lightCard,
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
