# mini-synth

Simple sound synthesiser using pygame and guizero

Other required modules: numpy

## Warning

If you edit the online version of this file, it may conflict with other changes in any checked-out versions.

## Development stages:

1. Make basic waveform generator with sine, triangle, sawtooth and square waves. (Done)

2. Add spaced sawtooth and pulse width control of square wave. (Done)

3. Add screen keyboard. (Done)

4. Make envelope shaper with controllable ADSR function to control tone amplitude. (Done)

5. Make variable lowpass and highpass, bandpass and bandstop filters to modify sound spectrum.

6. Add tremolo (amplitude wobble) and  vibrato (frequency wobble) to all waveforms?

7. Low frequency oscillators for modulating other parameters.

8. White and pink noise generators, random pitch and amplitude modulation.

9. Storage and recall of synth settings (patches).

10. Ring modulator, phasing, chorus, unison, reverb, resonnance filter module?

11. Melody recording and editing?

12. Spectrum analysis and display? Could be too much processing.

## Notes

When controlling the VCF from the envelope shaper, a frequency offset linked to the tone fundamental frequency
should perhaps be applied, to give the same kind of tone colour variation in all octaves.

The Elektor Formant uses exponential amplitude control in its Voltage Controlled Amplifier for the main envelope
and linear modulation for tremolo effects.

Tremolo effect may be produced in waveform generation functions by adding periodic time offsets to the
sample times arrays.

Are local objects automatically deleted on function exit?

All notes are currently the same loudness and duration. A more complicated KB interface might get around this.

The variable width waveforms have DC offsets which could be a problem in filter circuits using integrators.
Perhaps a DC blocking filter could be used or the offsets could be calculated an removed in the tone generators.

If being used as a sequencer/ pianola, how do note lengths relate to the envelope shape? Is it just the sustain
time that varies?

Can the program structure be modified to make maximum use of a processor with multiple CPU cores? (numpy is
believed to do this automatically for some functions.)

How can performance be measured?

Does the sampled waveform create noticeable pitch/period jitter on square aand sawtooth waveforms?

## Background reading:

Elektor magazine "Formant" synthesiser project book. (stored here)

## Contact:

https://en.wikibooks.org/wiki/User_talk:Unkle_Peter
