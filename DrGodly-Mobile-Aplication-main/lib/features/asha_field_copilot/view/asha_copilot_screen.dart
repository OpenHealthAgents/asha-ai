import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../viewmodel/asha_copilot_viewmodel.dart';
import 'widgets/giant_speak_button.dart';
import 'widgets/poc_vitals_bar.dart';
import 'widgets/traffic_light_card.dart';
import 'widgets/household_selector_sheet.dart';
import '../models/asha_triage_card.dart';

class AshaCopilotScreen extends StatefulWidget {
  const AshaCopilotScreen({super.key});

  @override
  State<AshaCopilotScreen> createState() => _AshaCopilotScreenState();
}

class _AshaCopilotScreenState extends State<AshaCopilotScreen> {
  bool _isListening = false;

  final List<Map<String, String>> _languages = [
    {'code': 'hi', 'label': 'हिन्दी'},
    {'code': 'or', 'label': 'ଓଡ଼ିଆ'},
    {'code': 'te', 'label': 'తెలుగు'},
    {'code': 'ta', 'label': 'தமிழ்'},
    {'code': 'bn', 'label': 'বাংলা'},
  ];

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AshaCopilotViewModel(),
      child: Consumer<AshaCopilotViewModel>(
        builder: (context, vm, child) {
          final hh = vm.selectedHousehold;
          final beneficiary = vm.selectedBeneficiary;

          return Scaffold(
            backgroundColor: const Color(0xFFF8FAFC),
            appBar: AppBar(
              backgroundColor: const Color(0xFF1E3A8A),
              elevation: 0,
              title: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.health_and_safety_rounded, color: Colors.white, size: 22),
                  ),
                  const SizedBox(width: 10),
                  const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'ASHA Field Copilot',
                        style: TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w900,
                          color: Colors.white,
                        ),
                      ),
                      Text(
                        'Offline Village Visit & Triage',
                        style: TextStyle(fontSize: 11, color: Color(0xFF93C5FD)),
                      ),
                    ],
                  ),
                ],
              ),
              actions: [
                // Offline Outbox Badge
                Center(
                  child: Container(
                    margin: const EdgeInsets.only(right: 14),
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: vm.pendingOutboxCount > 0
                          ? const Color(0xFFD97706)
                          : const Color(0xFF16A34A),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          vm.pendingOutboxCount > 0 ? Icons.cloud_off : Icons.cloud_done,
                          color: Colors.white,
                          size: 14,
                        ),
                        const SizedBox(width: 5),
                        Text(
                          vm.pendingOutboxCount > 0
                              ? '${vm.pendingOutboxCount} Queued'
                              : 'Online Sync',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            body: vm.isLoading
                ? const Center(child: CircularProgressIndicator())
                : SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // 1. Language Selector Pills
                        _buildLanguageSelector(vm),
                        const SizedBox(height: 12),

                        // 2. Active Household & Beneficiary Card
                        _buildHouseholdCard(context, vm, hh, beneficiary),
                        const SizedBox(height: 14),

                        // 3. Point-of-Care Vitals Bar (Bluetooth Device Stream)
                        PocVitalsBarWidget(
                          vitals: vm.currentVitals,
                          onScanBle: () {
                            // Demo simulation of BLE Cuff connection
                            vm.injectPocReading('BP_CUFF', {
                              'systolic_bp': 148.0,
                              'diastolic_bp': 96.0,
                              'spo2': 94.0,
                              'hemoglobin': 6.6,
                              'temperature_c': 37.2,
                            });
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Connected to BLE Field Kit: Vitals Ingested!'),
                                duration: Duration(seconds: 2),
                              ),
                            );
                          },
                        ),
                        const SizedBox(height: 20),

                        // 4. Voice-First Hero Action: GIANT SPEAK BUTTON
                        Center(
                          child: GiantSpeakButtonWidget(
                            isListening: _isListening,
                            languageCode: vm.selectedLanguageCode,
                            onStartListening: () async {
                              setState(() => _isListening = true);
                              await vm.startVoiceVisit();
                            },
                            onStopListening: () async {
                              setState(() => _isListening = false);
                              await vm.stopVoiceVisit();
                            },
                          ),
                        ),
                        const SizedBox(height: 16),

                        // 5. Real-time Transcript & Natural Language Entity Extraction
                        if (vm.currentTranscript.isNotEmpty) ...[
                          _buildTranscriptCard(vm),
                          const SizedBox(height: 14),
                        ],

                        // 6. TRAFFIC LIGHT TRIAGE CARDS (Red / Amber / Green)
                        if (vm.triageCards.isNotEmpty) ...[
                          const Row(
                            children: [
                              Icon(Icons.traffic_rounded, color: Color(0xFF0F172A), size: 20),
                              SizedBox(width: 8),
                              Text(
                                'AI Visit Triage & Guidelines',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w800,
                                  color: Color(0xFF0F172A),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          ...vm.triageCards.map((card) {
                            return TrafficLightCardWidget(
                              card: card,
                              isEscalated: vm.isEscalated,
                              onPrimaryAction: () {
                                if (card.light == TriageTrafficLight.red) {
                                  vm.escalateToPhc();
                                  _showEscalationDialog(context, vm);
                                } else if (card.light == TriageTrafficLight.green) {
                                  _showAudioPlayingSnackBar(context, card);
                                } else {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('Care gaps recorded on VHSND Due List!'),
                                    ),
                                  );
                                }
                              },
                            );
                          }),
                        ],
                        const SizedBox(height: 30),
                      ],
                    ),
                  ),
          );
        },
      ),
    );
  }

  Widget _buildLanguageSelector(AshaCopilotViewModel vm) {
    return SizedBox(
      height: 36,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: _languages.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final lang = _languages[index];
          final isSelected = lang['code'] == vm.selectedLanguageCode;

          return InkWell(
            onTap: () => vm.setLanguage(lang['code']!),
            borderRadius: BorderRadius.circular(18),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: isSelected ? const Color(0xFF1E3A8A) : Colors.white,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: isSelected ? const Color(0xFF1E3A8A) : const Color(0xFFCBD5E1),
                ),
              ),
              child: Text(
                lang['label']!,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: isSelected ? Colors.white : const Color(0xFF334155),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildHouseholdCard(
    BuildContext context,
    AshaCopilotViewModel vm,
    dynamic hh,
    dynamic beneficiary,
  ) {
    if (hh == null) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.home_work_rounded, color: Color(0xFF2563EB), size: 22),
                  const SizedBox(width: 8),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        hh.headName,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF0F172A),
                        ),
                      ),
                      Text(
                        '${hh.wardNumber} • LGD ${hh.villageLgdCode}',
                        style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                      ),
                    ],
                  ),
                ],
              ),
              TextButton.icon(
                onPressed: () {
                  showModalBottomSheet(
                    context: context,
                    isScrollControlled: true,
                    shape: const RoundedRectangleBorder(
                      borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                    ),
                    builder: (_) => HouseholdSelectorSheet(
                      households: vm.households,
                      selectedHousehold: vm.selectedHousehold,
                      onSelect: (newHh) => vm.selectHousehold(newHh),
                    ),
                  );
                },
                icon: const Icon(Icons.swap_horiz, size: 16),
                label: const Text('Change', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
              ),
            ],
          ),
          const Divider(height: 20, color: Color(0xFFF1F5F9)),
          // Beneficiary Switcher Chips
          Row(
            children: [
              const Text(
                'Beneficiary: ',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF64748B)),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Wrap(
                  spacing: 6,
                  children: (hh.members as List<dynamic>).map((m) {
                    final isSelected = m.id == beneficiary?.id;
                    return ChoiceChip(
                      label: Text(
                        '${m.name} ${m.isMaternal ? "(ANC)" : (m.isChild ? "(Child)" : "")}',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: isSelected ? Colors.white : const Color(0xFF1E293B),
                        ),
                      ),
                      selected: isSelected,
                      selectedColor: const Color(0xFF2563EB),
                      backgroundColor: const Color(0xFFF1F5F9),
                      onSelected: (_) => vm.selectBeneficiary(m),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTranscriptCard(AshaCopilotViewModel vm) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF0FDF4),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFBBF7D0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.mic, color: Color(0xFF16A34A), size: 18),
              SizedBox(width: 6),
              Text(
                'Transcribed Field Dialogue (Sarvam ASR)',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF166534),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            vm.currentTranscript,
            style: const TextStyle(
              fontSize: 14,
              fontStyle: FontStyle.italic,
              color: Color(0xFF14532D),
            ),
          ),
        ],
      ),
    );
  }

  void _showEscalationDialog(BuildContext context, AshaCopilotViewModel vm) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Row(
          children: [
            Icon(Icons.warning, color: Color(0xFFDC2626), size: 28),
            SizedBox(width: 10),
            Text('Urgent PHC Escalation', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'High-risk pregnancy protocol triggered.',
              style: TextStyle(fontWeight: FontWeight.w700, color: Color(0xFF991B1B)),
            ),
            const SizedBox(height: 8),
            Text(
              'Beneficiary: ${vm.selectedBeneficiary?.name}\n'
              'Blood Pressure: ${vm.currentVitals['systolic_bp']?.toInt()}/${vm.currentVitals['diastolic_bp']?.toInt()} mmHg\n'
              'Hemoglobin: ${vm.currentVitals['hemoglobin']} g/dL\n'
              'Dispatched to: Rampur Primary Health Centre Medical Officer\n'
              'Emergency Ambulance: Dialing 108...',
              style: const TextStyle(fontSize: 13, height: 1.5),
            ),
          ],
        ),
        actions: [
          ElevatedButton.icon(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFDC2626),
              foregroundColor: Colors.white,
            ),
            icon: const Icon(Icons.check),
            label: const Text('Confirmed'),
          ),
        ],
      ),
    );
  }

  void _showAudioPlayingSnackBar(BuildContext context, AshaTriageCard card) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        backgroundColor: const Color(0xFF166534),
        duration: const Duration(seconds: 4),
        content: Row(
          children: [
            const Icon(Icons.volume_up, color: Colors.white),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                'Playing: ${card.audioTitle ?? "Health Guide"}',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
