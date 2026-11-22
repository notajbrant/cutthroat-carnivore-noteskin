-- Reactor orb with glowing fractures, spinning blade ring and a beat heartbeat.
return Def.ActorFrame {
	Def.Sprite {
		Texture = NOTESKIN:GetPath("_CC", "Mine Spokes"),
		InitCommand = function(self)
			self:effectclock("beat"):spin():effectmagnitude(0, 0, -90)
		end,
	},
	Def.Sprite {
		Texture = NOTESKIN:GetPath("_CC", "Mine Base"),
	},
	Def.Sprite {
		Texture = NOTESKIN:GetPath("_CC", "Mine Glow"),
		InitCommand = function(self)
			self:blend("BlendMode_Add"):effectclock("beat")
				:diffuseramp():effectcolor1(1, 1, 1, 0.15):effectcolor2(1, 1, 1, 1)
		end,
	},
}
