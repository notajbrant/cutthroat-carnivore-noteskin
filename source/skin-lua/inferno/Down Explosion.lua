-- Cutthroat Carnivore noteskin "Inferno" - hit explosion / particle system.
-- Each hit shatters the arrow into iron fragments that blast outward, tumble and fall,
-- with a debris storm, spark streaks, rising embers, flash, ki rays, smoke and red
-- lightning. Three burst slots per column rotate so fast streams stack shatters
-- instead of cutting the previous one short. Holds charge a hyper-beam energy ball.

local rnd, cos, sin, pi, floor = math.random, math.cos, math.sin, math.pi, math.floor
local function T(name) return NOTESKIN:GetPath("_CC", name) end
local function atan2(y, x) return math.atan2(y, x) end

local SHARDS = {
	{ "Shard 01", 6.5, 17.5 },
	{ "Shard 02", -13.5, 13.0 },
	{ "Shard 03", 14.0, 3.0 },
	{ "Shard 04", -8.0, 6.5 },
	{ "Shard 05", -1.0, 19.0 },
	{ "Shard 06", 7.0, 5.5 },
	{ "Shard 07", 17.5, 10.0 },
	{ "Shard 08", 3.5, -8.5 },
	{ "Shard 09", -19.0, 6.0 },
	{ "Shard 10", 0.0, 4.5 },
	{ "Shard 11", -3.5, 26.5 },
	{ "Shard 12", -4.0, -9.5 },
	{ "Shard 13", 23.0, 1.5 },
	{ "Shard 14", 1.5, 12.0 },
	{ "Shard 15", 10.0, -25.0 },
	{ "Shard 16", -2.0, -18.0 },
	{ "Shard 17", -23.5, -8.5 },
	{ "Shard 18", 2.5, -3.0 },
	{ "Shard 19", -7.5, 0.0 },
	{ "Shard 20", -19.5, 0.0 },
	{ "Shard 21", -9.5, -23.0 },
	{ "Shard 22", 23.0, -8.5 },
	{ "Shard 23", 4.5, -18.0 },
	{ "Shard 24", 12.5, 15.0 },
	{ "Shard 25", -26.5, -1.0 },
	{ "Shard 26", -5.0, 13.5 },
	{ "Shard 27", -9.0, 20.0 },
	{ "Shard 28", 4.5, 26.0 },
}

local TIER = {
	W1   = { shatter = 1.00, debris = 26, sparks = 14, embers = 12, lightning = true,  flash = 1.00, smoke = 0.95 },
	W2   = { shatter = 0.92, debris = 22, sparks = 12, embers = 10, lightning = true,  flash = 0.90, smoke = 0.85 },
	W3   = { shatter = 0.75, debris = 14, sparks = 8,  embers = 6,  lightning = false, flash = 0.65, smoke = 0.65 },
	W4   = { shatter = 0.55, debris = 8,  sparks = 4,  embers = 3,  lightning = false, flash = 0.40, smoke = 0.45 },
	W5   = { shatter = 0.45, debris = 5,  sparks = 2,  embers = 2,  lightning = false, flash = 0.30, smoke = 0.35 },
	Held = { shatter = 0,    debris = 10, sparks = 12, embers = 8,  lightning = true,  flash = 0.85, smoke = 0.40 },
	Mine = { shatter = 0,    debris = 16, sparks = 12, embers = 6,  lightning = true,  flash = 0.90, smoke = 1.00, mine = true },
}
local MAX_DEBRIS, MAX_SPARKS, MAX_EMBERS, SLOTS = 26, 14, 12, 3

local ROT = { Left = 90, Down = 0, Up = 180, Right = -90, UpLeft = 135, UpRight = -135, DownLeft = 45, DownRight = -45 }
local colrot = 0
pcall(function() colrot = ROT[Var "Button"] or 0 end)
local cr, sr = cos(colrot * pi / 180), sin(colrot * pi / 180)
local function turn(x, y) return x * cr - y * sr, x * sin(colrot * pi / 180) + y * cr end

local function hide(self) self:visible(false) end

