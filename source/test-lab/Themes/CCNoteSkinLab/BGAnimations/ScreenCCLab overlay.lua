-- Lab: reads Save/cclab.txt  "song folder substring|noteskin|difficulty"
-- checks the theme-style noteskin preview path, then starts autoplay gameplay.
local function readfile(p)
	local f = RageFileUtil.CreateRageFile()
	if not f:Open(p, 1) then f:destroy() return nil end
	local s = f:Read(); f:Close(); f:destroy(); return s
end
return Def.ActorFrame {
	OnCommand = function(self) self:sleep(1):queuecommand("Go") end,
	GoCommand = function(self)
		local cfg = (readfile("Save/cclab.txt") or ""):gsub("%s+$", "")
		local want, skin, diff = cfg:match("^(.-)|(.-)|(.-)$")
		Trace("CCLAB: config " .. tostring(cfg))
		-- the same call Simply Love's NoteSkinPreview uses
		for _, b in ipairs({ "Left", "Down", "Up", "Right" }) do
			local ok, a = pcall(NOTESKIN.LoadActorForNoteSkin, NOTESKIN, b, "Tap Note", skin)
			Trace("CCLAB: preview " .. b .. " ok=" .. tostring(ok) .. " actor=" .. tostring(a ~= nil))
		end
		Trace("CCLAB: skin exists=" .. tostring(NOTESKIN:DoesNoteSkinExist(skin)))
		local song
		for _, s in ipairs(SONGMAN:GetAllSongs()) do
			if s:GetSongDir():find(want, 1, true) then song = s break end
		end
		if not song then Trace("CCLAB: song not found " .. want) return end
		GAMESTATE:JoinPlayer(PLAYER_1)
		GAMESTATE:SetCurrentPlayMode("PlayMode_Regular")
		GAMESTATE:SetCurrentStyle("single")
		GAMESTATE:SetCurrentSong(song)
		local pick
		for _, st in ipairs(song:GetStepsByStepsType("StepsType_Dance_Single")) do
			pick = pick or st
			if st:GetDifficulty() == diff then pick = st end
		end
		GAMESTATE:SetCurrentSteps(PLAYER_1, pick)
		for _, lvl in ipairs({ "ModsLevel_Preferred", "ModsLevel_Stage", "ModsLevel_Song", "ModsLevel_Current" }) do
			pcall(function()
				local po = GAMESTATE:GetPlayerState(PLAYER_1):GetPlayerOptions(lvl)
				po:NoteSkin(skin); po:CMod(420)
			end)
		end
		Trace("CCLAB: starting " .. song:GetSongDir() .. " " .. tostring(pick and pick:GetDifficulty()))
		SCREENMAN:SetNewScreen("ScreenGameplay")
	end,
}
