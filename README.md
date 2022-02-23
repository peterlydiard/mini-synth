# mini-synth

Simple sound synthesiser using pygame and guizero

Other required modules: numpy

Development stages:

## Development stages:

1. Make basic waveform generator with sine, triangle, sawtooth and square waves. (Done)

2. Add spaced sawtooth and pulse width control of square wave. (Done)

3. Add screen keyboard. (Done)

4 Make envelope shaper with controllable ADSR function to control tone amplitude.

5. Make variable low-pass and high-pass filter to modify sound spectrum.

6. Add tremolo (amplitude wobble) and  vibrato (frequency wobble) to all waveforms?

7. Low frequency oscillators for modulating other parameters.

8. White and pink noise generators, random pitch and amplitude modulation.

9. Storage and recall of synth settings (patches).

10. Ring modulator, phasing, chorus, unison, reverb, resonnance filter module?

11. Melody recording and editing?

12. Spectrum analysis and display? Could be too much processing.

## Notes

Tremolo effect may be produced in waveform generation functions by adding periodic time offsets to the
sample times arrays.

Are local objects automatically deleted on function exit?

All notes are currently the same loudness and duration. A more complicated KB interface might get around this.

The variable width waveforms have DC offsets which could be a problem in filter circuits using integrators.

If being used as a sequencer/ pianola, how do note lengths relate to the envelope shape? Is it just the sustain
time that varies?

## Contact:

https://en.wikibooks.org/wiki/User_talk:Unkle_Peter

## Background reading:

Elektor magazine "Formant" synthesiser project book. (stored here)
