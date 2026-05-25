return {
  {
    "catppuccin/nvim",
    name = "catppuccin",
    lazy = false, -- ensure it's available when LazyVim sets colorscheme
    opts = {
      flavour = "mocha", -- or latte/frappe/latte
      transparent_background = true, -- enable plugin-level transparency
      float = {
        transparent = true, -- enable transparent floating windows
        solid = true, -- use solid styling for floating windows, see |winborder|
      },
    },
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "catppuccin-mocha",
    },
  },
}

-- return {
--   require("tokyonight").setup({
--     style = "moon",
--     transparent = true,
--     -- on_colors = function(colors)
--     --   colors.bg = "#000000"
--     -- end,
--   }),
-- }
