-- Cutthroat Carnivore noteskin - hit explosion / particle system.
-- On a hit the arrow shatters: armour shards tumble outward, molten debris sprays,
-- sparks streak away and embers drift up, with a flash, ki rays, dark smoke and a
-- burst of red lightning on the best judgments. Holds crackle with an energy orb.

local rnd, cos, sin, atan2, pi = math.random, math.cos, math.sin, math.atan, math.pi
local function T(name) return NOTESKIN:GetPath("_CC", name) end
local function angle(y, x) return math.atan2 and math.atan2(y, x) or atan2(y, x) end

-- Shard texture + resting offset (noteskin units, Down arrow); together they rebuild the arrow.
local SHARDS = {
	{ "Shard 01", 7.5, 18.0 },
	{ "Shard 02", -10.5, 12.0 },
	{ "Shard 03", 14.0, 4.5 },
	{ "Shard 04", -1.0, 4.0 },
	{ "Shard 05", 1.5, -10.5 },
	{ "Shard 06", -19.0, 4.0 },
	{ "Shard 07", 9.0, -23.5 },
	{ "Shard 08", -3.0, 21.5 },
	{ "Shard 09", -23.0, -6.5 },
	{ "Shard 10", 24.0, 3.0 },
	{ "Shard 11", -6.5, -17.0 },
	{ "Shard 12", 23.5, -9.0 },
}

-- How hard each judgment hits.
local TIER = {
	W1    = { shatter = 1.00, debris = 18, sparks = 12, embers = 10, lightning = true,  flash = 1.00, smoke = 0.85 },
	W2    = { shatter = 0.90, debris = 14, sparks = 10, embers = 8,  lightning = true,  flash = 0.90, smoke = 0.75 },
	W3    = { shatter = 0.70, debris = 9,  sparks = 6,  embers = 5,  lightning = false, flash = 0.65, smoke = 0.55 },
	W4    = { shatter = 0.50, debris = 5,  sparks = 3,  embers = 3,  lightning = false, flash = 0.40, smoke = 0.40 },
	W5    = { shatter = 0.40, debris = 3,  sparks = 2,  embers = 2,  lightning = false, flash = 0.30, smoke = 0.30 },
	Held  = { shatter = 0,    debris = 6,  sparks = 8,  embers = 6,  lightning = false, flash = 0.70, smoke = 0.30 },
	Mine  = { shatter = 0,    debris = 10, sparks = 10, embers = 6,  lightning = true,  flash = 0.90, smoke = 0.90, mine = true },
}
local MAX_DEBRIS, MAX_SPARKS, MAX_EMBERS = 18, 12, 10

-- Column rotation, so embers can be counter-rotated to always rise up the screen.
local ROT = { Left = 90, Down = 0, Up = 180, Right = -90, UpLeft = 135, UpRight = -135, DownLeft = 45, DownRight = -45 }
local colrot = 0
pcall(function() colrot = ROT[Var "Button"] or 0 end)

local t = Def.ActorFrame {
	InitCommand = function(self) self.cc_bright = false end,
	BrightCommand = function(self) self.cc_bright = true end,
	DimCommand = function(self) self.cc_bright = false end,
	W1Command = function(self) self:playcommand("Burst", { tier = TIER.W1, bright = self.cc_bright }) end,
	W2Command = function(self) self:playcommand("Burst", { tier = TIER.W2, bright = self.cc_bright }) end,
	W3Command = function(self) self:playcommand("Burst", { tier = TIER.W3, bright = self.cc_bright }) end,
	W4Command = function(self) self:playcommand("Burst", { tier = TIER.W4, bright = false }) end,
	W5Command = function(self) self:playcommand("Burst", { tier = TIER.W5, bright = false }) end,
	ProW1Command = function(self) self:playcommand("W1") end,
	ProW2Command = function(self) self:playcommand("W1") end,
	ProW3Command = function(self) self:playcommand("W2") end,
	ProW4Command = function(self) self:playcommand("W3") end,
	ProW5Command = function(self) self:playcommand("W4") end,
	HeldCommand = function(self) self:playcommand("Burst", { tier = TIER.Held, bright = false }) end,
	HitMineCommand = function(self) self:playcommand("Burst", { tier = TIER.Mine, bright = true }) end,
}

