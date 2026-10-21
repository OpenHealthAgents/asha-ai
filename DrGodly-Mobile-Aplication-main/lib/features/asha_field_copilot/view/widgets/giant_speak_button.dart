import 'package:flutter/material.dart';

class GiantSpeakButtonWidget extends StatefulWidget {
  final bool isListening;
  final String languageCode;
  final VoidCallback onStartListening;
  final VoidCallback onStopListening;

  const GiantSpeakButtonWidget({
    super.key,
    required this.isListening,
    this.languageCode = 'hi',
    required this.onStartListening,
    required this.onStopListening,
  });

  @override
  State<GiantSpeakButtonWidget> createState() => _GiantSpeakButtonWidgetState();
}

class _GiantSpeakButtonWidgetState extends State<GiantSpeakButtonWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _animController;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    )..repeat(reverse: true);

    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.12).animate(
      CurvedAnimation(parent: _animController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  String _getLocalizedButtonText() {
    switch (widget.languageCode.substring(0, 2).toLowerCase()) {
      case 'or':
        return widget.isListening ? 'ଶୁଣୁଛି... ବନ୍ଦ କରିବାକୁ ଦବାନ୍ତୁ' : 'କହିବା ପାଇଁ ଏଠାରେ ଦବାନ୍ତୁ';
      case 'te':
        return widget.isListening ? 'వింటున్నాను... ఆపడానికి నొక్కండి' : 'మాట్లాడటానికి ఇక్కడ నొక్కండి';
      case 'ta':
        return widget.isListening ? 'கேட்கிறது... நிறுத்த அழுத்தவும்' : 'பேச இங்கு தொடவும்';
      case 'bn':
        return widget.isListening ? 'শুনছি... থামাতে চাপুন' : 'কথা বলতে এখানে চাপুন';
      case 'mr':
        return widget.isListening ? 'ऐकत आहे... थांबवण्यासाठी दाबा' : 'बोलण्यासाठी येथे दाबा';
      case 'hi':
      default:
        return widget.isListening ? 'सुन रहा हूँ... रोकने के लिए छुएं' : 'बातचीत शुरू करने के लिए दबाएं';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        GestureDetector(
          onTap: () {
            if (widget.isListening) {
              widget.onStopListening();
            } else {
              widget.onStartListening();
            }
          },
          child: AnimatedBuilder(
            animation: _scaleAnimation,
            builder: (context, child) {
              final scale = widget.isListening ? _scaleAnimation.value : 1.0;
              return Transform.scale(
                scale: scale,
                child: Container(
                  width: 110,
                  height: 110,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: widget.isListening
                          ? [const Color(0xFFEF4444), const Color(0xFFDC2626)]
                          : [const Color(0xFF2563EB), const Color(0xFF1D4ED8)],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: (widget.isListening
                                ? const Color(0xFFEF4444)
                                : const Color(0xFF2563EB))
                            .withValues(alpha: widget.isListening ? 0.45 : 0.3),
                        blurRadius: widget.isListening ? 26 : 14,
                        spreadRadius: widget.isListening ? 4 : 0,
                        offset: const Offset(0, 6),
                      ),
                    ],
                  ),
                  child: Center(
                    child: Icon(
                      widget.isListening ? Icons.stop_rounded : Icons.mic_rounded,
                      color: Colors.white,
                      size: 52,
                    ),
                  ),
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          decoration: BoxDecoration(
            color: widget.isListening
                ? const Color(0xFFFEE2E2)
                : const Color(0xFFEFF6FF),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: widget.isListening
                  ? const Color(0xFFFCA5A5)
                  : const Color(0xFFBFDBFE),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (widget.isListening) ...[
                const SizedBox(
                  width: 10,
                  height: 10,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Color(0xFFDC2626)),
                  ),
                ),
                const SizedBox(width: 8),
              ],
              Text(
                _getLocalizedButtonText(),
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                  color: widget.isListening
                      ? const Color(0xFF991B1B)
                      : const Color(0xFF1E40AF),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
