-- Cutthroat Carnivore "Voltage" hit effects (@VARIANT@).
-- A crisp star glint and shockwave, a spray of twinkling sparkles, and on the best
-- judgments the arrow shatters along glowing cracks while red lightning forks out.
-- Three burst slots per column rotate so fast streams stack instead of cutting off.
-- Holds charge a crackling energy orb with pulsing rings.
local rnd, cos, sin, pi, floor, min = math.random, math.cos, math.sin, math.pi, math.floor, math.min
local function T(name) return NOTESKIN:GetPath("_CC", name) end

local SHARDS = {
--@SHARDS@
}

local TIER = {
	W1   = { shatter = 1.00, twinkles = 24, streaks = 10, embers = 8, lightning = true,  star = 1.00, flash = 1.00, ring = 1.00 },
	W2   = { shatter = 0.90, twinkles = 18, streaks = 8, embers = 6, lightning = true,  star = 0.90, flash = 0.90, ring = 0.90 },
	W3   = { shatter = 0.60, twinkles = 10, streaks = 5, embers = 4, lightning = false, star = 0.65, flash = 0.70, ring = 0.60 },
	W4   = { shatter = 0,    twinkles = 5, streaks = 2, embers = 2, lightning = false, star = 0.40, flash = 0.45, ring = 0.35 },
	W5   = { shatter = 0,    twinkles = 2, streaks = 0, embers = 0, lightning = false, star = 0.25, flash = 0.30, ring = 0.20 },
	Held = { shatter = 0,    twinkles = 14, streaks = 6, embers = 6, lightning = true,  star = 0.90, flash = 0.90, ring = 0.90 },
	Mine = { shatter = 0,    twinkles = 10, streaks = 8, embers = 8, lightning = true,  star = 0.50, flash = 1.00, ring = 1.00, mine = true },
}
local MAX_TWINKLES, MAX_EMBERS, MAX_STREAKS, SLOTS = 24, 8, 10, 3

local ROT = { Left = 90, Down = 0, Up = 180, Right = -90, UpLeft = 135, UpRight = -135, DownLeft = 45, DownRight = -45 }
local colrot = 0
pcall(function() colrot = ROT[Var "Button"] or 0 end)
local cr, sr = cos(colrot * pi / 180), sin(colrot * pi / 180)
local function turn(x, y) return x * cr - y * sr, x * sr + y * cr end
local function hide(self) self:visible(false) end
-- the column's direction colour (same as the note rims) tints the sparkle layers
local COL = {
	Left = { 0.88, 0.32, 1.0 }, Down = { 0.12, 0.86, 1.0 }, Up = { 1, 1, 1 }, Right = { 1.0, 0.55, 0.08 },
	UpLeft = { 0.88, 0.32, 1.0 }, UpRight = { 1.0, 0.55, 0.08 },
	DownLeft = { 0.12, 0.86, 1.0 }, DownRight = { 1, 1, 1 }, Center = { 1.0, 0.9, 0.2 },
}
local dc = { 1, 1, 1 }
pcall(function() dc = COL[Var "Button"] or dc end)
local function dtint(self, k) -- k = 0 direction colour .. 1 white
	self:diffuse(dc[1] + (1 - dc[1]) * k, dc[2] + (1 - dc[2]) * k, dc[3] + (1 - dc[3]) * k, 1)
end
local function add(self) self:blend("BlendMode_Add"):visible(false) end

