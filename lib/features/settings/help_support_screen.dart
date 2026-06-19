import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shimmer/shimmer.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/theme/app_colors.dart';

class HelpSupportScreen extends StatefulWidget {
  const HelpSupportScreen({super.key});

  @override
  State<HelpSupportScreen> createState() => _HelpSupportScreenState();
}

class _HelpSupportScreenState extends State<HelpSupportScreen> {
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    // Simulate fetching FAQs and Support details
    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    });
  }

  Future<void> _sendSupportEmail() async {
    final Uri emailLaunchUri = Uri(
      scheme: 'mailto',
      path: 'powercortexguvnl@gmail.com',
      queryParameters: {
        'subject': 'PowerCortex Support Request',
      },
    );
    try {
      if (await canLaunchUrl(emailLaunchUri)) {
        await launchUrl(emailLaunchUri);
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Could not open default mail client.'),
              backgroundColor: Colors.redAccent,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error launching mail client: $e'),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBg : AppColors.lightBg,
      appBar: AppBar(
        title: const Text('Help & Support'),
      ),
      body: _isLoading ? _buildSkeletonLoader(isDark) : ListView(
        padding: const EdgeInsets.all(24),
        children: [
          // Header Illustration / Icon
          Center(
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppColors.primaryBlue.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.support_agent_rounded,
                size: 64,
                color: AppColors.primaryBlue,
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'How can we help you?',
            textAlign: TextAlign.center,
            style: GoogleFonts.poppins(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: isDark ? Colors.white : Colors.black,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Find answers to common questions or reach out to the PowerCortex grid command center.',
            textAlign: TextAlign.center,
            style: GoogleFonts.poppins(
              fontSize: 14,
              color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
            ),
          ),
          const SizedBox(height: 32),
          
          // Contact Options
          Text(
            'Contact Us',
            style: GoogleFonts.poppins(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: isDark ? Colors.white : Colors.black,
            ),
          ),
          const SizedBox(height: 16),
          _buildContactCard(
            context,
            isDark: isDark,
            icon: Icons.email_outlined,
            title: 'Email Support',
            subtitle: 'powercortexguvnl@gmail.com',
            onTap: _sendSupportEmail,
          ),
          const SizedBox(height: 32),

          // FAQs
          Text(
            'Frequently Asked Questions',
            style: GoogleFonts.poppins(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: isDark ? Colors.white : Colors.black,
            ),
          ),
          const SizedBox(height: 16),
          _buildFaqItem(
            isDark: isDark,
            question: 'How do I interpret the Transformer Health Score?',
            answer: 'The health score is an AI-generated metric (0-100) based on real-time DGA (Dissolved Gas Analysis) and oil temperature. A score below 40 indicates critical maintenance is required.',
          ),
          _buildFaqItem(
            isDark: isDark,
            question: 'What triggers a Power Theft Alert?',
            answer: 'Our Deep Learning models analyze Smart Meter telemetry in real-time. If it detects anomalies like sudden consumption drops without a corresponding load shedding event, an alert is triggered.',
          ),
          _buildFaqItem(
            isDark: isDark,
            question: 'Can I disable Two-Step Verification?',
            answer: 'Yes, but it is highly discouraged. Two-Step Verification ensures that only authorized grid operators can access the platform. You can disable it from the Security section in Settings.',
          ),
          _buildFaqItem(
            isDark: isDark,
            question: 'How do I generate a PDF report?',
            answer: 'Navigate to the Reports tab, select the specific asset (e.g. Transformer TR-004), specify your date range, and tap "Export PDF". The report will be downloaded to your device.',
          ),
        ],
      ),
    );
  }

  Widget _buildSkeletonLoader(bool isDark) {
    final baseColor = isDark ? Colors.grey[850]! : Colors.grey[300]!;
    final highlightColor = isDark ? Colors.grey[800]! : Colors.grey[100]!;

    return Shimmer.fromColors(
      baseColor: baseColor,
      highlightColor: highlightColor,
      child: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          // Header Icon Skeleton
          Center(
            child: Container(
              width: 112,
              height: 112,
              decoration: const BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
              ),
            ),
          ),
          const SizedBox(height: 24),
          
          // Title Skeleton
          Center(
            child: Container(
              height: 24,
              width: 220,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          ),
          const SizedBox(height: 8),
          
          // Subtitle Skeleton
          Center(
            child: Container(
              height: 14,
              width: 300,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          ),
          const SizedBox(height: 6),
          Center(
            child: Container(
              height: 14,
              width: 250,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          ),
          const SizedBox(height: 32),
          
          // Contact Options Header
          Container(
            height: 20,
            width: 120,
            margin: const EdgeInsets.only(right: 200),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
          const SizedBox(height: 16),
          
          // Contact Cards Skeleton
          _buildCardSkeleton(),
          const SizedBox(height: 32),

          // FAQs Header
          Container(
            height: 20,
            width: 240,
            margin: const EdgeInsets.only(right: 80),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
          const SizedBox(height: 16),
          
          // FAQ Items Skeleton
          _buildCardSkeleton(),
          const SizedBox(height: 12),
          _buildCardSkeleton(),
          const SizedBox(height: 12),
          _buildCardSkeleton(),
        ],
      ),
    );
  }

  Widget _buildCardSkeleton() {
    return Container(
      height: 72,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
      ),
    );
  }

  Widget _buildContactCard(BuildContext context, {required bool isDark, required IconData icon, required String title, required String subtitle, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isDark ? AppColors.darkCard : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
          ),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.primaryBlue.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(icon, color: AppColors.primaryBlue),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: GoogleFonts.poppins(
                      fontWeight: FontWeight.w600,
                      color: isDark ? Colors.white : Colors.black,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: GoogleFonts.poppins(
                      fontSize: 13,
                      color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.chevron_right,
              color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFaqItem({required bool isDark, required String question, required String answer}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
        ),
      ),
      child: ExpansionTile(
        title: Text(
          question,
          style: GoogleFonts.poppins(
            fontWeight: FontWeight.w500,
            fontSize: 14,
            color: isDark ? Colors.white : Colors.black,
          ),
        ),
        iconColor: AppColors.primaryBlue,
        collapsedIconColor: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        children: [
          Text(
            answer,
            style: GoogleFonts.poppins(
              fontSize: 13,
              height: 1.5,
              color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
            ),
          ),
        ],
      ),
    );
  }
}
