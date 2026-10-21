import 'package:flutter/material.dart';

class PocVitalsBarWidget extends StatelessWidget {
  final Map<String, dynamic> vitals;
  final VoidCallback onScanBle;

  const PocVitalsBarWidget({
    super.key,
    required this.vitals,
    required this.onScanBle,
  });

  @override
  Widget build(BuildContext context) {
    final systolic = vitals['systolic_bp'] as num?;
    final diastolic = vitals['diastolic_bp'] as num?;
    final spo2 = vitals['spo2'] as num?;
    final hb = vitals['hemoglobin'] as num?;
    final temp = vitals['temperature_c'] as num?;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E8F0)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(5),
                    decoration: BoxDecoration(
                      color: const Color(0xFFEFF6FF),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.bluetooth_connected, color: Color(0xFF2563EB), size: 18),
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'Point-of-Care Kit Readings',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF1E293B),
                    ),
                  ),
                ],
              ),
              InkWell(
                onTap: onScanBle,
                borderRadius: BorderRadius.circular(8),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.refresh, size: 14, color: Color(0xFF475569)),
                      SizedBox(width: 4),
                      Text(
                        'Pair Device',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Color(0xFF475569)),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              // BP
              Expanded(
                child: _buildVitalPill(
                  label: 'BP (mmHg)',
                  value: systolic != null ? '${systolic.toInt()}/${diastolic?.toInt()}' : '-- / --',
                  isWarning: (systolic != null && systolic >= 140) || (diastolic != null && diastolic >= 90),
                  icon: Icons.favorite,
                ),
              ),
              const SizedBox(width: 8),
              // SpO2
              Expanded(
                child: _buildVitalPill(
                  label: 'SpO2 (%)',
                  value: spo2 != null ? '${spo2.toInt()}%' : '-- %',
                  isWarning: spo2 != null && spo2 < 92,
                  icon: Icons.air,
                ),
              ),
              const SizedBox(width: 8),
              // Hemoglobin
              Expanded(
                child: _buildVitalPill(
                  label: 'Hb (g/dL)',
                  value: hb != null ? '$hb' : '--',
                  isWarning: hb != null && hb < 7.0,
                  icon: Icons.water_drop,
                ),
              ),
              const SizedBox(width: 8),
              // Temp
              Expanded(
                child: _buildVitalPill(
                  label: 'Temp (°C)',
                  value: temp != null ? '$temp°' : '--°',
                  isWarning: temp != null && temp >= 38.5,
                  icon: Icons.thermostat,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildVitalPill({
    required String label,
    required String value,
    required bool isWarning,
    required IconData icon,
  }) {
    final bgColor = isWarning ? const Color(0xFFFEE2E2) : const Color(0xFFF8FAFC);
    final textColor = isWarning ? const Color(0xFFDC2626) : const Color(0xFF0F172A);

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isWarning ? const Color(0xFFF87171) : const Color(0xFFE2E8F0),
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 12, color: isWarning ? const Color(0xFFDC2626) : Colors.grey[600]),
              const SizedBox(width: 3),
              Flexible(
                child: Text(
                  label,
                  style: TextStyle(
                    fontSize: 9,
                    color: isWarning ? const Color(0xFF991B1B) : Colors.grey[600],
                    fontWeight: FontWeight.w600,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w800,
              color: textColor,
            ),
          ),
        ],
      ),
    );
  }
}
