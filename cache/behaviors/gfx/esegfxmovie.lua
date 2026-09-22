module("EseGFxMovie", package.seeall)

-- Dummy implementation
function OnGFxFileLoad(selfID, strm)
end

function OnGFxFileDestroyed(selfID, strm)
end
-- Behavior
function OnPropertyUpdate(selfID, strm)
   if BehaviorAPI.HasMixin(selfID, "GFxInputRouter") == BehaviorAPI.ec_Yes then
   --   BehaviorAPI.SetProperty(selfID, "FocusInput", selfID)
   --   epgmGFx.SetInputFocus(selfID)
   end
end
