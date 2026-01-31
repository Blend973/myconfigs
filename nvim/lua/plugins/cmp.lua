return {
  {
    "saghen/blink.cmp",
    opts = {
      keymap = {
        preset = nil,
        ["<Tab>"] = { "select_next", "accept", "fallback" },
        ["<S-Tab>"] = { "select_prev", "fallback" },
        ["<CR>"] = { "accept", "fallback" },
        ["<C-y>"] = { "select_and_accept" },
      },
    },
  },
}