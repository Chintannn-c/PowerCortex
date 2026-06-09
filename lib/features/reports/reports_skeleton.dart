import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import '../../core/theme/skeleton_theme.dart';
import '../../widgets/skeleton/skeletons.dart';

/// Full-page skeleton for the Reports & Analytics screen.
///
/// Mimics the 3-tab layout: report list, model performance, data sources.
class ReportsSkeleton extends StatelessWidget {
  const ReportsSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Tab bar
        _tabBarSkeleton(context),
        context.sh(8),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: 5,
            itemBuilder: (_, __) => const Padding(
              padding: EdgeInsets.only(bottom: 10),
              child: SkeletonReportCard(),
            ),
          ),
        ),
      ],
    );
  }

  Widget _tabBarSkeleton(BuildContext context) {
    return SkeletonShimmer(
      child: Container(
        margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
        height: 46,
        decoration: BoxDecoration(
          color: SkeletonTheme.baseColor(context),
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }
}
