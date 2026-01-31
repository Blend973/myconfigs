return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        clangd = {
          mason = false,
          cmd = {
            "clangd",
            "--background-index",
            "--clang-tidy",
            "--header-insertion=iwyu",
          },
        },
        rust_analyzer = {
          mason = false,
          cmd = { "rust-analyzer" },
        },
        -- pyright = {
        --   mason = false,
        --   cmd = { "pyright-langserver", "--stdio" },
        -- },
        ty = {
          cmd = { "ty", "server" },
          filetypes = { "python" },
          mason = false,
          root_markers = { "pyproject.toml", "setup.py", ".git" },
          settings = {
            ty = {
              diagnosticMode = "openFilesOnly", -- Example setting from ty docs
            },
          },
        },
      },
    },
  },
}
