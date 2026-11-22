-- Lab: take a screenshot every 0.37 s (odd spacing catches explosions at different moments)
local n = 0
return Def.ActorFrame {
	OnCommand = function(self) self:sleep(2.0):queuecommand("Shot") end,
	ShotCommand = function(self)
		n = n + 1
		local ok, res, path = pcall(SaveScreenshot, PLAYER_1, false, false, "cclab_", string.format("_%03d", n))
		if n <= 2 or not ok then Trace("CCLAB: shot " .. n .. " ok=" .. tostring(ok) .. " " .. tostring(res) .. " " .. tostring(path)) end
		if n < 70 then self:sleep(0.37):queuecommand("Shot") end
	end,
}
