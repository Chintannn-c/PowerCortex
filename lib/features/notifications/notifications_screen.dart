import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/services/notification_service.dart';
import '../../core/theme/app_colors.dart';
import 'package:shimmer/shimmer.dart';

class NotificationsDrawer extends StatelessWidget {
  const NotificationsDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final controller = Get.find<NotificationService>();

    return Drawer(
      backgroundColor: isDark ? AppColors.darkBg : AppColors.lightBg,
      width: 360,
      child: Column(
        children: [
          _buildHeader(context, isDark, controller),
          Expanded(
            child: Obx(() {
              if (controller.isLoading.value && controller.notifications.isEmpty) {
                return _buildShimmer(isDark);
              }
              if (controller.notifications.isEmpty) {
                return _buildEmptyState(isDark);
              }
              return ListView.builder(
                padding: const EdgeInsets.symmetric(vertical: 8),
                itemCount: controller.notifications.length,
                itemBuilder: (context, index) {
                  final notif = controller.notifications[index];
                  return _buildNotificationTile(context, notif, isDark, controller);
                },
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context, bool isDark, NotificationService controller) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 48, 16, 16),
      color: isDark ? AppColors.darkCard : Colors.white,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              const Icon(Icons.notifications_active_outlined, color: AppColors.primaryBlue),
              const SizedBox(width: 10),
              Text(
                'Notifications',
                style: GoogleFonts.poppins(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: isDark ? AppColors.darkText : AppColors.lightText,
                ),
              ),
            ],
          ),
          Row(
            children: [
              Obx(() => controller.unreadCount.value > 0
                  ? Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.primaryBlue.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${controller.unreadCount.value} new',
                        style: GoogleFonts.outfit(
                          color: AppColors.primaryBlue,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    )
                  : const SizedBox.shrink()),
              const SizedBox(width: 8),
              Obx(() => controller.notifications.isNotEmpty
                  ? TextButton(
                      style: TextButton.styleFrom(
                        foregroundColor: AppColors.critical,
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      onPressed: () => controller.clearAllNotifications(),
                      child: Text(
                        'Clear All',
                        style: GoogleFonts.outfit(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    )
                  : const SizedBox.shrink()),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildNotificationTile(
    BuildContext context, 
    NotificationModel notif, 
    bool isDark, 
    NotificationService controller
  ) {
    IconData icon;
    Color color;
    String badgeText;
    
    switch (notif.type) {
      case 'asset':
        icon = Icons.electrical_services_outlined;
        color = AppColors.warning;
        badgeText = 'ASSET ALARM';
        break;
      case 'fault':
        icon = Icons.warning_amber_rounded;
        color = AppColors.critical;
        badgeText = notif.title.toLowerCase().contains('critical') ? 'CRITICAL FAULT' : 'GRID FAULT';
        break;
      case 'forecast':
        icon = Icons.trending_up_rounded;
        color = AppColors.info;
        badgeText = 'DEMAND FORECAST';
        break;
      case 'ai':
        icon = Icons.psychology_outlined;
        color = AppColors.primaryBlue;
        badgeText = 'AI INSIGHT';
        break;
      case 'report':
        icon = Icons.insert_chart_outlined;
        color = AppColors.healthy;
        badgeText = 'SYSTEM REPORT';
        break;
      default:
        icon = Icons.notifications_none_outlined;
        color = AppColors.primaryBlue;
        badgeText = 'ALERT';
    }

    if (notif.title.toLowerCase().contains('cascade') || notif.title.toLowerCase().contains('grouped')) {
      badgeText = 'AI CASCADE';
    }

    final cardBgColor = isDark
        ? (notif.isRead ? AppColors.darkCard : AppColors.darkCard.withValues(alpha: 0.85))
        : (notif.isRead ? Colors.white : Colors.blue.shade50.withValues(alpha: 0.45));

    final titleColor = isDark ? AppColors.darkText : AppColors.lightText;
    final msgColor = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;

    return Dismissible(
      key: Key(notif.id),
      direction: DismissDirection.endToStart,
      background: Container(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        decoration: BoxDecoration(
          color: AppColors.critical.withValues(alpha: 0.9),
          borderRadius: BorderRadius.circular(12),
        ),
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20.0),
        child: const Icon(Icons.delete_sweep_outlined, color: Colors.white, size: 24),
      ),
      onDismissed: (direction) {
        controller.deleteNotification(notif.id);
      },
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        decoration: BoxDecoration(
          color: cardBgColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: notif.isRead ? Colors.transparent : color.withValues(alpha: 0.25),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Container(
                  width: 4,
                  color: color,
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: color.withValues(alpha: 0.08),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                badgeText,
                                style: GoogleFonts.outfit(
                                  color: color,
                                  fontSize: 9,
                                  fontWeight: FontWeight.bold,
                                  letterSpacing: 0.4,
                                ),
                              ),
                            ),
                            Text(
                              _formatTime(notif.createdAt),
                              style: GoogleFonts.outfit(
                                fontSize: 10,
                                color: isDark 
                                    ? AppColors.darkTextSecondary.withValues(alpha: 0.5) 
                                    : AppColors.lightTextSecondary.withValues(alpha: 0.5),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        InkWell(
                          onTap: () {
                            controller.handleNotificationTap(notif);
                          },
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(icon, color: color, size: 16),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  notif.title,
                                  style: GoogleFonts.poppins(
                                    fontSize: 13,
                                    fontWeight: notif.isRead ? FontWeight.w500 : FontWeight.w600,
                                    color: titleColor,
                                    height: 1.25,
                                  ),
                                ),
                              ),
                              if (!notif.isRead) ...[
                                const SizedBox(width: 6),
                                Container(
                                  width: 6,
                                  height: 6,
                                  decoration: const BoxDecoration(
                                    color: AppColors.primaryBlue,
                                    shape: BoxShape.circle,
                                  ),
                                ),
                              ]
                            ],
                          ),
                        ),
                        const SizedBox(height: 6),
                        InkWell(
                          onTap: () {
                            controller.handleNotificationTap(notif);
                          },
                          child: Text(
                            notif.message,
                            style: GoogleFonts.outfit(
                              fontSize: 12,
                              color: msgColor,
                              height: 1.3,
                            ),
                          ),
                        ),
                        if (notif.type == 'fault' && badgeText.contains('CRITICAL')) ...[
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppColors.healthy,
                                  foregroundColor: Colors.white,
                                  elevation: 0,
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  minimumSize: Size.zero,
                                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                                ),
                                icon: const Icon(Icons.check, size: 12),
                                label: Text('Ack', style: GoogleFonts.outfit(fontSize: 10, fontWeight: FontWeight.w600)),
                                onPressed: () => controller.acknowledgeAlert(notif.id),
                              ),
                              const SizedBox(width: 6),
                              OutlinedButton.icon(
                                style: OutlinedButton.styleFrom(
                                  foregroundColor: AppColors.warning,
                                  side: const BorderSide(color: AppColors.warning),
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  minimumSize: Size.zero,
                                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                                ),
                                icon: const Icon(Icons.snooze, size: 12),
                                label: Text('Snooze', style: GoogleFonts.outfit(fontSize: 10, fontWeight: FontWeight.w600)),
                                onPressed: () => controller.snoozeAlert(notif.id),
                              ),
                              const Spacer(),
                              IconButton(
                                constraints: const BoxConstraints(),
                                padding: EdgeInsets.zero,
                                icon: Icon(Icons.delete_outline, color: titleColor.withValues(alpha: 0.4), size: 16),
                                onPressed: () => controller.deleteNotification(notif.id),
                              )
                            ],
                          ),
                        ] else ...[
                          const SizedBox(height: 4),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.end,
                            children: [
                              IconButton(
                                constraints: const BoxConstraints(),
                                padding: EdgeInsets.zero,
                                icon: Icon(Icons.delete_outline, color: titleColor.withValues(alpha: 0.35), size: 16),
                                onPressed: () => controller.deleteNotification(notif.id),
                              )
                            ],
                          )
                        ],
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

  String _formatTime(String isoString) {
    try {
      final date = DateTime.parse(isoString).toLocal();
      final now = DateTime.now();
      final diff = now.difference(date);
      if (diff.inMinutes < 60) {
        return '${diff.inMinutes}m ago';
      } else if (diff.inHours < 24) {
        return '${diff.inHours}h ago';
      }
      return '${date.day}/${date.month}/${date.year}';
    } catch (e) {
      return '';
    }
  }

  Widget _buildEmptyState(bool isDark) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkCard : Colors.grey.shade100,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.notifications_off_outlined,
                size: 48,
                color: isDark ? AppColors.darkTextSecondary.withValues(alpha: 0.4) : AppColors.lightTextSecondary.withValues(alpha: 0.4),
              ),
            ),
            const SizedBox(height: 20),
            Text(
              'All Caught Up!',
              style: GoogleFonts.poppins(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: isDark ? AppColors.darkText : AppColors.lightText,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'You have no new alerts. The grid is operating within healthy parameters.',
              textAlign: TextAlign.center,
              style: GoogleFonts.outfit(
                fontSize: 12,
                color: isDark ? AppColors.darkTextSecondary.withValues(alpha: 0.6) : AppColors.lightTextSecondary.withValues(alpha: 0.6),
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildShimmer(bool isDark) {
    final baseColor = isDark ? Colors.grey[850]! : Colors.grey[200]!;
    final highlightColor = isDark ? Colors.grey[800]! : Colors.grey[100]!;
    
    return ListView.builder(
      itemCount: 4,
      itemBuilder: (context, index) {
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Shimmer.fromColors(
            baseColor: baseColor,
            highlightColor: highlightColor,
            child: Container(
              height: 100,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        );
      },
    );
  }
}

