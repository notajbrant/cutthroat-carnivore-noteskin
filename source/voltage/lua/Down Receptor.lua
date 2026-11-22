-- Cutthroat Carnivore "Voltage" receptor (@VARIANT@).
-- BPM indicator: a lightning bolt strikes inside every receptor on each beat and
-- decays before the next one, so the flash rate IS the song's BPM. Beat 1 of every
-- measure strikes harder. Read straight from the song position, so it stays locked
-- through BPM changes, stops and warps.
local sheet = NOTESKIN:GetPath("_CC", "Receptor")
local ROT = { Left = 90, Down = 0, Up = 180, Right = -90, UpLeft = 135, UpRight = -135,
	DownLeft = 45, DownRight = -45, Center = 0 }
local colrot = 0
pcall(function() colrot = ROT[Var "Button"] or 0 end)
-- receptor outline in the column's direction colour (matches the notes' rims)
local COL = {
	Left = { 0.88, 0.32, 1.0 }, Down = { 0.12, 0.86, 1.0 }, Up = { 1, 1, 1 }, Right = { 1.0, 0.55, 0.08 },
	UpLeft = { 0.88, 0.32, 1.0 }, UpRight = { 1.0, 0.55, 0.08 },
	DownLeft = { 0.12, 0.86, 1.0 }, DownRight = { 1, 1, 1 }, Center = { 1.0, 0.9, 0.2 },
}
local dc = { 1, 1, 1 }
pcall(function() dc = COL[Var "Button"] or dc end)

local function song_beat()
	local ok, pos = pcall(function() return GAMESTATE:GetSongPosition() end)
	if ok and pos and pos.GetSongBeatVisible then return pos:GetSongBeatVisible() end
	return GAMESTATE:GetSongBeat()
end

return Def.ActorFrame {
	-- crackling aura while the panel is held
	Def.Sprite {
		Texture = NOTESKIN:GetPath("_CC", "Aura"),
		InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0):SetAllStateDelays(0.04) end,
		PressCommand = function(self) self:stoptweening():zoom(0.85):diffusealpha(0.95):decelerate(0.08):zoom(1) end,
		LiftCommand = function(self) self:stoptweening():decelerate(0.16):zoom(1.1):diffusealpha(0) end,
		NoneCommand = function(self) self:stoptweening():diffusealpha(0) end,
	},
	-- receptor frame
	Def.Sprite {
		Texture = sheet, Frame0000 = 0, Delay0000 = 1,
		InitCommand = function(self) self:diffuse(dc[1], dc[2], dc[3], 1) end,
		PressCommand = function(self) self:stoptweening():zoom(0.9):decelerate(0.1):zoom(1) end,
		LiftCommand = function(self) self:stoptweening():decelerate(0.1):zoom(1) end,
		NoneCommand = function(self) self:stoptweening():zoom(1) end,
	},
	-- beat indicator
	Def.ActorFrame {
		InitCommand = function(self)
			local rim, bolt, last, peak = nil, nil, nil, 1
			self:SetUpdateFunction(function(af)
				rim = rim or af:GetChild("Rim")
				bolt = bolt or af:GetChild("Bolt")
				if not (rim and bolt) then return end
				local beat = song_beat()
				local b = math.floor(beat)
				if b ~= last then
					last = b
					peak = (b % 4 == 0) and 1.18 or 1.0
					bolt:setstate(math.random(0, 3))
					bolt:rotationz(-colrot + math.random(-9, 9))
				end
				local a = 1 - (beat - b) * 2.4
				if a < 0 then a = 0 end
				a = a * a
				rim:diffusealpha(math.min(1, a * peak))
				bolt:diffusealpha(0.14 + 0.86 * math.min(1, a * 1.2))
				bolt:zoom((0.72 + 0.16 * a) * peak)
			end)
		end,
		Def.Sprite {
			Name = "Rim", Texture = sheet, Frame0000 = 1, Delay0000 = 1,
			InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0) end,
		},
		Def.Sprite {
			Name = "Bolt", Texture = NOTESKIN:GetPath("_CC", "Bolt"),
			InitCommand = function(self)
				self:blend("BlendMode_Add"):animate(false):setstate(0):diffusealpha(0):rotationz(-colrot)
			end,
		},
	},
	-- press flash
	Def.Sprite {
		Texture = sheet, Frame0000 = 2, Delay0000 = 1,
		InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0) end,
		PressCommand = function(self) self:stoptweening():diffusealpha(1):zoom(1.06):decelerate(0.1):zoom(1) end,
		LiftCommand = function(self) self:stoptweening():decelerate(0.14):diffusealpha(0) end,
		NoneCommand = function(self) self:stoptweening():diffusealpha(0) end,
	},
}
