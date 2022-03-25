
######################### Global constants #########################

# These values should not be changed, except in test code.

SAMPLE_RATE = 44100

# Voice parameters

MAX_TREMOLO_RATE = 100
MAX_TREMOLO_DEPTH = 100
MAX_VIBRATO_RATE = 100
MAX_VIBRATO_DEPTH = 100
MAX_HARMONIC_BOOST = 100

# ADSR shaper constants (times in milli-second units)

MAX_ATTACK = 100
MAX_DECAY = 100
MAX_SUSTAIN = 400
MAX_RELEASE = 100
MAX_ENVELOPE_TIME = MAX_ATTACK + MAX_DECAY + MAX_SUSTAIN + MAX_RELEASE

NUM_OCTAVES = 3
LOWEST_TONE = 110