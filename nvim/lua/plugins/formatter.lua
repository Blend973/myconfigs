return {
  "stevearc/conform.nvim",
  opts = {
    formatters_by_ft = {
      python = { "ruff_format" },
      c = { "clang_format" },
      cpp = { "clang_format" },
      objc = { "clang_format" },
    },
    formatters = {
      clang_format = {
        command = "clang-format", -- or full path if needed
        args = { "--assume-filename", "$FILENAME" },
        stdin = true,
      },
      ruff_format = {
        command = "ruff", -- or "local/ruff" if that's your binary path
        args = { "format", "--stdin-filename", "$FILENAME", "-" },
        stdin = true,
      },
    },
  },
}
