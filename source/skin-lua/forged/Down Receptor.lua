-- Receptor: lacquered frame, beat-synced edge flash, visor that ignites on press,
-- and a ki aura that flares while the panel is held.
local sheet = NOTESKIN:GetPath("_CC", "Receptor")

return Def.ActorFrame {
	-- ki aura (behind the frame)
	Def.Sprite {
		Texture = NOTESKIN:GetPath("_CC", "Aura"),
		InitCommand = function(self)
			self:blend("BlendMode_Add"):diffusealpha(0):SetAllStateDelays(0.045)
		end,
		PressCommand = function(self)
			self:stoptweening():zoom(0.85):diffusealpha(0.9):decelerate(0.1):zoom(1):diffusealpha(1)
		end,
		LiftCommand = function(self)
			self:stoptweening():decelerate(0.18):zoom(1.1):diffusealpha(0)
		end,
		NoneCommand = function(self) self:stoptweening():diffusealpha(0) end,
	},
	-- frame
	Def.Sprite {
		Texture = sheet,
		Frame0000 = 0, Delay0000 = 1,
		PressCommand = function(self) self:stoptweening():zoom(0.9):decelerate(0.12):zoom(1) end,
		LiftCommand = function(self) self:stoptweening():decelerate(0.12):zoom(1) end,
		NoneCommand = function(self) self:stoptweening():zoom(1) end,
	},
	-- beat flash: strikes on every beat and decays over the first quarter, read
	-- straight from the song position so it stays locked through BPM changes
	Def.ActorFrame {
		InitCommand = function(self)
			local flash
			self:SetUpdateFunction(function(af)
				flash = flash or af:GetChild("Flash")
				if not flash then return end
				local beat = 0
				local ok, pos = pcall(function() return GAMESTATE:GetSongPosition() end)
				if ok and pos and pos.GetSongBeatVisible then
					beat = pos:GetSongBeatVisible()
				else
					beat = GAMESTATE:GetSongBeat()
				end
				local f = beat - math.floor(beat)
				local a = 1 - f * 3.2
				if a < 0 then a = 0 end
				flash:diffusealpha(a * a)
			end)
		end,
		Def.Sprite {
			Name = "Flash",
			Texture = sheet,
			Frame0000 = 1, Delay0000 = 1,
			InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0) end,
		},
	},
	-- visor ignition on press
	Def.Sprite {
		Texture = sheet,
		Frame0000 = 2, Delay0000 = 1,
		InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0) end,
		PressCommand = function(self)
			self:stoptweening():diffusealpha(1):zoom(1.08):decelerate(0.1):zoom(1)
		end,
		LiftCommand = function(self) self:stoptweening():decelerate(0.15):diffusealpha(0) end,
		NoneCommand = function(self) self:stoptweening():diffusealpha(0) end,
	},
}