-- one burst slot (everything that fires on a hit)
local function Slot(slot)
	local f = Def.ActorFrame { Name = "Slot" .. slot }

	f[#f + 1] = Def.Sprite { Texture = T("FX Smoke"),
		InitCommand = function(self) self:visible(false) end,
		BurstCommand = function(self, p)
			self:finishtweening():visible(true):rotationz(rnd() * 360):zoom(0.6):diffusealpha(math.min(1, p.tier.smoke))
				:decelerate(0.65):zoom(1.25):addrotationz(45):diffusealpha(0):queuecommand("Hide")
		end, HideCommand = hide }

	f[#f + 1] = Def.Sprite { Texture = T("FX Flash"),
		InitCommand = function(self) self:blend("BlendMode_Add"):visible(false) end,
		BurstCommand = function(self, p)
			self:finishtweening():visible(true):zoom(0.45):diffusealpha(math.min(1, p.tier.flash * (p.bright and 1.1 or 1)) * 0.85)
				:decelerate(0.15):zoom(0.85):diffusealpha(0):queuecommand("Hide")
		end, HideCommand = hide }

	f[#f + 1] = Def.Sprite { Texture = T("FX Rays"),
		InitCommand = function(self) self:blend("BlendMode_Add"):visible(false) end,
		BurstCommand = function(self, p)
			if p.tier.mine then return end
			self:finishtweening():visible(true):rotationz(rnd() * 360):zoom(0.45):diffusealpha(0.85 * p.tier.flash)
				:decelerate(0.22):zoom(1.0):diffusealpha(0):queuecommand("Hide")
		end, HideCommand = hide }

	f[#f + 1] = Def.Sprite { Texture = T("FX Lightning"),
		InitCommand = function(self) self:blend("BlendMode_Add"):visible(false):SetAllStateDelays(0.03) end,
		BurstCommand = function(self, p)
			if not (p.tier.lightning or p.bright) then return end
			self:finishtweening():visible(true):setstate(floor(rnd() * 8)):rotationz(rnd() * 360):zoom(0.85)
				:diffusealpha(1):sleep(0.06):linear(0.1):zoom(0.95):diffusealpha(0):queuecommand("Hide")
		end, HideCommand = hide }

	f[#f + 1] = Def.Sprite { Texture = T("FX MineBlast"),
		InitCommand = function(self) self:blend("BlendMode_Add"):visible(false) end,
		BurstCommand = function(self, p)
			if not p.tier.mine then return end
			self:finishtweening():visible(true):zoom(0.4):diffusealpha(1):decelerate(0.3):zoom(1.2):diffusealpha(0):queuecommand("Hide")
		end, HideCommand = hide }

	-- screen-space layer: counter-rotated so gravity always pulls down the screen
	local g = Def.ActorFrame { InitCommand = function(self) self:rotationz(-colrot) end }

	for i, s in ipairs(SHARDS) do
		local tex, sx0, sy0 = s[1], s[2], s[3]
		local sx, sy = turn(sx0, sy0)            -- resting spot in screen space
		g[#g + 1] = Def.Sprite { Texture = T(tex),
			InitCommand = function(self) self:visible(false) end,
			BurstCommand = function(self, p)
				local k = p.tier.shatter
				if k <= 0 then return end
				local a = atan2(sy + 0.01, sx + 0.01) + (rnd() - 0.5) * 0.9
				local d = (55 + rnd() * 75) * k
				local spin = (rnd() * 2 - 1) * 540
				local ca, sa = cos(a), sin(a)
				local drop = 40 + rnd() * 55
				self:finishtweening():visible(true):xy(sx, sy):rotationz(colrot):zoom(1):diffusealpha(1)
					:decelerate(0.2):xy(sx + ca * d * 0.6, sy + sa * d * 0.6 - 8):rotationz(colrot + spin * 0.4)
					:accelerate(0.42):xy(sx + ca * d, sy + sa * d + drop):rotationz(colrot + spin):zoom(0.75):diffusealpha(0)
					:queuecommand("Hide")
			end, HideCommand = hide }
	end

	for i = 1, MAX_DEBRIS do
		g[#g + 1] = Def.Sprite { Texture = T("FX Debris"),
			InitCommand = function(self) self:visible(false) end,
			BurstCommand = function(self, p)
				if i > p.tier.debris then return end
				local a = rnd() * 2 * pi
				local d = 45 + rnd() * 95
				self:finishtweening():visible(true):xy(cos(a) * 5, sin(a) * 5):rotationz(rnd() * 360)
					:zoom(0.35 + rnd() * 0.55):diffusealpha(1)
					:decelerate(0.22):xy(cos(a) * d * 0.65, sin(a) * d * 0.65)
					:accelerate(0.35 + rnd() * 0.15):xy(cos(a) * d, sin(a) * d + 35 + rnd() * 45)
					:addrotationz((rnd() * 2 - 1) * 720):diffusealpha(0):queuecommand("Hide")
			end, HideCommand = hide }
	end

	for i = 1, MAX_SPARKS do
		g[#g + 1] = Def.Sprite { Texture = T("FX Spark"),
			InitCommand = function(self) self:blend("BlendMode_Add"):visible(false) end,
			BurstCommand = function(self, p)
				if i > p.tier.sparks then return end
				local a = rnd() * 2 * pi
				local d = 35 + rnd() * 70
				local z = 0.6 + rnd() * 0.7
				self:finishtweening():visible(true):rotationz(a * 180 / pi):xy(cos(a) * 8, sin(a) * 8)
					:zoomx(z):zoomy(1):diffusealpha(1)
					:decelerate(0.24):xy(cos(a) * d, sin(a) * d):zoomx(z * 0.2):diffusealpha(0):queuecommand("Hide")
			end, HideCommand = hide }
	end

	for i = 1, MAX_EMBERS do
		g[#g + 1] = Def.Sprite { Texture = T("FX Ember"),
			InitCommand = function(self) self:blend("BlendMode_Add"):visible(false) end,
			BurstCommand = function(self, p)
				if i > p.tier.embers then return end
				local a = rnd() * 2 * pi
				local d = 15 + rnd() * 35
				self:finishtweening():visible(true):xy(cos(a) * 6, sin(a) * 6):zoom(0.6 + rnd() * 0.5):diffusealpha(1)
					:decelerate(0.3):xy(cos(a) * d, sin(a) * d - 14)
					:linear(0.4 + rnd() * 0.25):addy(-26 - rnd() * 22):diffusealpha(0):queuecommand("Hide")
			end, HideCommand = hide }
	end
	f[#f + 1] = g
	return f
end

local t = Def.ActorFrame {
	InitCommand = function(self) self.cc_bright = false; self.cc_slot = 0 end,
	BrightCommand = function(self) self.cc_bright = true end,
	DimCommand = function(self) self.cc_bright = false end,
	FireCommand = function(self, p)
		self.cc_slot = self.cc_slot % SLOTS + 1
		local s = self:GetChild("Slot" .. self.cc_slot)
		if s then s:playcommand("Burst", p) end
	end,
	W1Command = function(self) self:playcommand("Fire", { tier = TIER.W1, bright = self.cc_bright }) end,
	W2Command = function(self) self:playcommand("Fire", { tier = TIER.W2, bright = self.cc_bright }) end,
	W3Command = function(self) self:playcommand("Fire", { tier = TIER.W3, bright = self.cc_bright }) end,
	W4Command = function(self) self:playcommand("Fire", { tier = TIER.W4, bright = false }) end,
	W5Command = function(self) self:playcommand("Fire", { tier = TIER.W5, bright = false }) end,
	ProW1Command = function(self) self:playcommand("W1") end,
	ProW2Command = function(self) self:playcommand("W1") end,
	ProW3Command = function(self) self:playcommand("W2") end,
	ProW4Command = function(self) self:playcommand("W3") end,
	ProW5Command = function(self) self:playcommand("W4") end,
	HeldCommand = function(self) self:playcommand("Fire", { tier = TIER.Held, bright = true }) end,
	HitMineCommand = function(self) self:playcommand("Fire", { tier = TIER.Mine, bright = true }) end,
}

-- hyper-beam charge: crackling energy ball at the receptor, pulsing rings outward
local ball = Def.ActorFrame {
	InitCommand = function(self) self:visible(false) end,
	HoldingOnCommand = function(self)
		self:stoptweening():visible(true):zoom(0.7):diffusealpha(1):decelerate(0.08):zoom(1.05)
		self:GetChild("A"):SetAllStateDelays(0.04); self:GetChild("B"):SetAllStateDelays(0.055)
		self:GetChild("R1"):playcommand("Pulse"); self:GetChild("R2"):sleep(0.14):queuecommand("Pulse")
	end,
	RollOnCommand = function(self)
		self:stoptweening():visible(true):zoom(0.7):diffusealpha(1):decelerate(0.08):zoom(1.15)
		self:GetChild("A"):SetAllStateDelays(0.022); self:GetChild("B"):SetAllStateDelays(0.03)
		self:GetChild("R1"):playcommand("Pulse"); self:GetChild("R2"):sleep(0.1):queuecommand("Pulse")
	end,
	HoldingOffCommand = function(self) self:stoptweening():decelerate(0.12):zoom(1.4):diffusealpha(0):queuecommand("Off") end,
	RollOffCommand = function(self) self:stoptweening():decelerate(0.12):zoom(1.4):diffusealpha(0):queuecommand("Off") end,
	OffCommand = function(self) self:visible(false); self:GetChild("R1"):stoptweening(); self:GetChild("R2"):stoptweening() end,
	Def.Sprite { Name = "A", Texture = T("FX HoldOrb"), InitCommand = function(self) self:blend("BlendMode_Add"):zoom(1.3) end },
	Def.Sprite { Name = "B", Texture = T("FX HoldOrb"),
		InitCommand = function(self)
			self:blend("BlendMode_Add"):rotationz(137):zoom(1.05):setstate(3)
				:diffuseshift():effectcolor1(1, 1, 1, 1):effectcolor2(1, 1, 1, 0.4):effectperiod(0.08)
		end },
	Def.Sprite { Name = "R1", Texture = T("FX Ring"),
		InitCommand = function(self) self:blend("BlendMode_Add"):diffuse(1, 0.35, 0.3, 0) end,
		PulseCommand = function(self)
			self:finishtweening():zoom(0.18):diffusealpha(1):decelerate(0.28):zoom(0.62):diffusealpha(0):queuecommand("Pulse")
		end },
	Def.Sprite { Name = "R2", Texture = T("FX Ring"),
		InitCommand = function(self) self:blend("BlendMode_Add"):diffuse(1, 0.8, 0.7, 0) end,
		PulseCommand = function(self)
			self:finishtweening():zoom(0.18):diffusealpha(0.9):decelerate(0.28):zoom(0.62):diffusealpha(0):queuecommand("Pulse")
		end },
}
t[#t + 1] = ball
for s = 1, SLOTS do t[#t + 1] = Slot(s) end
return t
