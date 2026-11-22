import os, shutil, sys
import sys
ART = sys.argv[1] if len(sys.argv) > 1 else 'build/art2'; SRC = sys.argv[2] if len(sys.argv) > 2 else 'skin/common'; DST = 'build/NoteSkins/dance'; PREFIX = sys.argv[3] if len(sys.argv) > 3 else 'cutthroat-carnivore'
METRICS = r'''# Cutthroat Carnivore noteskin - original art and code by Cutthroat Carnivore (Anthony Brant).
[Global]
FallbackNoteSkin=common

[NoteDisplay]
# Notes animate on the song's beat: 4 frames per beat, all notes in sync,
# so the lightning in every arrow strikes on the beat.
AnimationIsBeatBased=1
TapNoteAnimationLength=1
TapLiftAnimationLength=1
TapFakeAnimationLength=1
TapMineAnimationLength=1
HoldHeadAnimationLength=1
RollHeadAnimationLength=1
HoldBodyAnimationLength=1
RollBodyAnimationLength=1
HoldBottomCapAnimationLength=1
RollBottomCapAnimationLength=1
HoldTopCapAnimationLength=1
RollTopCapAnimationLength=1
HoldBodyAnimationIsVivid=0
RollBodyAnimationIsVivid=0
TapNoteAnimationIsVivid=0
TapLiftAnimationIsVivid=0
TapFakeAnimationIsVivid=0
HoldHeadAnimationIsVivid=0
RollHeadAnimationIsVivid=0

__COLOR__

DrawHoldHeadForTapsOnSameRow=0
DrawRollHeadForTapsOnSameRow=0
TapHoldRollOnRowMeansHold=1
HoldHeadIsAboveWavyParts=1
HoldTailIsAboveWavyParts=1
StartDrawingHoldBodyOffsetFromHead=0
StopDrawingHoldBodyOffsetFromTail=0
HoldLetGoGrayPercent=0.35
ReverseDrawOrder=1101
FlipHeadAndTailWhenReverse=1
FlipHoldBodyWhenReverse=1
TopHoldAnchorWhenReverse=1
'''
def color_block(kind, count):
    lines = []
    for part in ('TapNote', 'TapFake', 'TapLift', 'HoldHead', 'RollHead'):
        lines += [f'{part}NoteColorType={kind}', f'{part}NoteColorCount={count}',
                  f'{part}NoteColorTextureCoordSpacingX=0', f'{part}NoteColorTextureCoordSpacingY=0.0625']
    return '\n'.join(lines)
README = '''CUTTHROAT CARNIVORE NOTESKIN  ({variant})
Official noteskin of the Cutthroat Carnivore brand.

- Sith-armour arrows with a lightning-filled face that strikes on every beat
- Hits shatter the arrow: armour shards, molten debris, sparks, embers,
  flash, ki rays, smoke, and red lightning on the best judgments
- Lightsaber holds, force-lightning rolls, reactor-orb mines
- Receptors flash on the beat and flare a ki aura when you step

{colors}

All art and code are original. Free to use, share, edit and remix - just let
Cutthroat Carnivore know what you made so he can play it too.
Built for ITGmania (Simply Love / Cutthroat Carnivore theme); uses the standard
StepMania 5 noteskin format with FallbackNoteSkin=common.
'''
SKINS = {
    PREFIX: ('Quant', 'Denominator', 9,
        'Arrow colours by rhythm: 4th red, 8th blue, 12th purple, 16th gold,\n24th pink, 32nd orange, 48th cyan, 64th green, 192nd steel.'),
    PREFIX + '-cycle': ('Cycle', 'Progress', 12,
        'Arrow colours cycle through the beat (like the "cycle" skins).'),
}
for name, (pal, kind, count, colors) in SKINS.items():
    d = f'{DST}/{name}'
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for f in os.listdir(SRC): shutil.copy(f'{SRC}/{f}', f'{d}/{f}')
    for f in os.listdir(ART):
        if f.endswith('.lua') or ('FX Ring' in f and 'inferno' not in PREFIX): continue
        if ' Quant ' in f or ' Cycle ' in f:
            if f' {pal} ' not in f: continue
            g = f.replace(f' {pal} ', ' ')
        elif f.startswith('_CC Receptor Aura'):
            g = f.replace('_CC Receptor Aura', '_CC Aura')
        else:
            g = f
        shutil.copy(f'{ART}/{f}', f'{d}/{g}')
    open(f'{d}/metrics.ini', 'w').write(METRICS.replace('__COLOR__', color_block(kind, count)))
    open(f'{d}/README.txt', 'w').write(README.format(variant='Rhythm colours' if pal == 'Quant' else 'Cycle colours', colors=colors))
    print(name, len(os.listdir(d)), 'files')
