local hook = require 'core/hook'
hook.script_post_init:register('intentional probe failure', function()
  error('intentional hook failure')
end)
function init() end
function redraw() screen.clear(); screen.update() end
