-- Armoured arrow with a lightning-filled face. 4 frames per beat: the bolt strikes
-- on the beat and decays, so every note flashes in time with the song's BPM.
return Def.Sprite {
	Texture = NOTESKIN:GetPath("_CC", "Tap Note"),
	Frames = Sprite.LinearFrames(4, 1),
}