local function Slot(slot)
	local f = Def.ActorFrame { Name = "Slot" .. slot }

	f[#f + 1] = Def.Sprite { Texture = T("FX Flash"), InitCommand = add,
		BurstCommand = function(self, p)
			self:finishtweening():visible(true):zoom(0.4):diffusealpha(min(1, p.tier.flash))
				:decelerate(0.16):zoom(0.9):diffusealpha(0):queuecommand("Hide")
		end, HideCommand = hide }

	f[#f + 1] = Def.Sprite { Texture = T("FX ArrowGlow"), InitCommand = add,
		BurstCommand = function(self, p)
			if p.tier.mine then return end
			dtint(self, 0.25)
			self:finishtweening():visible(true):zoom(1.0):diffusealpha(min(1, p.tier.flash))
				:decelerate(0.24):zoom(1.5):diffusealpha(0):queuecommand("Hide")
		end, HideCommand = hide }

	f[#f + 1] = Def.Sprite { Texture = T("FX RingW"), InitCommand = add,
		BurstCommand = function(self, p)
			dtint(self, 0.1)
			self:finishtweening():visible(true):zoom(0.3):diffusealpha(p.tier.ring)
				:decelerate(0.3):zoom(0.8 + 0.3 * p.tier.ring):diffusealpha(0):queuecommand("Hide")
		end, HideCommand = hide }

	f[#f + 1] = Def.Sprite { Texture = T("FX Ring"), InitCommand = add,
		BurstCommand = function(self, p)
			self:finishtweening():visible(true):zoom(0.22):diffusealpha(p.tier.ring)
				:decelerate(0.26):zoom(0.62 + 0.25 * p.tier.ring):diffusealpha(0):queuecommand("Hide")
		end, HideCommand = hide }

	f[#f + 1] = Def.Sprite { Texture = T("FX Lightning"),
		InitCommand = function(self) add(self); self:animate(false) end,
		BurstCommand = function(self, p)
			if not (p.tier.lightning or p.bright) then return end
			self:finishtweening():visible(true):setstate(floor(rnd() * 8)):rotationz(rnd() * 360):zoom(0.78)
				:diffusealpha(1):sleep(0.05):linear(0.11):zoom(0.9):diffusealpha(0):queuecommand("Hide")
		end, HideCommand = hide }

	f[#f + 1] = Def.Sprite { Texture = T("FX MineBlast"), InitCommand = add,
		BurstCommand = function(self, p)
			if not p.tier.mine then return end
			self:finishtweening():visible(true):rotationz(rnd() * 360):zoom(0.35):diffusealpha(1)
				:decelerate(0.3):zoom(1.15):diffusealpha(0):queuecommand("Hide")
		end, HideCommand = hide }

	-- the star glint: a hard four-point flare, then a smaller one crossed at 45 degrees
	for k = 1, 2 do
		f[#f + 1] = Def.Sprite { Texture = T("FX Star"), InitCommand = add,
			BurstCommand = function(self, p)
				local s = p.tier.star * (k == 1 and 1 or 0.6)
				self:finishtweening():visible(true):rotationz((k - 1) * 45 + rnd() * 10 - 5)
					:zoom(0.2 * s):diffusealpha(1):sleep((k - 1) * 0.03)
					:decelerate(0.07):zoom(0.95 * s):accelerate(0.2):zoom(0.15 * s):diffusealpha(0)
					:queuecommand("Hide")
			end, HideCommand = hide }
	end

	-- screen-space layer: counter-rotated so gravity always pulls down the screen
	local g = Def.ActorFrame { InitCommand = function(self) self:rotationz(-colrot) end }

	for _, s in ipairs(SHARDS) do
		local sx, sy = turn(s[2], s[3])
		g[#g + 1] = Def.Sprite { Texture = T(s[1]),
			InitCommand = function(self) self:visible(false) end,
			BurstCommand = function(self, p)
				local k = p.tier.shatter
				if k <= 0 then return end
				local a = math.atan2(sy + 0.01, sx + 0.01) + (rnd() - 0.5) * 0.8
				local d = (50 + rnd() * 70) * k
				local spin = (rnd() * 2 - 1) * 480
				local ca, sa = cos(a), sin(a)
				local drop = 35 + rnd() * 50
				self:finishtweening():visible(true):xy(sx, sy):rotationz(colrot):zoom(1):diffusealpha(1)
					:decelerate(0.18):xy(sx + ca * d * 0.6, sy + sa * d * 0.6 - 6):rotationz(colrot + spin * 0.4)
					:accelerate(0.4):xy(sx + ca * d, sy + sa * d + drop):rotationz(colrot + spin)
					:zoom(0.7):diffusealpha(0):queuecommand("Hide")
			end, HideCommand = hide }
	end

	for i = 1, MAX_TWINKLES do
		g[#g + 1] = Def.Sprite { Texture = T("FX TwinkleW"), InitCommand = add,
			BurstCommand = function(self, p)
				if i > p.tier.twinkles then return end
				dtint(self, rnd() * 0.6)
				local a = rnd() * 2 * pi
				local d = 28 + rnd() * 62
				local z = 0.7 + rnd() * 0.9
				self:finishtweening():visible(true):xy(cos(a) * 6, sin(a) * 6):rotationz(rnd() * 90)
					:zoom(z):diffusealpha(1)
					:decelerate(0.26 + rnd() * 0.1):xy(cos(a) * d, sin(a) * d):addrotationz(90 + rnd() * 90)
					:linear(0.12):zoom(z * 1.25):linear(0.14):zoom(0):diffusealpha(0):queuecommand("Hide")
			end, HideCommand = hide }
	end

	for i = 1, MAX_STREAKS do
		g[#g + 1] = Def.Sprite { Texture = T("FX TwinkleW"), InitCommand = add,
			BurstCommand = function(self, p)
				if i > (p.tier.streaks or 0) then return end
				dtint(self, 0.35)
				local a = rnd() * 2 * pi
				local d = 55 + rnd() * 55
				self:finishtweening():visible(true):rotationz(a * 180 / pi):xy(cos(a) * 10, sin(a) * 10)
					:zoomx(3.2):zoomy(0.45):diffusealpha(1)
					:decelerate(0.22):xy(cos(a) * d, sin(a) * d):zoomx(0.6):zoomy(0.2):diffusealpha(0)
					:queuecommand("Hide")
			end, HideCommand = hide }
	end

	for i = 1, MAX_EMBERS do
		g[#g + 1] = Def.Sprite { Texture = T("FX Ember"), InitCommand = add,
			BurstCommand = function(self, p)
				if i > p.tier.embers then return end
				local a = rnd() * 2 * pi
				local d = 14 + rnd() * 30
				self:finishtweening():visible(true):xy(cos(a) * 6, sin(a) * 6):zoom(0.7 + rnd() * 0.6):diffusealpha(1)
					:decelerate(0.28):xy(cos(a) * d, sin(a) * d - 12)
					:linear(0.38 + rnd() * 0.22):addy(-24 - rnd() * 20):diffusealpha(0):queuecommand("Hide")
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
	W3Command = function(self) self:playcommand("Fire", { tier = TIER.W3, bright = false }) end,
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

-- hold charge: crackling energy orb at the receptor with rings pulsing outward
local ball = Def.ActorFrame {
	InitCommand = function(self) self:visible(false) end,
	HoldingOnCommand = function(self)
		self:stoptweening():visible(true):zoom(0.7):diffusealpha(1):decelerate(0.08):zoom(1.05)
		self:GetChild("R1"):playcommand("Pulse"); self:GetChild("R2"):sleep(0.14):queuecommand("Pulse")
	end,
	RollOnCommand = function(self) self:playcommand("HoldingOn"); self:zoom(1.15) end,
	HoldingOffCommand = function(self) self:stoptweening():decelerate(0.12):zoom(1.4):diffusealpha(0):queuecommand("Off") end,
	RollOffCommand = function(self) self:playcommand("HoldingOff") end,
	OffCommand = function(self) self:visible(false); self:GetChild("R1"):stoptweening(); self:GetChild("R2"):stoptweening() end,
	Def.Sprite { Name = "A", Texture = T("FX HoldOrb"),
		InitCommand = function(self) self:blend("BlendMode_Add"):zoom(1.25):SetAllStateDelays(0.04) end },
	Def.Sprite { Name = "B", Texture = T("FX HoldOrb"),
		InitCommand = function(self)
			self:blend("BlendMode_Add"):rotationz(137):zoom(1.0):setstate(3):SetAllStateDelays(0.055)
				:diffuseshift():effectcolor1(1, 1, 1, 1):effectcolor2(1, 1, 1, 0.45):effectperiod(0.08)
		end },
	Def.Sprite { Name = "R1", Texture = T("FX Ring"),
		InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0) end,
		PulseCommand = function(self)
			self:finishtweening():zoom(0.16):diffusealpha(1):decelerate(0.28):zoom(0.58):diffusealpha(0):queuecommand("Pulse")
		end },
	Def.Sprite { Name = "R2", Texture = T("FX Ring"),
		InitCommand = function(self) self:blend("BlendMode_Add"):diffusealpha(0) end,
		PulseCommand = function(self)
			self:finishtweening():zoom(0.16):diffusealpha(0.85):decelerate(0.28):zoom(0.58):diffusealpha(0):queuecommand("Pulse")
		end },
}
t[#t + 1] = ball
for s = 1, SLOTS do t[#t + 1] = Slot(s) end
return t