-- dark smoke (normal blend) - gives every hit some weight
t[#t + 1] = Def.Sprite {
	Texture = T("FX Smoke"),
	InitCommand = function(self) self:diffusealpha(0) end,
	BurstCommand = function(self, p)
		self:finishtweening():rotationz(rnd() * 360):zoom(0.55):diffusealpha(p.tier.smoke)
			:decelerate(0.5):zoom(1.0):addrotationz(40):diffusealpha(0)
	end,
}

-- hold / roll energy orb: crackles while the note is held
t[#t + 1] = Def.ActorFrame {
	InitCommand = function(self) self:diffusealpha(0) end,
	HoldingOnCommand = function(self)
		self:stoptweening():zoom(0.8):diffusealpha(1):decelerate(0.08):zoom(1)
		self:GetChild("A"):SetAllStateDelays(0.045); self:GetChild("B"):SetAllStateDelays(0.06)
	end,
	RollOnCommand = function(self)
		self:stoptweening():zoom(0.8):diffusealpha(1):decelerate(0.08):zoom(1.1)
		self:GetChild("A"):SetAllStateDelays(0.025); self:GetChild("B"):SetAllStateDelays(0.03)
	end,
	HoldingOffCommand = function(self) self:stoptweening():decelerate(0.12):zoom(1.3):diffusealpha(0) end,
	RollOffCommand = function(self) self:stoptweening():decelerate(0.12):zoom(1.3):diffusealpha(0) end,
	Def.Sprite {
		Name = "A", Texture = T("FX HoldOrb"),
		InitCommand = function(self) self:blend("BlendMode_Add"):zoom(1.15) end,
	},
	Def.Sprite {
		Name = "B", Texture = T("FX HoldOrb"),
		InitCommand = function(self)
			self:blend("BlendMode_Add"):rotationz(137):zoom(0.95):setstate(3)
				:diffuseshift():effectcolor1(1, 1, 1, 1):effectcolor2(1, 1, 1, 0.45):effectperiod(0.09)
		end,
	},
}

-- white-hot flash with an anamorphic streak
t[#t + 1] = Def.Sprite {
	Texture = T("FX Flash"),
	InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0) end,
	BurstCommand = function(self, p)
		local k = p.tier.flash * (p.bright and 1.1 or 1)
		self:finishtweening():zoom(0.55):diffusealpha(math.min(k, 1))
			:decelerate(0.16):zoom(0.95):diffusealpha(0)
	end,
}

-- ki rays
t[#t + 1] = Def.Sprite {
	Texture = T("FX Rays"),
	InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0) end,
	BurstCommand = function(self, p)
		if p.tier.mine then self:finishtweening():diffusealpha(0) return end
		self:finishtweening():rotationz(rnd() * 360):zoom(0.45):diffusealpha(0.85 * p.tier.flash)
			:decelerate(0.2):zoom(0.95):diffusealpha(0)
	end,
}

-- red lightning burst (best judgments, or any hit while the combo is lit)
t[#t + 1] = Def.Sprite {
	Texture = T("FX Lightning"),
	InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0):SetAllStateDelays(0.03) end,
	BurstCommand = function(self, p)
		if not (p.tier.lightning or p.bright) then self:finishtweening():diffusealpha(0) return end
		self:finishtweening():setstate(math.floor(rnd() * 8)):rotationz(rnd() * 360):zoom(0.8)
			:diffusealpha(1):sleep(0.05):linear(0.09):zoom(0.9):diffusealpha(0)
	end,
}

