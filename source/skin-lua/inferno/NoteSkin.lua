-- Cutthroat Carnivore noteskin - element router.
-- Every column is drawn from the Down artwork and rotated into place, so one set of
-- textures serves dance (4 panel), solo (6 panel) and anything else that asks.
local CC = {}

CC.Rotate = {
	Left = 90, Down = 0, Up = 180, Right = -90,
	UpLeft = 135, UpRight = -135, DownLeft = 45, DownRight = -45,
	Center = 0,
}

-- Elements that reuse another element's graphics.
CC.Redir = {
	["Tap Fake"] = "Tap Note",
	["Hold Head Active"] = "Tap Note",
	["Hold Head Inactive"] = "Tap Note",
	["Roll Head Active"] = "Tap Note",
	["Roll Head Inactive"] = "Tap Note",
	["Hold LiftTail Active"] = "Tap Lift",
	["Hold LiftTail Inactive"] = "Tap Lift",
	["Roll LiftTail Active"] = "Tap Lift",
	["Roll LiftTail Inactive"] = "Tap Lift",
	["Hold Explosion"] = "Explosion",
	["Roll Explosion"] = "Explosion",
	["Tap Explosion Bright"] = "Explosion",
	["Tap Explosion Dim"] = "Explosion",
}

-- Elements turned to face their column.
CC.Turn = {
	["Tap Note"] = true, ["Tap Fake"] = true, ["Tap Lift"] = true, ["Tap Mine"] = true,
	["Hold Head Active"] = true, ["Hold Head Inactive"] = true,
	["Roll Head Active"] = true, ["Roll Head Inactive"] = true,
	["Receptor"] = true, ["Explosion"] = true,
}

-- Hold/roll tails are not drawn (the bottom cap is the tail).
CC.Blank = {
	["Hold Tail Active"] = true, ["Hold Tail Inactive"] = true,
	["Roll Tail Active"] = true, ["Roll Tail Inactive"] = true,
}

function CC.Load()
	local sButton = Var "Button"
	local sElement = Var "Element"

	if CC.Blank[sElement] then
		if Var "SpriteOnly" then
			return LoadActor(NOTESKIN:GetPath("", "_blank"))
		end
		return Def.Actor {}
	end

	local element = CC.Redir[sElement] or sElement
	local t = LoadActor(NOTESKIN:GetPath("Down", element))

	if CC.Turn[sElement] then
		t.BaseRotationZ = CC.Rotate[sButton] or 0
	end
	return t
end

return CC
