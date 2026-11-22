# Build it yourself

Needs Python 3 with numpy, scipy, pillow and matplotlib
(`pip install numpy scipy pillow matplotlib`).

From `source/`:

```
cd scripts
CC_ARROW=v4 python3 fx_v2.py ../out/art notes receptor aura fx lightning mine
CC_ARROW=v4 CC_SHARDS=28 CC_SHARD_COL=0.62,0.58,0.56 python3 fx_v2.py ../out/art shards
python3 beam_v4.py ../out/art
python3 make_explosion_v4.py ../out/art "../skin-lua/inferno/Down Explosion.lua"
```

Then copy `skin-lua/inferno/*.lua` + everything in `out/art` (rename
`_CC Tap Note Quant ...` → `_CC Tap Note ...`, `_CC Receptor Aura` → `_CC Aura`) into a
folder in `NoteSkins/dance/`, with a `metrics.ini` like the one in the builds.
`assemble.py` does all of that automatically (paths at the top).

Tweak ideas: colours are the `QUANT` list in `fx_v2.py`; the beat-bolt shape is
`BOLT` in `arrow_v4.py`; burst strength per judgment is the `TIER` table in
`make_explosion_v4.py`.

## Test lab
`test-lab/` is an autoplay theme + chart covering every note colour, holds, rolls,
mines and lifts. Point a portable ITGmania copy at it to screenshot every build.