-- mine blast
t[#t + 1] = Def.Sprite {
	Texture = T("FX MineBlast"),
	InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0) end,
	BurstCommand = function(self, p)
		if not p.tier.mine then return end
		self:finishtweening():zoom(0.4):diffusealpha(1):decelerate(0.3):zoom(1.1):diffusealpha(0)
	end,
}

-- armour shards: start where they sit in the arrow, then blow apart
for i, s in ipairs(SHARDS) do
	local tex, sx, sy = s[1], s[2], s[3]
	t[#t + 1] = Def.Sprite {
		Texture = T(tex),
		InitCommand = function(self) self:xy(sx, sy):diffusealpha(0) end,
		BurstCommand = function(self, p)
			local k = p.tier.shatter
			if k <= 0 then return end
			local a = angle(sy + 0.01, sx + 0.01) + (rnd() - 0.5) * 0.7
			local d = (38 + rnd() * 32) * k
			local spin = (rnd() * 2 - 1) * 320
			local cx, cy = cos(a), sin(a)
			self:finishtweening():xy(sx, sy):rotationz(0):zoom(1):diffusealpha(1)
				:decelerate(0.24):xy(sx + cx * d * 0.75, sy + cy * d * 0.75):rotationz(spin * 0.7):zoom(0.92)
				:linear(0.2):xy(sx + cx * d, sy + cy * d):rotationz(spin):zoom(0.7):diffusealpha(0)
		end,
	}
end

-- molten debris spray
for i = 1, MAX_DEBRIS do
	t[#t + 1] = Def.Sprite {
		Texture = T("FX Debris"),
		InitCommand = function(self) self:diffusealpha(0) end,
		BurstCommand = function(self, p)
			if i > p.tier.debris then return end
			local a = rnd() * 2 * pi
			local d = (40 + rnd() * 65) * (0.6 + 0.4 * math.max(p.tier.shatter, 0.5))
			self:finishtweening():xy(cos(a) * 6, sin(a) * 6):rotationz(rnd() * 360)
				:zoom(0.5 + rnd() * 0.5):diffusealpha(1)
				:decelerate(0.3 + rnd() * 0.15):xy(cos(a) * d, sin(a) * d)
				:addrotationz((rnd() * 2 - 1) * 540):diffusealpha(0)
		end,
	}
end

-- spark streaks
for i = 1, MAX_SPARKS do
	t[#t + 1] = Def.Sprite {
		Texture = T("FX Spark"),
		InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0) end,
		BurstCommand = function(self, p)
			if i > p.tier.sparks then return end
			local a = rnd() * 2 * pi
			local d = 30 + rnd() * 55
			local z = 0.6 + rnd() * 0.6
			self:finishtweening():rotationz(a * 180 / pi):xy(cos(a) * 8, sin(a) * 8)
				:zoomx(z):zoomy(1):diffusealpha(1)
				:decelerate(0.22):xy(cos(a) * d, sin(a) * d):zoomx(z * 0.25):diffusealpha(0)
		end,
	}
end

-- embers rise up the screen whatever the column's rotation
local embers = Def.ActorFrame { InitCommand = function(self) self:rotationz(-colrot) end }
for i = 1, MAX_EMBERS do
	embers[#embers + 1] = Def.Sprite {
		Texture = T("FX Ember"),
		InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0) end,
		BurstCommand = function(self, p)
			if i > p.tier.embers then return end
			local a = rnd() * 2 * pi
			local d = 15 + rnd() * 30
			self:finishtweening():xy(cos(a) * 6, sin(a) * 6):zoom(0.6 + rnd() * 0.5):diffusealpha(1)
				:decelerate(0.3):xy(cos(a) * d, sin(a) * d - 14)
				:linear(0.35 + rnd() * 0.2):addy(-22 - rnd() * 18):diffusealpha(0)
		end,
	}
end
t[#t + 1] = embers

return t
