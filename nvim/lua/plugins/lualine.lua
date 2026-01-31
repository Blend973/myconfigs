return {
  "nvim-lualine/lualine.nvim",
  opts = function()
    local opts = LazyVim.opts("nvim-lualine/lualine.nvim") or {}
    opts.sections = opts.sections or {}
    opts.sections.lualine_z = opts.sections.lualine_z or {}
    table.insert(opts.sections.lualine_z, {
      function()
        return " " .. os.date("%I:%M %p")
      end,
    })
    return opts
  end,
}
