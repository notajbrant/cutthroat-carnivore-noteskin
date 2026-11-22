-- Cutthroat Carnivore "Voltage" note (@VARIANT@).
-- Three cues so every note reads at a glance, colour-blind or not:
--   * body colour + fill pattern + face symbol = the rhythm (4th, 8th, 16th ...)
--   * rim + halo colour = the direction (left magenta, down cyan, up white, right orange)
--   * the face symbol strikes on every beat (4 frames per beat)
local COL = {
	Left = { 0.88, 0.32, 1.0 }, Down = { 0.12, 0.86, 1.0 }, Up = { 1, 1, 1 }, Right = { 1.0, 0.55, 0.08 },
	UpLeft = { 0.88, 0.32, 1.0 }, UpRight = { 1.0, 0.55, 0.08 },
	DownLeft = { 0.12, 0.86, 1.0 }, DownRight = { 1, 1, 1 }, Center = { 1.0, 0.9, 0.2 },
}
local c = { 1, 1, 1 }
pcall(function() c = COL[Var "Button"] or c end)

return Def.ActorFrame {
	Def.Sprite {
		Texture = NOTESKIN:GetPath("_CC", "Tap Note"),
		Frames = Sprite.LinearFrames(4, 1),
	},
	Def.Sprite {
		Texture = NOTESKIN:GetPath("_CC", "Tap Rim"),
		Frames = Sprite.LinearFrames(4, 1),
		InitCommand = function(self) self:diffuse(c[1], c[2], c[3], 1) end,
	},
}
